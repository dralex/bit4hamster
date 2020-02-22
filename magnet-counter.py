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
import microbit as m

# Choose the appropriate value based on the cage & wheel configuration
THRESHOLD = 13000
TIME_LIMIT = 300
baseline = num = crossing = show_num = last_change = None

def update_display():
    if show_num:
        m.display.show(num, wait=False, loop=True)
    else:
        m.display.set_pixel(4, 0, 9)
        m.display.set_pixel(4, 4, 9 if crossing else 0)

def reset():
    global baseline, num, crossing, show_num, last_change
    baseline = m.compass.get_field_strength() # Take a baseline reading of magnetic strength
    num = 0
    crossing = False
    show_num = False
    last_change = time.ticks_ms()
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
            last_change = t
        update_display()
    elif crossing and abs(field - baseline) <= THRESHOLD:
        crossing = False
        update_display()

    if m.button_a.was_pressed():
        show_num = not show_num
        if not show_num:
            m.display.clear()
        update_display()
    elif m.button_b.was_pressed():
        reset()
