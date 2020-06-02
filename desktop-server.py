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
import os
import time
import datetime
import serial

DEFAULT_SERIAL_ADDRESS = '/dev/ttyACM0'
SERIAL_BAUD = 115200

SYSTEM_START = 'STA'
SYSTEM_TIME = 'TIM'
SYSTEM_LOG = 'LOG'
SYSTEM_EVENT = 'EVN'
SYSTEM_FILE = 'FIL'
SYSTEM_LINE = 'LIN'
SYSTEM_EOF = 'EOF'
SYSTEM_OK = 'OKE'

MODE_INIT = 0
MODE_LISTEN = 1

DATA_BYTES_ORDER = 'little'

LOG_FILENAME = 'log'
EVLOG_FILENAME = 'evlog'

def init_serial(addr):
    s = serial.Serial()
    s.port = addr
    s.baudrate = SERIAL_BAUD
    s.bytesize = serial.EIGHTBITS	# number of bits per bytes
    s.parity = serial.PARITY_NONE	# set parity check: no parity
    s.stopbits = serial.STOPBITS_ONE	# number of stop bits
    s.timeout = 1            		# non-block read
    s.xonxoff = False     		# disable software flow control
    s.rtscts = False     		# disable hardware (RTS/CTS) flow control
    s.dsrdtr = False       		# disable hardware (DSR/DTR) flow control
    s.writeTimeout = 2     		# timeout for write
    reset_serial(s)
    return s

def reset_serial(ser):
    if ser.isOpen():
        ser.close()
    try:
        ser.open()
        ser.reset_input_buffer()
        ser.reset_output_buffer()
    except serial.serialutil.SerialException as e:
        print('error open serial port: ' + str(e))

def usage():
    print('Hamster desktop server')
    print('Usage: {} <command> [flags]'.format(sys.argv[0]))
    print('Commands:')
    print('\tinit\tInitialize counter with system time')
    print('\tlisten\tWait for counter data & files')
    print('Flags:')
    print('\t-d <device>\tUse the specified tty device (default /dev/ttyACM0)')
    exit(1)

def rename_file(fpath):
    for letter in ('A', 'B', 'C', 'D'):
        checkpath = '{}-{}.txt'.format(fpath, letter)
        if os.path.exists(checkpath):
            postfix = 0
            newname = checkpath
            while os.path.exists(newname):
                newname = "{}-{}-{:02d}.txt".format(fpath, letter, postfix)
                postfix += 1
            os.rename(checkpath, newname)

if len(sys.argv) < 2:
    usage()

mode = None
command = sys.argv[1]
if command == 'init':
    mode = MODE_INIT
elif command == 'listen':
    mode = MODE_LISTEN
    tt = datetime.datetime.now().timetuple()
    month = tt[1]
    day = tt[2]
    dirname = 'data/{:02d}.{:02d}'.format(day, month)
    logfilename = '{}/{}'.format(dirname, LOG_FILENAME)
    evlogfilename = '{}/{}'.format(dirname, EVLOG_FILENAME)
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    else:
        rename_file(logfilename)
        rename_file(evlogfilename)
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

sport = init_serial(serial_address)
print('sending start')
sport.write(bytes('{}\r\n'.format(SYSTEM_START), 'utf-8'))
time.sleep(1)

while True:
    try:
        if not sport.isOpen():
            reset_serial(sport)
            time.sleep(1)
        elif mode == MODE_INIT:
            t = int(time.time())
            print('sending time {}'.format(t))
            sport.write(bytes('{} {}\r\n'.format(SYSTEM_TIME, t), 'utf-8'))
            time.sleep(1)
            line = None
            while True:
                line = str(sport.readline(), 'utf-8')
                if line:
                    if line.strip() == SYSTEM_OK:
                        print('time ok')
                    else:
                        print('bad line: {}'.format(line))
                    sport.close()
                    exit(0)
        elif mode == MODE_LISTEN:
            print('waiting data...')
            f = None
            while True:
                line = sport.readline()
                if line:
                    line = str(line, 'utf-8').strip()
                    code = line[0:3]
                    device = line[3:4]
                    rawdata = line[4:]
                    print('received {} "{}" from {}...'.format(code, rawdata, device))
                    if code == SYSTEM_LOG or code == SYSTEM_EVENT:
                        try:
                            data = bytes.fromhex(rawdata)
                        except ValueError:
                            print('bad hex data')
                            continue
                        if len(data) != 20:
                            print('bad data size')
                            continue
                        ts = int.from_bytes(data[0:4], DATA_BYTES_ORDER)
                        num = int.from_bytes(data[4:6], DATA_BYTES_ORDER)
                        temp1 = int.from_bytes(data[6:8], DATA_BYTES_ORDER)
                        temp2 = int.from_bytes(data[8:12], DATA_BYTES_ORDER)
                        temp = temp1 + float(temp2) / 1000000.0
                        light1 = int.from_bytes(data[12:14], DATA_BYTES_ORDER)
                        light2 = int.from_bytes(data[14:18], DATA_BYTES_ORDER)
                        light = light1 + float(light2) / 1000000.0
                        checksum = sum(data[0:18])
                        remote_cs = int.from_bytes(data[18:20], DATA_BYTES_ORDER)
                        if checksum != remote_cs:
                            print('bad log checksum')
                        local_ts = time.time()
                        dt = datetime.datetime.now()
                        print('{} received {}: {} {} {} {}'.format(dt.strftime('%H:%M:%S.%f'),
                                                                   code, ts, num, temp, light))
                        if code == SYSTEM_LOG:
                            name = logfilename
                        else:
                            name = evlogfilename
                        logf = open('{}.txt'.format(name), 'a')
                        logf.write('{} {} {} {} {} {}\n'.format(local_ts,
                                                                device,
                                                                ts,
                                                                num,
                                                                temp,
                                                                light))
                        logf.close()
                    elif code == SYSTEM_FILE:
                        if f:
                            print('file was already opened')
                        else:
                            filepath = '{}/{}'.format(dirname, rawdata)
                            f = open(filepath, 'w')
                            print('creating file {}'.format(filepath))
                    elif code == SYSTEM_EOF:
                        if not f:
                            print('file does not open')
                        else:
                            f.close()
                            f = None
                            print('file saved')
                    elif code == SYSTEM_LINE:
                        if not f:
                            print('file does not open')
                        else:
                            f.write('{}\r\n'.format(rawdata))
                    else:
                        print('bad code {}'.format(code))
    except serial.serialutil.SerialException as e:
        print('serial error: {}'.format(e))
        sport.close()
        exit(1)
