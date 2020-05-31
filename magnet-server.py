# -----------------------------------------------------------------------------
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# bit4hamster collection
#
# Hamster radio transfer server
#
# Author: Alexey Fedoseev <aleksey@fedoseev.net>, 2020
# -----------------------------------------------------------------------------

import time
import os
import radio # pylint: disable=import-error
import microbit as m # pylint: disable=import-error

DEVICE = 'Z'
RADIO_CHANNEL = 1

BAUD = 115200
SYSTEM_START = 'STA'
SYSTEM_TIME = 'TIM'
SYSTEM_LOG = 'LOG'
SYSTEM_EVENT = 'EVN'
SYSTEM_FILE = 'FIL'
SYSTEM_LINE = 'LIN'
SYSTEM_EOF = 'EOF'
SYSTEM_OK = 'OKE'

RECV_TIMEOUT = 10

RADIO_CODE_LOG = 'LOG'
RADIO_CODE_EVENT = 'EVN'
RADIO_CODE_FILE = 'FIL'
RADIO_CODE_LINE = 'LIN'
RADIO_CODE_EOF = 'EOF'

RADIO_BUFFER = 32
RADIO_QUEUE = 5

LIGHT = 3

serial_buf = ''
file_num = None
start_time = time.ticks_ms() # pylint: disable=no-member
global_time = 0
sending_file = False

def update_display(sentradio, sentserial):
    m.display.set_pixel(0, 0, LIGHT)
    m.display.set_pixel(0, 1, LIGHT if sentradio else 0)
    m.display.set_pixel(0, 2, LIGHT if sentserial else 0)

def init_serial():
    global serial_buf # pylint: disable=global-statement
    m.uart.init(BAUD)
    serial_buf = ''
    start_cmd = SYSTEM_START + '\r\n'
    while True:
        if m.uart.any():
            serial_buf += str(m.uart.read(), 'UTF-8')
        idx = serial_buf.find(start_cmd)
        if idx >= 0:
            serial_buf = serial_buf[idx + len(start_cmd):]
            break
        update_display(True, True)
        m.sleep(RECV_TIMEOUT)
        update_display(False, False)

def error(s):
    m.display.show(s, wait=True, loop=True)

def calculate_files():
    global file_num # pylint: disable=global-statement
    ll = os.listdir()
    file_num = len(ll)

def remove_files():
    global file_num # pylint: disable=global-statement
    ll = os.listdir()
    for f in ll:
        os.remove(f)
    file_num = 0

calculate_files()
init_serial()
radio.on()
radio.config(length=RADIO_BUFFER,
             queue=RADIO_QUEUE,
             channel=RADIO_CHANNEL)
while True:

    # Read serial port
    if m.uart.any():
        serial_buf += str(m.uart.read(), 'UTF-8')
    index = serial_buf.find('\r\n')
    if index >= 0:
        command = serial_buf[0:index].strip().split(' ')
        if command[0] == SYSTEM_TIME:
            global_time = int(command[1])
            start_time = time.ticks_ms() # pylint: disable=no-member
            m.uart.write(SYSTEM_OK + '\r\n')
        serial_buf = serial_buf[index + 2:]
        update_display(False, True)

    # Read radio
    msg = radio.receive_bytes()
    if msg:
        update_display(True, False)
        if msg[0:3] != b'\x01\x00\x01':
            error('bad microbit message')
        msg = msg[3:]
        code = str(msg[0:3], 'utf-8')
        device = str(msg[3:4], 'utf-8')
        msg = msg[4:]
        if code == RADIO_CODE_LOG:
            hexdump = ''.join('%02x' % i for i in msg)
            m.uart.write('{}{}{}\r\n'.format(SYSTEM_LOG, device, hexdump))
        elif code == RADIO_CODE_EVENT:
            hexdump = ''.join('%02x' % i for i in msg)
            m.uart.write('{}{}{}\r\n'.format(SYSTEM_EVENT, device, hexdump))
        elif code == RADIO_CODE_FILE:
            if sending_file:
                m.uart.write('{}{}\r\n'.format(SYSTEM_EOF, device))
            else:
                sending_file = True
            ts = time.ticks_ms() # pylint: disable=no-member
            filename = '{}-{}-{}.txt'.format(device, ts, str(msg, 'utf-8'))
            m.uart.write('{}{}{}\r\n'.format(SYSTEM_FILE, device, filename))
        elif code == RADIO_CODE_EOF:
            m.uart.write('{}{}\r\n'.format(SYSTEM_EOF, device))
            sending_file = False
        elif code == RADIO_CODE_LINE:
            m.uart.write('{}{}{}\r\n'.format(SYSTEM_LINE, device, str(msg, 'utf-8')))
        else:
            error('bad command code "{}"'.format(code))
    m.sleep(RECV_TIMEOUT)
    update_display(False, False)
