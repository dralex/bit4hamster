# -----------------------------------------------------------------------------
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# bit4hamster collection
#
# Hamster magnet counter program
#
# Author: Alexey Fedoseev <aleksey@fedoseev.net>, 2020
# -----------------------------------------------------------------------------

import microbit as m

# Choose the appropriate value based on the cage & wheel configuration
THRESHOLD = 13000
  
baseline = m.compass.get_field_strength() # Take a baseline reading of magnetic strength
num = 0
crossing = False

while True:
    field = m.compass.get_field_strength()

    if not crossing and abs(field - baseline) > THRESHOLD:
	    crossing = True    
            num = num + 1
    elif crossing:
        if abs(field - baseline) <= THRESHOLD:
            crossing = False
            m.display.clear()
        else:
            m.display.set_pixel(2, 2, 9)

    if m.button_a.was_pressed():
	m.display.show(num, wait = False, loop = True)
    elif m.button_b.was_pressed():
	baseline = m.compass.get_field_strength() # Take a baseline reading of magnetic strength
        num = 0
        crossing = False
        m.display.clear()

