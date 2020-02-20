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
    n = int(nu / 400) + 1
    for i in range(5):
	if i < n:
	    m.display.set_pixel(i, 0, 9)
	else:
	    m.display.set_pixel(i, 0, 0)

def update_display(to, cr, nu):
    if to:
        m.display.show(nu, wait = False, loop = True)
    else:
        m.display.set_pixel(2, 2, 9 if cr else 0)
        update_level(nu)

baseline = m.compass.get_field_strength() # Take a baseline reading of magnetic strength
num = 0
crossing = False
show_num = False
update_display(show_num, crossing, num)

while True:
    field = m.compass.get_field_strength()

    if not crossing and abs(field - baseline) > THRESHOLD:
	crossing = True	   
	num = num + 1
	update_display(show_num, crossing, num)
    elif crossing and abs(field - baseline) <= THRESHOLD:
	crossing = False
	update_display(show_num, crossing, num)
    if m.button_a.was_pressed():
        show_num = not show_num
	if not show_num: m.display.clear()
        update_display(show_num, crossing, num)
    elif m.button_b.was_pressed():
	baseline = m.compass.get_field_strength()
	num = 0
	crossing = False
	show_num = False
        m.display.clear()
	update_display(show_num, crossing, num)
