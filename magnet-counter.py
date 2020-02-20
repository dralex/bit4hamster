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
FILENAME = 'log.txt'
baseline = num = crossing = show_num = time_buf = None

def update_display():
    if show_num:
        m.display.show(num, wait=False, loop=True)
    else:
        m.display.set_pixel(2, 2, 9 if crossing else 0)
        n = int(num / 400) + 1
        for i in range(5):
            if i < n:
                m.display.set_pixel(i, 0, 9)
            else:
                m.display.set_pixel(i, 0, 0)

def sync_buf():
    f = open(FILENAME, 'w')
    for t in time_buf:
        f.write("{}\n".format(t))
    f.close()

def save_current_time():
    global time_buf
    time_buf.append(time.ticks_ms())

def reset():
    global baseline, num, crossing, show_num, time_buf
    baseline = m.compass.get_field_strength() # Take a baseline reading of magnetic strength
    num = 0
    crossing = False
    show_num = False
    time_buf = []
    save_current_time()
    sync_buf()
    m.display.clear()
    update_display()

reset()
while True:
    field = m.compass.get_field_strength()

    if not crossing and abs(field - baseline) > THRESHOLD:
        crossing = True
        num = num + 1
        save_current_time()
        update_display()
    elif crossing and abs(field - baseline) <= THRESHOLD:
        crossing = False
        update_display()

    if m.button_a.was_pressed():
        show_num = not show_num
        if not show_num:
            m.display.clear()
        sync_buf()
        update_display()
    elif m.button_b.was_pressed():
        reset()
