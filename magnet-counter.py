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
# Choose the appropriate value based on the cage & wheel configuration
THRESHOLD = 12500
SENSOR_LOG = True

TIME_LIMIT = 400			# 0.4 sec
SYNC_TIME = 30 * 60 * 1000 		# 30 min
SENSOR_SYNC_TIME = 5 * 60 * 1000 	# 5 min
SENSOR_MEASURE_TIME = 10 * 1000		# 10 sec
POWER_OFF_TIME = 12 * 60 * 60 * 1000 	# 12 hours

LOG_FILENAME_PREFIX = 'log' + DEVICE
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
temp_sum = light_sum = measure_count = sensor_measure = sensor_sync = None
power_is_on = start_time = None

def update_display():
    if show_num:
        m.display.show('{}.'.format(num), wait=False, loop=True)
    else:
        m.display.set_pixel(0, 4, LIGHT)
        m.display.set_pixel(4, 4, LIGHT if crossing else 0)

def get_sensors():
    global temp_sum, light_sum, measure_count  # pylint: disable=global-statement
    if not SENSOR_LOG:
        return (0.0, 0.0)
    update_sensors()
    temp_val = float(temp_sum) / measure_count
    light_val = float(light_sum) / measure_count
    temp_sum = light_sum = measure_count = 0
    return (temp_val, light_val)

def update_sensors():
    global temp_sum, light_sum, measure_count, sensor_measure  # pylint: disable=global-statement
    temp_sum += m.temperature()
    light_sum += m.pin0.read_analog()
    measure_count += 1
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
    global temp_sum, sensor_measure, light_sum, measure_count, sensor_sync # pylint: disable=global-statement
    global start_time, power_is_on  # pylint: disable=global-statement
    baseline = m.compass.get_field_strength() # Take a baseline reading of magnetic strength
    num = 0
    crossing = False
    show_num = False
    temp_sum = light_sum = measure_count = 0
    num_buf = []
    last_change = last_sync = sensor_sync = sensor_measure = start_time = time.ticks_ms() # pylint: disable=no-member
    calculate_files()
    m.display.clear()
    update_display()
    radio.on()
    radio.config(length=RADIO_BUFFER,
                 queue=RADIO_QUEUE,
                 channel=RADIO_CHANNEL)
    send_log(last_change, num, get_sensors())
    power_is_on = True

def send_single_event(typ, lsync, n, tmp=0.0, l=0.0):
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

def send_log(lsync, n, pair):
    global sensor_sync # pylint: disable=global-statement
    send_single_event(RADIO_CODE_LOG, lsync, n, pair[0], pair[1])
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
    last_sync = time.ticks_ms() # pylint: disable=no-member
    sensors = get_sensors()
    send_log(last_sync, num, sensors)
    num_buf.append((last_sync, num, sensors[0], sensors[1]))
    f = open(LOG_FILENAME.format(file_num), 'w')
    for n in num_buf:
        f.write("{}\n".format(' '.join(map(str, n))))
    f.close()

def power_off():
    global power_is_on # pylint: disable=global-statement
    send_full_log()
    m.display.clear()
    radio.off()
    power_is_on = False

reset()
while True:
    if power_is_on:
        t = time.ticks_ms() # pylint: disable=no-member

        field = m.compass.get_field_strength()

        if not crossing and abs(field - baseline) > THRESHOLD:
            crossing = True
            delta = t - last_change
            if delta > TIME_LIMIT:
                num = num + 1
                if not SENSOR_LOG:
                    send_single_event(RADIO_CODE_EVENT, t, num)
                last_change = t
            update_display()
        elif crossing and abs(field - baseline) <= THRESHOLD:
            crossing = False
            update_display()

        if t - last_sync >= SYNC_TIME:
            sync_data()

        if SENSOR_LOG:
            if t - sensor_sync >= SENSOR_SYNC_TIME:
                send_log(t, num, get_sensors())
            if t - sensor_measure >= SENSOR_MEASURE_TIME:
                update_sensors()

        if t - start_time >= POWER_OFF_TIME:
            power_off()

        if m.button_a.was_pressed():
            baseline = m.compass.get_field_strength() # Update baseline
            show_num = not show_num
            if not show_num:
                m.display.clear()
            else:
                send_full_log()
            update_display()
    else:
        m.display.set_pixel(0, 4, 1)
        m.sleep(1000)
        m.display.set_pixel(0, 4, 0)

    if m.button_b.was_pressed():
        remove_files()
        m.reset()
