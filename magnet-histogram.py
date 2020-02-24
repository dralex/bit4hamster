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
import microbit as m

# Choose the appropriate value based on the cage & wheel configuration
THRESHOLD = 13000
TIME_LIMIT = 400
SYNC_TIME = 3600000 # 1 hour
FILENAME = 'histogram.txt'
HIST_STEPS = 25
HIST_DELTA = 0.1
HIST_ROUND_SIGNS = 1
baseline = num = crossing = show_num = last_change = hist_dict = last_sync = None

def update_display():
    if show_num:
        m.display.show(num, wait=False, loop=True)
    else:
        m.display.set_pixel(0, 4, 9)
        m.display.set_pixel(4, 4, 9 if crossing else 0)

def reset():
    global baseline, num, crossing, show_num, last_change, hist_dict, last_sync
    baseline = m.compass.get_field_strength() # Take a baseline reading of magnetic strength
    num = 0
    crossing = False
    show_num = False
    hist_dict = [0] * HIST_STEPS
    last_change = last_sync = time.ticks_ms()
    m.display.clear()
    update_display()

def save_hist_value(d):
    global hist_dict
    index = int((1000.0 / d) / HIST_DELTA)
    if index >= HIST_STEPS:
        index = HIST_STEPS - 1
    hist_dict[index] += 1

def sync_hist():
    f = open(FILENAME, 'w')
    for i in range(HIST_STEPS):
        f.write("{} {}\n".format(i * HIST_DELTA, hist_dict[i]))
    f.close()
    last_sync = time.ticks_ms()

reset()
while True:
    field = m.compass.get_field_strength()
    t = time.ticks_ms()

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

    if t - last_sync > SYNC_TIME:
        sync_hist()

    if m.button_a.was_pressed():
        show_num = not show_num
        if not show_num:
            m.display.clear()
        update_display()
    elif m.button_b.was_pressed():
        reset()
