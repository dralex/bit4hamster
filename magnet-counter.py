# -----------------------------------------------------------------------------
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# bit4hamster collection
#
# Hamster magnet counter program
#
# Author: Alexey Fedoseev <aleksey@fedoseev.net>, 2020
# -----------------------------------------------------------------------------

import time
import os
import microbit as m

# Choose the appropriate value based on the cage & wheel configuration
THRESHOLD = 13000
FILENAME = 'log{}.txt'
MEMORY_LIMIT = 400
baseline = num = crossing = show_num = file_num = last_change = time_to_sync = time_buf = None

def update_display():
    if show_num:
        m.display.show(num, wait=False, loop=True)
    else:
        m.display.set_pixel(2, 2, 9 if crossing else 0)
        n = file_num + 1
        if n > 5:
            for i in range(5):
                m.display.set_pixel(i, 0, 9)
            n = n - 5
            y = 1
        else:
            for i in range(5):
                m.display.set_pixel(i, 1, 0)
            y = 0
        for i in range(5):
            if i < n:
                m.display.set_pixel(i, y, 9)
            else:
                m.display.set_pixel(i, y, 0)

def remove_files():
    ll = os.listdir()
    for f in ll:
        os.remove(f)

def sync_buf():
    global file_num, time_to_sync, time_buf
    f = open(FILENAME.format(file_num), 'w')
    for t in time_buf:
        f.write("{}\n".format(t))
    f.close()
    file_num += 1
    time_to_sync = False
    time_buf = []

def save_current_time():
    global last_change, time_buf
    last_change = time.ticks_ms()
    time_buf.append(last_change)

def reset():
    global baseline, num, crossing, show_num, file_num, time_to_sync, time_buf
    baseline = m.compass.get_field_strength() # Take a baseline reading of magnetic strength
    num = 0
    crossing = False
    show_num = False
    file_num = 0
    time_to_sync = False
    time_buf = []
    save_current_time()
    m.display.clear()
    update_display()

reset()
while True:
    field = m.compass.get_field_strength()

    if not crossing and abs(field - baseline) > THRESHOLD:
        crossing = True
        num = num + 1
        save_current_time()
        time_to_sync = len(time_buf) > MEMORY_LIMIT
        update_display()
    elif crossing and abs(field - baseline) <= THRESHOLD:
        crossing = False
        update_display()

    if time_to_sync and time.ticks_ms() - last_change > 3000: # sync on 3 sec delay
        sync_buf()

    if m.button_a.was_pressed():
        show_num = not show_num
        if not show_num:
            m.display.clear()
        update_display()
    elif m.button_b.was_pressed():
        remove_files()
        reset()
