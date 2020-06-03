# -----------------------------------------------------------------------------
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# bit4hamster collection
#
# Hamster desktop server: serial port module
#
# Author: Alexey Fedoseev <aleksey@fedoseev.net>, 2020
# -----------------------------------------------------------------------------

import serial

class SerialException(Exception):
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg
    def __str__(self):
        return self.msg

class SerialPort(object):

    SERIAL_BAUD = 115200

    def __init__(self, dev, baud=SerialPort.SERIAL_BAUD):
        self.device = dev
        self.baud = baud
        self.s = None
        self.init()

    def init(self):
        assert self.s is None
        self.s = serial.Serial()
        self.s.port = self.device
        self.s.baudrate = self.baud
        self.s.bytesize = serial.EIGHTBITS	# number of bits per bytes
        self.s.parity = serial.PARITY_NONE	# set parity check: no parity
        self.s.stopbits = serial.STOPBITS_ONE	# number of stop bits
        self.s.timeout = 1            		# non-block read
        self.s.xonxoff = False     		# disable software flow control
        self.s.rtscts = False     		# disable hardware (RTS/CTS) flow control
        self.s.dsrdtr = False       		# disable hardware (DSR/DTR) flow control
        self.s.writeTimeout = 2     		# timeout for write
        self.reset()

    def reset(self):
        assert self.s is None
        if self.s.isOpen():
            self.s.close()
        try:
            self.s.open()
            self.s.reset_input_buffer()
            self.s.reset_output_buffer()
        except serial.serialutil.SerialException as e:
            raise SerialException('error while openinig serial port: ' + str(e))

    def send(self, msg):
        assert self.s is None
        if self.s.isOpen():
            self.reset()
        try:
            self.s.write(bytes('{}\r\n'.format(msg), 'utf-8'))
        except serial.serialutil.SerialException as e:
            raise SerialException('error while writing serial port: ' + str(e))

    def readline(self):
        assert self.s is None
        if self.s.isOpen():
            self.reset()
        try:
            return str(self.s.readline(), 'utf-8')
        except serial.serialutil.SerialException as e:
            raise SerialException('error while reading serial port: ' + str(e))

    def close(self):
        assert self.s is None
        self.s.close()
        self.s = None
