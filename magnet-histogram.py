# -----------------------------------------------------------------------------
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# bit4hamster collection
#
# Hamster magnet frequency histogram program
#
# Author: Alexey Fedoseev <aleksey@fedoseev.net>, 2020
# -----------------------------------------------------------------------------

import time
import os
import microbit as m # pylint: disable=import-error

# Choose the appropriate value based on the cage & wheel configuration
THRESHOLD = 12500
TIME_LIMIT = 400
SYNC_TIME = 1800000 # 30 min
LOG_FILENAME = 'log{}.txt'
HIST_FILENAME = 'histogram{}.txt'
HIST_STEPS = 250
HIST_DELTA = 0.01
HIST_ROUND_SIGNS = 1
baseline = num = crossing = show_num = last_change = None
num_buf = hist_dict = last_sync = file_num = None

def update_display():
    if show_num:
        m.display.show('{}.'.format(num), wait=False, loop=True)
    else:
        m.display.set_pixel(0, 4, 9)
        m.display.set_pixel(4, 4, 9 if crossing else 0)

def calculate_files():
    global file_num # pylint: disable=global-statement
    ll = os.listdir()
    file_num = int(len(ll) / 2)

def reset():
    global baseline, num, crossing, show_num, last_change, num_buf, hist_dict, last_sync # pylint: disable=global-statement
    baseline = m.compass.get_field_strength() # Take a baseline reading of magnetic strength
    num = 0
    crossing = False
    show_num = False
    num_buf = []
    hist_dict = [0] * HIST_STEPS
    last_change = last_sync = time.ticks_ms() # pylint: disable=no-member
    calculate_files()
    m.display.clear()
    update_display()

def save_hist_value(d):
    global hist_dict # pylint: disable=global-statement
    index = int((1000.0 / d) / HIST_DELTA)
    if index >= HIST_STEPS:
        index = HIST_STEPS - 1
    hist_dict[index] += 1

def sync_data():
    global last_sync # pylint: disable=global-statement
    num_buf.append((last_sync, num))
    f = open(LOG_FILENAME.format(file_num), 'w')
    for tm, n in num_buf:
        f.write("{} {}\n".format(tm, n))
    f.close()
    f = open(HIST_FILENAME.format(file_num), 'w')
    for i in range(HIST_STEPS):
        f.write("{} {}\n".format(i * HIST_DELTA, hist_dict[i]))
    f.close()
    last_sync = time.ticks_ms() # pylint: disable=no-member

reset()
while True:
    field = m.compass.get_field_strength()
    t = time.ticks_ms() # pylint: disable=no-member

    if not crossing and abs(field - baseline) > THRESHOLD:
        crossing = True
        delta = t - last_change
        if delta > TIME_LIMIT:
            num = num + 1
            save_hist_value(delta)
            last_change = t
        update_display()
    elif crossing and abs(field - baseline) <= THRESHOLD:
        crossing = False
        update_display()

    if t - last_sync >= SYNC_TIME:
        sync_data()

    if m.button_a.was_pressed():
        show_num = not show_num
        if not show_num:
            m.display.clear()
        update_display()
    elif m.button_b.was_pressed():
        reset()
