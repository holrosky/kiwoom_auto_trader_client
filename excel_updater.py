import datetime
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
        spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1hITBvQyCT8Jk_0fk8Hurg1ZXuz9AajuzCX5wMsey3t8/edit#gid=0'
        # 스프레스시트 문서 가져오기
        self.doc = gc.open_by_url(spreadsheet_url)

        self.queue = deque()

        # 시트 선택하기

        add_excel_thread = threading.Thread(target=self.add_trade_info_to_excel)
        add_excel_thread.start()


    def add_trade_info_to_excel_queue(self, type, info):
        self.queue.append((type, info))
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

                    if data[0] == 'total':
                        worksheet = self.doc.worksheet('종합')
                    elif data[0] == 'enter' or data[0] == 'clear':
                        worksheet = self.doc.worksheet('진입/청산')

                    worksheet.insert_row(data[1], 2)
                    error_flag = False

            except Exception as e:
                time.sleep(1)
                error_flag = True

            time.sleep(0.5)