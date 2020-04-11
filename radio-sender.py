# -----------------------------------------------------------------------------
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# bit4hamster collection
#
# Hamster radio sender test program
#
# Author: Alexey Fedoseev <aleksey@fedoseev.net>, 2020
# -----------------------------------------------------------------------------

import time
import radio # pylint: disable=import-error
import microbit as m # pylint: disable=import-error

DEVICE = 'A'

DEFAULT_TRIES = 3
DEFAULT_TIMEOUT = 1000
RECV_TIMEOUT = 10

CMD_GET_TIME = 'GET_TIME'
CMD_DATA_START = 'DATA_START'
CMD_DATA_VECTOR = 'DATA_VECT'
CMD_DATA_END = 'DATA_END'
CMD_DATA_RESET = 'DATA_RESET'

global_data = [(1,),
               (2, 2),
               (3, 3, 3),
               (4, 4, 4, 4)]

def debug(s):
    m.display.show(s, wait=True, loop=False)
def error(s):
    m.display.show(s, wait=True, loop=True)

def radio_recv(timeout):
    start_time = t = time.ticks_ms() # pylint: disable=no-member
    while t - start_time < timeout:
        msg = radio.receive()
        if msg:
            return msg
        m.sleep(RECV_TIMEOUT)
        t = time.ticks_ms() # pylint: disable=no-member
    return None

def send_command(cmd, *args):
    cmd_string = '{} {} {}'.format(DEVICE, cmd, ' '.join(map(str, args)))
    tries = DEFAULT_TRIES
    result = None
    while tries > 0:
        radio.send(cmd_string)
        msg = radio_recv(DEFAULT_TIMEOUT)
        if msg:
            args = msg.strip().split(' ')
            if args[0] == DEVICE:
                if args[1] == cmd:
                    result = (True, args[2:])
                else:
                    result = (False, 'bad answer {}'.format(msg))
                break
        tries -= 1
    if not result:
        result = (False, 'send timeout')
    return result

def get_time():
    radio.on()
    status, args = send_command(CMD_GET_TIME)
    the_time = None
    if status:
        the_time = int(args[0])
        debug('time {}'.format(the_time))
    else:
        error('error {}'.format(args))
    radio.off()
    return the_time

def send_data(typ, data):
    radio.on()
    res = send_command(CMD_DATA_START, typ, len(data))
    if res[0]:
        debug('1')
        for d in data:
            res = send_command(CMD_DATA_VECTOR, ' '.join(map(str, d)))
            if not res[0]:
                break
        debug('2')
        if res[0]:
            res = send_command(CMD_DATA_END)
            if res[0]:
                debug('3')
                radio.off()
                return True
    send_command(CMD_DATA_RESET)
    error('error {}'.format(res[1]))
    radio.off()
    return False

debug(DEVICE)
while True:
    if m.button_a.was_pressed():
        send_data('ARRAY', global_data)
    if m.button_b.was_pressed():
        get_time()
