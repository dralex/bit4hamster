# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# bit4hamster collection
#
# Hamster lab: groogle spreadsheets data uploader
#
# Author: Alexey Fedoseev <aleksey@fedoseev.net>, 2020
# -----------------------------------------------------------------------------

import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.auth
from debug import dprint

class SheetException(Exception):
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg
    def __str__(self):
        return self.msg

class HamsterSheet(object):

    SHEET_NAME_FORMAT = 'hamster 2.0 {}'
    SECRET_FILE = 'credentials.json'
    USER_ID = 'aleksey.fedoseev@gmail.com'
    SEPARATOR = ' '

    def __init__(self, date, event_log, summary_log):
        self.__create_sheet(date)
        self.__share_to(self.USER_ID)
        self.__insert_summary_log(summary_log)
        self.__insert_event_log(event_log)

    def get_url(self):
        return self.__sheet_id

    def __create_sheet(self, date):
        name = self.SHEET_NAME_FORMAT.format(date)
        scope = ['https://www.googleapis.com/auth/spreadsheets',
                 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(self.SECRET_FILE, scope)
        self.__client = gspread.authorize(creds)
        try:
            self.__sheet = self.__client.open(name)
        except gspread.SpreadsheetNotFound:
            pass
        except gspread.exceptions.GSpreadException as e:
            raise SheetException('error while creating sheet: {}'.format(e))
        except google.auth.exceptions.TransportError as e:
            raise SheetException('sheets connection error: {}'.format(e))
        else:
            self.__client.del_spreadsheet(self.__sheet.id)
        self.__sheet = self.__client.create(name)
        self.__sheet_id = self.__sheet.id
        dprint('created {}'.format(self.__sheet_id))
        self.__sheet = self.__sheet.sheet1
        self.__sheet.update_title(date)

    def __share_to(self, user):
        self.__client.insert_permission(self.__sheet_id, user,
                                        perm_type='user', role='reader', with_link=False)

    def __insert_array(self, r, array):
        cells = self.__sheet.range(r)
        for idx, value in enumerate(array):
            cells[idx].value = value
        self.__sheet.update_cells(cells, value_input_option='USER_ENTERED')

    def __insert_matrix(self, r, array):
        columns = len(array[0])
        cells = self.__sheet.range(r)
        for rowidx, a in enumerate(array):
            for colidx, value in enumerate(a):
                cells[rowidx * columns + colidx].value = value
        self.__sheet.update_cells(cells, value_input_option='USER_ENTERED')

    def __insert_event_log(self, event_log):
        try:
            keys = sorted(event_log.keys())
            if not keys:
                return
            self.__insert_array('G1:{}1'.format(chr(ord('G') + len(keys) - 1)), keys)
            for k in keys:
                column = chr(ord('G') + k)
                events = event_log[k]
                self.__insert_array('{}1:{}{}'.format(column, column, len(events)),
                                    events)
        except gspread.exceptions.GSpreadException as e:
            raise SheetException('error while saving events log: {}'.format(e))
        except google.auth.exceptions.TransportError as e:
            raise SheetException('error while saving events log: {}'.format(e))

    def __insert_summary_log(self, summary_log):
        try:
            if 'A' not in summary_log:
                return
            log = summary_log['A']
            if not log:
                return
            matrix = []
            for i, cell in enumerate(log):
                tt = datetime.datetime.fromtimestamp(cell[0]).timetuple()
                hour, minute, sec = tt[3:6]
                if i == 0:
                    s = '0'
                else:
                    s = '=C{}-C{}'.format(i + 2, i + 1)
                matrix.append(('{:02d}:{:02d}:{:02d}'.format(hour, minute, sec),
                               cell[1], cell[2], cell[3], cell[4], s))
                self.__insert_matrix('A1:F{}'.format(len(log)), matrix)
        except gspread.exceptions.GSpreadException as e:
            raise SheetException('error while saving summary log: {}'.format(e))
        except google.auth.exceptions.TransportError as e:
            raise SheetException('error while saving summary log: {}'.format(e))
