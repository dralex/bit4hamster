# -----------------------------------------------------------------------------
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# bit4hamster collection
#
# Hamster magnet memory testing program
#
# Author: Alexey Fedoseev <aleksey@fedoseev.net>, 2020
# -----------------------------------------------------------------------------

import time
import os
import microbit as m

FILENAME = 'log{}.txt'
MEMORY_LIMIT = 200
file_num = last_change = time_buf = buf_size = None

def update_display():
    file_rows = int(file_num / 5)
    file_columns = file_num % 5
    for i in range(5):
        if i < file_rows:
            for j in range(5):
                m.display.set_pixel(j, i, 9)
        elif i == file_rows:
            for j in range(5):
                if j <= file_columns:
                    m.display.set_pixel(j, i, 9)
                else:
                    m.display.set_pixel(j, i, 0)
        else:
            for j in range(5):
                m.display.set_pixel(j, i, 0)

def sync_buf():
    global file_num, time_to_sync, time_buf, buf_size
    f = open(FILENAME.format(file_num), 'wb')
    for i in range(buf_size):
        s = time_buf[i].to_bytes(4, 'little')
        f.write(s)
    f.close()
    file_num += 1
    time_to_sync = False
    buf_size = 0

file_num = 0
ll = os.listdir()
for fn in ll:
    os.remove(fn)
time_to_sync = False
buf_size = 0
time_buf = [0] * MEMORY_LIMIT
m.display.clear()
update_display()

while True:
    last_change = time.ticks_ms()
    time_buf[buf_size] = last_change + 1000000
    buf_size += 1
    if buf_size == MEMORY_LIMIT:
        sync_buf()
        update_display()
