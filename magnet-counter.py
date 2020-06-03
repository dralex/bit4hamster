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
import os
import microbit as m # pylint: disable=import-error
import radio # pylint: disable=import-error

DEVICE = 'A'
if DEVICE == 'A':
    # Choose the appropriate value based on the cage & wheel configuration
    THRESHOLD = 12500
    SENSOR_LOG = True
    EVENT_LOG = False
    SEND_DELAY = 0     		# 0 ms
else:
    THRESHOLD = 12000
    SENSOR_LOG = False
    EVENT_LOG = True
    SEND_DELAY = 0     		# 0 ms

TIME_LIMIT = 400		# 0.4 sec
SYNC_TIME = 1800000 		# 30 min
SENSOR_SYNC_TIME = 300000 	# 5 min
SENSOR_MEASURE_TIME = 10000 	# 10 sec

LOG_FILENAME_PREFIX = 'log'
LOG_FILENAME = LOG_FILENAME_PREFIX + '{}.txt'

RADIO_CODE_LOG = 'LOG'
RADIO_CODE_EVENT = 'EVN'
RADIO_CODE_FILE = 'FIL'
RADIO_CODE_LINE = 'LIN'
RADIO_CODE_EOF = 'EOF'
DATA_BYTES_ORDER = 'little'
SEND_TIMEOUT = 10
RADIO_BUFFER = 32
RADIO_QUEUE = 2
RADIO_CHANNEL = 1

LIGHT = 3

baseline = num = crossing = show_num = last_change = None
num_buf = last_sync = file_num = None
temp_sum = temp_count = light_sum = light_count = sensor_measure = sensor_sync = None

def update_display():
    if show_num:
        m.display.show('{}.'.format(num), wait=False, loop=True)
    else:
        m.display.set_pixel(0, 4, LIGHT)
        m.display.set_pixel(4, 4, LIGHT if crossing else 0)

def get_temperature():
    global temp_sum, temp_count  # pylint: disable=global-statement
    update_temperature()
    temp_val = float(temp_sum) / temp_count
    temp_sum = temp_count = 0
    return temp_val

def update_temperature():
    global temp_sum, temp_count, sensor_measure  # pylint: disable=global-statement
    temp_sum += m.temperature()
    temp_count += 1
    sensor_measure = time.ticks_ms() # pylint: disable=no-member

def get_light():
    global light_sum, light_count # pylint: disable=global-statement
    update_light()
    light_val = float(light_sum) / light_count
    light_sum = light_count = 0
    return light_val

def update_light():
    global light_sum, light_count, sensor_measure # pylint: disable=global-statement
    if SENSOR_LOG:
        light_sum += m.pin0.read_analog()
    light_count += 1
    sensor_measure = time.ticks_ms() # pylint: disable=no-member

def calculate_files():
    global file_num # pylint: disable=global-statement
    ll = os.listdir()
    file_num = int(len(ll) / 2)

def remove_files():
    ll = os.listdir()
    for f in ll:
        os.remove(f)

def reset():
    global baseline, num, crossing, show_num, last_change, num_buf, last_sync # pylint: disable=global-statement
    global temp_sum, temp_count, sensor_measure, light_sum, light_count, sensor_sync # pylint: disable=global-statement
    baseline = m.compass.get_field_strength() # Take a baseline reading of magnetic strength
    num = 0
    crossing = False
    show_num = False
    temp_sum = temp_count = light_sum = light_count = 0
    num_buf = []
    last_change = last_sync = sensor_sync = sensor_measure = time.ticks_ms() # pylint: disable=no-member
    calculate_files()
    m.display.clear()
    update_display()

def send_single_event(typ, lsync, n, tmp, l):
    radio_buf = (lsync.to_bytes(4, DATA_BYTES_ORDER) + # pylint: disable=no-member
                 n.to_bytes(2, DATA_BYTES_ORDER) + # pylint: disable=no-member
                 int(tmp).to_bytes(2, DATA_BYTES_ORDER) + # pylint: disable=no-member
                 int((tmp - int(tmp)) * 1000000).to_bytes(4, DATA_BYTES_ORDER) + # pylint: disable=no-member
                 int(l).to_bytes(2, DATA_BYTES_ORDER) + # pylint: disable=no-member
                 int((l - int(l)) * 1000000).to_bytes(4, DATA_BYTES_ORDER)) # pylint: disable=no-member
    checksum = sum(radio_buf) # pylint: disable=no-member
    radio_buf = (bytes(typ, 'utf-8') +
                 bytes(DEVICE, 'utf-8') +
                 radio_buf +
                 checksum.to_bytes(2, DATA_BYTES_ORDER)) # pylint: disable=no-member
    radio.send(radio_buf)

def send_log(lsync, n, tmp, l):
    global sensor_sync # pylint: disable=global-statement
    send_single_event(RADIO_CODE_LOG, lsync, n, tmp, l)
    sensor_sync = time.ticks_ms() # pylint: disable=no-member

def send_full_log():
    radio.send('{}{}{}'.format(RADIO_CODE_FILE, DEVICE, LOG_FILENAME_PREFIX))
    for n in num_buf:
        m.sleep(SEND_TIMEOUT)
        radio.send('{}{}{}'.format(RADIO_CODE_LINE, DEVICE, ' '.join(map(str, n))))
    m.sleep(SEND_TIMEOUT)
    radio.send('{}{}'.format(RADIO_CODE_EOF, DEVICE))

def sync_data():
    global last_sync # pylint: disable=global-statement
    a = (last_sync, num, get_temperature(), get_light())
    send_log(*a)
    num_buf.append(a)
    f = open(LOG_FILENAME.format(file_num), 'w')
    for n in num_buf:
        f.write("{}\n".format(' '.join(map(str, n))))
    f.close()
    last_sync = time.ticks_ms() # pylint: disable=no-member

radio.on()
radio.config(length=RADIO_BUFFER,
             queue=RADIO_QUEUE,
             channel=RADIO_CHANNEL)
reset()
while True:
    field = m.compass.get_field_strength()
    t = time.ticks_ms() # pylint: disable=no-member

    if not crossing and abs(field - baseline) > THRESHOLD:
        crossing = True
        delta = t - last_change
        if delta > TIME_LIMIT:
            num = num + 1
            if EVENT_LOG:
                if SEND_DELAY:
                    m.sleep(SEND_DELAY)
                send_single_event(RADIO_CODE_EVENT, t, num,
                                  get_temperature(), get_light())
            last_change = t
        update_display()
    elif crossing and abs(field - baseline) <= THRESHOLD:
        crossing = False
        update_display()

    if t - last_sync >= SYNC_TIME:
        sync_data()

    if SENSOR_LOG:
        if t - sensor_sync >= SENSOR_SYNC_TIME:
            send_log(t, num, get_temperature(), get_light())
        if t - sensor_measure >= SENSOR_MEASURE_TIME:
            update_temperature()
            update_light()

    if m.button_a.was_pressed():
        baseline = m.compass.get_field_strength() # Update baseline
        show_num = not show_num
        if not show_num:
            m.display.clear()
        else:
            send_full_log()
        update_display()
    elif m.button_b.was_pressed():
        remove_files()
        m.reset()
