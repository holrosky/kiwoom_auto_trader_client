import os
import sys
import threading
from collections import deque

import pandas
import json

from multiprocessing import Process, freeze_support
from PyQt5.QtWidgets import QMainWindow, QApplication


import aws_mqtt
import excel_updater
import kiwoom_api
import pyautogui
import pygetwindow as gw
import datetime
import pytz
import time

import strategy
import telegram_message


class KiwoomAutoTrader():
    def __init__(self):
        super().__init__()

        self.telegram = telegram_message.TelegramMessage(self)
        self.kiwoom = kiwoom_api.KiwoomAPI(self)
        self.aws_mqtt = aws_mqtt.AWS_mqtt(self)
        self.excel_updater = excel_updater.ExcelUpdater()

        self.real_data_queue = deque()
        self.order_queue = deque()
        self.complete_order_queue_dict = {}

        self.ENTER_BUY_SIGNAL = 0
        self.ENTER_SELL_SIGNAL = 1
        self.CLEAR_BUY_SIGNAL = 2
        self.CLEAR_SELL_SIGNAL = 3

        with open("config.json", "r", encoding="UTF8") as st_json:
            json_data = json.load(st_json)

        self.sCode = json_data['sCode']
        self.kiwoom_id = json_data['client_id']
        self.max_chart_length = int(json_data['max_chart_length'])

        self.has_position_dict = {}
        self.enter_type_dict = {}
        self.enter_price_dict = {}
        self.quant_dict = {}

        self.already_calced_list = []
        self.num_of_calc_indicator = 0

        self.trade_profit_dict = {}

        self.last_enter_strategy_position = {}

        self.acc_num_list = []

        self.load_needed = True
        self.first_run = True

        self.tick_dataframe_dict = {}
        self.tick_unit_list = []

        self.min_dataframe_dict = {}
        self.min_unit_list = []

        self.day_dataframe = pandas.DataFrame()

        self.stretegy_list = []

        self.populate_strategy()

        self.init()

    def init(self):
        self.kiwoom.login()
        print('login done!')

        if self.kiwoom.get_connect_state() == 1:
            print('login successful!')
            print('account password input process starting...')

            self.acc_pwd_process = Process(target=auto_acc_pwd_input)
            self.acc_pwd_process.start()

            self.kiwoom.kiwoom.dynamicCall('GetCommonFunc(QString, QString)', 'ShowAccountWindow', '')

            self.set_acc_num_list()
            #self.set_trade_profit_info()

            for each in self.acc_num_list:
                self.set_position_info(each)
                self.complete_order_queue_dict[each] = deque()

            self.kiwoom.start_subscribe_real_data(self.sCode)

            load_chart_thread = threading.Thread(target=self.load_charts)
            load_chart_thread.start()

    def load_charts(self):
        try:
            while True:
                if self.load_needed:
                    error = True

                    while error:
                        with open("setting.json", "r", encoding='utf-8') as st_json:
                            json_data = json.load(st_json)

                        try:
                            json_arr = json_data['strategy_list']
                            error = False
                        except Exception as e:
                            exc_type, exc_obj, exc_tb = sys.exc_info()
                            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                            print(e, fname, exc_tb.tb_lineno)

                    tick_set = set()
                    min_set = set()
                    indicator_list = []
                    day_dataframe_needed = False

                    for each in json_arr:
                        enter_buy_list = each['enter_buy']
                        enter_sell_list = each['enter_sell']
                        clear_buy_list = each['clear_buy']
                        clear_sell_list = each['clear_sell']

                        indicator_list.append(enter_buy_list)
                        indicator_list.append(enter_sell_list)
                        indicator_list.append(clear_buy_list)
                        indicator_list.append(clear_sell_list)

                        for each_list in indicator_list:
                            for each_indicator in each_list:
                                try:
                                    if each_indicator['left_indicator_time_type'] == 'tick':
                                        tick_set.add(int(each_indicator['left_indicator_unit']))

                                    elif each_indicator['left_indicator_time_type'] == 'min':
                                        min_set.add(int(each_indicator['left_indicator_unit']))

                                    elif each_indicator['left_indicator_time_type'] == 'day':
                                        day_dataframe_needed = True

                                    if each_indicator['right_indicator_time_type'] == 'tick':
                                        tick_set.add(int(each_indicator['right_indicator_unit']))

                                    elif each_indicator['right_indicator_time_type'] == 'min':
                                        min_set.add(int(each_indicator['right_indicator_unit']))

                                    elif each_indicator['right_indicator_time_type'] == 'day':
                                        day_dataframe_needed = True
                                except Exception as e:
                                    pass
                                try:
                                    if each_indicator['indicator_time_type'] == 'tick':
                                        tick_set.add(int(each_indicator['indicator_unit']))

                                    elif each_indicator['indicator_time_type'] == 'min':
                                        min_set.add(int(each_indicator['indicator_unit']))

                                    elif each_indicator['indicator_time_type'] == 'day':
                                        day_dataframe_needed = True
                                except Exception as e:
                                    pass

                                try:
                                    if each_indicator['name'] == '가격지표':
                                        day_dataframe_needed = True

                                except Exception as e:
                                    pass

                    self.tick_unit_list = sorted(tick_set)
                    self.min_unit_list = sorted(min_set)

                    for each in self.tick_unit_list:
                        if each not in self.tick_dataframe_dict:
                            self.tick_dataframe_dict[each] = self.kiwoom.get_ohlcv(self.sCode, 'tick', each)


                    for each in self.min_unit_list:
                        if each not in self.min_dataframe_dict:
                            self.min_dataframe_dict[each] = self.kiwoom.get_ohlcv(self.sCode, 'min', each)



                    if day_dataframe_needed and self.day_dataframe.empty:
                        #print('load day')
                        self.day_dataframe = self.kiwoom.get_ohlcv(self.sCode, 'day', '0')

                    if not day_dataframe_needed and not self.day_dataframe.empty:
                        #print('del day')
                        self.day_dataframe = pandas.DataFrame()

                    remove_key_tick_dict = []
                    remove_key_min_dict = []

                    for k, v in self.tick_dataframe_dict.items():
                        if k not in self.tick_unit_list:
                            remove_key_tick_dict.append(k)

                    for k, v in self.min_dataframe_dict.items():
                        if k not in self.min_unit_list:
                            remove_key_min_dict.append(k)

                    list(map(self.tick_dataframe_dict.pop, remove_key_tick_dict))
                    list(map(self.min_dataframe_dict.pop, remove_key_min_dict))

                    for each in self.stretegy_list:
                        each.load_strategy()

                    if self.first_run:
                        self.first_run = False
                        process_real_data_thread = threading.Thread(target=self.process_real_data)
                        process_real_data_thread.start()

                        process_order_thread = threading.Thread(target=self.process_order)
                        process_order_thread.start()

                    self.load_needed = False

                else:
                    time.sleep(0.1)

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, fname, exc_tb.tb_lineno)

    def populate_strategy(self):
        with open("setting.json", "r", encoding='utf-8') as st_json:
            json_data = json.load(st_json)

        json_arr = json_data['strategy_list']

        for position in range(len(json_arr)):
            self.stretegy_list.append(strategy.Strategy(self, position))

    def set_acc_num_list(self):
        try:
            with open("setting.json", "r", encoding="UTF8") as st_json:
                json_data = json.load(st_json)

            self.acc_num_list = self.kiwoom.get_login_info('ACCNO').split(';')
            self.acc_num_list.pop()

            print('acc_list : ', self.acc_num_list)

            json_data['acc_num_list'] = self.acc_num_list

            with open('setting.json', 'w', encoding="UTF8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)

        except Exception as e:
            print('set_acc_error')

    def set_position_info(self, acc_num):
        try:
            with open("position.json", "r", encoding="UTF8") as st_json:
                json_data = json.load(st_json)

            is_same = True

            for each in self.acc_num_list:
                if each not in json_data:
                    is_same = False
                    break

            if not is_same:
                json_data = {}
                for each in self.acc_num_list:
                    json_data[each] = {}

                with open('position.json', 'w', encoding="UTF8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)

        except Exception as e:
            print('set_position_info')

    def set_trade_profit_info(self):
        if self.is_ny_market_open():
            print('market open')
            now = datetime.datetime.now()

            for each in self.has_position_dict:
                day_profit_info = self.get_day_profit(each, now.strftime("%Y%m%d"))
                print(each)
                self.trade_profit_dict[each] = float(day_profit_info['청산손익'])
        else:
            print('market close')
            for each in self.has_position_dict:
                self.trade_profit_dict[each] = 0

    # A call-back function to update required chart dataframes, which is called by Kiwoom API upon trade occurs
    def real_data_recv(self, recv_data):
        self.real_data_queue.append(recv_data)

    # Once chart is updated, get the signal
    def process_real_data(self):
        while True:
            try:
                if self.real_data_queue:
                    recv_data = self.real_data_queue.popleft()

                    #print('큐 길이 :', len(self.real_data_queue))

                    try:

                        for k, v in self.tick_dataframe_dict.items():
                            self.tick_dataframe_dict[k] = self.append_tick_df(recv_data, v, k)

                    except Exception as e:
                        pass

                    try:
                        for k, v in self.min_dataframe_dict.items():
                            self.min_dataframe_dict[k] = self.append_min_df(recv_data, v, k)



                    except Exception as e:
                        pass

                    try:
                        if not self.day_dataframe.empty:
                            self.day_dataframe = self.append_day_df(recv_data, self.day_dataframe)
                    except Exception as e:
                        pass

                    self.trim_chart()

                    for each in self.stretegy_list:
                        each.get_signal()

                    self.num_of_calc_indicator = len(self.already_calced_list)
                    self.already_calced_list = []

                else:
                    time.sleep(0.00001)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(e, fname, exc_tb.tb_lineno)


    def process_order(self):
        while True:
            try:
                if self.order_queue:
                    order_data = self.order_queue.popleft()
                    print(order_data)

                    try:
                        with open("position.json", "r", encoding="UTF8") as st_json:
                            json_data = json.load(st_json)
                    except Exception as e:
                        print(e)
                        self.order_queue.append(order_data)
                        continue

                    if str(order_data['position']) not in json_data[order_data['acc_num']]:
                        json_data[order_data['acc_num']][str(order_data['position'])] = {}
                    if 'quant' not in json_data[order_data['acc_num']][str(order_data['position'])]:
                        json_data[order_data['acc_num']][str(order_data['position'])]['quant'] = 0
                    if 'avg_price' not in json_data[order_data['acc_num']][str(order_data['position'])]:
                        json_data[order_data['acc_num']][str(order_data['position'])]['avg_price'] = 0

                        with open('position.json', 'w', encoding="UTF8") as f:
                            json.dump(json_data, f, ensure_ascii=False, indent=4)


                    if json_data[order_data['acc_num']][str(order_data['position'])]['quant'] == 0 and (
                            order_data['type'] == self.CLEAR_BUY_SIGNAL or order_data['type'] == self.CLEAR_SELL_SIGNAL):

                        temp = {}
                        temp['type'] = -1

                        self.complete_order_queue_dict[order_data['acc_num']].append(temp)

                    else:
                        if order_data['type'] == self.ENTER_BUY_SIGNAL or order_data['type'] == self.CLEAR_SELL_SIGNAL:
                            result = self.kiwoom.send_order('시장가매수', '1010', order_data['acc_num'], 2, self.sCode,
                                                            int(order_data['quant']), '0', '0', '1', '')
                        elif order_data['type'] == self.ENTER_SELL_SIGNAL or order_data['type'] == self.CLEAR_BUY_SIGNAL:
                            result = self.kiwoom.send_order('시장가매도', '1010', order_data['acc_num'], 1, self.sCode,
                                                            int(order_data['quant']), '0', '0', '1', '')

                        if result != 0:
                            self.order_queue.append(order_data)

                else:
                    time.sleep(0.00001)


            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(e, fname, exc_tb.tb_lineno)

    def process_complete_order(self, data):
        try:
            with open("position.json", "r", encoding="UTF8") as st_json:
                json_data = json.load(st_json)

            json_data[data['acc_num']][str(data['position'])]['quant'] += data['quant']

            if json_data[data['acc_num']][str(data['position'])]['quant'] == 0:
                json_data[data['acc_num']][str(data['position'])]['avg_price'] = 0
            else:
                json_data[data['acc_num']][str(data['position'])]['avg_price'] = data['avg_price']

            with open('position.json', 'w', encoding="UTF8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, fname, exc_tb.tb_lineno)

    # Update tick-chart upon trade data from Kiwoom server
    def append_tick_df(self, msg, df_in, tick_unit):
        multiple_msg_list = msg.split(',')

        for msg_each in multiple_msg_list:
            msg_info = msg_each.split(';')
            price = float(msg_info[1])
            vol = int(msg_info[2])

            if df_in['date'].iloc[-1] == '':
                now = datetime.datetime.now()
                nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')

                df_in['date'].iloc[-1] = nowDatetime

            if df_in['open'].iloc[-1] == 0:
                df_in['open'].iloc[-1] = price

            if df_in['tick'].iloc[-1] < tick_unit:
                df_in['tick'].iloc[-1] += 1

                if df_in['high'].iloc[-1] < price:
                    df_in['high'].iloc[-1] = price
                elif df_in['low'].iloc[-1] > price:
                    df_in['low'].iloc[-1] = price

                df_in['close'].iloc[-1] = price
                df_in['vol'].iloc[-1] += vol

            else:
                now = datetime.datetime.now()
                nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')

                dict = {'date': str(nowDatetime),
                        'open': price,
                        'high': price,
                        'low': price,
                        'close': price,
                        'vol': vol,
                        'tick': 1}

                df_dictionary = pandas.DataFrame([dict])
                df_in = pandas.concat([df_in, df_dictionary], ignore_index=True)

        return df_in

    def append_min_df(self, msg, df_in, min_unit):
        multiple_msg_list = msg.split(',')
        for msg_each in multiple_msg_list:
            msg_info = msg_each.split(';')
            trade_date_time = str(msg_info[0])
            price = float(msg_info[1])
            vol = int(msg_info[2])

            current_time = trade_date_time + ':00'

            latest_intergrated_df_time = str(df_in['date'].iloc[-1])

            current_time = datetime.datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')
            latest_intergrated_df_time = datetime.datetime.strptime(latest_intergrated_df_time, '%Y-%m-%d %H:%M:%S')

            diff = current_time - latest_intergrated_df_time

            if (int(diff.seconds) == 0) or (int(diff.seconds) % (min_unit * 60) != 0):
                if df_in['high'].iloc[-1] < price:
                    df_in['high'].iloc[-1] = price
                elif df_in['low'].iloc[-1] > price:
                    df_in['low'].iloc[-1] = price

                df_in['close'].iloc[-1] = price
                df_in['vol'].iloc[-1] += vol

            else:
                dict = {'date': str(current_time),
                        'open': price,
                        'high': price,
                        'low': price,
                        'close': price,
                        'vol': vol}

                df_dictionary = pandas.DataFrame([dict])
                df_in = pandas.concat([df_in, df_dictionary], ignore_index=True)

        return df_in
    # Update minute-chart upon trade data from Kiwoom server
    # def append_min_df(self, msg, df_in, min_unit):
    #     multiple_msg_list = msg.split(',')
    #
    #     temp_df = df_in.copy()
    #
    #     for msg_each in multiple_msg_list:
    #         msg_info = msg_each.split(';')
    #         trade_date_time = str(msg_info[0])
    #         price = float(msg_info[1])
    #         vol = int(msg_info[2])
    #
    #         current_time = trade_date_time + ':00'
    #
    #         latest_intergrated_df_time = str(temp_df['date'].iloc[-1])
    #
    #         current_time = datetime.datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')
    #         latest_intergrated_df_time = datetime.datetime.strptime(latest_intergrated_df_time, '%Y-%m-%d %H:%M:%S')
    #
    #         diff = current_time - latest_intergrated_df_time
    #
    #         if (int(diff.seconds) == 0) or (int(diff.seconds) % (min_unit * 60) != 0):
    #             if temp_df['high'].iloc[-1] < price:
    #                 temp_df['high'].iloc[-1] = price
    #             elif temp_df['low'].iloc[-1] > price:
    #                 temp_df['low'].iloc[-1] = price
    #
    #             temp_df['close'].iloc[-1] = price
    #             temp_df['vol'].iloc[-1] += vol
    #
    #         else:
    #             dict = {'date': str(current_time),
    #                     'open': price,
    #                     'high': price,
    #                     'low': price,
    #                     'close': price,
    #                     'vol': vol}
    #
    #             temp_df = temp_df.append(dict, ignore_index=True)
    #
    #     return temp_df

    # Update day-chart upon trade data from Kiwoom server
    def append_day_df(self, msg, df_in):
        multiple_msg_list = msg.split(',')

        for msg_each in multiple_msg_list:
            msg_info = msg_each.split(';')
            trade_date_time = str(msg_info[0])
            price = float(msg_info[1])
            vol = int(msg_info[2])

            if df_in['high'].iloc[-1] < price:
                df_in['high'].iloc[-1] = price
            elif df_in['low'].iloc[-1] > price:
                df_in['low'].iloc[-1] = price

            df_in['close'].iloc[-1] = price
            df_in['vol'].iloc[-1] += vol

        return df_in

    def trim_chart(self):
        for k, v in self.tick_dataframe_dict.items():
            if len(v) > self.max_chart_length:
                self.tick_dataframe_dict[k] = v[1:]

        for k, v in self.min_dataframe_dict.items():
            if len(v) > self.max_chart_length:
                self.min_dataframe_dict[k] = v[1:]

    def is_load_needed(self, bool):
        self.load_needed = bool

    def get_df(self, type, unit):
        if type == 'min':
            return self.min_dataframe_dict[unit]
        elif type == 'tick':
            return self.tick_dataframe_dict[unit]
        elif type == 'day':
            return self.day_dataframe

    def get_day_profit(self, acc_no, time):
        print('acc_no : ', acc_no)
        print('time : ', time)
        now = datetime.datetime.now()
        time = datetime.datetime.strptime(time, "%Y%m%d")
        diff = now - time

        if now.hour >= 0 and now.hour < 7:
            if diff.days <= 1:
                now = now - datetime.timedelta(days=1)
                today = now.strftime('%Y%m%d')

            else:
                today = time.strftime('%Y%m%d')
        else:

            today = time.strftime('%Y%m%d')

        return self.kiwoom.get_day_profit(acc_no, today)

    def is_ny_market_open(self):
        tz_ny = pytz.timezone('America/New_York')
        begin_time = datetime.time(18, 0, 0)
        end_time = datetime.time(17, 0, 0)

        check_time = datetime.datetime.now(tz_ny).time()
        if begin_time < end_time:
            return check_time >= begin_time and check_time <= end_time
        else:  # crosses midnight
            return check_time >= begin_time or check_time <= end_time

    def add_trade_info_to_excel(self, type, info):
        info['kiwoom_id'] = self.kiwoom_id
        info['sCode'] = self.sCode

        if type == 'total':
            temp = [info['trade_type'], info['strategy_name'], info['sCode'], info['kiwoom_id'], info['acc_num'], info['quant'], info['enter_type'],
                    info['enter_time'], info['enter_price'], info['enter_indicator'], info['clear_type'], info['clear_time'], info['clear_price'],
                    info['clear_indicator'], info['program_price_profit_tick'], info['real_price_profit_tick'], info['total_profit_dollar']]

        elif type == 'enter' or type == 'clear':
            temp = [info['trade_type'], info['strategy_name'], info['sCode'], info['kiwoom_id'], info['acc_num'],
                    info['quant'], info[type + '_type'], info['order_send_time'], info['order_complete_time'], info[type + '_time'],
                    info[type + '_price'], info[type + '_indicator']]

        self.excel_updater.add_trade_info_to_excel_queue(type, temp)


    def print_chart_data(self, msg):
        print(self.get_df(msg['type'], msg['unit']))

    def save_chart_data(self, msg):
        df = self.get_df(msg['type'], msg['unit'])
        df.to_csv(str(self.sCode) + '_' + str(msg['type']) + '_' + str(msg['unit']) + '.csv')

    def send_telegram(self, msg):
        self.telegram.send_message(msg)

    def add_strategy(self):
        self.stretegy_list.append(strategy.Strategy(self, len(self.stretegy_list)))

    def remove_strategy(self, position):
        if self.stretegy_list[position].has_position and not self.stretegy_list[position].is_virtual_trade() and not self.stretegy_list[position].is_simulation_strategy:
            temp_msg = {}
            temp_msg['command'] = 'remove_result_from_auto_trader'
            temp_msg['position'] = position
            temp_msg['result'] = -1

            self.aws_mqtt.publish_message(temp_msg)

        else:
            for each in self.stretegy_list:
                each.remove_strategy(position)

            self.stretegy_list.pop(position)

            temp_msg = {}
            temp_msg['command'] = 'remove_result_from_auto_trader'
            temp_msg['position'] = position
            temp_msg['result'] = 0

            self.aws_mqtt.publish_message(temp_msg)

    def get_current_price(self):
        for k, v in self.min_dataframe_dict.items():
            return v['close'].iloc[-1]

        for k, v in self.tick_dataframe_dict.items():
            return v['close'].iloc[-1]

        return self.day_dataframe['close'].iloc[-1]

    def clear_position_from_user(self, position):
        self.stretegy_list[position].clear_position_req(from_user=True)

def auto_acc_pwd_input():
    flag = True
    is_disappear = False
    while not is_disappear:
        try:
            win = gw.getWindowsWithTitle('계좌번호')[0]
            time.sleep(0.5)
            win.activate()  # 윈도우 활성화
            time.sleep(0.5)
            center = pyautogui.locateCenterOnScreen('account.png')
            time.sleep(0.5)
            pyautogui.click(center)
            time.sleep(0.5)
            with open("config.json", "r", encoding="UTF8") as st_json:
                json_data = json.load(st_json)

            if json_data['test_mode'] == 'yes':
                pyautogui.write('0000', interval=0.1)
            elif  json_data['test_mode'] == 'no':
                pyautogui.write(json_data['acc_password'], interval=0.1)
            pyautogui.press('tab')
            pyautogui.press('tab')
            pyautogui.press('enter')
            pyautogui.press('esc')

            flag = False
        except Exception as e:
            print(e)
            if not flag:
                is_disappear = True
            time.sleep(1)

if __name__ == "__main__":
    freeze_support()
    app = QApplication(sys.argv)
    kiwoom_main = KiwoomAutoTrader()
    app.exec_()