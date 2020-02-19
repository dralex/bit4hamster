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
 
def update_level(nu):
    n = int(nu / 200) + 1
    for i in range(5):
        if i < n:
            m.display.set_pixel(i, 0, 9)
        else:
            m.display.set_pixel(i, 0, 0)

baseline = m.compass.get_field_strength() # Take a baseline reading of magnetic strength
num = 0
crossing = False

update_level(num)
while True:
    field = m.compass.get_field_strength()

    if not crossing and abs(field - baseline) > THRESHOLD:
        crossing = True    
        num = num + 1
        m.display.set_pixel(2, 2, 9)
        update_level(num)   
    elif crossing and abs(field - baseline) <= THRESHOLD:
        crossing = False
        m.display.set_pixel(2, 2, 0)

    if m.button_a.was_pressed():
	m.display.show(num, wait = False, loop = True)
    elif m.button_b.was_pressed():
	baseline = m.compass.get_field_strength() # Take a baseline reading of magnetic strength
        num = 0
        crossing = False
        m.display.clear()
        update_level(num)

