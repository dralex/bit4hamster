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
import microbit as m # pylint: disable=import-error

# Choose the appropriate value based on the cage & wheel configuration
THRESHOLD = 12000
TIME_LIMIT = 400
INTERVAL_DELAY = 2500
SYNC_DELAY = 3000 # sync on 3 sec delay
SYNC_MAND_DELAY = 3600000 # 1 hour delay - sync mandatory
FULL_FILENAME = 'fulllog{}.txt'
LOG_FILENAME = 'log{}.txt'
HIST_FILENAME = 'histogram{}.txt'
MEMORY_LIMIT = 100
MEMORY_TO_SYNC = MEMORY_LIMIT / 2
HIST_STEPS = 250
HIST_DELTA = 0.01
HIST_ROUND_SIGNS = 1
baseline = num = crossing = show_num = file_num = last_change = None
time_to_sync = time_buf = buf_size = last_sync = int_start = int_num = None
fullfile_num = num_buf = hist_dict = None

def update_display():
    if show_num:
        m.display.show('{}.'.format(num), wait=False, loop=True)
    else:
        file_rows = int(fullfile_num / 5)
        file_columns = fullfile_num % 5

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
    global file_num, fullfile_num # pylint: disable=global-statement
    ll = os.listdir()
    fullfile_num = file_num = len(ll)

def remove_files():
    ll = os.listdir()
    for f in ll:
        os.remove(f)

def sync_buf():
    global fullfile_num, time_to_sync, time_buf, buf_size, last_sync # pylint: disable=global-statement
    f = open(FULL_FILENAME.format(fullfile_num), 'w')
    for i in range(buf_size):
        i_st, i_end, i_num = time_buf[i * 3: (i + 1) * 3]
        f.write("{} {} {}\n".format(i_st, i_end, i_num))
    f.close()
    num_buf.append((last_sync, num))
    f = open(LOG_FILENAME.format(file_num), 'w')
    for tm, n in num_buf:
        f.write("{} {}\n".format(tm, n))
    f.close()
    f = open(HIST_FILENAME.format(file_num), 'w')
    for i in range(HIST_STEPS):
        f.write("{} {}\n".format(i * HIST_DELTA, hist_dict[i]))
    f.close()
    fullfile_num += 1
    time_to_sync = False
    last_sync = time.ticks_ms() # pylint: disable=no-member
    buf_size = 0

def save_hist_value(d):
    global hist_dict # pylint: disable=global-statement
    index = int((1000.0 / d) / HIST_DELTA)
    if index >= HIST_STEPS:
        index = HIST_STEPS - 1
    hist_dict[index] += 1

def save_interval(t_a, t_b, n):
    global time_buf, buf_size, time_to_sync # pylint: disable=global-statement
    idx = buf_size * 3
    time_buf[idx] = t_a
    time_buf[idx + 1] = t_b
    time_buf[idx + 2] = n
    buf_size += 1
    if not time_to_sync:
        time_to_sync = buf_size > MEMORY_TO_SYNC

def reset():
    global baseline, num, crossing, show_num, time_to_sync, time_buf # pylint: disable=global-statement
    global last_change, buf_size, last_sync, int_num, int_start # pylint: disable=global-statement
    global num_buf, hist_dict # pylint: disable=global-statement
    baseline = m.compass.get_field_strength() # Take a baseline reading of magnetic strength
    num = int_num = 0
    crossing = False
    show_num = False
    calculate_files()
    time_to_sync = False
    num_buf = []
    if hist_dict:
        for i in range(HIST_STEPS):
            hist_dict[i] = 0 # pylint: disable=unsupported-assignment-operation
    else:
        hist_dict = [0] * HIST_STEPS
    buf_size = 0
    if time_buf is None:
        time_buf = [0] * MEMORY_LIMIT * 3
    last_change = int_start = last_sync = time.ticks_ms() # pylint: disable=no-member
    m.display.clear()
    update_display()

reset()
while True:
    field = m.compass.get_field_strength()
    t = time.ticks_ms() # pylint: disable=no-member
    delta = t - last_change

    if not crossing and abs(field - baseline) > THRESHOLD:
        crossing = True
        if delta > TIME_LIMIT:
            if delta > INTERVAL_DELAY:
                save_interval(int_start, last_change, num - int_num)
                int_start = t
                int_num = num
            num = num + 1
            save_hist_value(delta)
            last_change = t
        update_display()
    elif crossing and abs(field - baseline) <= THRESHOLD:
        crossing = False
        update_display()

    if t - last_sync > SYNC_MAND_DELAY:
        time_to_sync = True

    if buf_size == MEMORY_LIMIT or time_to_sync and delta > SYNC_DELAY:
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
