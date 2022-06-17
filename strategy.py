import copy
import datetime
import json
import os
import sys
import threading
import time

import indicator

# MNQU22/sinbokli/test/asdjop
# {
#   "command": "print_chart_data",
#   "type": "min",
#   "unit": 1
# }

class Strategy():
    def __init__(self, parent, position):
        super().__init__()
        self.parent = parent
        self.position = position

        # if position == 0:
        #     test_thread = threading.Thread(target=self.test_thread)
        #     test_thread.start()

        self.indicator = indicator.Indicator()

        self.is_strategy_loading = True
        self.profit_limit_flag = False
        self.time_range_out_msg_sent = False
        self.time_range_in_msg_sent = False
        self.quant_need_update = True
        self.first_loading_position_check = True
        self.checking_real_position_running = False

        self.last_tema_ma_cross_setting = {}
        self.last_tema_ma_cross_value = {}

        self.last_parabolic_clear_setting = {}
        self.last_parabolic_clear_value = {}

        self.last_parabolic_enter_value = {}
        self.last_parabolic_enter_value_temp = {}

        self.last_parabolic_enter_time = ''
        self.last_parabolic_enter_time_temp = ''
        self.parabolic_same_bar_enter_times = 0

        #self.clear_at_same_bar = False
        self.parabolic_same_time_msg_sent = False

        self.indicator_dict_already_false = True

        self.indicator_dict = {}

        self.parabolic_dict = {}

        self.has_position = False
        self.waiting_enter_type = ''

        self.last_enter_type = ''
        self.current_check_position_type = ''
        self.enter_type = ''
        self.enter_price = 0
        self.current_price = 0

        self.ENTER_BUY_SIGNAL = 0
        self.ENTER_SELL_SIGNAL = 1
        self.CLEAR_BUY_SIGNAL = 2
        self.CLEAR_SELL_SIGNAL = 3

        self.CONDITION_MEET = 4
        self.CONDITION_FAIL = 5
        self.CONDITION_PASS = 6

        self.strategy_name = ''
        self.running_status = False
        self.is_simulation_strategy = True
        self.trade_account = ''
        self.max_loss = 0
        self.max_profit = 0
        self.trade_time = []
        self.quant_list = []
        self.quant = 0

        self.current_total_profit_tick = 0

        self.strategy_json = {}
        self.or_strategy_dict = {}

        self.is_there_first_meet_virtual_indicator = False
        self.is_there_box_virtual_indicator = False

        self.is_first_meet_virtual_indicator_running = False
        self.is_box_virtual_indicator_running = False

        self.current_total_profit_enter_times = 0
        self.current_total_tick_for_virtual_trade = 0

        self.virtual_current_loss_total_tick = 0
        self.virtual_current_total_enter_times = 0
        self.virtual_current_consecutive_loss_times = 0
        self.virtual_current_consecutive_profit_preserve_times = 0
        self.virtual_current_consecutive_loss_and_profit_preserve_times = 0

        self.virtual_rerun_type = 'tick'
        self.virtual_rerun_unit = 0
        self.virtual_loss_total_tick = 0
        self.virtual_total_enter_times = 0
        self.virtual_consecutive_loss_times = 0
        self.virtual_consecutive_profit_preserve_times = 0
        self.virtual_consecutive_loss_and_profit_preserve_times = 0

        self.virtual_pending_min = 0
        self.virtual_first_enter_time = None
        self.virtual_last_enter_time = None

        self.need_to_load_position = False

        self.tick_unit = 0.25
        self.tick_value = 0.5

        self.stop_trailing_on = False
        self.preserve_profit_on = False
        self.clear_by_preserver_profit = False

        self.is_there_ai_clear = False

        self.stop_trailing_price = 0
        self.preserve_profit_price = 0

        self.telegram_msg = ''

        self.enter_time_for_excel = None
        self.clear_time_for_excel = None

        self.excel_enter_indicator = ''
        self.excel_clear_indicator = ''

        self.is_there_start_for_prev_minus_current = False
        self.is_prev_minus_current_activated = True

        self.load_strategy()

    def load_strategy(self):
        try:
            self.is_strategy_loading = True

            with open("setting.json", "r", encoding='utf-8') as st_json:
                json_data = json.load(st_json)

            json_arr = json_data['strategy_list']
            self.strategy_json = json_arr[self.position]

            self.check_acc_num_changed(self.strategy_json['trade_account'])


            try:
                self.strategy_name = self.strategy_json['strategy_name']
                self.is_simulation_strategy = True if self.strategy_json['is_simulation'] == 'true' else False
                self.trade_account = self.strategy_json['trade_account']
                self.quant_list = self.strategy_json['quant']
                if self.strategy_json['running_status'] == 'true':
                    self.max_loss = int(self.strategy_json['max_loss'])
                    self.max_profit = int(self.strategy_json['max_profit'])
                self.trade_time = self.strategy_json['trade_time']
            except Exception as e:
                print(e)

            with open("position.json", "r", encoding="UTF8") as st_json:
                json_data = json.load(st_json)

            if str(self.position) not in json_data[self.trade_account]:
                json_data[self.trade_account][str(self.position)] = {}
            if 'quant' not in json_data[self.trade_account][str(self.position)]:
                json_data[self.trade_account][str(self.position)]['quant'] = 0
            if 'avg_price' not in json_data[self.trade_account][str(self.position)]:
                json_data[self.trade_account][str(self.position)]['avg_price'] = 0

            with open('position.json', 'w', encoding="UTF8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)



            if not self.running_status and self.strategy_json['running_status'] == 'true':
            #if self.strategy_json != json_arr[self.position]:
                print('load_needed')
                self.set_position_info()
                self.profit_limit_flag = False
                self.time_range_out_msg_sent = False
                self.time_range_in_msg_sent = False
                self.quant_need_update = True
                self.first_loading_position_check = True

                self.only_once_check = True
                self.already_exist_position = False

                self.stop_trailing_on = False
                self.preserve_profit_on = False
                self.clear_by_preserver_profit = False

                self.last_parabolic_enter_value = {}
                self.last_parabolic_enter_value_temp = {}

                self.last_parabolic_enter_time = ''
                self.last_parabolic_enter_time_temp = ''

                self.parabolic_same_time_msg_sent = False
                self.parabolic_dict = {}

                temp = {'enter_buy': '매수', 'enter_sell': '매도', 'clear_buy' : '매수청산', 'clear_sell' : '매도청산'}

                self.is_there_first_meet_virtual_indicator = False
                self.is_there_box_virtual_indicator = False

                self.is_first_meet_virtual_indicator_running = False
                self.is_box_virtual_indicator_running = False

                self.indicator_dict = {
                    'MA': {},
                    'TEMA': {},
                    'RSI': {},
                    'PARABOLIC': {},
                    'MACD': {}
                }

                self.is_there_start_for_prev_minus_current = False
                self.is_prev_minus_current_activated = True

                for k, v in temp.items():
                    enter_list = self.strategy_json[k]

                    for each in enter_list:
                        if each['name'] == '가상매매지표 (먼저만족)':
                            self.is_there_first_meet_virtual_indicator = True
                            self.is_there_box_virtual_indicator = False

                            self.is_first_meet_virtual_indicator_running = True
                            self.is_box_virtual_indicator_running = False

                            self.current_total_profit_enter_times = 0
                            self.current_total_tick_for_virtual_trade = 0

                            self.virtual_current_loss_total_tick = 0
                            self.virtual_current_total_enter_times = 0
                            self.virtual_current_consecutive_loss_times = 0
                            self.virtual_current_consecutive_profit_preserve_times = 0
                            self.virtual_current_consecutive_loss_and_profit_preserve_times = 0

                            self.virtual_rerun_type = each['rerun_profit_type']
                            self.virtual_rerun_unit = int(each['rerun_profit_unit'])
                            self.virtual_loss_total_tick = int(each['loss_total_tick'])
                            self.virtual_total_enter_times = int(each['total_enter_times'])
                            self.virtual_consecutive_loss_times = int(each['consecutive_loss_times'])
                            self.virtual_consecutive_profit_preserve_times = int(
                                each['consecutive_profit_preserve_times'])
                            self.virtual_consecutive_loss_and_profit_preserve_times = int(
                                each['consecutive_loss_and_profit_preserve_times'])


                        elif each['name'] == '가상매매지표 (박스권체크)':
                            self.is_there_first_meet_virtual_indicator = False
                            self.is_there_box_virtual_indicator = True

                            self.is_first_meet_virtual_indicator_running = False
                            self.is_box_virtual_indicator_running = True

                            self.current_total_profit_enter_times = 0
                            self.current_total_tick_for_virtual_trade = 0

                            self.virtual_current_total_enter_times = 0

                            self.virtual_rerun_type = each['rerun_profit_type']
                            self.virtual_rerun_unit = int(each['rerun_profit_unit'])
                            self.virtual_total_enter_times = int(each['total_enter_times'])
                            self.virtual_pending_min = int(each['pending_min'])

                        elif each['name'] == '기준선-배열/거리' or each['name'] == '기준선-크로스':
                            if each['left_indicator_type'] == 'ma':
                                self.indicator_dict['MA'][each['left_indicator_time_type'] + '_' + each['left_indicator_unit'] + '_' + each['left_indicator_period']] = False

                            if each['right_indicator_type'] == 'ma':
                                self.indicator_dict['MA'][each['right_indicator_time_type'] + '_' + each['right_indicator_unit'] + '_' + each['right_indicator_period']] = False

                            if each['left_indicator_type'] == 'tema':
                                self.indicator_dict['TEMA'][each['left_indicator_time_type'] + '_' + each['left_indicator_unit'] + '_' + each['left_indicator_period']] = False

                            if each['right_indicator_type'] == 'tema':
                                self.indicator_dict['TEMA'][each['right_indicator_time_type'] + '_' + each['right_indicator_unit'] + '_' + each['right_indicator_period']] = False

                        elif each['name'] == '기준선-직전봉' or each['name'] == '기준선-현재가':
                            if each['indicator_type'] == 'ma':
                                self.indicator_dict['MA'][each['indicator_time_type'] + '_' + each['indicator_unit'] + '_' + each['indicator_period']] = False

                            if each['indicator_type'] == 'tema':
                                self.indicator_dict['TEMA'][each['indicator_time_type'] + '_' + each['indicator_unit'] + '_' + each['indicator_period']] = False

                        elif each['name'] == 'RSI':
                            self.indicator_dict['RSI'][each['indicator_time_type'] + '_' + each['indicator_unit'] + '_' + each['rsi_period']] = False


                        elif each['name'] == 'MACD 크로스' or each['name'] == 'MACD / Osc 현재값' or each['name'] == 'MACD Osc 비교':
                            self.indicator_dict['MACD'][each['indicator_time_type'] + '_' + each['indicator_unit'] + '_' + each['macd_short']
                                                        + '_' + each['macd_long'] + '_' + each['macd_signal']] = False

                        elif each['name'] == '파라볼릭':
                            self.indicator_dict['PARABOLIC'][each['indicator_time_type'] + '_' + each['indicator_unit'] + '_' + each['prabolic_value_one'] + '_' + each['prabolic_value_two']] = False

                        elif each['name'] == '직전봉-현재가' and each['is_start'] == 'true':
                            self.is_there_start_for_prev_minus_current = True
                            self.is_prev_minus_current_activated = False

                        self.indicator_dict_already_false = True

                self.is_there_ai_clear = False if len(self.strategy_json['ai_clear']) == 0 else True

                if self.need_to_load_position:
                    self.parent.get_position_info(self.trade_account)

                self.current_total_profit_tick = 0
                self.reset_cross_check()

            self.running_status = True if self.strategy_json['running_status'] == 'true' else False
            self.is_strategy_loading = False
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, fname, exc_tb.tb_lineno)

    def get_signal(self):
        try:
            if not self.need_to_load_position:
                if not self.is_strategy_loading:
                    if self.running_status:
                        if (self.is_in_time() or self.is_virtual_trade()) and not self.profit_limit_flag:
                            self.calc_indicators()

                            if not self.has_position:
                                if self.quant_need_update:
                                    self.quant_need_update = False
                                    self.set_quant()

                                temp = {'enter_buy': '매수', 'enter_sell': '매도'}
                                for k, v in temp.items():
                                    self.current_check_position_type = v
                                    enter_list = self.strategy_json[k]

                                    now = datetime.datetime.now()

                                    self.telegram_msg = '전략명 : ' + self.strategy_name + ' (' + v + ' 만족)\n'
                                    self.telegram_msg += '계약수 : ' + str(self.quant) + '\n'
                                    self.telegram_msg += '전략 확인 시작 시간 : \n' + now.strftime('%Y-%m-%d %H:%M:%S.%f') + '\n'

                                    enter_meet = True

                                    self.or_strategy_dict = {}
                                    for each in enter_list:
                                        if self.indicator_check(each) == self.CONDITION_FAIL:
                                            enter_meet = False
                                            break


                                    if enter_meet:
                                        now = datetime.datetime.now()
                                        for each in self.or_strategy_dict:
                                            if not self.or_strategy_dict[each]:
                                                enter_meet = False
                                                break



                                    if enter_meet:
                                        now = datetime.datetime.now()
                                        print('전략만족 : ', now.strftime('%Y-%m-%d %H:%M:%S.%f'))
                                        if self.virtual_first_enter_time == None:
                                            self.virtual_first_enter_time = datetime.datetime.now()

                                        if self.is_simulation_strategy or self.is_virtual_trade():

                                            self.enter_position_req(enter_type=v)


                                        else:
                                            now = datetime.datetime.now()
                                            print('전략만족 - 3 : ', now.strftime('%Y-%m-%d %H:%M:%S.%f'))

                                            if v == '매수':
                                                self.waiting_enter_type = '매수'
                                                self.parent.order_queue.append(
                                                    {'type': self.ENTER_BUY_SIGNAL, 'acc_num': self.trade_account,
                                                     'quant': self.quant, 'position': self.position})
                                            else:
                                                self.waiting_enter_type = '매도'
                                                self.parent.order_queue.append(
                                                    {'type': self.ENTER_SELL_SIGNAL, 'acc_num': self.trade_account,
                                                     'quant': self.quant, 'position': self.position})

                                            self.enter_position_req()

                                        break

                                self.reset_cross_check()

                            else:
                                self.parabolic_same_time_msg_sent = False
                                self.current_price = self.parent.get_current_price()

                                now = datetime.datetime.now()

                                self.telegram_msg = '전략명 : ' + self.strategy_name + ' (청산 만족)\n'
                                self.telegram_msg += '계약수 : ' + str(self.quant) + '\n'
                                self.telegram_msg += '전략 확인 시작 시간 : \n' + now.strftime('%Y-%m-%d %H:%M:%S.%f') + '\n'

                                if self.need_to_clear_position_by_profit_limit():
                                    if self.is_simulation_strategy:
                                        self.clear_position_req(from_user=False)

                                    else:
                                        if self.enter_type == '매수':
                                            self.waiting_enter_type = '매도'
                                            self.parent.order_queue.append({'type': self.CLEAR_BUY_SIGNAL, 'acc_num': self.trade_account,'quant': self.quant, 'position' : self.position})
                                        else:
                                            self.waiting_enter_type = '매수'
                                            self.parent.order_queue.append({'type': self.CLEAR_SELL_SIGNAL, 'acc_num': self.trade_account,'quant': self.quant, 'position' : self.position})

                                        self.clear_position_req(from_user=False)

                                else:
                                    clear_meet = False

                                    if self.is_there_ai_clear:
                                        clear_list = self.strategy_json['ai_clear']

                                        for each in clear_list:
                                            if self.ai_indicator_check(each) == self.CONDITION_MEET:
                                                clear_meet = True
                                                break

                                    else:
                                        clear_list = self.strategy_json['clear_buy'] if self.enter_type == '매수' else self.strategy_json[
                                            'clear_sell']


                                        for each in clear_list:
                                            if self.indicator_check(each) == self.CONDITION_MEET:
                                                clear_meet = True
                                                break

                                    if clear_meet:
                                        self.quant_need_update = True
                                        if self.is_simulation_strategy or self.is_virtual_trade():
                                            self.clear_position_req(from_user=False)

                                        else:
                                            now = datetime.datetime.now()
                                            print('전략만족 - 3 : ', now.strftime('%Y-%m-%d %H:%M:%S.%f'))

                                            if self.enter_type == '매수':
                                                self.waiting_enter_type = '매도'
                                                self.parent.order_queue.append({'type': self.CLEAR_BUY_SIGNAL, 'acc_num': self.trade_account, 'quant': self.quant, 'position' : self.position})
                                            else:
                                                self.waiting_enter_type = '매수'
                                                self.parent.order_queue.append({'type': self.CLEAR_SELL_SIGNAL, 'acc_num': self.trade_account,'quant': self.quant, 'position' : self.position})

                                            self.clear_position_req(from_user=False)

                        else:
                            if not self.indicator_dict_already_false:
                                for k, v in self.indicator_dict.items():
                                    for kk, vv in v.items():
                                        self.indicator_dict[k][kk] = False

                                self.indicator_dict_already_false = True
            else:
                if not self.checking_real_position_running:
                    self.checking_real_position_running = True
                    checking_real_position_thread = threading.Thread(target=self.set_real_position)
                    checking_real_position_thread.start()

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, fname, exc_tb.tb_lineno)

    def indicator_check(self, info):
        try:
            if info['name'] == '기준선-배열/거리':
                left_col_name = ''

                left_df = self.parent.get_df(info['left_indicator_time_type'], int(info['left_indicator_unit']))

                if info['left_indicator_type'] == 'ma':
                    left_col_name = 'MA_' + info['left_indicator_period']
                    #left_df = self.indicator.get_ma(left_df, int(info['left_indicator_period']))
                elif info['left_indicator_type'] == 'tema':
                    left_col_name = 'TEMA_' + info['left_indicator_period']
                    #left_df = self.indicator.get_tema(left_df, int(info['left_indicator_period']))

                right_col_name = ''

                right_df = self.parent.get_df(info['right_indicator_time_type'], int(info['right_indicator_unit']))

                if info['right_indicator_type'] == 'ma':
                    right_col_name = 'MA_' + info['right_indicator_period']
                    #right_df = self.indicator.get_ma(right_df, int(info['right_indicator_period']))
                elif info['right_indicator_type'] == 'tema':
                    right_col_name = 'TEMA_' + info['right_indicator_period']
                    #right_df = self.indicator.get_tema(right_df, int(info['right_indicator_period']))

                left_val = left_df[left_col_name].iloc[-1] if info['time_type'] == 'real' else \
                left_df[left_col_name].iloc[-2]
                right_val = right_df[right_col_name].iloc[-1] if info['time_type'] == 'real' else \
                right_df[right_col_name].iloc[-2]

                tick_diff_from = int(info['tick_diff_from'])
                tick_diff_to = int(info['tick_diff_to'])

                diff_val = round(left_val - right_val, 2)

                if self.has_position:
                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)

                    if (self.enter_type == '매수' and self.enter_price > self.current_price) or (
                            self.enter_type == '매도' and self.enter_price < self.current_price):
                        profit = profit * -1

                    target_clear_tick_from = int(info['target_clear_tick_from'])
                    target_clear_tick_to = int(info['target_clear_tick_to'])

                    if target_clear_tick_from <= profit <= target_clear_tick_to:
                        pass
                    else:
                        return self.CONDITION_FAIL

                # print(self.telegram_msg)

                if tick_diff_from <= int(diff_val // self.tick_unit) and int(
                        diff_val // self.tick_unit) <= tick_diff_to:

                    self.telegram_msg += '==============\n'

                    self.telegram_msg += '지표명 : ' + info['name'] + '\n'

                    self.telegram_msg += '봉타입 : 실시간\n' if info['time_type'] == 'real' else '봉타입 : 직전봉\n'

                    self.telegram_msg += '가장 최근 봉시간(1) : ' + left_df['date'].iloc[-1] + '\n'
                    self.telegram_msg += '가장 최근 봉시간(2) : ' + right_df['date'].iloc[-1] + '\n'

                    word_dict = {'day': '일', 'min': '분', 'tick': '틱'}

                    self.telegram_msg += info['left_indicator_unit'] + str(
                        word_dict[info['left_indicator_time_type']]) + '봉 ' + left_col_name + ' : ' + str(
                        left_val) + '\n'

                    self.telegram_msg += info['right_indicator_unit'] + str(
                        word_dict[info['right_indicator_time_type']]) + '봉 ' + right_col_name + ' : ' + str(
                        right_val) + '\n'

                    self.telegram_msg += '두 값 차이 : ' + str(diff_val) + '\n'
                    self.telegram_msg += '두 값 틱차이 : ' + str(int(diff_val // self.tick_unit)) + '\n'
                    self.telegram_msg += '틱 범위 : ' + str(tick_diff_from) + ' ~ ' + str(tick_diff_to) + '\n'

                    return self.CONDITION_MEET
                else:
                    return self.CONDITION_FAIL

            elif info['name'] == '기준선-크로스':
                test_flag = False
                if self.last_tema_ma_cross_setting and self.last_enter_type == self.current_check_position_type:
                    return self.CONDITION_FAIL

                if self.last_tema_ma_cross_setting == info:
                    info = self.last_tema_ma_cross_setting
                    pre_left_val = self.last_tema_ma_cross_value['pre_left_val']
                    pre_right_val = self.last_tema_ma_cross_value['pre_right_val']

                    current_left_val = self.last_tema_ma_cross_value['current_left_val']
                    current_right_val = self.last_tema_ma_cross_value['current_right_val']

                    left_col_name = self.last_tema_ma_cross_value['left_col_name']
                    right_col_name = self.last_tema_ma_cross_value['right_col_name']

                else:
                    test_flag = True
                    left_col_name = ''

                    left_df = self.parent.get_df(info['left_indicator_time_type'], int(info['left_indicator_unit']))

                    if info['left_indicator_type'] == 'ma':
                        left_col_name = 'MA_' + info['left_indicator_period']
                        #left_df = self.indicator.get_ma(left_df, int(info['left_indicator_period']))
                    elif info['left_indicator_type'] == 'tema':
                        left_col_name = 'TEMA_' + info['left_indicator_period']
                        #left_df = self.indicator.get_tema(left_df, int(info['left_indicator_period']))

                    right_col_name = ''

                    right_df = self.parent.get_df(info['right_indicator_time_type'], int(info['right_indicator_unit']))

                    if info['right_indicator_type'] == 'ma':
                        right_col_name = 'MA_' + info['right_indicator_period']
                        #right_df = self.indicator.get_ma(right_df, int(info['right_indicator_period']))
                    elif info['right_indicator_type'] == 'tema':
                        right_col_name = 'TEMA_' + info['right_indicator_period']
                        #right_df = self.indicator.get_tema(right_df, int(info['right_indicator_period']))

                    if info['time_type'] == 'real':
                        pre_left_val = left_df[left_col_name].iloc[-2]
                        pre_right_val = right_df[right_col_name].iloc[-2]
                        current_left_val = left_df[left_col_name].iloc[-1]
                        current_right_val = right_df[right_col_name].iloc[-1]
                    else:
                        pre_left_val = left_df[left_col_name].iloc[-3]
                        pre_right_val = right_df[right_col_name].iloc[-3]
                        current_left_val = left_df[left_col_name].iloc[-2]
                        current_right_val = right_df[right_col_name].iloc[-2]

                        # print(self.telegram_msg)

                if self.has_position:
                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)

                    if (self.enter_type == '매수' and self.enter_price > self.current_price) or (
                            self.enter_type == '매도' and self.enter_price < self.current_price):
                        profit = profit * -1

                    target_clear_tick_from = int(info['target_clear_tick_from'])
                    target_clear_tick_to = int(info['target_clear_tick_to'])

                    if target_clear_tick_from <= profit <= target_clear_tick_to:
                        pass
                    else:
                        return self.CONDITION_FAIL

                if (info['cross_type'] == 'golden_cross' and pre_left_val < pre_right_val and current_left_val > current_right_val) or \
                        (info['cross_type'] == 'dead_cross' and pre_left_val > pre_right_val and current_left_val < current_right_val):

                    self.telegram_msg += '==============\n'

                    self.telegram_msg += '지표명 : ' + info['name'] + '\n'

                    self.telegram_msg += '봉타입 : 실시간\n' if info['time_type'] == 'real' else '봉타입 : 직전봉\n'

                    if test_flag:
                        self.telegram_msg += '가장 최근 봉시간(1) : ' + left_df['date'].iloc[-1] + '\n'
                        self.telegram_msg += '가장 최근 봉시간(2) : ' + right_df['date'].iloc[-1] + '\n'


                    if info['cross_type'] == 'golden_cross':
                        self.telegram_msg += '크로스 타입 : 골든크로스\n'
                    else:
                        self.telegram_msg += '크로스 타입 : 데드크로스\n'

                    word_dict = {'day': '일', 'min': '분', 'tick': '틱'}

                    self.telegram_msg += info['left_indicator_unit'] + str(
                        word_dict[info['left_indicator_time_type']]) + '봉 기준선 ' + left_col_name + ' : ' + str(
                        current_left_val) + '\n'
                    self.telegram_msg += info['left_indicator_unit'] + str(
                        word_dict[info['left_indicator_time_type']]) + '봉 이전 ' + left_col_name + ' : ' + str(
                        pre_left_val) + '\n'

                    self.telegram_msg += info['right_indicator_unit'] + str(
                        word_dict[info['right_indicator_time_type']]) + '봉 기준선 ' + right_col_name + ' : ' + str(
                        current_right_val) + '\n'
                    self.telegram_msg += info['right_indicator_unit'] + str(
                        word_dict[info['right_indicator_time_type']]) + '봉 이전 ' + right_col_name + ' : ' + str(
                        pre_right_val) + '\n'

                    if self.has_position:
                        self.last_tema_ma_cross_setting = info
                        self.last_tema_ma_cross_value['pre_left_val'] = pre_left_val
                        self.last_tema_ma_cross_value['pre_right_val'] = pre_right_val

                        self.last_tema_ma_cross_value['current_left_val'] = current_left_val
                        self.last_tema_ma_cross_value['current_right_val'] = current_right_val

                        self.last_tema_ma_cross_value['left_col_name'] = left_col_name
                        self.last_tema_ma_cross_value['right_col_name'] = right_col_name

                    return self.CONDITION_MEET

                # elif not self.has_position and ((self.ma_cross_swapping_check and info['left_indicator_type'] == 'ma' and info['right_indicator_type'] == 'ma') or \
                #         (self.tema_cross_swapping_check and info['left_indicator_type'] == 'tema' and info['right_indicator_type'] == 'tema')):
                #
                #     print('self.last_enter_type : ', self.last_enter_type)
                #     print('self.current_check_position_type : ', self.current_check_position_type)
                #     if self.last_enter_type != self.current_check_position_type:
                #
                #         self.telegram_msg += '==============\n'
                #
                #         self.telegram_msg += '지표명 : ' + info['name'] + '\n'
                #
                #         self.telegram_msg += '!!!포지션 스왑입니다.!!!\n'
                #         self.telegram_msg += self.current_check_position_type + ' 진입합니다.\n'
                #
                #         return self.CONDITION_MEET

                else:
                    return self.CONDITION_FAIL


            elif info['name'] == '기준선-직전봉':
                col_name = ''

                df = self.parent.get_df(info['indicator_time_type'], int(info['indicator_unit']))

                if info['indicator_type'] == 'ma':
                    col_name = 'MA_' + info['indicator_period']
                    #df = self.indicator.get_ma(df, int(info['indicator_period']))
                elif info['indicator_type'] == 'tema':
                    col_name = 'TEMA_' + info['indicator_period']
                    #df = self.indicator.get_tema(df, int(info['indicator_period']))

                pre_val = df[info['ohcl_type']].iloc[-2]
                current_val = df[col_name].iloc[-2]

                tick_diff_from = int(info['tick_diff_from'])
                tick_diff_to = int(info['tick_diff_to'])

                diff_val = round(current_val - pre_val, 2)

                # print(self.telegram_msg)

                if self.has_position:
                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)

                    if (self.enter_type == '매수' and self.enter_price > self.current_price) or (
                            self.enter_type == '매도' and self.enter_price < self.current_price):
                        profit = profit * -1

                    target_clear_tick_from = int(info['target_clear_tick_from'])
                    target_clear_tick_to = int(info['target_clear_tick_to'])

                    if target_clear_tick_from <= profit <= target_clear_tick_to:
                        pass
                    else:
                        return self.CONDITION_FAIL

                if tick_diff_from <= int(diff_val // self.tick_unit) and int(
                        diff_val // self.tick_unit) <= tick_diff_to:

                    self.telegram_msg += '==============\n'

                    self.telegram_msg += '지표명 : ' + info['name'] + '\n'

                    self.telegram_msg += '가장 최근 봉시간 : ' + df['date'].iloc[-1] + '\n'

                    word_ohcl_dict = {'open': '시가', 'high': '고가', 'close': '종가', 'low': '저가'}

                    word_dict = {'day': '일', 'min': '분', 'tick': '틱'}

                    self.telegram_msg += info['indicator_unit'] + str(
                        word_dict[info['indicator_time_type']]) + '봉 기준선 ' + col_name + ' : ' + str(current_val) + '\n'
                    self.telegram_msg += info['indicator_unit'] + str(
                        word_dict[info['indicator_time_type']]) + '봉 직전봉 ' + \
                                         word_ohcl_dict[info['ohcl_type']] + ' : ' + str(pre_val) + '\n'

                    self.telegram_msg += '두 값 차이 : ' + str(diff_val) + '\n'
                    self.telegram_msg += '두 값 틱차이 : ' + str(int(diff_val // self.tick_unit)) + '\n'
                    self.telegram_msg += '틱 범위 : ' + str(tick_diff_from) + ' ~ ' + str(tick_diff_to) + '\n'

                    return self.CONDITION_MEET
                else:
                    return self.CONDITION_FAIL

            elif info['name'] == '기준선-현재가':
                col_name = ''

                df = self.parent.get_df(info['indicator_time_type'], int(info['indicator_unit']))

                if info['indicator_type'] == 'ma':
                    col_name = 'MA_' + info['indicator_period']
                    #df = self.indicator.get_ma(df, int(info['indicator_period']))
                elif info['indicator_type'] == 'tema':
                    col_name = 'TEMA_' + info['indicator_period']
                    #df = self.indicator.get_tema(df, int(info['indicator_period']))

                current_val = df[col_name].iloc[-1]
                current_price = df['close'].iloc[-1]

                tick_diff_from = int(info['tick_diff_from'])
                tick_diff_to = int(info['tick_diff_to'])

                diff_val = round(current_val - current_price, 2)

                if info['name'] not in self.or_strategy_dict:
                    self.or_strategy_dict[info['name']] = False

                # print(self.telegram_msg)

                if self.has_position:
                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)

                    if (self.enter_type == '매수' and self.enter_price > self.current_price) or (
                            self.enter_type == '매도' and self.enter_price < self.current_price):
                        profit = profit * -1

                    target_clear_tick_from = int(info['target_clear_tick_from'])
                    target_clear_tick_to = int(info['target_clear_tick_to'])

                    if target_clear_tick_from <= profit <= target_clear_tick_to:
                        pass
                    else:
                        return self.CONDITION_FAIL

                if tick_diff_from <= int(diff_val // self.tick_unit) and int(
                        diff_val // self.tick_unit) <= tick_diff_to:

                    self.telegram_msg += '==============\n'

                    self.telegram_msg += '지표명 : ' + info['name'] + '\n'

                    self.telegram_msg += '가장 최근 봉시간 : ' + df['date'].iloc[-1] + '\n'

                    word_dict = {'day': '일', 'min': '분', 'tick': '틱'}

                    self.telegram_msg += info['indicator_unit'] + str(
                        word_dict[info['indicator_time_type']]) + '봉 기준선 ' + col_name + ' : ' + str(current_val) + '\n'

                    self.telegram_msg += '현재 가격 : ' + str(current_price) + '\n'

                    self.telegram_msg += '두 값 차이 : ' + str(diff_val) + '\n'
                    self.telegram_msg += '두 값 틱차이 : ' + str(int(diff_val // self.tick_unit)) + '\n'
                    self.telegram_msg += '틱 범위 : ' + str(tick_diff_from) + ' ~ ' + str(tick_diff_to) + '\n'

                    self.or_strategy_dict[info['name']] = True

                    return self.CONDITION_MEET
                else:
                    return self.CONDITION_PASS

            elif info['name'] == '파라볼릭':
                test_flag = False
                if self.last_parabolic_clear_setting and self.last_enter_type == self.current_check_position_type:
                    return self.CONDITION_FAIL

                df = self.parent.get_df(info['indicator_time_type'], int(info['indicator_unit']))

                PSAR_name = 'PSAR_' + str(info['prabolic_value_one']) + '_' + str(info['prabolic_value_two'])

                temp = copy.deepcopy(self.last_parabolic_clear_setting)
                temp['same_bar_enter_times'] = info['same_bar_enter_times']
                temp['target_clear_tick_from'] = info['target_clear_tick_from']
                temp['target_clear_tick_to'] = info['target_clear_tick_to']

                if temp == info:
                    pre_psar = self.last_parabolic_clear_value['pre_psar']
                    pre_price = self.last_parabolic_clear_value['pre_price']

                    current_psar = self.last_parabolic_clear_value['current_psar']
                    current_price = self.last_parabolic_clear_value['current_price']

                else:
                    test_flag = True

                    if self.last_parabolic_enter_time != df['date'].iloc[-1]:
                        self.parabolic_same_bar_enter_times = 0
                        self.last_parabolic_enter_time = ''



                    if info['time_type'] == 'real':
                        pre_psar = df[PSAR_name].iloc[-2]
                        pre_price = df['close'].iloc[-2]
                        current_psar = df[PSAR_name].iloc[-1]
                        current_price = df['close'].iloc[-1]

                        if self.parabolic_same_bar_enter_times > 0:
                            if self.has_position:
                                if self.parabolic_same_bar_enter_times == 1:
                                    if self.enter_type == '매수' and current_psar >= current_price or \
                                            self.enter_type == '매도' and current_psar <= current_price:

                                        self.telegram_msg += '==============\n'

                                        self.telegram_msg += '지표명 : ' + info['name'] + '(' + info['prabolic_value_one'] + '/' + info['prabolic_value_two'] + ')\n'
                                        self.telegram_msg += '같은 봉에서 파라볼릭 지표값 (' + str(current_psar) + ')에 도달하여 청산합니다.\n'

                                        #self.clear_at_same_bar = True
                                        self.last_parabolic_clear_setting = info

                                        return self.CONDITION_MEET
                                    else:
                                        return self.CONDITION_FAIL
                                else:
                                    if self.enter_type == '매수' and df['low'].iloc[-1] == current_price or \
                                            self.enter_type == '매도' and df['high'].iloc[-1] == current_price:

                                        current_psar = df['low'].iloc[-1] if self.enter_type == '매수' else df['high'].iloc[-1]

                                        self.telegram_msg += '==============\n'

                                        self.telegram_msg += '지표명 : ' + info['name'] + '(' + info['prabolic_value_one'] + '/' + info['prabolic_value_two'] + ')\n'
                                        self.telegram_msg += '같은 봉에서 파라볼릭 지표값 (' + str(current_psar) + ')에 도달하여 청산합니다.\n'

                                        #self.clear_at_same_bar = True
                                        self.last_parabolic_clear_setting = info

                                        return self.CONDITION_MEET
                                    else:
                                        return self.CONDITION_FAIL

                            else:
                                if temp == info:
                                    if self.parabolic_same_bar_enter_times >= int(
                                            info['same_bar_enter_times']) and not self.has_position:
                                        temp_msg = '!!!시뮬레이션 전략입니다!!!\n' if self.is_simulation_strategy else ''
                                        temp_msg += '!!!가상매매 중입니다!!!\n' if self.is_virtual_trade() else ''
                                        temp_msg = '전략명 : ' + self.strategy_name + '\n'
                                        temp_msg += '파라볼릭 지표가 같은봉 반대 진입 조건을 만족하였지만 설정 횟수만큼 진입을 하였으므로 진입하지 않습니다.\n'

                                        if not self.parabolic_same_time_msg_sent:
                                            self.parabolic_same_time_msg_sent = True
                                            self.parent.send_telegram(temp_msg)

                                        return self.CONDITION_FAIL

                                    self.telegram_msg += '==============\n'

                                    self.telegram_msg += '지표명 : ' + info['name'] + '(' + info['prabolic_value_one'] + '/' + info['prabolic_value_two'] + ')\n'
                                    self.telegram_msg += '같은 봉에서 반대 진입 합니다.\n'

                                    return self.CONDITION_MEET
                                else:
                                    return self.CONDITION_FAIL

                    else:
                        pre_psar = df[PSAR_name].iloc[-3]
                        pre_price = df['close'].iloc[-3]
                        current_psar = df[PSAR_name].iloc[-2]
                        current_price = df['close'].iloc[-2]

                diff_val = round(current_psar - current_price, 2)

                if self.has_position:
                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)

                    if (self.enter_type == '매수' and self.enter_price > self.current_price) or (
                            self.enter_type == '매도' and self.enter_price < self.current_price):
                        profit = profit * -1

                    target_clear_tick_from = int(info['target_clear_tick_from'])
                    target_clear_tick_to = int(info['target_clear_tick_to'])

                    if target_clear_tick_from <= profit <= target_clear_tick_to:
                        pass
                    else:
                        return self.CONDITION_FAIL

                if (info['prabolic_type'] == 'buy' and current_price > current_psar) or \
                        (info['prabolic_type'] == 'sell' and current_price < current_psar) or \
                        (info['prabolic_type'] == 'golden_cross' and pre_price < pre_psar and current_price > current_psar) or \
                        (info['prabolic_type'] == 'dead_cross' and pre_price > pre_psar and current_price < current_psar):


                    # if self.last_parabolic_enter_value and \
                    #         self.last_parabolic_enter_value['pre_psar'] == pre_psar and \
                    #         self.last_parabolic_enter_value['current_psar'] == current_psar and \
                    #         not self.has_position:
                    #     temp_msg = '!!!시뮬레이션 전략입니다!!!\n' if self.is_simulation_strategy else ''
                    #     temp_msg += '!!!가상매매 중입니다!!!\n' if self.is_virtual_trade() else ''
                    #     temp_msg = '전략명 : ' + self.strategy_name + '\n'
                    #     temp_msg += '파라볼릭 지표가 진입 조건을 만족하였지만 이미 같은 파라볼릭 값으로 진입을 하였으므로 진입하지 않습니다.\n'
                    #
                    #     if not self.parabolic_same_time_msg_sent:
                    #         self.parabolic_same_time_msg_sent = True
                    #         self.parent.send_telegram(temp_msg)
                    #
                    #     return self.CONDITION_FAIL


                    self.telegram_msg += '==============\n'

                    self.telegram_msg += '지표명 : ' + info['name'] + '(' + info['prabolic_value_one'] + '/' + info[
                        'prabolic_value_two'] + ')\n'

                    if test_flag:
                        self.telegram_msg += '가장 최근 봉시간 : ' + df['date'].iloc[-1] + '\n'


                    self.telegram_msg += '봉타입 : 실시간\n' if info['time_type'] == 'real' else '봉타입 : 직전봉\n'

                    word_dict = {'buy': '매수', 'sell': '매도', 'golden_cross': '골든크로스', 'dead_cross': '데드크로스'}
                    self.telegram_msg += '기준 : ' + word_dict[info['prabolic_type']] + '\n'

                    word_dict = {'day': '일', 'min': '분', 'tick': '틱'}

                    if info['time_type'] == 'real':
                        self.telegram_msg += info['indicator_unit'] + word_dict[
                            info['indicator_time_type']] + '봉 파라볼릭 현재값 : ' + str(current_psar) + '\n'
                        self.telegram_msg += info['indicator_unit'] + word_dict[
                            info['indicator_time_type']] + '봉 현재 가격 : ' + str(current_price) + '\n'

                        if info['prabolic_type'] == 'golden_cross' or info['prabolic_type'] == 'dead_cross':
                            self.telegram_msg += info['indicator_unit'] + word_dict[
                                info['indicator_time_type']] + '봉 파라볼릭 직전값 : ' + str(pre_psar) + '\n'
                            self.telegram_msg += info['indicator_unit'] + word_dict[
                                info['indicator_time_type']] + '봉 직전 가격 : ' + str(pre_price) + '\n'

                    else:
                        self.telegram_msg += info['indicator_unit'] + word_dict[
                            info['indicator_time_type']] + '봉 파라볼릭 직전값 : ' + str(current_psar) + '\n'
                        self.telegram_msg += info['indicator_unit'] + word_dict[
                            info['indicator_time_type']] + '봉 직전 가격 : ' + str(current_price) + '\n'

                        if info['prabolic_type'] == 'golden_cross' or info['prabolic_type'] == 'dead_cross':
                            self.telegram_msg += info['indicator_unit'] + word_dict[
                                info['indicator_time_type']] + '봉 파라볼릭 두번 직전값 : ' + str(pre_psar) + '\n'
                            self.telegram_msg += info['indicator_unit'] + word_dict[
                                info['indicator_time_type']] + '봉 두번 직전 가격 : ' + str(pre_price) + '\n'

                    self.telegram_msg += '두 값 차이 : ' + str(diff_val) + '\n'
                    self.telegram_msg += '두 값 틱차이 : ' + str(int(diff_val // self.tick_unit)) + '\n'

                    if self.has_position:
                        self.last_parabolic_clear_setting = info
                        self.last_parabolic_clear_value['pre_psar'] = pre_psar
                        self.last_parabolic_clear_value['pre_price'] = pre_price

                        self.last_parabolic_clear_value['current_psar'] = current_psar
                        self.last_parabolic_clear_value['current_price'] = current_price

                    else:
                        self.last_parabolic_enter_value_temp['pre_psar'] = pre_psar
                        self.last_parabolic_enter_value_temp['current_psar'] = current_psar

                        self.last_parabolic_enter_time_temp = df['date'].iloc[-1]

                    return self.CONDITION_MEET
                else:
                    return self.CONDITION_FAIL

            elif info['name'] == 'RSI':
                df = self.parent.get_df(info['indicator_time_type'], int(info['indicator_unit']))

                col_name = 'RSI_' + info['rsi_period']
                #df = self.indicator.get_rsi(df, int(info['rsi_period']))

                current_val = df[col_name].iloc[-1]

                rsi_from = int(info['rsi_from'])
                rsi_to = int(info['rsi_to'])

                # print(self.telegram_msg)

                if self.has_position:
                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)

                    if (self.enter_type == '매수' and self.enter_price > self.current_price) or (
                            self.enter_type == '매도' and self.enter_price < self.current_price):
                        profit = profit * -1

                    target_clear_tick_from = int(info['target_clear_tick_from'])
                    target_clear_tick_to = int(info['target_clear_tick_to'])

                    if target_clear_tick_from <= profit <= target_clear_tick_to:
                        pass
                    else:
                        return self.CONDITION_FAIL

                if rsi_from <= current_val and current_val <= rsi_to:

                    self.telegram_msg += '==============\n'

                    self.telegram_msg += '지표명 : ' + info['name'] + '\n'

                    self.telegram_msg += '가장 최근 봉시간 : ' + df['date'].iloc[-1] + '\n'

                    word_dict = {'day': '일', 'min': '분', 'tick': '틱'}

                    self.telegram_msg += info['indicator_unit'] + str(
                        word_dict[info['indicator_time_type']]) + '봉 ' + col_name + ' 값 : ' + str(
                        round(current_val, 2)) + '\n'

                    self.telegram_msg += 'RSI 범위 : ' + str(rsi_from) + ' ~ ' + str(rsi_to) + '\n'

                    return self.CONDITION_MEET
                else:
                    return self.CONDITION_FAIL

            elif info['name'] == '직전봉-현재가':
                df = self.parent.get_df(info['indicator_time_type'], int(info['indicator_unit']))

                pre_price_dict = {}
                pre_price_dict['open'] = df['open'].iloc[-2]
                pre_price_dict['high'] = df['high'].iloc[-2]
                pre_price_dict['close'] = df['close'].iloc[-2]
                pre_price_dict['low'] = df['low'].iloc[-2]
                pre_price_dict['middle'] = (pre_price_dict['high'] + pre_price_dict['low']) / 2

                current_price = df['close'].iloc[-1]

                tick_diff_from = int(info['tick_diff_from'])
                tick_diff_to = int(info['tick_diff_to'])

                if info['name'] not in self.or_strategy_dict:
                    self.or_strategy_dict[info['name']] = False

                diff_val = pre_price_dict[info['ohcl_type']] - current_price

                # print(self.telegram_msg)

                if self.has_position:
                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)

                    if (self.enter_type == '매수' and self.enter_price > self.current_price) or (
                            self.enter_type == '매도' and self.enter_price < self.current_price):
                        profit = profit * -1

                    target_clear_tick_from = int(info['target_clear_tick_from'])
                    target_clear_tick_to = int(info['target_clear_tick_to'])

                    if target_clear_tick_from <= profit <= target_clear_tick_to:
                        pass
                    else:
                        return self.CONDITION_FAIL

                else:
                    if self.is_there_start_for_prev_minus_current:
                        if self.is_prev_minus_current_activated:
                            pass
                        else:
                            if info['is_start'] == 'true':
                                pass
                            else:
                                return self.CONDITION_PASS

                if ((info['bar_status'] == 'bull' and pre_price_dict['open'] <= pre_price_dict['close']) or \
                    (info['bar_status'] == 'bear' and pre_price_dict['open'] >= pre_price_dict['close']) or \
                    (info['bar_status'] == 'all')) and \
                        (tick_diff_from <= int(diff_val // self.tick_unit) and int(
                            diff_val // self.tick_unit) <= tick_diff_to):

                    if info['is_start'] == 'true':
                        self.is_prev_minus_current_activated = True

                    self.telegram_msg += '==============\n'

                    self.telegram_msg += '지표명 : ' + info['name'] + '\n'

                    self.telegram_msg += '가장 최근 봉시간 : ' + df['date'].iloc[-1] + '\n'

                    word_ohcl_dict = {'open': '시가', 'high': '고가', 'close': '종가', 'low': '저가', 'middle': '중심가'}
                    word_dict = {'day': '일', 'min': '분', 'tick': '틱'}

                    self.telegram_msg += '직전봉 가격 기준 : ' + word_ohcl_dict[info['ohcl_type']] + '\n'
                    if info['bar_status'] == 'bull':
                        self.telegram_msg += '직전봉 종류 : 양봉\n'
                    elif info['bar_status'] == 'bear':
                        self.telegram_msg += '직전봉 종류 : 음봉\n'
                    elif info['bar_status'] == 'all':
                        self.telegram_msg += '직전봉 종류 : 구별안함\n'

                    self.telegram_msg += info['indicator_unit'] + str(
                        word_dict[info['indicator_time_type']]) + '봉 직전봉 값 : ' + str(
                        pre_price_dict[info['ohcl_type']]) + '\n'
                    self.telegram_msg += '현재 가격 : ' + str(current_price) + '\n'

                    self.telegram_msg += '두 값 차이 : ' + str(diff_val) + '\n'
                    self.telegram_msg += '두 값 틱차이 : ' + str(int(diff_val // self.tick_unit)) + '\n'
                    self.telegram_msg += '틱 범위 : ' + str(tick_diff_from) + ' ~ ' + str(tick_diff_to) + '\n'

                    self.or_strategy_dict[info['name']] = True

                    return self.CONDITION_MEET
                else:
                    return self.CONDITION_PASS

            elif info['name'] == '직전봉의 상태값':
                df = self.parent.get_df(info['indicator_time_type'], int(info['indicator_unit']))

                pre_open = df['open'].iloc[-2]
                pre_close = df['close'].iloc[-2]

                tick_diff_from = int(info['tick_diff_from'])

                # print(self.telegram_msg)

                if self.has_position:
                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)

                    if (self.enter_type == '매수' and self.enter_price > self.current_price) or (
                            self.enter_type == '매도' and self.enter_price < self.current_price):
                        profit = profit * -1

                    target_clear_tick_from = int(info['target_clear_tick_from'])
                    target_clear_tick_to = int(info['target_clear_tick_to'])

                    if target_clear_tick_from <= profit <= target_clear_tick_to:
                        pass
                    else:
                        return self.CONDITION_FAIL

                if (info['bar_status'] == 'bull' and pre_open <= pre_close and pre_open + (
                        self.tick_unit * tick_diff_from) < pre_close) or \
                        (info['bar_status'] == 'bear' and pre_open >= pre_close and pre_open - (
                                self.tick_unit * tick_diff_from) > pre_close):

                    self.telegram_msg += '==============\n'

                    self.telegram_msg += '지표명 : ' + info['name'] + '\n'

                    self.telegram_msg += '가장 최근 봉시간 : ' + df['date'].iloc[-1] + '\n'

                    word_dict = {'day': '일', 'min': '분', 'tick': '틱'}

                    self.telegram_msg += info['indicator_unit'] + str(
                        word_dict[info['indicator_time_type']]) + '봉 직전봉 틱차이 : ' + str(
                        int(abs(pre_open - pre_close) / self.tick_unit)) + '\n'

                    self.telegram_msg += '틱 차이 기준 : ' + str(tick_diff_from) + ' 틱 이상 \n'

                    return self.CONDITION_MEET
                else:
                    return self.CONDITION_FAIL

            elif info['name'] == '현재봉의 상태값':
                df = self.parent.get_df(info['indicator_time_type'], int(info['indicator_unit']))

                current_open = df['open'].iloc[-1]
                current_close = df['close'].iloc[-1]

                tick_diff_from = int(info['tick_diff_from'])

                # print(self.telegram_msg)

                if self.has_position:
                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)

                    if (self.enter_type == '매수' and self.enter_price > self.current_price) or (
                            self.enter_type == '매도' and self.enter_price < self.current_price):
                        profit = profit * -1

                    target_clear_tick_from = int(info['target_clear_tick_from'])
                    target_clear_tick_to = int(info['target_clear_tick_to'])

                    if target_clear_tick_from <= profit <= target_clear_tick_to:
                        pass
                    else:
                        return self.CONDITION_FAIL

                if (info['bar_status'] == 'bull' and current_open <= current_close and current_open + (
                        self.tick_unit * tick_diff_from) < current_close) or \
                        (info['bar_status'] == 'bear' and current_open >= current_close and current_open - (
                                self.tick_unit * tick_diff_from) > current_close):

                    self.telegram_msg += '==============\n'

                    self.telegram_msg += '지표명 : ' + info['name'] + '\n'

                    self.telegram_msg += '가장 최근 봉시간 : ' + df['date'].iloc[-1] + '\n'

                    word_dict = {'day': '일', 'min': '분', 'tick': '틱'}

                    self.telegram_msg += info['indicator_unit'] + str(
                        word_dict[info['indicator_time_type']]) + '봉 현재봉 틱차이 : ' + str(
                        int(abs(current_open - current_close) / self.tick_unit)) + '\n'

                    self.telegram_msg += '틱 차이 기준 : ' + str(tick_diff_from) + ' 틱 이상 \n'

                    return self.CONDITION_MEET
                else:
                    return self.CONDITION_FAIL

            elif info['name'] == '최근 n개봉':
                df = self.parent.get_df(info['indicator_time_type'], int(info['indicator_unit']))
                current_price = df['close'].iloc[-1]
                max_val = 0
                min_val = 9999999

                if info['type'] == 'high':
                    for i in range(1, int(info['num_of_bar']) + 1):
                        max_val = max(max_val, df['high'].iloc[i * -1])

                    result_val = max_val

                    diff_val = current_price - max_val
                else:
                    for i in range(1, int(info['num_of_bar'] + 1)):
                        min_val = min(min_val, df['low'].iloc[i * -1])

                    result_val = min_val
                    diff_val = min_val - current_price

                tick_diff_from = int(info['tick_diff_from'])
                tick_diff_to = int(info['tick_diff_to'])

                if info['name'] not in self.or_strategy_dict:
                    self.or_strategy_dict[info['name']] = False

                # print(self.telegram_msg)

                if self.has_position:
                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)

                    if (self.enter_type == '매수' and self.enter_price > self.current_price) or (
                            self.enter_type == '매도' and self.enter_price < self.current_price):
                        profit = profit * -1

                    target_clear_tick_from = int(info['target_clear_tick_from'])
                    target_clear_tick_to = int(info['target_clear_tick_to'])

                    if target_clear_tick_from <= profit <= target_clear_tick_to:
                        pass
                    else:
                        return self.CONDITION_FAIL


                if tick_diff_from <= int(diff_val // self.tick_unit) and int(
                        diff_val // self.tick_unit) <= tick_diff_to:

                    self.telegram_msg += '==============\n'

                    self.telegram_msg += '지표명 : ' + info['name'] + '\n'

                    self.telegram_msg += '가장 최근 봉시간 : ' + df['date'].iloc[-1] + '\n'

                    word_dict = {'day': '일', 'min': '분', 'tick': '틱'}
                    type_word_dict = {'high': '고', 'low': '저'}

                    self.telegram_msg += info['indicator_unit'] + str(
                        word_dict[info['indicator_time_type']]) + '봉 최근 ' + \
                                         info['num_of_bar'] + '개 봉의 최' + type_word_dict[info['type']] \
                                         + '가 : ' + str(result_val) + '\n'

                    self.telegram_msg += '현재 가격 : ' + str(current_price) + '\n'

                    self.telegram_msg += '두 값 차이 : ' + str(diff_val) + '\n'
                    self.telegram_msg += '두 값 틱차이 : ' + str(int(diff_val // self.tick_unit)) + '\n'
                    self.telegram_msg += '틱 범위 : ' + str(tick_diff_from) + ' ~ ' + str(tick_diff_to) + '\n'

                    self.or_strategy_dict[info['name']] = True

                    return self.CONDITION_MEET
                else:
                    return self.CONDITION_PASS

            elif info['name'] == 'MACD 크로스':
                df = self.parent.get_df(info['indicator_time_type'], int(info['indicator_unit']))
                MACD_Osc_name = 'MACD_Osc_' + info['macd_short'] + '_' + info['macd_long'] + '_' + info['macd_signal']
                #df = self.indicator.get_macd(df, float(info['macd_short']), float(info['macd_long']), float(info['macd_signal']))

                if self.has_position:
                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)

                    if (self.enter_type == '매수' and self.enter_price > self.current_price) or (
                            self.enter_type == '매도' and self.enter_price < self.current_price):
                        profit = profit * -1

                    target_clear_tick_from = int(info['target_clear_tick_from'])
                    target_clear_tick_to = int(info['target_clear_tick_to'])

                    if target_clear_tick_from <= profit <= target_clear_tick_to:
                        pass
                    else:
                        return self.CONDITION_FAIL

                current_val = 0
                pre_val = 0

                num_of_skip = 0

                if info['time_type'] == 'real':
                    start_index = 1
                else:
                    start_index = 2

                for i in range(start_index, len(df)):
                    if current_val == 0 :
                        if df[MACD_Osc_name].iloc[i * -1] != 0:
                            current_val = df[MACD_Osc_name].iloc[i * -1]
                        else:
                            num_of_skip += 1
                    else:
                        if df[MACD_Osc_name].iloc[i * -1] != 0:
                            pre_val = df[MACD_Osc_name].iloc[i * -1]
                            break
                        else:
                            num_of_skip += 1

                if (info['macd_cross_type'] == 'golden_cross' and pre_val < 0 and current_val > 0) or \
                        (info['macd_cross_type'] == 'dead_cross' and pre_val > 0 and current_val < 0):

                    self.telegram_msg += '==============\n'
                    self.telegram_msg += '지표명 : ' + info['name'] + '\n'
                    self.telegram_msg += '가장 최근 봉시간 : ' + df['date'].iloc[-1] + '\n'
                    self.telegram_msg += '봉타입 : 실시간\n' if info['time_type'] == 'real' else '봉타입 : 직전봉\n'
                    self.telegram_msg += '크로스타입 : 골든크로스\n' if info['macd_cross_type'] == 'golden_cross' else '크로스타입 : 데드크로스\n'

                    if info['time_type'] == 'real':
                        self.telegram_msg += '현재봉 MACD Osc : ' + str(current_val) + '\n'
                        self.telegram_msg += '직전봉 MACD Osc : ' + str(pre_val) + '\n'
                    else:
                        self.telegram_msg += '직전봉 MACD Osc : ' + str(current_val) + '\n'
                        self.telegram_msg += '두번 전 봉 MACD Osc : ' + str(pre_val) + '\n'

                    self.telegram_msg += 'Osc 값이 0으로 스킵된 봉 수 : ' + str(num_of_skip) + '\n'

                    return self.CONDITION_MEET

                else:
                    return self.CONDITION_FAIL

            elif info['name'] == 'MACD / Osc 현재값':
                df = self.parent.get_df(info['indicator_time_type'], int(info['indicator_unit']))

                MACD_name = 'MACD_' + info['macd_short'] + '_' + info['macd_long'] + '_' + info['macd_signal']
                MACD_Osc_name = 'MACD_Osc_' + info['macd_short'] + '_' + info['macd_long'] + '_' + info['macd_signal']
                #df = self.indicator.get_macd(df, float(info['macd_short']), float(info['macd_long']), float(info['macd_signal']))

                if self.has_position:
                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)

                    if (self.enter_type == '매수' and self.enter_price > self.current_price) or (
                            self.enter_type == '매도' and self.enter_price < self.current_price):
                        profit = profit * -1

                    target_clear_tick_from = int(info['target_clear_tick_from'])
                    target_clear_tick_to = int(info['target_clear_tick_to'])

                    if target_clear_tick_from <= profit <= target_clear_tick_to:
                        pass
                    else:
                        return self.CONDITION_FAIL

                if (float(info['macd_val_from']) <= df[MACD_name].iloc[-1] <= float(info['macd_val_to'])) or \
                        (float(info['macd_osc_val_from']) <= df[MACD_Osc_name].iloc[-1] <= float(info['macd_osc_val_to'])):

                    self.telegram_msg += '==============\n'

                    self.telegram_msg += '지표명 : ' + info['name'] + '\n'

                    self.telegram_msg += '가장 최근 봉시간 : ' + df['date'].iloc[-1] + '\n'

                    self.telegram_msg += '설정 MACD 값 범위 : ' + str(info['macd_val_from']) + ' ~ ' + str(info['macd_val_to']) + '\n'
                    self.telegram_msg += '현재 MACD 값 : ' + str(df[MACD_name].iloc[-1]) + '\n'

                    self.telegram_msg += '설정 MACD Osc 값 범위 : ' + str(info['macd_osc_val_from']) + ' ~ ' + str(info['macd_osc_val_to']) + '\n'
                    self.telegram_msg += '현재 MACD Osc 값 : ' + str(df[MACD_Osc_name].iloc[-1]) + '\n'

                    return self.CONDITION_MEET

                else:
                    return self.CONDITION_FAIL

            elif info['name'] == 'MACD Osc 비교':
                df = self.parent.get_df(info['indicator_time_type'], int(info['indicator_unit']))
                MACD_Osc_name = 'MACD_Osc_' + info['macd_short'] + '_' + info['macd_long'] + '_' + info['macd_signal']
                #df = self.indicator.get_macd(df, float(info['macd_short']), float(info['macd_long']), float(info['macd_signal']))

                if self.has_position:
                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)

                    if (self.enter_type == '매수' and self.enter_price > self.current_price) or (
                            self.enter_type == '매도' and self.enter_price < self.current_price):
                        profit = profit * -1

                    target_clear_tick_from = int(info['target_clear_tick_from'])
                    target_clear_tick_to = int(info['target_clear_tick_to'])

                    if target_clear_tick_from <= profit <= target_clear_tick_to:
                        pass
                    else:
                        return self.CONDITION_FAIL

                if (info['macd_compare_type'] == '0' and df[MACD_Osc_name].iloc[-3] > df[MACD_Osc_name].iloc[-2]) or \
                        (info['macd_compare_type'] == '1' and df[MACD_Osc_name].iloc[-3] < df[MACD_Osc_name].iloc[-2]) or \
                        (info['macd_compare_type'] == '2' and df[MACD_Osc_name].iloc[-2] > df[MACD_Osc_name].iloc[-1]) or \
                        (info['macd_compare_type'] == '3' and df[MACD_Osc_name].iloc[-2] < df[MACD_Osc_name].iloc[-1]):
                    self.telegram_msg += '==============\n'

                    self.telegram_msg += '지표명 : ' + info['name'] + '\n'

                    self.telegram_msg += '가장 최근 봉시간 : ' + df['date'].iloc[-1] + '\n'

                    word_dict = {'0': '두번째 전봉 Osc > 첫번째 전봉 Osc', '1': '두번째 전봉 Osc < 첫번째 전봉 Osc', '2': '첫번째 전봉 Osc > 현재봉 Osc', '3': '첫번째 전봉 Osc < 현재봉 Osc'}

                    self.telegram_msg += '비교 타입 : ' + word_dict[info['macd_compare_type']] + '\n'

                    self.telegram_msg += '두번째 전봉 MACD Osc : ' + str(df[MACD_Osc_name].iloc[-3]) + '\n'
                    self.telegram_msg += '첫번째 전봉 MACD Osc : ' + str(df[MACD_Osc_name].iloc[-2]) + '\n'
                    self.telegram_msg += '현재봉 MACD Osc : ' + str(df[MACD_Osc_name].iloc[-1]) + '\n'

                    return self.CONDITION_MEET
                else:
                    return self.CONDITION_FAIL

            elif info['name'] == '가격지표':
                df = self.parent.get_df('day', 0)

                if info['first_type'] == 'manual':
                    first_val = float(info['manual_price'])
                else:
                    temp = info['first_type'].split('_')

                    if 'middle' not in temp:
                        first_val = df[temp[1]].iloc[-2] if temp[0] == 'prev' else df[temp[1]].iloc[-1]
                    else:
                        first_val = (df['high'].iloc[-2] + df['low'].iloc[-2]) / 2 if temp[0] == 'prev' else \
                            (df['high'].iloc[-1] + df['low'].iloc[-1]) / 2

                current_price = df['close'].iloc[-1]

                diff_val = first_val - current_price

                first_tick_diff_from = int(info['first_tick_diff_from'])
                first_tick_diff_to = int(info['first_tick_diff_to'])

                if info['name'] not in self.or_strategy_dict:
                    self.or_strategy_dict[info['name']] = False

                # print(self.telegram_msg)
                if self.has_position:
                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)

                    if (self.enter_type == '매수' and self.enter_price > self.current_price) or (
                            self.enter_type == '매도' and self.enter_price < self.current_price):
                        profit = profit * -1

                    first_target_clear_tick_from = int(info['first_target_clear_tick_from'])
                    first_target_clear_tick_to = int(info['frist_target_clear_tick_to'])

                    if first_target_clear_tick_from <= profit <= first_target_clear_tick_to:
                        pass
                    else:
                        return self.CONDITION_FAIL

                if first_tick_diff_from <= int(diff_val // self.tick_unit) and int(
                        diff_val // self.tick_unit) <= first_tick_diff_to:

                    self.telegram_msg += '==============\n'

                    self.telegram_msg += '지표명 : ' + info['name'] + '(1)\n'

                    self.telegram_msg += '가장 최근 봉시간 : ' + df['date'].iloc[-1] + '\n'

                    word_dict = {'prev': '전일', 'today': '당일', 'open': '시가', 'high': '고가', 'close': '종가', 'low': '저가',
                                 'middle': '중심가'}

                    if info['first_type'] == 'manual':
                        self.telegram_msg += '기준선 가격 기준 : 수동\n'
                    else:
                        self.telegram_msg += '기준선 가격 기준 : ' + word_dict[temp[0]] + word_dict[temp[1]] + '\n'

                    self.telegram_msg += '기준선 가격 : ' + str(first_val) + '\n'
                    self.telegram_msg += '현재 가격 : ' + str(current_price) + '\n'

                    self.telegram_msg += '두 값 차이 : ' + str(diff_val) + '\n'
                    self.telegram_msg += '두 값 틱차이 : ' + str(int(diff_val // self.tick_unit)) + '\n'
                    self.telegram_msg += '틱 범위 : ' + str(first_tick_diff_from) + ' ~ ' + str(first_tick_diff_to) + '\n'

                    self.or_strategy_dict[info['name']] = True

                    return self.CONDITION_MEET

                else:
                    second_val = df['low'].iloc[-1] if info['second_type'] == 'today_low' else df['high'].iloc[-1]
                    today_middle = (df['high'].iloc[-1] + df['low'].iloc[-1]) / 2

                    second_calc_val = second_val * (int(info['second_numerator']) / 10)
                    diff_val = today_middle - second_calc_val

                    second_tick_diff_from = int(info['second_tick_diff_from'])
                    second_tick_diff_to = int(info['second_tick_diff_to'])

                    # print(self.telegram_msg)

                    if self.has_position:
                        profit = abs(self.current_price - self.enter_price)
                        profit = int(profit // self.tick_unit)

                        if (self.enter_type == '매수' and self.enter_price > self.current_price) or (
                                self.enter_type == '매도' and self.enter_price < self.current_price):
                            profit = profit * -1

                        second_target_clear_tick_from = int(info['second_target_clear_tick_from'])
                        second_target_clear_tick_to = int(info['second_target_clear_tick_to'])

                        if second_target_clear_tick_from <= profit <= second_target_clear_tick_to:
                            pass
                        else:
                            return self.CONDITION_FAIL

                    if second_tick_diff_from <= int(diff_val // self.tick_unit) and int(
                            diff_val // self.tick_unit) <= second_tick_diff_to:

                        self.telegram_msg += '==============\n'

                        self.telegram_msg += '지표명 : ' + info['name'] + '(2)\n'

                        self.telegram_msg += '가장 최근 봉시간 : ' + df['date'].iloc[-1] + '\n'

                        word_dict = {'today_high': '당일고가', 'today_low': '당일저가'}

                        self.telegram_msg += '당일중심가 : ' + str(today_middle) + '\n'
                        self.telegram_msg += word_dict[info['second_type']] + ' : ' + str(second_val) + '\n'
                        self.telegram_msg += word_dict[info['second_type']] + ' ' + info[
                            'second_numerator'] + '/10 : ' + str(second_calc_val) + '\n'

                        self.telegram_msg += '두 값 차이 : ' + str(diff_val) + '\n'
                        self.telegram_msg += '두 값 틱차이 : ' + str(int(diff_val // self.tick_unit)) + '\n'
                        self.telegram_msg += '틱 범위 : ' + str(second_tick_diff_from) + ' ~ ' + str(
                            second_tick_diff_to) + '\n'

                        self.or_strategy_dict[info['name']] = True

                        return self.CONDITION_MEET

                    else:
                        return self.CONDITION_PASS

            elif info['name'] == '스탑트레일링':
                start_hour = int(info['start_hour'])
                start_min = int(info['start_min'])
                end_hour = int(info['end_hour'])
                end_min = int(info['end_min'])

                if self.is_time_between(datetime.time(int(start_hour % 24), int(start_min % 60), 0), datetime.time(int(end_hour % 24), int(end_min % 60), 0)):

                    condition_tick = int(info['condition_tick'])
                    return_tick = int(info['return_tick'])

                    if self.enter_type == '매수':
                        if self.stop_trailing_on:
                            if self.current_price >= self.stop_trailing_price:
                                self.stop_trailing_price = self.current_price
                                # print('최고 이익가 : ', self.stop_trailing_price)

                            elif self.current_price <= self.stop_trailing_price - (self.tick_unit * return_tick):
                                self.stop_trailing_on = False

                                self.telegram_msg += '==============\n'

                                self.telegram_msg += '지표명 : ' + info['name'] + '\n'

                                self.telegram_msg += '발동 설정 값 : ' + str(condition_tick) + '틱\n'
                                self.telegram_msg += '리턴 설정 값 : ' + str(return_tick) + '틱\n'
                                self.telegram_msg += '진입가 : ' + str(self.enter_price) + '\n'
                                self.telegram_msg += '현재가 : ' + str(self.current_price) + '\n'
                                self.telegram_msg += '최대 이익 틱 : ' + str(
                                    int((self.stop_trailing_price - self.enter_price) / self.tick_unit)) + '\n'
                                self.telegram_msg += '청산 틱 : ' + str(
                                    int((self.current_price - self.enter_price) / self.tick_unit)) + '\n'

                                self.stop_trailing_price = 0

                                return self.CONDITION_MEET

                        else:
                            if self.current_price >= self.enter_price + (self.tick_unit * condition_tick):
                                self.stop_trailing_price = self.current_price
                                self.stop_trailing_on = True

                                temp_msg = '!!!시뮬레이션 전략입니다!!!\n' if self.is_simulation_strategy else ''
                                temp_msg += '!!!가상매매 중입니다!!!\n' if self.is_virtual_trade() else ''

                                temp_msg += '전략 이름 : ' + self.strategy_name + '\n'
                                temp_msg += '스탑트레일링 기능이 발동되었습니다.\n'
                                temp_msg += '발동 조건 틱 : ' + str(condition_tick) + '\n'

                                temp_msg += '진입가 : ' + str(self.enter_price) + '\n'
                                temp_msg += '현재가 : ' + str(self.current_price) + '\n'

                                self.parent.send_telegram(temp_msg)

                                # print(temp)

                    else:
                        if self.stop_trailing_on:
                            if self.current_price <= self.stop_trailing_price:
                                self.stop_trailing_price = self.current_price

                            elif self.current_price > self.stop_trailing_price + (self.tick_unit * return_tick):
                                self.stop_trailing_on = False

                                self.telegram_msg += '==============\n'

                                self.telegram_msg += '지표명 : ' + info['name'] + '\n'

                                self.telegram_msg += '발동 설정 값 : ' + str(condition_tick) + '틱\n'
                                self.telegram_msg += '리턴 설정 값 : ' + str(return_tick) + '틱\n'
                                self.telegram_msg += '진입가 : ' + str(self.enter_price) + '\n'
                                self.telegram_msg += '현재가 : ' + str(self.current_price) + '\n'
                                self.telegram_msg += '최대 이익 틱 : ' + str(
                                    int((self.enter_price - self.stop_trailing_price) / self.tick_unit)) + '\n'
                                self.telegram_msg += '청산 틱 : ' + str(
                                    int((self.enter_price - self.current_price) / self.tick_unit)) + '\n'

                                self.stop_trailing_price = 0
                                return self.CONDITION_MEET

                        else:
                            if self.current_price <= self.enter_price - (self.tick_unit * condition_tick):
                                self.stop_trailing_price = self.current_price
                                self.stop_trailing_on = True

                                temp_msg = '!!!시뮬레이션 전략입니다!!!\n' if self.is_simulation_strategy else ''
                                temp_msg += '!!!가상매매 중입니다!!!\n' if self.is_virtual_trade() else ''

                                temp_msg += '전략 이름 : ' + self.strategy_name + '\n'
                                temp_msg += '스탑트레일링 기능이 발동되었습니다.\n'
                                temp_msg += '발동 조건 틱 : ' + str(condition_tick) + '\n'

                                temp_msg += '진입가 : ' + str(self.enter_price) + '\n'
                                temp_msg += '현재가 : ' + str(self.current_price) + '\n'

                                self.parent.send_telegram(temp_msg)

                return self.CONDITION_PASS

            elif info['name'] == '이익보존':
                start_hour = int(info['start_hour'])
                start_min = int(info['start_min'])
                end_hour = int(info['end_hour'])
                end_min = int(info['end_min'])

                if self.is_time_between(datetime.time(int(start_hour % 24), int(start_min % 60), 0), datetime.time(int(end_hour % 24), int(end_min % 60), 0)):

                    condition_tick = int(info['condition_tick'])
                    return_tick = int(info['return_tick'])

                    if self.enter_type == '매수':
                        if self.preserve_profit_on:
                            if self.current_price <= self.preserve_profit_price - (self.tick_unit * return_tick):
                                self.preserve_profit_on = False
                                self.preserve_profit_price = 0

                                self.telegram_msg += '==============\n'

                                self.telegram_msg += '지표명 : ' + info['name'] + '\n'

                                self.telegram_msg += '발동 설정 값 : ' + str(condition_tick) + '틱\n'
                                self.telegram_msg += '리턴 설정 값 : ' + str(return_tick) + '틱\n'
                                self.telegram_msg += '진입가 : ' + str(self.enter_price) + '\n'
                                self.telegram_msg += '현재가 : ' + str(self.current_price) + '\n'
                                self.telegram_msg += '청산 틱 : ' + str(
                                    int((self.current_price - self.enter_price) / self.tick_unit)) + '\n'

                                self.clear_by_preserver_profit = True

                                return self.CONDITION_MEET

                        else:
                            if self.current_price >= self.enter_price + (self.tick_unit * condition_tick):
                                self.preserve_profit_price = self.current_price
                                self.preserve_profit_on = True

                                temp_msg = '!!!시뮬레이션 전략입니다!!!\n' if self.is_simulation_strategy else ''
                                temp_msg += '!!!가상매매 중입니다!!!\n' if self.is_virtual_trade() else ''

                                temp_msg += '전략 이름 : ' + self.strategy_name + '\n'
                                temp_msg += '이익 보존 기능이 발동되었습니다.\n'
                                temp_msg += '발동 조건 틱 : ' + str(condition_tick) + '\n'
                                temp_msg += '진입가 : ' + str(self.enter_price) + '\n'
                                temp_msg += '현재가 : ' + str(self.current_price) + '\n'

                                self.parent.send_telegram(temp_msg)


                    else:
                        if self.preserve_profit_on:
                            if self.current_price >= self.preserve_profit_price + (
                                    self.tick_unit * return_tick):
                                self.preserve_profit_on = False
                                self.preserve_profit_price = 0

                                self.telegram_msg += '==============\n'

                                self.telegram_msg += '지표명 : ' + info['name'] + '\n'

                                self.telegram_msg += '발동 설정 값 : ' + str(condition_tick) + '틱\n'
                                self.telegram_msg += '리턴 설정 값 : ' + str(return_tick) + '틱\n'
                                self.telegram_msg += '진입가 : ' + str(self.enter_price) + '\n'
                                self.telegram_msg += '현재가 : ' + str(self.current_price) + '\n'
                                self.telegram_msg += '청산 틱 : ' + str(
                                    int((self.enter_price - self.current_price) / self.tick_unit)) + '\n'

                                self.clear_by_preserver_profit = True

                                return self.CONDITION_MEET

                        else:
                            if self.current_price <= self.enter_price - (self.tick_unit * condition_tick):
                                self.preserve_profit_price = self.current_price
                                self.preserve_profit_on = True

                                temp_msg = '!!!시뮬레이션 전략입니다!!!\n' if self.is_simulation_strategy else ''
                                temp_msg += '!!!가상매매 중입니다!!!\n' if self.is_virtual_trade() else ''

                                temp_msg += '전략 이름 : ' + self.strategy_name + '\n'
                                temp_msg += '이익 보존 기능이 발동되었습니다.\n'
                                temp_msg += '발동 조건 틱 : ' + str(condition_tick) + '\n'
                                temp_msg += '진입가 : ' + str(self.enter_price) + '\n'
                                temp_msg += '현재가 : ' + str(self.current_price) + '\n'

                                self.parent.send_telegram(temp_msg)

                return self.CONDITION_PASS


            elif info['name'] == '틱 청산':
                start_hour = int(info['start_hour'])
                start_min = int(info['start_min'])
                end_hour = int(info['end_hour'])
                end_min = int(info['end_min'])

                if self.is_time_between(datetime.time(int(start_hour % 24), int(start_min % 60), 0), datetime.time(int(end_hour % 24), int(end_min % 60), 0)):

                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)
                    if (self.enter_type == '매수' and self.enter_price > self.current_price) or (self.enter_type == '매도' and self.enter_price < self.current_price):
                        profit = profit * -1


                    profit_tick = int(info['profit_tick'])
                    loss_tick = int(info['loss_tick'])

                    if profit <= loss_tick * -1 or profit_tick <= profit:
                        self.telegram_msg += '==============\n'

                        self.telegram_msg += '지표명 : ' + info['name'] + '\n'

                        self.telegram_msg += '익절 틱 값 : ' + str(profit_tick) + '틱\n'
                        self.telegram_msg += '손절 틱 값 : ' + str(loss_tick) + '틱\n'
                        self.telegram_msg += '진입가 : ' + str(self.enter_price) + '\n'
                        self.telegram_msg += '현재가 : ' + str(self.current_price) + '\n'
                        self.telegram_msg += '청산 틱 : ' + str(profit) + '\n'

                        return self.CONDITION_MEET

                return self.CONDITION_PASS


        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, fname, exc_tb.tb_lineno)

    def ai_indicator_check(self, info):
        try:
            if info['name'] == '스탑트레일링':
                start_hour = int(info['start_hour'])
                start_min = int(info['start_min'])
                end_hour = int(info['end_hour'])
                end_min = int(info['end_min'])

                if self.is_time_between(datetime.time(int(start_hour % 24), int(start_min % 60), 0), datetime.time(int(end_hour % 24), int(end_min % 60), 0)):

                    profit_from = int(info['profit_from'])
                    profit_to = int(info['profit_to'])

                    if int(profit_from) <= int(self.current_total_profit_tick) <= int(profit_to):

                        condition_tick = int(info['condition_tick'])
                        return_tick = int(info['return_tick'])

                        if self.enter_type == '매수':
                            if self.stop_trailing_on:
                                if self.current_price >= self.stop_trailing_price:
                                    self.stop_trailing_price = self.current_price
                                    # print('최고 이익가 : ', self.stop_trailing_price)

                                elif self.current_price <= self.stop_trailing_price - (self.tick_unit * return_tick):
                                    self.stop_trailing_on = False

                                    self.telegram_msg += '==============\n'
                                    self.telegram_msg += '!!!AI 청산 지표입니다.!!!\n'
                                    self.telegram_msg += '지표명 : ' + info['name'] + '\n'

                                    self.telegram_msg += '발동 설정 값 : ' + str(condition_tick) + '틱\n'
                                    self.telegram_msg += '리턴 설정 값 : ' + str(return_tick) + '틱\n'
                                    self.telegram_msg += '진입가 : ' + str(self.enter_price) + '\n'
                                    self.telegram_msg += '현재가 : ' + str(self.current_price) + '\n'
                                    self.telegram_msg += '최대 이익 틱 : ' + str(
                                        int((self.stop_trailing_price - self.enter_price) / self.tick_unit)) + '\n'
                                    self.telegram_msg += '청산 틱 : ' + str(
                                        int((self.current_price - self.enter_price) / self.tick_unit)) + '\n'

                                    self.stop_trailing_price = 0

                                    return self.CONDITION_MEET

                            else:
                                if self.current_price >= self.enter_price + (self.tick_unit * condition_tick):
                                    self.stop_trailing_price = self.current_price
                                    self.stop_trailing_on = True

                                    temp_msg = '!!!시뮬레이션 전략입니다!!!\n' if self.is_simulation_strategy else ''
                                    temp_msg += '!!!가상매매 중입니다!!!\n' if self.is_virtual_trade() else ''
                                    temp_msg += '!!!AI 청산 지표입니다.!!!\n'

                                    temp_msg += '전략 이름 : ' + self.strategy_name + '\n'
                                    temp_msg += '스탑트레일링 기능이 발동되었습니다.\n'
                                    temp_msg += '발동 조건 틱 : ' + str(condition_tick) + '\n'

                                    temp_msg += '진입가 : ' + str(self.enter_price) + '\n'
                                    temp_msg += '현재가 : ' + str(self.current_price) + '\n'

                                    self.parent.send_telegram(temp_msg)

                                    # print(temp)

                        else:
                            if self.stop_trailing_on:
                                if self.current_price <= self.stop_trailing_price:
                                    self.stop_trailing_price = self.current_price

                                elif self.current_price > self.stop_trailing_price + (self.tick_unit * return_tick):
                                    self.stop_trailing_on = False

                                    self.telegram_msg += '==============\n'
                                    self.telegram_msg += '!!!AI 청산 지표입니다.!!!\n'
                                    self.telegram_msg += '지표명 : ' + info['name'] + '\n'

                                    self.telegram_msg += '발동 설정 값 : ' + str(condition_tick) + '틱\n'
                                    self.telegram_msg += '리턴 설정 값 : ' + str(return_tick) + '틱\n'
                                    self.telegram_msg += '진입가 : ' + str(self.enter_price) + '\n'
                                    self.telegram_msg += '현재가 : ' + str(self.current_price) + '\n'
                                    self.telegram_msg += '최대 이익 틱 : ' + str(
                                        int((self.enter_price - self.stop_trailing_price) / self.tick_unit)) + '\n'
                                    self.telegram_msg += '청산 틱 : ' + str(
                                        int((self.enter_price - self.current_price) / self.tick_unit)) + '\n'

                                    self.stop_trailing_price = 0
                                    return self.CONDITION_MEET

                            else:
                                if self.current_price <= self.enter_price - (self.tick_unit * condition_tick):
                                    self.stop_trailing_price = self.current_price
                                    self.stop_trailing_on = True

                                    temp_msg = '!!!시뮬레이션 전략입니다!!!\n' if self.is_simulation_strategy else ''
                                    temp_msg += '!!!가상매매 중입니다!!!\n' if self.is_virtual_trade() else ''
                                    temp_msg += '!!!AI 청산 지표입니다.!!!\n'
                                    temp_msg += '전략 이름 : ' + self.strategy_name + '\n'
                                    temp_msg += '스탑트레일링 기능이 발동되었습니다.\n'
                                    temp_msg += '발동 조건 틱 : ' + str(condition_tick) + '\n'

                                    temp_msg += '진입가 : ' + str(self.enter_price) + '\n'
                                    temp_msg += '현재가 : ' + str(self.current_price) + '\n'

                                    self.parent.send_telegram(temp_msg)

                return self.CONDITION_PASS

            elif info['name'] == '이익보존':
                start_hour = int(info['start_hour'])
                start_min = int(info['start_min'])
                end_hour = int(info['end_hour'])
                end_min = int(info['end_min'])

                if self.is_time_between(datetime.time(int(start_hour % 24), int(start_min % 60), 0), datetime.time(int(end_hour % 24), int(end_min % 60), 0)):
                    profit_from = int(info['profit_from'])
                    profit_to = int(info['profit_to'])

                    if int(profit_from) <= int(self.current_total_profit_tick) <= int(profit_to):
                        condition_tick = int(info['condition_tick'])
                        return_tick = int(info['return_tick'])

                        if self.enter_type == '매수':
                            if self.preserve_profit_on:
                                if self.current_price <= self.preserve_profit_price - (self.tick_unit * return_tick):
                                    self.preserve_profit_on = False
                                    self.preserve_profit_price = 0

                                    self.telegram_msg += '==============\n'
                                    self.telegram_msg += '!!!AI 청산 지표입니다.!!!\n'
                                    self.telegram_msg += '지표명 : ' + info['name'] + '\n'

                                    self.telegram_msg += '발동 설정 값 : ' + str(condition_tick) + '틱\n'
                                    self.telegram_msg += '리턴 설정 값 : ' + str(return_tick) + '틱\n'
                                    self.telegram_msg += '진입가 : ' + str(self.enter_price) + '\n'
                                    self.telegram_msg += '현재가 : ' + str(self.current_price) + '\n'
                                    self.telegram_msg += '청산 틱 : ' + str(
                                        int((self.current_price - self.enter_price) / self.tick_unit)) + '\n'

                                    self.clear_by_preserver_profit = True

                                    return self.CONDITION_MEET

                            else:
                                if self.current_price >= self.enter_price + (self.tick_unit * condition_tick):
                                    self.preserve_profit_price = self.current_price
                                    self.preserve_profit_on = True

                                    temp_msg = '!!!시뮬레이션 전략입니다!!!\n' if self.is_simulation_strategy else ''
                                    temp_msg += '!!!가상매매 중입니다!!!\n' if self.is_virtual_trade() else ''
                                    temp_msg += '!!!AI 청산 지표입니다.!!!\n'
                                    temp_msg += '전략 이름 : ' + self.strategy_name + '\n'
                                    temp_msg += '이익 보존 기능이 발동되었습니다.\n'
                                    temp_msg += '발동 조건 틱 : ' + str(condition_tick) + '\n'
                                    temp_msg += '진입가 : ' + str(self.enter_price) + '\n'
                                    temp_msg += '현재가 : ' + str(self.current_price) + '\n'

                                    self.parent.send_telegram(temp_msg)


                        else:
                            if self.preserve_profit_on:
                                if self.current_price >= self.preserve_profit_price + (self.tick_unit * return_tick):
                                    self.preserve_profit_on = False
                                    self.preserve_profit_price = 0

                                    self.telegram_msg += '==============\n'
                                    self.telegram_msg += '!!!AI 청산 지표입니다.!!!\n'
                                    self.telegram_msg += '지표명 : ' + info['name'] + '\n'

                                    self.telegram_msg += '발동 설정 값 : ' + str(condition_tick) + '틱\n'
                                    self.telegram_msg += '리턴 설정 값 : ' + str(return_tick) + '틱\n'
                                    self.telegram_msg += '진입가 : ' + str(self.enter_price) + '\n'
                                    self.telegram_msg += '현재가 : ' + str(self.current_price) + '\n'
                                    self.telegram_msg += '청산 틱 : ' + str(
                                        int((self.enter_price - self.current_price) / self.tick_unit)) + '\n'

                                    self.clear_by_preserver_profit = True

                                    return self.CONDITION_MEET

                            else:
                                if self.current_price <= self.enter_price - (self.tick_unit * condition_tick):
                                    self.preserve_profit_price = self.current_price
                                    self.preserve_profit_on = True

                                    temp_msg = '!!!시뮬레이션 전략입니다!!!\n' if self.is_simulation_strategy else ''
                                    temp_msg += '!!!가상매매 중입니다!!!\n' if self.is_virtual_trade() else ''
                                    temp_msg += '!!!AI 청산 지표입니다.!!!\n'
                                    temp_msg += '전략 이름 : ' + self.strategy_name + '\n'
                                    temp_msg += '이익 보존 기능이 발동되었습니다.\n'
                                    temp_msg += '발동 조건 틱 : ' + str(condition_tick) + '\n'
                                    temp_msg += '진입가 : ' + str(self.enter_price) + '\n'
                                    temp_msg += '현재가 : ' + str(self.current_price) + '\n'

                                    self.parent.send_telegram(temp_msg)

                return self.CONDITION_PASS


            elif info['name'] == '틱 청산':
                start_hour = int(info['start_hour'])
                start_min = int(info['start_min'])
                end_hour = int(info['end_hour'])
                end_min = int(info['end_min'])

                if self.is_time_between(datetime.time(int(start_hour % 24), int(start_min % 60), 0), datetime.time(int(end_hour % 24), int(end_min % 60), 0)):
                    profit_from = int(info['profit_from'])
                    profit_to = int(info['profit_to'])

                    if int(profit_from) <= int(self.current_total_profit_tick) <= int(profit_to):

                        profit = abs(self.current_price - self.enter_price)
                        profit = int(profit // self.tick_unit)
                        if (self.enter_type == '매수' and self.enter_price > self.current_price) or (self.enter_type == '매도' and self.enter_price < self.current_price):
                            profit = profit * -1


                        profit_tick = int(info['profit_tick'])
                        loss_tick = int(info['loss_tick'])

                        if profit <= loss_tick * -1 or profit_tick <= profit:
                            self.telegram_msg += '==============\n'
                            self.telegram_msg += '!!!AI 청산 지표입니다.!!!\n'
                            self.telegram_msg += '지표명 : ' + info['name'] + '\n'

                            self.telegram_msg += '익절 틱 값 : ' + str(profit_tick) + '틱\n'
                            self.telegram_msg += '손절 틱 값 : ' + str(loss_tick) + '틱\n'
                            self.telegram_msg += '진입가 : ' + str(self.enter_price) + '\n'
                            self.telegram_msg += '현재가 : ' + str(self.current_price) + '\n'
                            self.telegram_msg += '청산 틱 : ' + str(profit) + '\n'

                            return self.CONDITION_MEET

                return self.CONDITION_PASS


        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, fname, exc_tb.tb_lineno)

    def is_virtual_trade(self):
        if (self.is_there_first_meet_virtual_indicator and self.is_first_meet_virtual_indicator_running) or \
                (self.is_there_box_virtual_indicator and self.is_box_virtual_indicator_running):
            return True

        return False

    def update_virtual_trade(self, profit):
        try:
            if self.is_virtual_trade():
                self.current_total_profit_enter_times = 0
                self.current_total_tick_for_virtual_trade = 0
                self.virtual_current_total_enter_times += 1

                if profit > 0:
                    self.virtual_current_consecutive_loss_times = 0
                else:
                    self.virtual_current_consecutive_loss_times += 1

                self.virtual_current_loss_total_tick += profit

                if self.clear_by_preserver_profit:
                    self.virtual_current_consecutive_profit_preserve_times += 1
                    self.clear_by_preserver_profit = False
                else:
                    self.virtual_current_consecutive_profit_preserve_times = 0

                self.virtual_current_consecutive_loss_and_profit_preserve_times = self.virtual_current_consecutive_loss_times + self.virtual_current_consecutive_profit_preserve_times

            else:
                if profit > 0:
                    self.current_total_profit_enter_times += 1

                self.current_total_tick_for_virtual_trade += profit

            if self.is_there_first_meet_virtual_indicator:
                if self.is_first_meet_virtual_indicator_running:
                    if (self.virtual_current_loss_total_tick <= self.virtual_loss_total_tick * -1) or \
                            (self.virtual_current_total_enter_times >= self.virtual_total_enter_times) or \
                            (self.virtual_current_consecutive_loss_times >= self.virtual_consecutive_loss_times) or \
                            (self.virtual_current_consecutive_profit_preserve_times >= self.virtual_consecutive_profit_preserve_times) or \
                            (self.virtual_current_consecutive_loss_and_profit_preserve_times >= self.virtual_consecutive_loss_and_profit_preserve_times):
                        self.is_first_meet_virtual_indicator_running = False

                        temp_msg = '!!!시뮬레이션 전략입니다!!!\n' if self.is_simulation_strategy else ''
                        temp_msg += '전략 이름 : ' + self.strategy_name + '\n'
                        temp_msg += '가상매매 (먼저만족)을 중단합니다.\n'

                        word_dict = {'tick': '틱', 'times': '회'}

                        temp_msg += '재실행 설정 값 : ' + str(self.virtual_rerun_unit) + \
                                    word_dict[str(self.virtual_rerun_type)] + ' 익절 후 재실행' + '\n'

                        temp_msg += '설정 누적 손절 틱수 : ' + str(self.virtual_loss_total_tick) + '\n'
                        temp_msg += '현재 누적 손절 틱수 : ' + str(
                            self.virtual_current_loss_total_tick) + '\n\n'

                        temp_msg += '설정 통합 진입 횟수 : ' + str(self.virtual_total_enter_times) + '\n'
                        temp_msg += '현재 통합 진입 횟수 : ' + str(
                            self.virtual_current_total_enter_times) + '\n\n'

                        temp_msg += '설정 연속 손절 횟수 : ' + str(
                            self.virtual_consecutive_loss_times) + '\n'
                        temp_msg += '현재 연속 손절 횟수 : ' + str(
                            self.virtual_current_consecutive_loss_times) + '\n\n'

                        temp_msg += '설정 연속 이익 보존 횟수 : ' + str(
                            self.virtual_consecutive_profit_preserve_times) + '\n'
                        temp_msg += '현재 연속 이익 보존 횟수 : ' + str(
                            self.virtual_current_consecutive_profit_preserve_times) + '\n\n'

                        temp_msg += '설정 연속 (손절+이익보존) 횟수 : ' + str(
                            self.virtual_consecutive_loss_and_profit_preserve_times) + '\n'
                        temp_msg += '현재 연속 (손절+이익보존) 횟수 : ' + str(
                            self.virtual_current_consecutive_loss_and_profit_preserve_times) + '\n'

                        self.parent.send_telegram(temp_msg)
                else:
                    if (self.virtual_rerun_type == 'tick' and self.virtual_rerun_unit <= self.current_total_tick_for_virtual_trade) or \
                        (self.virtual_rerun_type == 'times' and self.virtual_rerun_unit <= self.current_total_profit_enter_times):
                        self.is_first_meet_virtual_indicator_running = True

                        temp_msg = '!!!시뮬레이션 전략입니다!!!\n' if self.is_simulation_strategy else ''
                        temp_msg += '전략 이름 : ' + self.strategy_name + '\n'
                        temp_msg += '가상매매 (먼저만족)을 재실행 합니다.\n'

                        word_dict = {'tick': '틱', 'times': '회'}

                        temp_msg += '재실행 설정 값 : ' + str(self.virtual_rerun_unit) + \
                                    word_dict[str(self.virtual_rerun_type)] + ' 익절 후 재실행' + '\n'

                        temp_msg += '현재 익절 진입 횟수 : ' + str(
                            self.current_total_profit_enter_times) + '\n\n'

                        temp_msg += '현재 총 익절 틱수 : ' + str(
                            self.current_total_tick_for_virtual_trade) + '\n\n'

                        self.current_total_profit_enter_times = 0
                        self.current_total_tick_for_virtual_trade = 0

                        self.virtual_current_loss_total_tick = 0
                        self.virtual_current_total_enter_times = 0
                        self.virtual_current_consecutive_loss_times = 0
                        self.virtual_current_consecutive_profit_preserve_times = 0
                        self.virtual_current_consecutive_loss_and_profit_preserve_times = 0

                        self.parent.send_telegram(temp_msg)

            elif self.is_there_box_virtual_indicator:
                current_time = datetime.datetime.now()
                current_pending_min = (current_time - self.virtual_first_enter_time).total_seconds() // 60.0

                if self.is_box_virtual_indicator_running:
                    if current_pending_min < self.virtual_pending_min:
                        if self.virtual_current_total_enter_times >= self.virtual_total_enter_times:
                            self.is_box_virtual_indicator_running = False

                            temp_msg = '!!!시뮬레이션 전략입니다!!!\n' if self.is_simulation_strategy else ''
                            temp_msg += '전략 이름 : ' + self.strategy_name + '\n'
                            temp_msg += '가상매매 (박스권체크)를 중단합니다.\n'

                            word_dict = {'tick': '틱', 'times': '회'}

                            temp_msg += '재실행 설정 값 : ' + str(self.virtual_rerun_unit) + \
                                        word_dict[str(self.virtual_rerun_type)] + ' 익절 후 재실행' + '\n'

                            temp_msg += '설정 대기 시간 : ' + str(self.virtual_pending_min) + '분 \n'
                            temp_msg += '현재 대기 시간 : ' + str(int(current_pending_min)) + '분 \n\n'

                            temp_msg += '설정 통합 진입 횟수 : ' + str(self.virtual_total_enter_times) + '\n'
                            temp_msg += '현재 통합 진입 횟수 : ' + str(self.virtual_current_total_enter_times) + '\n\n'

                            self.parent.send_telegram(temp_msg)

                    else:
                        if (self.virtual_last_enter_time - self.virtual_first_enter_time).total_seconds() // 60.0 == 0:
                            self.virtual_first_enter_time = datetime.datetime.now()
                            self.current_total_profit_enter_times = 0
                            self.current_total_tick_for_virtual_trade = 0

                            self.virtual_current_total_enter_times = 0

                            temp_msg = '!!!시뮬레이션 전략입니다!!!\n' if self.is_simulation_strategy else ''
                            temp_msg += '전략 이름 : ' + self.strategy_name + '\n'
                            temp_msg += '가상매매 (박스권체크)의 시간이 초과되어 연장합니다.\n'

                            word_dict = {'tick': '틱', 'times': '회'}

                            temp_msg += '재실행 설정 값 : ' + str(self.virtual_rerun_unit) + \
                                        word_dict[str(self.virtual_rerun_type)] + ' 익절 후 재실행' + '\n'

                            temp_msg += '설정 대기 시간 : ' + str(self.virtual_pending_min) + '분 \n'
                            temp_msg += '현재 대기 시간 : ' + str(int(current_pending_min)) + '분 \n\n'

                            self.parent.send_telegram(temp_msg)

                        else:
                            self.virtual_first_enter_time == self.virtual_last_enter_time

                else:
                    if (self.virtual_rerun_type == 'tick' and self.virtual_rerun_unit <= self.current_total_tick_for_virtual_trade) or \
                            (self.virtual_rerun_type == 'times' and self.virtual_rerun_unit <= self.current_total_profit_enter_times):
                        self.is_box_virtual_indicator_running = True

                        temp_msg = '!!!시뮬레이션 전략입니다!!!\n' if self.is_simulation_strategy else ''
                        temp_msg += '전략 이름 : ' + self.strategy_name + '\n'
                        temp_msg += '가상매매 (박스권체크)를 재실행 합니다.\n'

                        word_dict = {'tick': '틱', 'times': '회'}

                        temp_msg += '재실행 설정 값 : ' + str(self.virtual_rerun_unit) + \
                                    word_dict[str(self.virtual_rerun_type)] + ' 익절 후 재실행' + '\n'

                        temp_msg += '현재 익절 진입 횟수 : ' + str(
                            self.current_total_profit_enter_times) + '\n\n'

                        temp_msg += '현재 총 익절 틱수 : ' + str(
                            self.current_total_tick_for_virtual_trade) + '\n\n'

                        self.current_total_profit_enter_times = 0
                        self.current_total_tick_for_virtual_trade = 0

                        self.virtual_current_total_enter_times = 0

                        self.virtual_first_enter_time = None

                        self.parent.send_telegram(temp_msg)


        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, fname, exc_tb.tb_lineno)

    def set_quant(self):
        if len(self.quant_list) == 0:
            self.quant = 1
        else:
            for each in self.quant_list:
                profit_from, profit_to, target_quant = each.split(';')

                if int(profit_from) <= int(self.current_total_profit_tick) <= int(profit_to):
                    self.quant = int(target_quant)

                    return

            self.quant = 1

    def is_profit_meet_limit(self):
        if self.current_total_profit_tick <= self.max_loss or self.max_profit <= self.current_total_profit_tick:
            if not self.profit_limit_flag:
                self.profit_limit_flag = True

                temp_msg = '!!!시뮬레이션 전략입니다!!!\n' if self.is_simulation_strategy else ''
                temp_msg += '전략 이름 : ' + self.strategy_name + '\n'
                temp_msg += '설정된 최대 손절/익절 값에 도달하여 매매를 중지합니다.\n'

                temp_msg += '현재 청산 이익 틱: ' + str(int(self.current_total_profit_tick)) + '\n'
                temp_msg += '설정 최대 손절 틱 : ' + str(self.max_loss) + '\n'
                temp_msg += '설정 최대 익절 틱 : ' + str(self.max_profit) + '\n'

                self.parent.send_telegram(temp_msg)

            return True
        return False

    def enter_position_req(self, enter_type=''):
        if self.is_simulation_strategy or self.is_virtual_trade():
            if self.is_virtual_trade():
                self.telegram_msg = '!!!가상매매 중입니다!!!\n' + self.telegram_msg
            if self.is_simulation_strategy:
                self.telegram_msg = '!!!시뮬레이션 전략입니다!!!\n' + self.telegram_msg

            self.has_position = True
            self.last_enter_type = enter_type
            self.enter_type = enter_type
            self.enter_price = self.parent.get_current_price()

            now = datetime.datetime.now()
            self.enter_time_for_excel = now.strftime('%Y-%m-%d %H:%M:%S.%f')

        else:
            self.need_to_load_position = True

        now = datetime.datetime.now()
        self.telegram_msg += '==============\n'
        self.telegram_msg += '해당 전략 기존 총 누적 틱 : \n' + str(self.current_total_profit_tick) + '\n'
        self.telegram_msg += '==============\n'
        self.telegram_msg += '전략 확인 종료 시간 : \n' + now.strftime('%Y-%m-%d %H:%M:%S.%f') + '\n'

        print('전략 확인 종료 시간 : ', now.strftime('%Y-%m-%d %H:%M:%S.%f'))


        self.excel_enter_indicator = self.telegram_msg
        self.parent.send_telegram(self.telegram_msg)

        self.reset_cross_check()
        self.last_parabolic_enter_value = self.last_parabolic_enter_value_temp

        if self.last_parabolic_enter_time == self.last_parabolic_enter_time_temp or self.last_parabolic_enter_time == '':
            self.parabolic_same_bar_enter_times += 1

        self.last_parabolic_enter_time = self.last_parabolic_enter_time_temp

        if self.is_simulation_strategy or self.is_virtual_trade():
            info = {}

            info['trade_type'] = '가상매매' if self.is_virtual_trade() else '시뮬레이션'
            info['strategy_name'] = self.strategy_name
            info['acc_num'] = self.trade_account
            info['quant'] = self.quant
            info['enter_type'] = '매수' if self.enter_type == '매수' else '매도'
            info['enter_time'] = self.enter_time_for_excel
            info['enter_price'] = self.enter_price
            info['order_send_time'] = self.enter_time_for_excel
            info['order_complete_time'] = self.enter_time_for_excel
            info['enter_indicator'] = self.excel_enter_indicator

            self.parent.add_trade_info_to_excel('enter', info)

    def clear_position_req(self, from_user):
        try:
            if from_user:
                self.excel_clear_indicator = ''

                if self.is_virtual_trade():
                    self.excel_clear_indicator += '!!!가상매매 중입니다!!!\n'
                if self.is_simulation_strategy:
                    self.excel_clear_indicator += '!!!시뮬레이션 전략입니다!!!\n'

                self.excel_clear_indicator += '유저에 의해 강제 청산 되었습니다.\n'

            else:
                if self.is_virtual_trade():
                    self.telegram_msg = '!!!가상매매 중입니다!!!\n' + self.telegram_msg
                if self.is_simulation_strategy:
                    self.telegram_msg = '!!!시뮬레이션 전략입니다!!!\n' + self.telegram_msg

                now = datetime.datetime.now()
                self.telegram_msg += '==============\n'
                self.telegram_msg += '해당 전략 기존 총 누적 틱 : \n' + str(self.current_total_profit_tick) + '\n'
                self.telegram_msg += '==============\n'
                self.telegram_msg += '전략 확인 종료 시간 : \n' + now.strftime('%Y-%m-%d %H:%M:%S.%f') + '\n'

                self.excel_clear_indicator = self.telegram_msg

                self.parent.send_telegram(self.telegram_msg)

            if self.is_simulation_strategy or self.is_virtual_trade():
                if self.has_position:
                    self.current_price = self.parent.get_current_price()
                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)
                    if self.enter_type == '매수':
                        if self.enter_price < self.current_price:
                            result = '익절'
                        else:
                            result = '손절'
                            profit = profit * -1
                    elif self.enter_type == '매도':
                        if self.enter_price > self.current_price:
                            result = '익절'
                        else:
                            result = '손절'
                            profit = profit * -1

                    if not self.is_virtual_trade():
                        self.current_total_profit_tick += profit * self.quant

                    now = datetime.datetime.now()
                    self.clear_time_for_excel = now.strftime('%Y-%m-%d %H:%M:%S.%f')
                    #
                    # self.telegram_msg = '!!!시뮬레이션 전략입니다!!!\n' if self.is_simulation_strategy else ''
                    # self.telegram_msg += '!!!가상매매 중입니다!!!\n' if self.is_virtual_trade() else ''
                    # self.telegram_msg += '!!!AI 청산입니다!!!\n' if self.is_there_ai_clear else ''
                    # self.telegram_msg += '현재 포지션을 청산합니다. (' + result + ')\n'
                    # self.telegram_msg += '전략 이름 : ' + self.strategy_name + '\n'
                    # self.telegram_msg += '계약 수 : ' + str(self.quant) + '\n'
                    # self.telegram_msg += '진입가 : ' + str(self.enter_price) + '\n'
                    # self.telegram_msg += '현재가 : ' + str(current_price) + '\n'
                    # self.telegram_msg += '청산 수익 틱 : ' + str(profit) + '\n'
                    # self.telegram_msg += '해당 전략 누적 수익 틱 : ' + str(self.current_total_profit_tick) + '\n'
                    #
                    # self.parent.send_telegram(self.telegram_msg)

                    info = {}

                    info['trade_type'] = '가상매매' if self.is_virtual_trade() else '시뮬레이션'
                    info['strategy_name'] = self.strategy_name
                    info['acc_num'] = self.trade_account
                    info['quant'] = self.quant
                    info['clear_type'] = '매도' if self.enter_type == '매수' else '매수'
                    info['clear_time'] = self.clear_time_for_excel
                    info['clear_price'] = current_price
                    info['order_send_time'] = self.clear_time_for_excel
                    info['order_complete_time'] = self.clear_time_for_excel
                    info['clear_indicator'] = self.excel_clear_indicator

                    self.parent.add_trade_info_to_excel('clear', info)

                    info['enter_type'] = '매수' if self.enter_type == '매수' else '매도'
                    info['enter_time'] = self.enter_time_for_excel
                    info['enter_price'] = self.enter_price
                    info['enter_indicator'] = self.excel_enter_indicator

                    info['program_price_profit_tick'] = profit
                    info['real_price_profit_tick'] = profit
                    info['total_profit_dollar'] = profit * self.tick_value * self.quant

                    self.parent.add_trade_info_to_excel('total', info)

                    self.update_virtual_trade(profit * self.quant)

                    self.has_position = False
                    self.enter_type = ''
                    self.enter_price = 0

                    if from_user:
                        temp = {}
                        temp['command'] = 'clear_position_from_auto_trader'
                        temp['result'] = '0'

                        self.parent.aws_mqtt.publish_message(temp)
                elif from_user:
                        temp = {}
                        temp['command'] = 'clear_position_from_auto_trader'
                        temp['result'] = '-1'

                        self.parent.aws_mqtt.publish_message(temp)
            else:
                if self.has_position:
                    self.need_to_load_position = True

                    if from_user:
                        if self.enter_type == '매수':
                            self.waiting_enter_type = '매도'
                            self.parent.order_queue.append({'type': self.CLEAR_BUY_SIGNAL, 'acc_num': self.trade_account, 'quant': self.quant,'position': self.position})
                        else:
                            self.waiting_enter_type = '매수'
                            self.parent.order_queue.append({'type': self.CLEAR_SELL_SIGNAL, 'acc_num': self.trade_account, 'quant': self.quant,'position': self.position})


                        self.telegram_msg = '현재 포지션을 강제 청산합니다.\n'
                        self.telegram_msg += '전략 이름 : ' + self.strategy_name + '\n'

                        self.parent.send_telegram(self.telegram_msg)

                        temp = {}
                        temp['command'] = 'clear_position_from_auto_trader'
                        temp['result'] = '0'

                        self.parent.aws_mqtt.publish_message(temp)

                elif from_user:
                        temp = {}
                        temp['command'] = 'clear_position_from_auto_trader'
                        temp['result'] = '-1'

                        self.parent.aws_mqtt.publish_message(temp)

            self.stop_trailing_price = 0
            self.stop_trailing_on = False

            self.preserve_profit_price = 0
            self.preserve_profit_on = False

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, fname, exc_tb.tb_lineno)

    def set_real_position(self):
        while self.need_to_load_position:
            if self.parent.complete_order_queue_dict[self.trade_account]:
                data = self.parent.complete_order_queue_dict[self.trade_account].popleft()

                if data['type'] == -1:
                    self.enter_type = ''
                    self.enter_price = 0
                    self.has_position = False

                    temp_msg = '전략 이름 : ' + self.strategy_name + '\n'
                    temp_msg += '해당 계좌에는 포지션이 없으므로 청산할 수 없습니다.\n'
                    temp_msg += '진입을 다시 계산합니다.\n'

                    self.need_to_load_position = False

                    self.parent.send_telegram(temp_msg)

                elif data['type'] == self.waiting_enter_type and self.has_position and int(data['sum_of_clear_quant']) == int(self.quant):
                    real_profit = int((data['sum_of_profit'] // self.tick_value) // int(data['sum_of_clear_quant']))

                    self.current_price = self.parent.get_current_price()

                    program_profit = abs(self.current_price - self.enter_price)
                    program_profit = int(program_profit // self.tick_unit)


                    if (self.enter_type == '매수' and self.enter_price > self.current_price) or (
                            self.enter_type == '매도' and self.enter_price < self.current_price):
                        program_profit = program_profit * -1

                    now = datetime.datetime.now()
                    self.clear_time_for_excel = now.strftime('%Y-%m-%d %H:%M:%S.%f')

                    info = {}

                    info['trade_type'] = '진입'
                    info['strategy_name'] = self.strategy_name

                    info['acc_num'] = self.trade_account
                    info['quant'] = self.quant
                    info['clear_type'] = '매도' if self.enter_type == '매수' else '매수'
                    info['clear_time'] = self.clear_time_for_excel
                    if self.enter_type == '매수':
                        info['clear_price'] = round(self.enter_price + (real_profit * self.tick_unit), 2)
                    else:
                        info['clear_price'] = round(self.enter_price - (real_profit * self.tick_unit), 2)

                    info['order_send_time'] = data['order_send_time']
                    info['order_complete_time'] = data['order_complete_time']
                    info['clear_indicator'] = self.excel_clear_indicator

                    self.parent.add_trade_info_to_excel('clear', info)

                    info['enter_type'] = '매수' if self.enter_type == '매수' else '매도'
                    info['enter_time'] = self.enter_time_for_excel
                    info['enter_price'] = self.enter_price
                    info['enter_indicator'] = self.excel_enter_indicator

                    info['program_price_profit_tick'] = program_profit
                    info['real_price_profit_tick'] = real_profit
                    info['total_profit_dollar'] = data['sum_of_profit']

                    self.parent.add_trade_info_to_excel('total', info)

                    self.current_total_profit_tick += real_profit

                    print('총 누적 수익 : ', self.current_total_profit_tick)
                    self.update_virtual_trade(data['sum_of_profit'])

                    temp = {}

                    temp['acc_num'] = self.trade_account
                    temp['position'] = self.position
                    temp['quant'] = self.quant * -1 if self.enter_type == '매수' else self.quant

                    self.parent.process_complete_order(temp)

                    self.set_position_info()

                    self.need_to_load_position = False

                elif data['type'] == self.waiting_enter_type and not self.has_position and int(data['sum_of_enter_quant']) == int(self.quant):
                    temp = {}

                    temp['acc_num'] = self.trade_account
                    temp['avg_price'] = float(data['avg_price'])
                    temp['position'] = self.position
                    temp['quant'] = int(data['sum_of_enter_quant']) if data['type'] == '매수' else int(data['sum_of_enter_quant']) * -1

                    self.parent.process_complete_order(temp)

                    self.set_position_info()

                    now = datetime.datetime.now()
                    self.enter_time_for_excel = now.strftime('%Y-%m-%d %H:%M:%S.%f')

                    info = {}

                    info['trade_type'] = '진입'
                    info['strategy_name'] = self.strategy_name
                    info['acc_num'] = self.trade_account
                    info['quant'] = self.quant
                    info['enter_type'] = self.enter_type
                    info['enter_time'] = self.enter_time_for_excel
                    info['enter_price'] = self.enter_price
                    info['order_send_time'] = data['order_send_time']
                    info['order_complete_time'] = data['order_complete_time']
                    info['enter_indicator'] = self.excel_enter_indicator

                    self.parent.add_trade_info_to_excel('enter', info)

                    now = datetime.datetime.now()

                    self.need_to_load_position = False
                else:
                    print('putback')
                    self.parent.complete_order_queue_dict[self.trade_account].append(data)
                    time.sleep(0.1)
            else:
                time.sleep(0.01)
        self.checking_real_position_running = False

    def set_position_info(self):
        try:
            with open("position.json", "r", encoding="UTF8") as st_json:
                json_data = json.load(st_json)

            if json_data[self.trade_account][str(self.position)]['quant'] == 0:
                self.has_position = False
                self.enter_type = ''
                self.enter_price = 0
            else:
                self.has_position = True

                self.enter_type = '매도' if json_data[self.trade_account][str(self.position)]['quant'] < 0 else '매수'
                self.last_enter_type = self.enter_type
                self.enter_price = json_data[self.trade_account][str(self.position)]['avg_price']
                self.quant = abs(json_data[self.trade_account][str(self.position)]['quant'])

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, fname, exc_tb.tb_lineno)

    def check_acc_num_changed(self, acc_num):
        if acc_num != self.trade_account and self.trade_account:
            with open("position.json", "r", encoding="UTF8") as st_json:
                json_data = json.load(st_json)

            temp = json_data[self.trade_account][str(self.position)]

            del json_data[self.trade_account][str(self.position)]

            self.trade_account = acc_num

            json_data[self.trade_account][str(self.position)] = temp

            with open('position.json', 'w', encoding="UTF8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)

    def need_to_clear_position_by_profit_limit(self):
        try:
            if not self.profit_limit_flag and not self.is_virtual_trade():

                profit = abs(self.current_price - self.enter_price)
                profit = int(profit // self.tick_unit) * self.quant
                if (self.enter_type == '매수' and self.enter_price > self.current_price) or (
                        self.enter_type == '매도' and self.enter_price < self.current_price):
                    profit = profit * -1


                if self.current_total_profit_tick + profit <= self.max_loss or self.max_profit <= self.current_total_profit_tick + profit:
                    self.profit_limit_flag = True

                    self.telegram_msg += '==============\n'
                    self.telegram_msg += '설정된 최대 손절/익절 값에 도달하여 청산 후 매매를 중지합니다.\n'

                    self.telegram_msg += '현재 청산 이익 틱: ' + str(int(self.current_total_profit_tick)) + '\n'
                    self.telegram_msg += '현재 매매 이익 틱: ' + str(int(profit)) + '\n'
                    self.telegram_msg += '설정 최대 손절 틱 : ' + str(self.max_loss) + '\n'
                    self.telegram_msg += '설정 최대 익절 틱 : ' + str(self.max_profit) + '\n'

                    self.parent.send_telegram(self.telegram_msg)

                    return True
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, fname, exc_tb.tb_lineno)
        return False

    def is_in_time(self):
        try:
            is_in_time = False
            if len(self.trade_time) == 0:
                is_in_time = True
            else:
                for each in self.trade_time:
                    start_hour, start_min, end_hour, end_min = each.split(';')

                    start_hour = int(int(start_hour) % 24)
                    start_min = int(int(start_min) % 60)
                    end_hour = int(int(end_hour) % 24)
                    end_min = int(int(end_min) % 60)


                    if self.is_time_between(datetime.time(start_hour, start_min, 0), datetime.time(end_hour, end_min, 0)):
                        if not self.time_range_in_msg_sent:
                            self.telegram_msg = '!!!시뮬레이션 전략입니다!!!\n' if self.is_simulation_strategy else ''
                            self.telegram_msg += '전략 이름 : ' + self.strategy_name + '\n'
                            self.telegram_msg += '설정된 매매 시간을 만족하여 매매를 시작합니다.\n\n'
                            self.parent.send_telegram(self.telegram_msg)

                            self.time_range_in_msg_sent = True

                            self.reset_cross_check()

                        self.time_range_out_msg_sent = False
                        is_in_time = True
                        break

                if not is_in_time and not self.time_range_out_msg_sent:
                    self.time_range_out_msg_sent = True
                    self.time_range_in_msg_sent = False
                    self.telegram_msg = '!!!시뮬레이션 전략입니다!!!\n' if self.is_simulation_strategy else ''
                    self.telegram_msg += '전략 이름 : ' + self.strategy_name + '\n'
                    self.telegram_msg += '설정된 매매 시간을 벗어나 매매를 중단합니다.\n'
                    if self.is_there_first_meet_virtual_indicator or self.is_there_box_virtual_indicator:
                        self.telegram_msg += '가상매매는 영향을 받지 않습니다.\n'
                    self.parent.send_telegram(self.telegram_msg)

                    self.reset_cross_check()

                if not is_in_time and self.has_position and not self.is_virtual_trade() and not self.need_to_load_position:
                    print('clear by time limit!')
                    if self.enter_type == '매수':
                        self.waiting_enter_type = '매도'
                        self.parent.order_queue.append({'type': self.CLEAR_BUY_SIGNAL, 'acc_num': self.trade_account, 'quant': self.quant,'position': self.position})
                    else:
                        self.waiting_enter_type = '매수'
                        self.parent.order_queue.append({'type': self.CLEAR_SELL_SIGNAL, 'acc_num': self.trade_account, 'quant': self.quant,'position': self.position})

                    self.clear_position_req(from_user=False)

            return is_in_time
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, fname, exc_tb.tb_lineno)

    def reset_cross_check(self):
        self.last_tema_ma_cross_setting = {}
        self.last_tema_ma_cross_value = {}

        self.last_parabolic_clear_setting = {}
        self.last_parabolic_clear_value = {}

    def calc_indicators(self):
        try:
            self.indicator_dict_already_false = False

            for k, v in self.indicator_dict.items():
                if k == 'MA' or k == 'TEMA' or k == 'RSI':
                    for kk, vv in v.items():
                        if k + '_' + kk not in self.parent.already_calced_list:
                            indicator_time_type, indicator_unit, indicator_period = kk.split('_')

                            indicator_period = int(indicator_period)

                            df = self.parent.get_df(indicator_time_type, int(indicator_unit))

                            if k == 'MA':
                                df = self.indicator.get_ma(df, indicator_period, calc_only_last=self.indicator_dict[k][kk])
                            elif k == 'TEMA':
                                df = self.indicator.get_tema(df, indicator_period, calc_only_last=self.indicator_dict[k][kk])
                            elif k == 'RSI':
                                df = self.indicator.get_rsi(df, indicator_period, calc_only_last=self.indicator_dict[k][kk])

                            self.indicator_dict[k][kk] = True
                            self.parent.already_calced_list.append(k + '_' + kk)



                elif k == 'PARABOLIC':
                    for kk, vv in v.items():
                        if k + '_' + kk not in self.parent.already_calced_list:
                            indicator_time_type, indicator_unit, af, af_max = kk.split('_')

                            df = self.parent.get_df(indicator_time_type, int(indicator_unit))
                            df = self.indicator.get_parabolic(df, af=float(af), af_max=float(af_max), calc_only_last=self.indicator_dict[k][kk])

                            self.indicator_dict[k][kk] = True
                            self.parent.already_calced_list.append(k + '_' + kk)


                elif k == 'MACD':
                    for kk, vv in v.items():
                        if k + '_' + kk not in self.parent.already_calced_list:
                            indicator_time_type, indicator_unit, short, long, signal = kk.split('_')

                            df = self.parent.get_df(indicator_time_type, int(indicator_unit))
                            df = self.indicator.get_macd(df, int(short), int(long), int(signal), calc_only_last=self.indicator_dict[k][kk])

                            self.indicator_dict[k][kk] = True
                            self.parent.already_calced_list.append(k + '_' + kk)

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, fname, exc_tb.tb_lineno)

    def remove_strategy(self, removed_position):
        if self.position >= removed_position:
            with open("position.json", "r", encoding="UTF8") as st_json:
                json_data = json.load(st_json)

            position_info = json_data[self.trade_account][str(self.position)]

            del json_data[self.trade_account][str(self.position)]

            if self.position != removed_position:
                self.position -= 1
                json_data[self.trade_account][str(self.position)] = position_info

            with open('position.json', 'w', encoding="UTF8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)

    def is_time_between(self, begin_time, end_time):
        # If check time is not given, default to current UTC time
        check_time = datetime.datetime.now().time()

        if begin_time < end_time:
            return check_time >= begin_time and check_time <= end_time
        else:  # crosses midnight
            return check_time >= begin_time or check_time <= end_time

    def test_thread(self):
        while True:
            try:
                df = self.parent.get_df('min', 1)
                time.sleep(1)
                start = time.time()
                self.indicator.get_ma(df, 5, calc_only_last=False)
                end = time.time()
                print("ma_slow : ", end - start)

                start = time.time()
                self.indicator.get_ma(df, 5, calc_only_last=True)
                end = time.time()
                print("ma_fast : ", end - start)

                start = time.time()
                self.indicator.get_tema(df, 5, calc_only_last=False)
                end = time.time()
                print("tema_slow : ", end - start)

                start = time.time()
                self.indicator.get_tema(df, 5, calc_only_last=True)
                end = time.time()
                print("tema_fast : ", end - start)


                df = self.parent.get_df("min", 1)
                start = time.time()
                self.indicator.get_macd(df, 12, 26, 9, calc_only_last=False)
                end = time.time()
                print("MACD_slow: ", end - start)

                df = self.parent.get_df("min", 1)
                start = time.time()
                self.indicator.get_macd(df, 12, 26, 9, calc_only_last=True)
                end = time.time()
                print("MACD_fast: ", end - start)


                start = time.time()
                self.indicator.get_parabolic(df, 0.05, 0.05, calc_only_last=False)
                end = time.time()
                print("parabolic_slow : ", end - start)

                start = time.time()
                self.indicator.get_parabolic(df, 0.05, 0.05, calc_only_last=True)
                end = time.time()
                print("parabolic_fast : ", end - start)


                start = time.time()
                self.indicator.get_rsi(df, 14, calc_only_last=False)
                end = time.time()
                print("RSI_slow : ", end - start)

                start = time.time()
                self.indicator.get_rsi(df, 14, calc_only_last=True)
                end = time.time()
                print("RSI_fast : ", end - start)

            except Exception as e:
                pass
                time.sleep(0.1)