# -----------------------------------------------------------------------------
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# bit4hamster collection
#
# Hamster light sensor & temperature testing program
#
# Author: Alexey Fedoseev <aleksey@fedoseev.net>, 2020
# -----------------------------------------------------------------------------

import microbit as m # pylint: disable=import-error

while True:
    l = m.pin0.read_analog()
    t = m.temperature()
    m.display.show('l={};t={};'.format(l, t), wait=True, loop=False)
    m.sleep(1000)
