# -----------------------------------------------------------------------------
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# bit4hamster collection
#
# Hamster desktop server: serial exchange protocol module
#
# Author: Alexey Fedoseev <aleksey@fedoseev.net>, 2020
# -----------------------------------------------------------------------------

import time
import datetime
from debug import dprint
from logger import EventLogger

class SerialProtocol(object):

    STATE_START = 0
    STATE_TIME = 1
    STATE_WAIT = 2

    SYSTEM_START = 'STA'
    SYSTEM_TIME = 'TIM'
    SYSTEM_LOG = 'LOG'
    SYSTEM_EVENT = 'EVN'
    SYSTEM_FILE = 'FIL'
    SYSTEM_LINE = 'LIN'
    SYSTEM_EOF = 'EOF'
    SYSTEM_OK = 'OKE'

    DATA_BYTES_ORDER = 'little'

    def __init__(self, sport):
        assert sport is not None
        self.state = self.STATE_START
        self.sport = sport
        self.logger = EventLogger()
        self.__prev_date = None
        self.__check_day()

    def init(self):
        assert self.state == self.STATE_START
        dprint('sending start...')
        self.sport.send(self.SYSTEM_START)
        time.sleep(1)

    def send_time(self, timeout=None):
        t = time.time()
        dprint('sending time {}'.format(int(t)))
        self.sport.send('{} {}'.format(self.SYSTEM_TIME, int(t)))
        time.sleep(1)
        line = None
        start_t = t = time.time()
        while timeout is None or (t - start_t >= timeout):
            line = self.sport.readline()
            if line:
                if line.strip() == self.SYSTEM_OK:
                    dprint('time ok')
                    return True
                else:
                    dprint('bad line: {}'.format(line))
            t = time.time()
        dprint('protocol timeout')
        return False

    def __check_day(self):
        dt = datetime.datetime.now()
        if self.__prev_date is None:
            self.__prev_date = dt
        else:
            tt1 = self.__prev_date.timetuple()
            tt2 = self.__prev_date.timetuple()
            if tt1[3] < 12 and tt2[3] >= 12:
                dprint('-' * 80)
                dprint('starting new day {:02d}.{:02d}'.format(tt2[2], tt2[1]))
                self.logger.newday()

    def listen(self):
        while True:
            self.__check_day()

            line = self.sport.readline()
            if line:
                code = line[0:3]
                device = line[3:4]
                rawdata = line[4:]
                dprint('received {} "{}" from {}...'.format(code, rawdata, device))
                if code == self.SYSTEM_LOG or code == self.SYSTEM_EVENT:
                    try:
                        data = bytes.fromhex(rawdata)
                    except ValueError:
                        dprint('bad hex data')
                        continue
                    if len(data) != 20:
                        dprint('bad data size')
                        continue
                    ts = int.from_bytes(data[0:4], self.DATA_BYTES_ORDER)
                    num = int.from_bytes(data[4:6], self.DATA_BYTES_ORDER)
                    temp1 = int.from_bytes(data[6:8], self.DATA_BYTES_ORDER)
                    temp2 = int.from_bytes(data[8:12], self.DATA_BYTES_ORDER)
                    temp = temp1 + float(temp2) / 1000000.0
                    light1 = int.from_bytes(data[12:14], self.DATA_BYTES_ORDER)
                    light2 = int.from_bytes(data[14:18], self.DATA_BYTES_ORDER)
                    light = light1 + float(light2) / 1000000.0
                    checksum = sum(data[0:18])
                    remote_cs = int.from_bytes(data[18:20], self.DATA_BYTES_ORDER)
                    if checksum != remote_cs:
                        dprint('bad log checksum')
                    else:
                        dt = datetime.datetime.now()
                        dprint('{} received {}: {} {} {} {}'.format(dt.strftime('%H:%M:%S.%f'),
                                                                    code, ts, num, temp, light))
                        if code == self.SYSTEM_LOG:
                            self.logger.summary(device, ts, num, temp, light)
                        else:
                            self.logger.event(device, ts, num, temp, light)
                elif code == self.SYSTEM_FILE:
                    self.logger.start_log(rawdata)
                elif code == self.SYSTEM_EOF:
                    self.logger.finish_log()
                elif code == self.SYSTEM_LINE:
                    parts = rawdata.split(' ')
                    if len(parts) != 4:
                        dprint('wrong log string')
                    else:
                        ts = int(parts[0])
                        num = int(parts[1])
                        temp = float(parts[2])
                        light = float(parts[3])
                        self.logger.log_data(device, ts, num, temp, light)
                else:
                    dprint('bad protocol code {}'.format(code))
