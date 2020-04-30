#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# bit4hamster collection
#
# Hamster lab groogle spreadsheets data uploader
#
# Author: Alexey Fedoseev <aleksey@fedoseev.net>, 2020
# -----------------------------------------------------------------------------

import sys
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.auth

SECRET_FILE = 'credentials.json'
USER_ID = 'aleksey.fedoseev@gmail.com'
DATA_DIR = 'data'

LOG_FILE = 'log0.txt'
HISTOGRAM_FILE = 'histogram0.txt'
FULLLOG_FILE = 'fulllog.txt'
SEPARATOR = ' '
DEFAULT_START_TIME = '20:00'
TOTAL_SHEET_NAME = 'Total'

def create_sheet(name):
    scope = ['https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(SECRET_FILE, scope)
    client = gspread.authorize(creds)
    try:
        sh = client.open(name)
    except gspread.SpreadsheetNotFound:
        pass
    else:
        client.del_spreadsheet(sh.id)
    sh = client.create(name)
    print('Created new sheet {}'.format(sh.id))
    client.insert_permission(sh.id, USER_ID,
                             perm_type='user', role='reader', with_link=False)
    return sh

def error(msg):
    print(msg)
    exit(2)

def usage():
    print('Hamster google sheets data uploader')
    print('Usage: {} <command>'.format(sys.argv[0]))
    print('Commands:')
    print('\tupload <date> [start_time]\tUpload the hamster data to sheets '
          'creating new worksheet for the <date>')
    exit(1)

def read_csv_file(filename):
    try:
        f = open(filename)
    except FileNotFoundError:
        return None
    d = []
    for line in f:
        parts = line.strip().split(SEPARATOR)
        d.append(parts)
    f.close()
    return d

def insert_array(sh, r, array):
    cells = sh.range(r)
    for idx, value in enumerate(array):
        cells[idx].value = value
    sh.update_cells(cells, value_input_option='USER_ENTERED')

def insert_matrix(sh, r, array):
    columns = len(array[0])
    cells = sh.range(r)
    for rowidx, a in enumerate(array):
        for colidx, value in enumerate(a):
            cells[rowidx * columns + colidx].value = value
    sh.update_cells(cells, value_input_option='USER_ENTERED')

if __name__ == '__main__':
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        usage()

    command = sys.argv[1]
    if command == 'upload':
        if len(sys.argv) < 3:
            usage()
        elif len(sys.argv) == 4:
            start_time = sys.argv[3]
        else:
            start_time = DEFAULT_START_TIME
        date = sys.argv[2]
        datadir = os.listdir(DATA_DIR)
        if date not in datadir:
            error('No date {} found in the data dir {}'.format(date, DATA_DIR))
        datedir = "{}/{}".format(DATA_DIR, date)
    else:
        usage()

    try:
        if command == 'upload':
            logdata = read_csv_file("{}/{}".format(datedir, LOG_FILE))
            histdata = read_csv_file("{}/{}".format(datedir, HISTOGRAM_FILE))
            fulldata = read_csv_file("{}/{}".format(datedir, FULLLOG_FILE))

            if not logdata and not histdata and not fulldata:
                error('No data to upload in the dir {}'.format(datedir))

            table = create_sheet('hamster {}'.format(date))
            sheet = table.sheet1
            sheet.update_title(date)
            sheet.update('A1', start_time, raw=False)
            if logdata:
                insert_array(sheet, 'B1:F1', (0, 0, '=D2', '=E2', 0))
                rows = len(logdata)
                data = []
                for i in range(rows):
                    data.append('=$A$1+time(0,0,B{}/1000)'.format(i + 2))
                insert_array(sheet, 'A2:A{}'.format(rows + 1), data)
                data = []
                for i in range(rows):
                    data.append('=C{}-C{}'.format(i + 2, i + 1))
                insert_array(sheet, 'F2:F{}'.format(rows + 1), data)
                if len(logdata[0]) != 4:
                    error('Bad log file data')
                insert_matrix(sheet, 'B2:E{}'.format(rows + 1), logdata)

                sheet2 = table.add_worksheet(TOTAL_SHEET_NAME, 100, 10, index=None)
                insert_array(sheet2, 'A1:G1', (date, 'A',
                                               "=max('{}'!C1:'{}'!C22)".format(date, date),
                                               '=round(C1*0.23*PI(),0)',
                                               "=average('{}'!D2:'{}'!D22)".format(date, date),
                                               "=average('{}'!E2:'{}'!E22)".format(date, date),
                                               '=D1'))
                data = []
                for i in range(rows):
                    data.append((date,
                                 "='{}'!A{}".format(date, i + 1),
                                 "='{}'!D{}".format(date, i + 1),
                                 "='{}'!E{}".format(date, i + 1),
                                 "='{}'!F{}".format(date, i + 1)))
                insert_matrix(sheet2, 'A3:E{}'.format(rows + 3), data)
            if histdata:
                rows = len(histdata)
                if len(histdata[0]) != 2:
                    error('Bad histogram file data')
                insert_matrix(sheet, 'G1:H{}'.format(rows + 1), histdata)
            if fulldata:
                rows = len(fulldata)
                cols = len(fulldata[0])
                if cols != 3:
                    error('Bad fulllog file data')
                data = []
                for i in range(rows):
                    data.append('=$A$1+time(0,0,J{}/1000)'.format(i + 1))
                insert_array(sheet, 'I1:I{}'.format(rows + 1), data)
                insert_matrix(sheet, 'J1:L{}'.format(rows + 1), fulldata)
                data = []
                for i in range(rows):
                    data.append('=round(L{}*pi()*0.23,1)'.format(i + 1))
                insert_array(sheet, 'M1:M{}'.format(rows + 1), data)
    except google.auth.exceptions.TransportError as e:
        error('Sheets connection error: {}'.format(e))
    except gspread.exceptions.APIError as e:
        error('Sheets error: {}'.format(e))
