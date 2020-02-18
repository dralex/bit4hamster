# -----------------------------------------------------------------------------
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# bit4hamster collection
#
# Hamster magnet counter program
#
# Author: Alexey Fedoseev <aleksey@fedoseev.net>, 2019
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
        m.display.show(num, wait = False, loop = True)
    elif crossing and abs(field - baseline) <= THRESHOLD:
        crossing = False
