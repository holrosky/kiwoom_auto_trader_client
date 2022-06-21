import datetime
import json
import os
import sys
import threading
import time
from collections import deque

import gspread
from oauth2client.service_account import ServiceAccountCredentials

class ExcelUpdater():
    def __init__(self):
        super().__init__()

        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive',
        ]
        json_file_name = 'excel_credential.json'
        credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file_name, scope)
        gc = gspread.authorize(credentials)

        with open("config.json", "r", encoding="UTF8") as st_json:
            json_data = json.load(st_json)

        spreadsheet_url = json_data['excel_url']
        # 스프레스시트 문서 가져오기
        self.doc = gc.open_by_url(spreadsheet_url)

        self.queue = deque()

        # 시트 선택하기

        add_excel_thread = threading.Thread(target=self.add_trade_info_to_excel)
        add_excel_thread.start()

        # worksheet = self.doc.worksheet('종합')
        # print('hhh : ', worksheet.find("8989898989").row)
        # worksheet.delete_rows(worksheet.find("8989898989").row)



    def add_trade_info_to_excel_queue(self, type, info, enter_id):
        self.queue.append((type, info, enter_id))
        # if type == 'total':
        #     worksheet = self.doc.worksheet('종합')
        # elif type == 'enter' or type == 'clear':
        #     worksheet = self.doc.worksheet('진입/청산')
        #
        # worksheet.insert_row(info, 2)

    def add_trade_info_to_excel(self):
        error_flag = False
        data = tuple()

        while True:
            try:
                if error_flag:
                    worksheet.insert_row(data[1], 2)
                    error_flag = False

                if self.queue:
                    data = self.queue.popleft()

                    if data[0] == 'clear':
                        try:
                            worksheet = self.doc.worksheet('진입')
                            worksheet.delete_rows(worksheet.find(data[2]).row)

                        except Exception as e:
                            exc_type, exc_obj, exc_tb = sys.exc_info()
                            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                            print(e, fname, exc_tb.tb_lineno)

                        worksheet = self.doc.worksheet('청산')

                    elif data[0] == 'enter':
                        worksheet = self.doc.worksheet('진입')

                    worksheet.insert_row(data[1], 2)
                    error_flag = False

            except Exception as e:
                time.sleep(1)
                error_flag = True

            time.sleep(0.5)