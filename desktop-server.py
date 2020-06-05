# -----------------------------------------------------------------------------
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# bit4hamster collection
#
# Hamster desktop server
#
# Author: Alexey Fedoseev <aleksey@fedoseev.net>, 2020
# -----------------------------------------------------------------------------

import sys
from serialport import SerialPort, SerialException
from serialprotocol import SerialProtocol
from debug import dprint

MODE_INIT = 0
MODE_LISTEN = 1

DEFAULT_SERIAL_ADDRESS = '/dev/ttyACM0'

def usage():
    dprint('Hamster desktop server')
    dprint('Usage: {} <command> [flags]'.format(sys.argv[0]))
    dprint('Commands:')
    dprint('\tinit\tInitialize counter with system time')
    dprint('\tlisten\tWait for counter data & files')
    dprint('Flags:')
    dprint('\t-d <device>\tUse the specified '
           'tty device (default {})'.format(DEFAULT_SERIAL_ADDRESS))
    exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage()

    mode = None
    command = sys.argv[1]
    if command == 'init':
        mode = MODE_INIT
    elif command == 'listen':
        mode = MODE_LISTEN
    else:
        usage()

    serial_address = DEFAULT_SERIAL_ADDRESS
    if len(sys.argv) > 2:
        flagargs = sys.argv[2:]
        if len(flagargs) % 2 != 0:
            usage()
        flags = int(len(flagargs) / 2)
        for i in range(flags):
            theflag = flagargs[i * 2]
            thearg = flagargs[i * 2 + 1]
            if theflag == '-d':
                serial_address = thearg

    sport = SerialPort(serial_address)
    protocol = SerialProtocol(sport)

    try:
        protocol.init()

        if mode == MODE_INIT:
            protocol.send_time(5)
            exit(0)

        assert mode == MODE_LISTEN
        dprint('waiting data...')
        protocol.listen()

    except KeyboardInterrupt:
        dprint('keyboard interrupt. saving state...')
        if mode == MODE_LISTEN:
            protocol.save_state()
    except SerialException as e:
        dprint('serial error: {}'.format(e))
        sport.close()
        exit(1)
