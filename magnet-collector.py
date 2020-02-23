# -----------------------------------------------------------------------------
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# bit4hamster collection
#
# Hamster magnet data collection program
#
# Author: Alexey Fedoseev <aleksey@fedoseev.net>, 2020
# -----------------------------------------------------------------------------

import time
import os
import microbit as m

# Choose the appropriate value based on the cage & wheel configuration
THRESHOLD = 13000
TIME_LIMIT = 400
SYNC_DELAY = 3000 # sync on 3 sec delay
FILENAME = 'log{}.txt'
MEMORY_LIMIT = 500
MEMORY_TO_SYNC = MEMORY_LIMIT / 2
baseline = num = crossing = show_num = file_num = last_change = None
time_to_sync = time_buf = buf_size = None

def update_display():
    if show_num:
        m.display.show(num, wait=False, loop=True)
    else:
        file_rows = int(file_num / 5)
        file_columns = file_num % 5

        for i in range(5):
            if i < file_rows:
                for j in range(5):
                    m.display.set_pixel(j, i, 9)
            elif i == file_rows:
                for j in range(5):
                    if j <= file_columns:
                        m.display.set_pixel(j, i, 9)
                    else:
                        m.display.set_pixel(j, i, 0)
            else:
                for j in range(5):
                    m.display.set_pixel(j, i, 0)

        m.display.set_pixel(4, 4, 9 if crossing else 0)

def calculate_files():
    global file_num
    ll = os.listdir()
    file_num = len(ll)

def remove_files():
    ll = os.listdir()
    for f in ll:
        os.remove(f)

def sync_buf():
    global file_num, time_to_sync, time_buf, buf_size
    f = open(FILENAME.format(file_num), 'w')
    for i in range(buf_size):
        f.write("{}\n".format(time_buf[i]))
    f.close()
    file_num += 1
    time_to_sync = False
    buf_size = 0

def save_current_time():
    global last_change, time_buf, buf_size
    last_change = time.ticks_ms()
    time_buf[buf_size] = last_change
    buf_size += 1

def reset():
    global baseline, num, crossing, show_num, time_to_sync, time_buf, buf_size
    baseline = m.compass.get_field_strength() # Take a baseline reading of magnetic strength
    num = 0
    crossing = False
    show_num = False
    calculate_files()
    time_to_sync = False
    buf_size = 0
    time_buf = [0] * MEMORY_LIMIT
    save_current_time()
    m.display.clear()
    update_display()

reset()
while True:
    field = m.compass.get_field_strength()
    t = time.ticks_ms()

    if not crossing and abs(field - baseline) > THRESHOLD:
        crossing = True
        if t - last_change > TIME_LIMIT:
            num = num + 1
            save_current_time()
            time_to_sync = len(time_buf) > MEMORY_TO_SYNC
        update_display()
    elif crossing and abs(field - baseline) <= THRESHOLD:
        crossing = False
        update_display()

    if buf_size == MEMORY_LIMIT or (time_to_sync and t - last_change > SYNC_DELAY):
        sync_buf()
        update_display()

    if m.button_a.was_pressed():
        show_num = not show_num
        if not show_num:
            m.display.clear()
        update_display()
    elif m.button_b.was_pressed():
        remove_files()
        reset()
