# -----------------------------------------------------------------------------
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# bit4hamster collection
#
# Hamster radio receiver program
#
# Author: Alexey Fedoseev <aleksey@fedoseev.net>, 2020
# -----------------------------------------------------------------------------

import time
import os
import radio # pylint: disable=import-error
import microbit as m # pylint: disable=import-error

DEVICE = 'Z'

RECV_TIMEOUT = 10

CMD_GET_TIME = 'GET_TIME'
CMD_DATA_START = 'DATA_START'
CMD_DATA_VECTOR = 'DATA_VECT'
CMD_DATA_END = 'DATA_END'
CMD_DATA_RESET = 'DATA_RESET'

start_time = time.ticks_ms() # pylint: disable=no-member
global_time = 1001
receiving = {}

def send_command(todev, cmd_name, *cmd_args):
    cmd_string = '{} {} {}'.format(todev, cmd_name, ' '.join(map(str, cmd_args)))
    radio.send(cmd_string)

def save_data(device, data):
    timestamp = time.ticks_ms() # pylint: disable=no-member
    filename = '{}-{}-{}.txt'.format(device, data['data_type'], timestamp)
    f = open(filename, 'w')
    for dline in data['data']:
        f.write("{}\n".format(' '.join(map(str, dline))))
    f.close()

def info(s):
    m.display.show(s, wait=False, loop=True)
def debug(s):
    m.display.show(s, wait=True, loop=False)
def error(s):
    m.display.show(s, wait=True, loop=True)

def remove_files():
    ll = os.listdir()
    for f in ll:
        os.remove(f)

debug(DEVICE)
remove_files()
radio.on()
while True:
    msg = radio.receive()
    if msg:
        args = msg.strip().split(' ')
        if not args:
            error('bad incoming message "{}" args: {}')
        else:
            fromdev = args[0]
            cmd = args[1]
            info('from {} cmd {}'.format(fromdev, cmd))
            if cmd == CMD_GET_TIME:
                t = time.ticks_ms() # pylint: disable=no-member
                send_command(fromdev, CMD_GET_TIME, global_time + t - start_time)
            elif cmd == CMD_DATA_START:
                if len(args) != 4:
                    error('bad incoming command "{}" - bad args'.format(msg))
                elif fromdev in receiving:
                    error('double data start "{}"'.format(msg))
                else:
                    receiving[fromdev] = {
                        'data': [],
                        'data_type': args[2]
                    }
                    send_command(fromdev, CMD_DATA_START)
            elif cmd == CMD_DATA_VECTOR:
                if fromdev not in receiving:
                    error('bad incoming command "{}" - not receiving'.format(msg))
                elif len(args) < 3:
                    error('bad incoming command "{}" - bad args'.format(msg))
                else:
                    d = []
                    for a in args[2:]:
                        if a.find('.') >= 0:
                            d.append(float(a))
                        else:
                            d.append(int(a))
                    receiving[fromdev]['data'].append(d)
                    send_command(fromdev, CMD_DATA_VECTOR)
            elif cmd == CMD_DATA_END:
                if fromdev not in receiving:
                    error('bad incoming command "{}" - not receiving'.format(msg))
                else:
                    r = receiving[fromdev]
                    save_data(fromdev, r)
                    size = len(r['data'])
                    info('received from {} {} {}'.format(fromdev, r['data_type'], size))
                    send_command(fromdev, CMD_DATA_END)
                    del receiving[fromdev]
            elif cmd == CMD_DATA_RESET:
                if fromdev not in receiving:
                    error('bad incoming command "{}" - not receiving'.format(msg))
                else:
                    info('reset {}'.format(fromdev))
                    del receiving[fromdev]
                    send_command(fromdev, CMD_DATA_RESET)
            else:
                error('bad command name "{}"'.format(cmd))
    m.sleep(RECV_TIMEOUT)
