import copy
import datetime
import json
import os
import sys
import threading
import time

import indicator

import random
import string

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

        self.virtual_start_hour = 0
        self.virtual_start_min = 0
        self.virtual_end_hour = 0
        self.virtual_end_min = 0

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

        self.enter_id = ''

        self.excel_enter_indicator = ''
        self.excel_clear_indicator = ''

        self.is_there_start_for_prev_minus_current = False
        self.is_prev_minus_current_activated = True

        self.profit_total_clear_flag = False

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
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(e, fname, exc_tb.tb_lineno)

            with open("position.json", "r", encoding="UTF8") as st_json:
                json_data = json.load(st_json)

            if str(self.position) not in json_data[self.trade_account]:
                json_data[self.trade_account][str(self.position)] = {}
            if 'quant' not in json_data[self.trade_account][str(self.position)]:
                json_data[self.trade_account][str(self.position)]['quant'] = 0
            if 'avg_price' not in json_data[self.trade_account][str(self.position)]:
                json_data[self.trade_account][str(self.position)]['avg_price'] = 0
            if 'enter_id' not in json_data[self.trade_account][str(self.position)]:
                json_data[self.trade_account][str(self.position)]['enter_id'] = ''

            with open('position.json', 'w', encoding="UTF8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)

            if not self.running_status and self.strategy_json['running_status'] == 'false':
                self.set_position_info()

            elif not self.running_status and self.strategy_json['running_status'] == 'true':
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

                temp = {'enter_buy': '??????', 'enter_sell': '??????', 'clear_buy' : '????????????', 'clear_sell' : '????????????'}

                self.is_there_first_meet_virtual_indicator = False
                self.is_there_box_virtual_indicator = False

                self.is_first_meet_virtual_indicator_running = False
                self.is_box_virtual_indicator_running = False

                self.indicator_dict = {
                    'MA': {},
                    'TEMA': {},
                    'RSI': {},
                    'PARABOLIC': {},
                    'PARABOLIC_HIGH_LOW': {},
                    'MACD': {}
                }

                self.is_there_start_for_prev_minus_current = False
                self.is_prev_minus_current_activated = True

                self.profit_total_clear_flag = False

                for k, v in temp.items():
                    enter_list = self.strategy_json[k]

                    for each in enter_list:
                        if each['name'] == '?????????????????? (????????????)':
                            self.virtual_start_hour = int(each['start_hour'])
                            self.virtual_start_min = int(each['start_min'])
                            self.virtual_end_hour = int(each['end_hour'])
                            self.virtual_end_min = int(each['end_min'])

                            self.is_there_first_meet_virtual_indicator = True
                            self.is_there_box_virtual_indicator = False

                            self.is_first_meet_virtual_indicator_running = True if not self.has_position else False
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


                        elif each['name'] == '?????????????????? (???????????????)':
                            self.virtual_start_hour = int(each['start_hour'])
                            self.virtual_start_min = int(each['start_min'])
                            self.virtual_end_hour = int(each['end_hour'])
                            self.virtual_end_min = int(each['end_min'])

                            self.is_there_first_meet_virtual_indicator = False
                            self.is_there_box_virtual_indicator = True

                            self.is_first_meet_virtual_indicator_running = False
                            self.is_box_virtual_indicator_running = True if not self.has_position else False

                            self.current_total_profit_enter_times = 0
                            self.current_total_tick_for_virtual_trade = 0

                            self.virtual_current_total_enter_times = 0

                            self.virtual_rerun_type = each['rerun_profit_type']
                            self.virtual_rerun_unit = int(each['rerun_profit_unit'])
                            self.virtual_total_enter_times = int(each['total_enter_times'])
                            self.virtual_pending_min = int(each['pending_min'])

                        elif each['name'] == '?????????-??????/??????' or each['name'] == '?????????-?????????':
                            if each['left_indicator_type'] == 'ma':
                                self.indicator_dict['MA'][each['left_indicator_time_type'] + '_' + each['left_indicator_unit'] + '_' + each['left_indicator_period']] = False

                            if each['right_indicator_type'] == 'ma':
                                self.indicator_dict['MA'][each['right_indicator_time_type'] + '_' + each['right_indicator_unit'] + '_' + each['right_indicator_period']] = False

                            if each['left_indicator_type'] == 'tema':
                                self.indicator_dict['TEMA'][each['left_indicator_time_type'] + '_' + each['left_indicator_unit'] + '_' + each['left_indicator_period']] = False

                            if each['right_indicator_type'] == 'tema':
                                self.indicator_dict['TEMA'][each['right_indicator_time_type'] + '_' + each['right_indicator_unit'] + '_' + each['right_indicator_period']] = False

                        elif each['name'] == '?????????-?????????' or each['name'] == '?????????-?????????':
                            if each['indicator_type'] == 'ma':
                                self.indicator_dict['MA'][each['indicator_time_type'] + '_' + each['indicator_unit'] + '_' + each['indicator_period']] = False

                            if each['indicator_type'] == 'tema':
                                self.indicator_dict['TEMA'][each['indicator_time_type'] + '_' + each['indicator_unit'] + '_' + each['indicator_period']] = False

                        elif each['name'] == 'RSI':
                            self.indicator_dict['RSI'][each['indicator_time_type'] + '_' + each['indicator_unit'] + '_' + each['rsi_period']] = False


                        elif each['name'] == 'MACD ?????????' or each['name'] == 'MACD / Osc ?????????' or each['name'] == 'MACD Osc ??????'or each['name'] == 'MACD Osc ?????? ??????':
                            self.indicator_dict['MACD'][each['indicator_time_type'] + '_' + each['indicator_unit'] + '_' + each['macd_short']
                                                        + '_' + each['macd_long'] + '_' + each['macd_signal']] = False

                        elif each['name'] == '????????????':
                            self.indicator_dict['PARABOLIC'][each['indicator_time_type'] + '_' + each['indicator_unit'] + '_' + each['prabolic_value_one'] + '_' + each['prabolic_value_two']] = False

                        elif each['name'] == '???????????? ???/???-??????':
                            self.indicator_dict['PARABOLIC_HIGH_LOW'][each['indicator_time_type'] + '_' + each['indicator_unit'] + '_' + each['prabolic_value_one'] + '_' + each['prabolic_value_two']] = False

                        elif each['name'] == '?????????-?????????' and each['is_start'] == 'true':
                            self.is_there_start_for_prev_minus_current = True
                            self.is_prev_minus_current_activated = False

                        self.indicator_dict_already_false = True

                self.is_there_ai_clear = False if len(self.strategy_json['ai_clear']) == 0 else True

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
                        if (self.is_in_time() or self.is_virtual_trade()) and not self.profit_limit_flag and not self.profit_total_clear_flag:
                            self.current_price = self.parent.get_current_price()
                            self.calc_indicators()

                            if not self.has_position:
                                if self.quant_need_update:
                                    self.quant_need_update = False
                                    self.set_quant()

                                temp = {'enter_buy': '??????', 'enter_sell': '??????'}
                                for k, v in temp.items():
                                    self.current_check_position_type = v
                                    enter_list = self.strategy_json[k]

                                    now = datetime.datetime.now()

                                    self.telegram_msg = '????????? : ' + self.strategy_name + ' (' + v + ' ??????)\n'
                                    self.telegram_msg += '????????? : ' + str(self.quant) + '\n'
                                    self.telegram_msg += '?????? ?????? ?????? ?????? : \n' + now.strftime('%Y-%m-%d %H:%M:%S.%f') + '\n'

                                    enter_meet = True

                                    self.or_strategy_dict = {}
                                    for each in enter_list:
                                        if self.indicator_check(each) == self.CONDITION_FAIL:
                                            enter_meet = False
                                            break


                                    if enter_meet:
                                        for each in self.or_strategy_dict:
                                            if not self.or_strategy_dict[each]:
                                                enter_meet = False
                                                break

                                    if enter_meet:
                                        now = datetime.datetime.now()

                                        if self.virtual_first_enter_time == None:
                                            self.virtual_first_enter_time = datetime.datetime.now()

                                        if self.is_simulation_strategy or self.is_virtual_trade():
                                            if self.is_virtual_trade():
                                                if self.is_time_between(datetime.time(self.virtual_start_hour % 24, self.virtual_start_min % 60, 0), \
                                                                     datetime.time(self.virtual_end_hour % 24, self.virtual_end_min % 60, 0)):
                                                    print(str(self.strategy_name) + ' ?????? : ' + str(
                                                        now.strftime('%Y-%m-%d %H:%M:%S.%f')))
                                                    self.enter_position_req(enter_type=v)
                                            else:
                                                print(str(self.strategy_name) + ' ?????? : ' + str(
                                                    now.strftime('%Y-%m-%d %H:%M:%S.%f')))
                                                self.enter_position_req(enter_type=v)


                                        else:
                                            if v == '??????':
                                                self.waiting_enter_type = '??????'
                                                self.parent.order_queue.append(
                                                    {'type': self.ENTER_BUY_SIGNAL, 'acc_num': self.trade_account,
                                                     'quant': self.quant, 'position': self.position})

                                            else:
                                                self.waiting_enter_type = '??????'
                                                self.parent.order_queue.append(
                                                    {'type': self.ENTER_SELL_SIGNAL, 'acc_num': self.trade_account,
                                                     'quant': self.quant, 'position': self.position})

                                            print(str(self.strategy_name) + ' ?????? : ' + str(now.strftime('%Y-%m-%d %H:%M:%S.%f')))
                                            self.enter_position_req()

                                        break

                                self.reset_cross_check()

                            else:
                                self.parabolic_same_time_msg_sent = False

                                now = datetime.datetime.now()

                                self.telegram_msg = '????????? : ' + self.strategy_name + ' (?????? ??????)\n'
                                self.telegram_msg += '????????? : ' + str(self.quant) + '\n'
                                self.telegram_msg += '?????? ?????? ?????? ?????? : \n' + now.strftime('%Y-%m-%d %H:%M:%S.%f') + '\n'

                                if self.need_to_clear_position_by_profit_limit():
                                    if self.is_simulation_strategy:
                                        self.clear_position_req()

                                    else:
                                        if self.enter_type == '??????':
                                            self.waiting_enter_type = '??????'
                                            self.parent.order_queue.append({'type': self.CLEAR_BUY_SIGNAL, 'acc_num': self.trade_account,'quant': self.quant, 'position' : self.position})
                                        else:
                                            self.waiting_enter_type = '??????'
                                            self.parent.order_queue.append({'type': self.CLEAR_SELL_SIGNAL, 'acc_num': self.trade_account,'quant': self.quant, 'position' : self.position})

                                        self.clear_position_req()

                                else:
                                    clear_meet = False
                                    self.or_strategy_dict = {}

                                    if self.is_there_ai_clear:
                                        clear_list = self.strategy_json['ai_clear']


                                        for each in clear_list:
                                            if self.ai_indicator_check(each) == self.CONDITION_MEET:
                                                clear_meet = True
                                                break

                                    else:
                                        clear_list = self.strategy_json['clear_buy'] if self.enter_type == '??????' else self.strategy_json[
                                            'clear_sell']

                                        for each in clear_list:
                                            if self.indicator_check(each) == self.CONDITION_MEET:
                                                clear_meet = True
                                                break

                                    if clear_meet:
                                        self.quant_need_update = True
                                        if self.is_simulation_strategy or self.is_virtual_trade():
                                            self.clear_position_req()

                                        else:
                                            now = datetime.datetime.now()
                                            print('???????????? - 3 : ', now.strftime('%Y-%m-%d %H:%M:%S.%f'))

                                            if self.enter_type == '??????':
                                                self.waiting_enter_type = '??????'
                                                self.parent.order_queue.append({'type': self.CLEAR_BUY_SIGNAL, 'acc_num': self.trade_account, 'quant': self.quant, 'position' : self.position})
                                            else:
                                                self.waiting_enter_type = '??????'
                                                self.parent.order_queue.append({'type': self.CLEAR_SELL_SIGNAL, 'acc_num': self.trade_account,'quant': self.quant, 'position' : self.position})

                                            self.clear_position_req()

                        else:
                            if not self.indicator_dict_already_false:
                                for k, v in self.indicator_dict.items():
                                    for kk, vv in v.items():
                                        self.indicator_dict[k][kk] = False

                                self.indicator_dict_already_false = True
            # else:
            #     if not self.checking_real_position_running:
            #         self.checking_real_position_running = True
            #         checking_real_position_thread = threading.Thread(target=self.set_real_position)
            #         checking_real_position_thread.start()

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, fname, exc_tb.tb_lineno)

    def indicator_check(self, info):
        try:
            if info['name'] == '?????????-??????/??????':
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

                    if (self.enter_type == '??????' and self.enter_price > self.current_price) or (
                            self.enter_type == '??????' and self.enter_price < self.current_price):
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

                    self.telegram_msg += '????????? : ' + info['name'] + '\n'

                    self.telegram_msg += '????????? : ?????????\n' if info['time_type'] == 'real' else '????????? : ?????????\n'

                    self.telegram_msg += '?????? ?????? ?????????(1) : ' + left_df['date'].iloc[-1] + '\n'
                    self.telegram_msg += '?????? ?????? ?????????(2) : ' + right_df['date'].iloc[-1] + '\n'

                    word_dict = {'day': '???', 'min': '???', 'tick': '???'}

                    self.telegram_msg += info['left_indicator_unit'] + str(
                        word_dict[info['left_indicator_time_type']]) + '??? ' + left_col_name + ' : ' + str(
                        left_val) + '\n'

                    self.telegram_msg += info['right_indicator_unit'] + str(
                        word_dict[info['right_indicator_time_type']]) + '??? ' + right_col_name + ' : ' + str(
                        right_val) + '\n'

                    self.telegram_msg += '??? ??? ?????? : ' + str(diff_val) + '\n'
                    self.telegram_msg += '??? ??? ????????? : ' + str(int(diff_val // self.tick_unit)) + '\n'
                    self.telegram_msg += '??? ?????? : ' + str(tick_diff_from) + ' ~ ' + str(tick_diff_to) + '\n'

                    return self.CONDITION_MEET
                else:
                    return self.CONDITION_FAIL

            elif info['name'] == '?????????-?????????':
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

                    if (self.enter_type == '??????' and self.enter_price > self.current_price) or (
                            self.enter_type == '??????' and self.enter_price < self.current_price):
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

                    self.telegram_msg += '????????? : ' + info['name'] + '\n'

                    self.telegram_msg += '????????? : ?????????\n' if info['time_type'] == 'real' else '????????? : ?????????\n'

                    if test_flag:
                        self.telegram_msg += '?????? ?????? ?????????(1) : ' + left_df['date'].iloc[-1] + '\n'
                        self.telegram_msg += '?????? ?????? ?????????(2) : ' + right_df['date'].iloc[-1] + '\n'


                    if info['cross_type'] == 'golden_cross':
                        self.telegram_msg += '????????? ?????? : ???????????????\n'
                    else:
                        self.telegram_msg += '????????? ?????? : ???????????????\n'

                    word_dict = {'day': '???', 'min': '???', 'tick': '???'}

                    self.telegram_msg += info['left_indicator_unit'] + str(
                        word_dict[info['left_indicator_time_type']]) + '??? ????????? ' + left_col_name + ' : ' + str(
                        current_left_val) + '\n'
                    self.telegram_msg += info['left_indicator_unit'] + str(
                        word_dict[info['left_indicator_time_type']]) + '??? ?????? ' + left_col_name + ' : ' + str(
                        pre_left_val) + '\n'

                    self.telegram_msg += info['right_indicator_unit'] + str(
                        word_dict[info['right_indicator_time_type']]) + '??? ????????? ' + right_col_name + ' : ' + str(
                        current_right_val) + '\n'
                    self.telegram_msg += info['right_indicator_unit'] + str(
                        word_dict[info['right_indicator_time_type']]) + '??? ?????? ' + right_col_name + ' : ' + str(
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
                #         self.telegram_msg += '????????? : ' + info['name'] + '\n'
                #
                #         self.telegram_msg += '!!!????????? ???????????????.!!!\n'
                #         self.telegram_msg += self.current_check_position_type + ' ???????????????.\n'
                #
                #         return self.CONDITION_MEET

                else:
                    return self.CONDITION_FAIL


            elif info['name'] == '?????????-?????????':
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

                    if (self.enter_type == '??????' and self.enter_price > self.current_price) or (
                            self.enter_type == '??????' and self.enter_price < self.current_price):
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

                    self.telegram_msg += '????????? : ' + info['name'] + '\n'

                    self.telegram_msg += '?????? ?????? ????????? : ' + df['date'].iloc[-1] + '\n'

                    word_ohcl_dict = {'open': '??????', 'high': '??????', 'close': '??????', 'low': '??????'}

                    word_dict = {'day': '???', 'min': '???', 'tick': '???'}

                    self.telegram_msg += info['indicator_unit'] + str(
                        word_dict[info['indicator_time_type']]) + '??? ????????? ' + col_name + ' : ' + str(current_val) + '\n'
                    self.telegram_msg += info['indicator_unit'] + str(
                        word_dict[info['indicator_time_type']]) + '??? ????????? ' + \
                                         word_ohcl_dict[info['ohcl_type']] + ' : ' + str(pre_val) + '\n'

                    self.telegram_msg += '??? ??? ?????? : ' + str(diff_val) + '\n'
                    self.telegram_msg += '??? ??? ????????? : ' + str(int(diff_val // self.tick_unit)) + '\n'
                    self.telegram_msg += '??? ?????? : ' + str(tick_diff_from) + ' ~ ' + str(tick_diff_to) + '\n'

                    return self.CONDITION_MEET
                else:
                    return self.CONDITION_FAIL

            elif info['name'] == '?????????-?????????':
                if info['name'] not in self.or_strategy_dict:
                    self.or_strategy_dict[info['name']] = False

                if not self.or_strategy_dict[info['name']]:
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

                    # print(self.telegram_msg)

                    if self.has_position:
                        profit = abs(self.current_price - self.enter_price)
                        profit = int(profit // self.tick_unit)

                        if (self.enter_type == '??????' and self.enter_price > self.current_price) or (
                                self.enter_type == '??????' and self.enter_price < self.current_price):
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

                        self.telegram_msg += '????????? : ' + info['name'] + '\n'

                        self.telegram_msg += '?????? ?????? ????????? : ' + df['date'].iloc[-1] + '\n'

                        word_dict = {'day': '???', 'min': '???', 'tick': '???'}

                        self.telegram_msg += info['indicator_unit'] + str(
                            word_dict[info['indicator_time_type']]) + '??? ????????? ' + col_name + ' : ' + str(current_val) + '\n'

                        self.telegram_msg += '?????? ?????? : ' + str(current_price) + '\n'

                        self.telegram_msg += '??? ??? ?????? : ' + str(diff_val) + '\n'
                        self.telegram_msg += '??? ??? ????????? : ' + str(int(diff_val // self.tick_unit)) + '\n'
                        self.telegram_msg += '??? ?????? : ' + str(tick_diff_from) + ' ~ ' + str(tick_diff_to) + '\n'

                        self.or_strategy_dict[info['name']] = True

                        return self.CONDITION_MEET
                    else:
                        return self.CONDITION_PASS


            elif info['name'] == 'Pivot-?????????':
                if info['name'] not in self.or_strategy_dict:
                    self.or_strategy_dict[info['name']] = False

                if not self.or_strategy_dict[info['name']]:
                    df = self.parent.get_df('day', '0')
                    df = self.indicator.get_pivot(df)

                    current_val = df[info['pivot_type']].iloc[-1]

                    df = self.parent.get_df(info['indicator_time_type'], int(info['indicator_unit']))
                    pre_val = df[info['ohcl_type']].iloc[-2]

                    tick_diff_from = int(info['tick_diff_from'])
                    tick_diff_to = int(info['tick_diff_to'])

                    diff_val = round(current_val - pre_val, 2)

                    # print(self.telegram_msg)

                    if self.has_position:
                        profit = abs(self.current_price - self.enter_price)
                        profit = int(profit // self.tick_unit)

                        if (self.enter_type == '??????' and self.enter_price > self.current_price) or (
                                self.enter_type == '??????' and self.enter_price < self.current_price):
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

                        self.telegram_msg += '????????? : ' + info['name'] + '\n'

                        self.telegram_msg += '?????? ?????? ????????? : ' + df['date'].iloc[-1] + '\n'

                        word_ohcl_dict = {'open': '??????', 'high': '??????', 'close': '??????', 'low': '??????'}

                        word_pivot_dict = {'second_resistance': '2?????????', 'first_resistance': '1?????????', 'pivot_point': '?????????', 'first_support': '1?????????', 'second_support': '2?????????'}

                        word_time_type_dict = {'day': '???', 'min': '???', 'tick': '???'}

                        self.telegram_msg += '?????? ' + str(word_pivot_dict[info['pivot_type']]) + ' : ' + str(current_val) + '\n'

                        self.telegram_msg += info['indicator_unit'] + str(word_time_type_dict[info['indicator_time_type']]) + '??? ????????? ' + word_ohcl_dict[info['ohcl_type']] + ' : ' + str(pre_val) + '\n'

                        self.telegram_msg += '??? ??? ?????? : ' + str(diff_val) + '\n'
                        self.telegram_msg += '??? ??? ????????? : ' + str(int(diff_val // self.tick_unit)) + '\n'
                        self.telegram_msg += '??? ?????? : ' + str(tick_diff_from) + ' ~ ' + str(tick_diff_to) + '\n'

                        self.or_strategy_dict[info['name']] = True

                        return self.CONDITION_MEET
                    else:
                        return self.CONDITION_PASS

            elif info['name'] == 'Pivot-?????????':
                if info['name'] not in self.or_strategy_dict:
                    self.or_strategy_dict[info['name']] = False

                if not self.or_strategy_dict[info['name']]:
                    df = self.parent.get_df('day', '0')
                    df = self.indicator.get_pivot(df)

                    current_val = df[info['pivot_type']].iloc[-1]
                    current_price = df['close'].iloc[-1]

                    tick_diff_from = int(info['tick_diff_from'])
                    tick_diff_to = int(info['tick_diff_to'])

                    diff_val = round(current_val - current_price, 2)

                    if self.has_position:
                        profit = abs(self.current_price - self.enter_price)
                        profit = int(profit // self.tick_unit)

                        if (self.enter_type == '??????' and self.enter_price > self.current_price) or (
                                self.enter_type == '??????' and self.enter_price < self.current_price):
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

                        self.telegram_msg += '????????? : ' + info['name'] + '\n'

                        self.telegram_msg += '?????? ?????? ????????? : ' + df['date'].iloc[-1] + '\n'

                        word_pivot_dict = {'second_resistance': '2?????????', 'first_resistance': '1?????????', 'pivot_point': '?????????',
                                           'first_support': '1?????????', 'second_support': '2?????????'}

                        self.telegram_msg += '?????? ' + str(word_pivot_dict[info['pivot_type']]) + ' : ' + str(
                            current_val) + '\n'

                        self.telegram_msg += '?????? ?????? : ' + str(current_price) + '\n'

                        self.telegram_msg += '??? ??? ?????? : ' + str(diff_val) + '\n'
                        self.telegram_msg += '??? ??? ????????? : ' + str(int(diff_val // self.tick_unit)) + '\n'
                        self.telegram_msg += '??? ?????? : ' + str(tick_diff_from) + ' ~ ' + str(tick_diff_to) + '\n'

                        self.or_strategy_dict[info['name']] = True

                        return self.CONDITION_MEET
                    else:
                        return self.CONDITION_PASS

            elif info['name'] == '????????????':
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
                                    if self.enter_type == '??????' and current_psar >= current_price or \
                                            self.enter_type == '??????' and current_psar <= current_price:

                                        self.telegram_msg += '==============\n'

                                        self.telegram_msg += '????????? : ' + info['name'] + '(' + info['prabolic_value_one'] + '/' + info['prabolic_value_two'] + ')\n'
                                        self.telegram_msg += '?????? ????????? ???????????? ????????? (' + str(current_psar) + ')??? ???????????? ???????????????.\n'

                                        #self.clear_at_same_bar = True
                                        self.last_parabolic_clear_setting = info

                                        self.last_parabolic_clear_value['pre_psar'] = current_psar
                                        self.last_parabolic_clear_value['pre_price'] = current_psar

                                        if self.enter_type == '??????':
                                            self.last_parabolic_clear_value['current_psar'] = df['high'].iloc[-1]
                                        elif self.enter_type == '??????':
                                            self.last_parabolic_clear_value['current_psar'] = df['low'].iloc[-1]
                                        self.last_parabolic_clear_value['current_price'] = current_price

                                        return self.CONDITION_MEET
                                    else:
                                        return self.CONDITION_FAIL
                                else:
                                    if self.enter_type == '??????' and df['low'].iloc[-1] == current_price or \
                                            self.enter_type == '??????' and df['high'].iloc[-1] == current_price:

                                        current_psar = df['low'].iloc[-1] if self.enter_type == '??????' else df['high'].iloc[-1]

                                        self.telegram_msg += '==============\n'

                                        self.telegram_msg += '????????? : ' + info['name'] + '(' + info['prabolic_value_one'] + '/' + info['prabolic_value_two'] + ')\n'
                                        self.telegram_msg += '?????? ????????? ???????????? ????????? (' + str(current_psar) + ')??? ???????????? ???????????????.\n'

                                        #self.clear_at_same_bar = True
                                        self.last_parabolic_clear_setting = info

                                        self.last_parabolic_clear_value['pre_psar'] = current_price
                                        self.last_parabolic_clear_value['pre_price'] = current_price

                                        if self.enter_type == '??????':
                                            self.last_parabolic_clear_value['current_psar'] = df['high'].iloc[-1]
                                        elif self.enter_type == '??????':
                                            self.last_parabolic_clear_value['current_psar'] = df['low'].iloc[-1]
                                        self.last_parabolic_clear_value['current_price'] = current_price

                                        return self.CONDITION_MEET
                                    else:
                                        return self.CONDITION_FAIL

                            else:
                                if temp == info:
                                    if self.parabolic_same_bar_enter_times >= int(info['same_bar_enter_times']):
                                        temp_msg = '!!!??????????????? ???????????????!!!\n' if self.is_simulation_strategy else ''
                                        temp_msg += '!!!???????????? ????????????!!!\n' if self.is_virtual_trade() else ''
                                        temp_msg = '????????? : ' + self.strategy_name + '\n'
                                        temp_msg += '???????????? ????????? ????????? ?????? ?????? ????????? ?????????????????? ?????? ???????????? ????????? ??????????????? ???????????? ????????????.\n'

                                        if not self.parabolic_same_time_msg_sent:
                                            self.parabolic_same_time_msg_sent = True
                                            self.parent.send_telegram(temp_msg)

                                        return self.CONDITION_FAIL

                                    self.telegram_msg += '==============\n'

                                    self.telegram_msg += '????????? : ' + info['name'] + '(' + info['prabolic_value_one'] + '/' + info['prabolic_value_two'] + ')\n'
                                    self.telegram_msg += '?????? ????????? ?????? ?????? ?????????.\n'

                                    self.last_parabolic_enter_time_temp = df['date'].iloc[-1]

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

                    if (self.enter_type == '??????' and self.enter_price > self.current_price) or (
                            self.enter_type == '??????' and self.enter_price < self.current_price):
                        profit = profit * -1

                    target_clear_tick_from = int(info['target_clear_tick_from'])
                    target_clear_tick_to = int(info['target_clear_tick_to'])

                    if target_clear_tick_from <= profit <= target_clear_tick_to:
                        pass
                    else:
                        return self.CONDITION_FAIL

                if (info['prabolic_type'] == 'buy' and current_price >= current_psar) or \
                        (info['prabolic_type'] == 'sell' and current_price <= current_psar) or \
                        (info['prabolic_type'] == 'golden_cross' and pre_price <= pre_psar and current_price >= current_psar) or \
                        (info['prabolic_type'] == 'dead_cross' and pre_price >= pre_psar and current_price <= current_psar):


                    # if self.last_parabolic_enter_value and \
                    #         self.last_parabolic_enter_value['pre_psar'] == pre_psar and \
                    #         self.last_parabolic_enter_value['current_psar'] == current_psar and \
                    #         not self.has_position:
                    #     temp_msg = '!!!??????????????? ???????????????!!!\n' if self.is_simulation_strategy else ''
                    #     temp_msg += '!!!???????????? ????????????!!!\n' if self.is_virtual_trade() else ''
                    #     temp_msg = '????????? : ' + self.strategy_name + '\n'
                    #     temp_msg += '???????????? ????????? ?????? ????????? ?????????????????? ?????? ?????? ???????????? ????????? ????????? ??????????????? ???????????? ????????????.\n'
                    #
                    #     if not self.parabolic_same_time_msg_sent:
                    #         self.parabolic_same_time_msg_sent = True
                    #         self.parent.send_telegram(temp_msg)
                    #
                    #     return self.CONDITION_FAIL


                    self.telegram_msg += '==============\n'

                    self.telegram_msg += '????????? : ' + info['name'] + '(' + info['prabolic_value_one'] + '/' + info[
                        'prabolic_value_two'] + ')\n'

                    if test_flag:
                        self.telegram_msg += '?????? ?????? ????????? : ' + df['date'].iloc[-1] + '\n'


                    self.telegram_msg += '????????? : ?????????\n' if info['time_type'] == 'real' else '????????? : ?????????\n'

                    word_dict = {'buy': '??????', 'sell': '??????', 'golden_cross': '???????????????', 'dead_cross': '???????????????'}
                    self.telegram_msg += '?????? : ' + word_dict[info['prabolic_type']] + '\n'

                    word_dict = {'day': '???', 'min': '???', 'tick': '???'}

                    if info['time_type'] == 'real':
                        self.telegram_msg += info['indicator_unit'] + word_dict[
                            info['indicator_time_type']] + '??? ???????????? ????????? : ' + str(current_psar) + '\n'
                        self.telegram_msg += info['indicator_unit'] + word_dict[
                            info['indicator_time_type']] + '??? ?????? ?????? : ' + str(current_price) + '\n'

                        if info['prabolic_type'] == 'golden_cross' or info['prabolic_type'] == 'dead_cross':
                            self.telegram_msg += info['indicator_unit'] + word_dict[
                                info['indicator_time_type']] + '??? ???????????? ????????? : ' + str(pre_psar) + '\n'
                            self.telegram_msg += info['indicator_unit'] + word_dict[
                                info['indicator_time_type']] + '??? ?????? ?????? : ' + str(pre_price) + '\n'

                    else:
                        self.telegram_msg += info['indicator_unit'] + word_dict[
                            info['indicator_time_type']] + '??? ???????????? ????????? : ' + str(current_psar) + '\n'
                        self.telegram_msg += info['indicator_unit'] + word_dict[
                            info['indicator_time_type']] + '??? ?????? ?????? : ' + str(current_price) + '\n'

                        if info['prabolic_type'] == 'golden_cross' or info['prabolic_type'] == 'dead_cross':
                            self.telegram_msg += info['indicator_unit'] + word_dict[
                                info['indicator_time_type']] + '??? ???????????? ?????? ????????? : ' + str(pre_psar) + '\n'
                            self.telegram_msg += info['indicator_unit'] + word_dict[
                                info['indicator_time_type']] + '??? ?????? ?????? ?????? : ' + str(pre_price) + '\n'

                    self.telegram_msg += '??? ??? ?????? : ' + str(diff_val) + '\n'
                    self.telegram_msg += '??? ??? ????????? : ' + str(int(diff_val // self.tick_unit)) + '\n'

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


            elif info['name'] == '???????????? ???/???-??????':
                if info['name'] not in self.or_strategy_dict:
                    self.or_strategy_dict[info['name']] = False

                if not self.or_strategy_dict[info['name']]:
                    df = self.parent.get_df(info['indicator_time_type'], int(info['indicator_unit']))

                    indicator_val = [df['H1_' + str(info['prabolic_value_one']) + '_' + str(info['prabolic_value_two'])].iloc[-1],
                                     df['H2_' + str(info['prabolic_value_one']) + '_' + str(info['prabolic_value_two'])].iloc[-1],
                                     df['M_' + str(info['prabolic_value_one']) + '_' + str(info['prabolic_value_two'])].iloc[-1],
                                     df['L2_' + str(info['prabolic_value_one']) + '_' + str(info['prabolic_value_two'])].iloc[-1],
                                     df['L1_' + str(info['prabolic_value_one']) + '_' + str(info['prabolic_value_two'])].iloc[-1]]

                    price = df['close'].iloc[-1] if info['price_type'] == 'real' else df['close'].iloc[-2]

                    diff_val = round(indicator_val[int(info['high_low_type'])] - price, 2)

                    tick_diff_from = int(info['tick_diff_from'])
                    tick_diff_to = int(info['tick_diff_to'])

                    if self.has_position:
                        profit = abs(self.current_price - self.enter_price)
                        profit = int(profit // self.tick_unit)

                        if (self.enter_type == '??????' and self.enter_price > self.current_price) or (
                                self.enter_type == '??????' and self.enter_price < self.current_price):
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

                        self.telegram_msg += '????????? : ' + info['name'] + '(' + info['prabolic_value_one'] + '/' + info[
                            'prabolic_value_two'] + ')\n'

                        word_high_low_type_dict = {"0": "H1", "1": "H2", "2": "M", "3": "L2", "4": "L1"}
                        word_time_dict = {'day': '???', 'min': '???', 'tick': '???'}

                        if info['price_type'] == 'real':
                            self.telegram_msg += info['indicator_unit'] + word_time_dict[
                                info['indicator_time_type']] + '??? ???????????? : ' + str(price) + '\n'
                        else:
                            self.telegram_msg += info['indicator_unit'] + word_time_dict[
                                info['indicator_time_type']] + '??? ????????? ?????? : ' + str(price) + '\n'

                        for i in range(len(indicator_val)):
                            self.telegram_msg += word_high_low_type_dict[str(i)] + ' ??? : ' + str(indicator_val[i]) + '\n'
                        self.telegram_msg += '??? ??? ?????? : ' + str(diff_val) + '\n'

                        self.or_strategy_dict[info['name']] = True

                        return self.CONDITION_MEET
                    else:
                        return self.CONDITION_PASS

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

                    if (self.enter_type == '??????' and self.enter_price > self.current_price) or (
                            self.enter_type == '??????' and self.enter_price < self.current_price):
                        profit = profit * -1

                    target_clear_tick_from = int(info['target_clear_tick_from'])
                    target_clear_tick_to = int(info['target_clear_tick_to'])

                    if target_clear_tick_from <= profit <= target_clear_tick_to:
                        pass
                    else:
                        return self.CONDITION_FAIL

                if rsi_from <= current_val and current_val <= rsi_to:

                    self.telegram_msg += '==============\n'

                    self.telegram_msg += '????????? : ' + info['name'] + '\n'

                    self.telegram_msg += '?????? ?????? ????????? : ' + df['date'].iloc[-1] + '\n'

                    word_dict = {'day': '???', 'min': '???', 'tick': '???'}

                    self.telegram_msg += info['indicator_unit'] + str(
                        word_dict[info['indicator_time_type']]) + '??? ' + col_name + ' ??? : ' + str(
                        round(current_val, 2)) + '\n'

                    self.telegram_msg += 'RSI ?????? : ' + str(rsi_from) + ' ~ ' + str(rsi_to) + '\n'

                    return self.CONDITION_MEET
                else:
                    return self.CONDITION_FAIL

            elif info['name'] == '?????????-?????????':
                if info['name'] not in self.or_strategy_dict:
                    self.or_strategy_dict[info['name']] = False

                if not self.or_strategy_dict[info['name']]:
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

                    diff_val = pre_price_dict[info['ohcl_type']] - current_price

                    if self.has_position:
                        profit = abs(self.current_price - self.enter_price)
                        profit = int(profit // self.tick_unit)

                        if (self.enter_type == '??????' and self.enter_price > self.current_price) or (
                                self.enter_type == '??????' and self.enter_price < self.current_price):
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

                        self.telegram_msg += '????????? : ' + info['name'] + '\n'

                        self.telegram_msg += '?????? ?????? ????????? : ' + df['date'].iloc[-1] + '\n'

                        word_ohcl_dict = {'open': '??????', 'high': '??????', 'close': '??????', 'low': '??????', 'middle': '?????????'}
                        word_dict = {'day': '???', 'min': '???', 'tick': '???'}

                        self.telegram_msg += '????????? ?????? ?????? : ' + word_ohcl_dict[info['ohcl_type']] + '\n'
                        if info['bar_status'] == 'bull':
                            self.telegram_msg += '????????? ?????? : ??????\n'
                        elif info['bar_status'] == 'bear':
                            self.telegram_msg += '????????? ?????? : ??????\n'
                        elif info['bar_status'] == 'all':
                            self.telegram_msg += '????????? ?????? : ????????????\n'

                        self.telegram_msg += info['indicator_unit'] + str(
                            word_dict[info['indicator_time_type']]) + '??? ????????? ??? : ' + str(
                            pre_price_dict[info['ohcl_type']]) + '\n'
                        self.telegram_msg += '?????? ?????? : ' + str(current_price) + '\n'

                        self.telegram_msg += '??? ??? ?????? : ' + str(diff_val) + '\n'
                        self.telegram_msg += '??? ??? ????????? : ' + str(int(diff_val // self.tick_unit)) + '\n'
                        self.telegram_msg += '??? ?????? : ' + str(tick_diff_from) + ' ~ ' + str(tick_diff_to) + '\n'

                        self.or_strategy_dict[info['name']] = True

                        return self.CONDITION_MEET
                    else:
                        return self.CONDITION_PASS

            elif info['name'] == '???????????? ?????????':
                df = self.parent.get_df(info['indicator_time_type'], int(info['indicator_unit']))

                pre_open = df['open'].iloc[-2]
                pre_close = df['close'].iloc[-2]

                tick_diff_from = int(info['tick_diff_from'])

                # print(self.telegram_msg)

                if self.has_position:
                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)

                    if (self.enter_type == '??????' and self.enter_price > self.current_price) or (
                            self.enter_type == '??????' and self.enter_price < self.current_price):
                        profit = profit * -1

                    target_clear_tick_from = int(info['target_clear_tick_from'])
                    target_clear_tick_to = int(info['target_clear_tick_to'])

                    if target_clear_tick_from <= profit <= target_clear_tick_to:
                        pass
                    else:
                        return self.CONDITION_FAIL

                if (info['bar_status'] == 'bull' and pre_open <= pre_close and pre_open + (
                        self.tick_unit * tick_diff_from) <= pre_close) or \
                        (info['bar_status'] == 'bear' and pre_open >= pre_close and pre_open - (
                                self.tick_unit * tick_diff_from) >= pre_close):

                    self.telegram_msg += '==============\n'

                    self.telegram_msg += '????????? : ' + info['name'] + '\n'

                    self.telegram_msg += '?????? ?????? ????????? : ' + df['date'].iloc[-1] + '\n'

                    word_dict = {'day': '???', 'min': '???', 'tick': '???'}

                    self.telegram_msg += info['indicator_unit'] + str(
                        word_dict[info['indicator_time_type']]) + '??? ????????? ????????? : ' + str(
                        int(abs(pre_open - pre_close) / self.tick_unit)) + '\n'

                    self.telegram_msg += '??? ?????? ?????? : ' + str(tick_diff_from) + ' ??? ?????? \n'

                    return self.CONDITION_MEET
                else:
                    return self.CONDITION_FAIL

            elif info['name'] == '???????????? ?????????':
                df = self.parent.get_df(info['indicator_time_type'], int(info['indicator_unit']))

                current_open = df['open'].iloc[-1]
                current_close = df['close'].iloc[-1]

                tick_diff_from = int(info['tick_diff_from'])

                # print(self.telegram_msg)

                if self.has_position:
                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)

                    if (self.enter_type == '??????' and self.enter_price > self.current_price) or (
                            self.enter_type == '??????' and self.enter_price < self.current_price):
                        profit = profit * -1

                    target_clear_tick_from = int(info['target_clear_tick_from'])
                    target_clear_tick_to = int(info['target_clear_tick_to'])

                    if target_clear_tick_from <= profit <= target_clear_tick_to:
                        pass
                    else:
                        return self.CONDITION_FAIL

                if (info['bar_status'] == 'bull' and current_open <= current_close and current_open + (
                        self.tick_unit * tick_diff_from) <= current_close) or \
                        (info['bar_status'] == 'bear' and current_open >= current_close and current_open - (
                                self.tick_unit * tick_diff_from) >= current_close):

                    self.telegram_msg += '==============\n'

                    self.telegram_msg += '????????? : ' + info['name'] + '\n'

                    self.telegram_msg += '?????? ?????? ????????? : ' + df['date'].iloc[-1] + '\n'

                    word_dict = {'day': '???', 'min': '???', 'tick': '???'}

                    self.telegram_msg += info['indicator_unit'] + str(
                        word_dict[info['indicator_time_type']]) + '??? ????????? ????????? : ' + str(
                        int(abs(current_open - current_close) / self.tick_unit)) + '\n'

                    self.telegram_msg += '??? ?????? ?????? : ' + str(tick_diff_from) + ' ??? ?????? \n'

                    return self.CONDITION_MEET
                else:
                    return self.CONDITION_FAIL

            elif info['name'] == '?????? n??????':
                if info['name'] not in self.or_strategy_dict:
                    self.or_strategy_dict[info['name']] = False

                if not self.or_strategy_dict[info['name']]:
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
                        for i in range(1, int(info['num_of_bar']) + 1):
                            min_val = min(min_val, df['low'].iloc[i * -1])

                        result_val = min_val
                        diff_val = min_val - current_price

                    tick_diff_from = int(info['tick_diff_from'])
                    tick_diff_to = int(info['tick_diff_to'])

                    # print(self.telegram_msg)

                    if self.has_position:
                        profit = abs(self.current_price - self.enter_price)
                        profit = int(profit // self.tick_unit)

                        if (self.enter_type == '??????' and self.enter_price > self.current_price) or (
                                self.enter_type == '??????' and self.enter_price < self.current_price):
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

                        self.telegram_msg += '????????? : ' + info['name'] + '\n'

                        self.telegram_msg += '?????? ?????? ????????? : ' + df['date'].iloc[-1] + '\n'

                        word_dict = {'day': '???', 'min': '???', 'tick': '???'}
                        type_word_dict = {'high': '???', 'low': '???'}

                        self.telegram_msg += info['indicator_unit'] + str(
                            word_dict[info['indicator_time_type']]) + '??? ?????? ' + \
                                             info['num_of_bar'] + '??? ?????? ???' + type_word_dict[info['type']] \
                                             + '??? : ' + str(result_val) + '\n'

                        self.telegram_msg += '?????? ?????? : ' + str(current_price) + '\n'

                        self.telegram_msg += '??? ??? ?????? : ' + str(diff_val) + '\n'
                        self.telegram_msg += '??? ??? ????????? : ' + str(int(diff_val // self.tick_unit)) + '\n'
                        self.telegram_msg += '??? ?????? : ' + str(tick_diff_from) + ' ~ ' + str(tick_diff_to) + '\n'

                        self.or_strategy_dict[info['name']] = True

                        return self.CONDITION_MEET
                    else:
                        return self.CONDITION_PASS

            elif info['name'] == 'MACD ?????????':
                df = self.parent.get_df(info['indicator_time_type'], int(info['indicator_unit']))
                MACD_Osc_name = 'MACD_Osc_' + info['macd_short'] + '_' + info['macd_long'] + '_' + info['macd_signal']
                #df = self.indicator.get_macd(df, float(info['macd_short']), float(info['macd_long']), float(info['macd_signal']))

                if self.has_position:
                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)

                    if (self.enter_type == '??????' and self.enter_price > self.current_price) or (
                            self.enter_type == '??????' and self.enter_price < self.current_price):
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
                    self.telegram_msg += '????????? : ' + info['name'] + '\n'
                    self.telegram_msg += '?????? ?????? ????????? : ' + df['date'].iloc[-1] + '\n'
                    self.telegram_msg += '????????? : ?????????\n' if info['time_type'] == 'real' else '????????? : ?????????\n'
                    self.telegram_msg += '??????????????? : ???????????????\n' if info['macd_cross_type'] == 'golden_cross' else '??????????????? : ???????????????\n'

                    if info['time_type'] == 'real':
                        self.telegram_msg += '????????? MACD Osc : ' + str(current_val) + '\n'
                        self.telegram_msg += '????????? MACD Osc : ' + str(pre_val) + '\n'
                    else:
                        self.telegram_msg += '????????? MACD Osc : ' + str(current_val) + '\n'
                        self.telegram_msg += '?????? ??? ??? MACD Osc : ' + str(pre_val) + '\n'

                    self.telegram_msg += 'Osc ?????? 0?????? ????????? ??? ??? : ' + str(num_of_skip) + '\n'

                    return self.CONDITION_MEET

                else:
                    return self.CONDITION_FAIL

            elif info['name'] == 'MACD / Osc ?????????':
                df = self.parent.get_df(info['indicator_time_type'], int(info['indicator_unit']))

                MACD_name = 'MACD_' + info['macd_short'] + '_' + info['macd_long'] + '_' + info['macd_signal']
                MACD_Osc_name = 'MACD_Osc_' + info['macd_short'] + '_' + info['macd_long'] + '_' + info['macd_signal']
                #df = self.indicator.get_macd(df, float(info['macd_short']), float(info['macd_long']), float(info['macd_signal']))

                if self.has_position:
                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)

                    if (self.enter_type == '??????' and self.enter_price > self.current_price) or (
                            self.enter_type == '??????' and self.enter_price < self.current_price):
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

                    self.telegram_msg += '????????? : ' + info['name'] + '\n'

                    self.telegram_msg += '?????? ?????? ????????? : ' + df['date'].iloc[-1] + '\n'

                    self.telegram_msg += '?????? MACD ??? ?????? : ' + str(info['macd_val_from']) + ' ~ ' + str(info['macd_val_to']) + '\n'
                    self.telegram_msg += '?????? MACD ??? : ' + str(df[MACD_name].iloc[-1]) + '\n'

                    self.telegram_msg += '?????? MACD Osc ??? ?????? : ' + str(info['macd_osc_val_from']) + ' ~ ' + str(info['macd_osc_val_to']) + '\n'
                    self.telegram_msg += '?????? MACD Osc ??? : ' + str(df[MACD_Osc_name].iloc[-1]) + '\n'

                    return self.CONDITION_MEET

                else:
                    return self.CONDITION_FAIL

            elif info['name'] == 'MACD Osc ??????':
                df = self.parent.get_df(info['indicator_time_type'], int(info['indicator_unit']))
                MACD_Osc_name = 'MACD_Osc_' + info['macd_short'] + '_' + info['macd_long'] + '_' + info['macd_signal']
                #df = self.indicator.get_macd(df, float(info['macd_short']), float(info['macd_long']), float(info['macd_signal']))

                if self.has_position:
                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)

                    if (self.enter_type == '??????' and self.enter_price > self.current_price) or (
                            self.enter_type == '??????' and self.enter_price < self.current_price):
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

                    self.telegram_msg += '????????? : ' + info['name'] + '\n'

                    self.telegram_msg += '?????? ?????? ????????? : ' + df['date'].iloc[-1] + '\n'

                    word_dict = {'0': '????????? ?????? Osc > ????????? ?????? Osc', '1': '????????? ?????? Osc < ????????? ?????? Osc', '2': '????????? ?????? Osc > ????????? Osc', '3': '????????? ?????? Osc < ????????? Osc'}

                    self.telegram_msg += '?????? ?????? : ' + word_dict[info['macd_compare_type']] + '\n'

                    self.telegram_msg += '????????? ?????? MACD Osc : ' + str(df[MACD_Osc_name].iloc[-3]) + '\n'
                    self.telegram_msg += '????????? ?????? MACD Osc : ' + str(df[MACD_Osc_name].iloc[-2]) + '\n'
                    self.telegram_msg += '????????? MACD Osc : ' + str(df[MACD_Osc_name].iloc[-1]) + '\n'

                    return self.CONDITION_MEET
                else:
                    return self.CONDITION_FAIL

            elif info['name'] == 'MACD Osc ?????? ??????':
                df = self.parent.get_df(info['indicator_time_type'], int(info['indicator_unit']))
                MACD_Osc_name = 'MACD_Osc_' + info['macd_short'] + '_' + info['macd_long'] + '_' + info['macd_signal']
                #df = self.indicator.get_macd(df, float(info['macd_short']), float(info['macd_long']), float(info['macd_signal']))

                if self.has_position:
                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)

                    if (self.enter_type == '??????' and self.enter_price > self.current_price) or (
                            self.enter_type == '??????' and self.enter_price < self.current_price):
                        profit = profit * -1

                    target_clear_tick_from = int(info['target_clear_tick_from'])
                    target_clear_tick_to = int(info['target_clear_tick_to'])

                    if target_clear_tick_from <= profit <= target_clear_tick_to:
                        pass
                    else:
                        return self.CONDITION_FAIL

                condition_meet = True
                num_of_bar = int(info['num_of_bar'])
                count = 0
                p1 = -2
                p2 = -3

                osc_val_list = []

                while count < num_of_bar-1:
                    osc_val_list.append(df[MACD_Osc_name].iloc[p1])

                    if (info['macd_change_type'] == 'increase' and df[MACD_Osc_name].iloc[p2] > df[MACD_Osc_name].iloc[p1]) or \
                        (info['macd_change_type'] == 'decrease' and df[MACD_Osc_name].iloc[p2] < df[MACD_Osc_name].iloc[p1]):
                        condition_meet = False
                        break
                    elif df[MACD_Osc_name].iloc[p2] == df[MACD_Osc_name].iloc[p1]:
                        p2 -= 1

                    else:
                        count += 1
                        p1 -= 1
                        p2 -= 1

                osc_val_list.append(df[MACD_Osc_name].iloc[p1])

                if condition_meet:
                    self.telegram_msg += '==============\n'

                    self.telegram_msg += '????????? : ' + info['name'] + '\n'

                    self.telegram_msg += '?????? ?????? ????????? : ' + df['date'].iloc[-1] + '\n'

                    word_dict = {'increase': '??????', 'decrease': '??????'}

                    self.telegram_msg += '?????? ?????? : ' + word_dict[info['macd_change_type']] + '\n'
                    self.telegram_msg += '?????? ??? ?????? : ' + str(num_of_bar) + '???\n'

                    for i in range(len(osc_val_list)):
                        self.telegram_msg += str(i+1) + ' ?????? ?????? MACD Osc : ' + str(osc_val_list[i]) + '\n'

                    return self.CONDITION_MEET
                else:
                    return self.CONDITION_FAIL

            elif info['name'] == '????????????':
                if info['name'] not in self.or_strategy_dict:
                    self.or_strategy_dict[info['name']] = False

                if not self.or_strategy_dict[info['name']]:
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

                    # print(self.telegram_msg)

                    if self.has_position:
                        profit = abs(self.current_price - self.enter_price)
                        profit = int(profit // self.tick_unit)

                        if (self.enter_type == '??????' and self.enter_price > self.current_price) or (
                                self.enter_type == '??????' and self.enter_price < self.current_price):
                            profit = profit * -1

                        first_target_clear_tick_from = int(info['first_target_clear_tick_from'])
                        first_target_clear_tick_to = int(info['first_target_clear_tick_to'])

                        if first_target_clear_tick_from <= profit <= first_target_clear_tick_to:
                            pass
                        else:
                            return self.CONDITION_FAIL

                    if first_tick_diff_from <= int(diff_val // self.tick_unit) and int(
                            diff_val // self.tick_unit) <= first_tick_diff_to:

                        self.telegram_msg += '==============\n'

                        self.telegram_msg += '????????? : ' + info['name'] + '(1)\n'

                        self.telegram_msg += '?????? ?????? ????????? : ' + df['date'].iloc[-1] + '\n'

                        word_dict = {'prev': '??????', 'today': '??????', 'open': '??????', 'high': '??????', 'close': '??????', 'low': '??????',
                                     'middle': '?????????'}

                        if info['first_type'] == 'manual':
                            self.telegram_msg += '????????? ?????? ?????? : ??????\n'
                        else:
                            self.telegram_msg += '????????? ?????? ?????? : ' + word_dict[temp[0]] + word_dict[temp[1]] + '\n'

                        self.telegram_msg += '????????? ?????? : ' + str(first_val) + '\n'
                        self.telegram_msg += '?????? ?????? : ' + str(current_price) + '\n'

                        self.telegram_msg += '??? ??? ?????? : ' + str(diff_val) + '\n'
                        self.telegram_msg += '??? ??? ????????? : ' + str(int(diff_val // self.tick_unit)) + '\n'
                        self.telegram_msg += '??? ?????? : ' + str(first_tick_diff_from) + ' ~ ' + str(first_tick_diff_to) + '\n'

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

                            if (self.enter_type == '??????' and self.enter_price > self.current_price) or (
                                    self.enter_type == '??????' and self.enter_price < self.current_price):
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

                            self.telegram_msg += '????????? : ' + info['name'] + '(2)\n'

                            self.telegram_msg += '?????? ?????? ????????? : ' + df['date'].iloc[-1] + '\n'

                            word_dict = {'today_high': '????????????', 'today_low': '????????????'}

                            self.telegram_msg += '??????????????? : ' + str(today_middle) + '\n'
                            self.telegram_msg += word_dict[info['second_type']] + ' : ' + str(second_val) + '\n'
                            self.telegram_msg += word_dict[info['second_type']] + ' ' + info[
                                'second_numerator'] + '/10 : ' + str(second_calc_val) + '\n'

                            self.telegram_msg += '??? ??? ?????? : ' + str(diff_val) + '\n'
                            self.telegram_msg += '??? ??? ????????? : ' + str(int(diff_val // self.tick_unit)) + '\n'
                            self.telegram_msg += '??? ?????? : ' + str(second_tick_diff_from) + ' ~ ' + str(
                                second_tick_diff_to) + '\n'

                            self.or_strategy_dict[info['name']] = True

                            return self.CONDITION_MEET

                        else:
                            return self.CONDITION_PASS

            elif info['name'] == '??????????????????':
                start_hour = int(info['start_hour'])
                start_min = int(info['start_min'])
                end_hour = int(info['end_hour'])
                end_min = int(info['end_min'])

                if self.is_time_between(datetime.time(int(start_hour % 24), int(start_min % 60), 0), datetime.time(int(end_hour % 24), int(end_min % 60), 0)):

                    condition_tick = int(info['condition_tick'])
                    return_tick = int(info['return_tick'])

                    if self.enter_type == '??????':
                        if self.stop_trailing_on:
                            if self.current_price >= self.stop_trailing_price:
                                self.stop_trailing_price = self.current_price
                                # print('?????? ????????? : ', self.stop_trailing_price)

                            elif self.current_price <= self.stop_trailing_price - (self.tick_unit * return_tick):
                                self.stop_trailing_on = False

                                self.telegram_msg += '==============\n'

                                self.telegram_msg += '????????? : ' + info['name'] + '\n'

                                self.telegram_msg += '?????? ?????? ??? : ' + str(condition_tick) + '???\n'
                                self.telegram_msg += '?????? ?????? ??? : ' + str(return_tick) + '???\n'
                                self.telegram_msg += '????????? : ' + str(self.enter_price) + '\n'
                                self.telegram_msg += '????????? : ' + str(self.current_price) + '\n'
                                self.telegram_msg += '?????? ?????? ??? : ' + str(
                                    int((self.stop_trailing_price - self.enter_price) / self.tick_unit)) + '\n'
                                self.telegram_msg += '?????? ??? : ' + str(
                                    int((self.current_price - self.enter_price) / self.tick_unit)) + '\n'

                                self.stop_trailing_price = 0

                                return self.CONDITION_MEET

                        else:
                            if self.current_price >= self.enter_price + (self.tick_unit * condition_tick):
                                self.stop_trailing_price = self.current_price
                                self.stop_trailing_on = True

                                temp_msg = '!!!??????????????? ???????????????!!!\n' if self.is_simulation_strategy else ''
                                temp_msg += '!!!???????????? ????????????!!!\n' if self.is_virtual_trade() else ''

                                temp_msg += '?????? ?????? : ' + self.strategy_name + '\n'
                                temp_msg += '?????????????????? ????????? ?????????????????????.\n'
                                temp_msg += '?????? ?????? ??? : ' + str(condition_tick) + '\n'

                                temp_msg += '????????? : ' + str(self.enter_price) + '\n'
                                temp_msg += '????????? : ' + str(self.current_price) + '\n'

                                self.parent.send_telegram(temp_msg)

                                # print(temp)

                    else:
                        if self.stop_trailing_on:
                            if self.current_price <= self.stop_trailing_price:
                                self.stop_trailing_price = self.current_price

                            elif self.current_price > self.stop_trailing_price + (self.tick_unit * return_tick):
                                self.stop_trailing_on = False

                                self.telegram_msg += '==============\n'

                                self.telegram_msg += '????????? : ' + info['name'] + '\n'

                                self.telegram_msg += '?????? ?????? ??? : ' + str(condition_tick) + '???\n'
                                self.telegram_msg += '?????? ?????? ??? : ' + str(return_tick) + '???\n'
                                self.telegram_msg += '????????? : ' + str(self.enter_price) + '\n'
                                self.telegram_msg += '????????? : ' + str(self.current_price) + '\n'
                                self.telegram_msg += '?????? ?????? ??? : ' + str(
                                    int((self.enter_price - self.stop_trailing_price) / self.tick_unit)) + '\n'
                                self.telegram_msg += '?????? ??? : ' + str(
                                    int((self.enter_price - self.current_price) / self.tick_unit)) + '\n'

                                self.stop_trailing_price = 0
                                return self.CONDITION_MEET

                        else:
                            if self.current_price <= self.enter_price - (self.tick_unit * condition_tick):
                                self.stop_trailing_price = self.current_price
                                self.stop_trailing_on = True

                                temp_msg = '!!!??????????????? ???????????????!!!\n' if self.is_simulation_strategy else ''
                                temp_msg += '!!!???????????? ????????????!!!\n' if self.is_virtual_trade() else ''

                                temp_msg += '?????? ?????? : ' + self.strategy_name + '\n'
                                temp_msg += '?????????????????? ????????? ?????????????????????.\n'
                                temp_msg += '?????? ?????? ??? : ' + str(condition_tick) + '\n'

                                temp_msg += '????????? : ' + str(self.enter_price) + '\n'
                                temp_msg += '????????? : ' + str(self.current_price) + '\n'

                                self.parent.send_telegram(temp_msg)

                return self.CONDITION_PASS

            elif info['name'] == '????????????':
                start_hour = int(info['start_hour'])
                start_min = int(info['start_min'])
                end_hour = int(info['end_hour'])
                end_min = int(info['end_min'])

                if self.is_time_between(datetime.time(int(start_hour % 24), int(start_min % 60), 0), datetime.time(int(end_hour % 24), int(end_min % 60), 0)):

                    condition_tick = int(info['condition_tick'])
                    return_tick = int(info['return_tick'])

                    if self.enter_type == '??????':
                        if self.preserve_profit_on:
                            if self.current_price <= self.preserve_profit_price - (self.tick_unit * return_tick):
                                self.preserve_profit_on = False
                                self.preserve_profit_price = 0

                                self.telegram_msg += '==============\n'

                                self.telegram_msg += '????????? : ' + info['name'] + '\n'

                                self.telegram_msg += '?????? ?????? ??? : ' + str(condition_tick) + '???\n'
                                self.telegram_msg += '?????? ?????? ??? : ' + str(return_tick) + '???\n'
                                self.telegram_msg += '????????? : ' + str(self.enter_price) + '\n'
                                self.telegram_msg += '????????? : ' + str(self.current_price) + '\n'
                                self.telegram_msg += '?????? ??? : ' + str(
                                    int((self.current_price - self.enter_price) / self.tick_unit)) + '\n'

                                self.clear_by_preserver_profit = True

                                return self.CONDITION_MEET

                        else:
                            if self.current_price >= self.enter_price + (self.tick_unit * condition_tick):
                                self.preserve_profit_price = self.current_price
                                self.preserve_profit_on = True

                                temp_msg = '!!!??????????????? ???????????????!!!\n' if self.is_simulation_strategy else ''
                                temp_msg += '!!!???????????? ????????????!!!\n' if self.is_virtual_trade() else ''

                                temp_msg += '?????? ?????? : ' + self.strategy_name + '\n'
                                temp_msg += '?????? ?????? ????????? ?????????????????????.\n'
                                temp_msg += '?????? ?????? ??? : ' + str(condition_tick) + '\n'
                                temp_msg += '????????? : ' + str(self.enter_price) + '\n'
                                temp_msg += '????????? : ' + str(self.current_price) + '\n'

                                self.parent.send_telegram(temp_msg)


                    else:
                        if self.preserve_profit_on:
                            if self.current_price >= self.preserve_profit_price + (
                                    self.tick_unit * return_tick):
                                self.preserve_profit_on = False
                                self.preserve_profit_price = 0

                                self.telegram_msg += '==============\n'

                                self.telegram_msg += '????????? : ' + info['name'] + '\n'

                                self.telegram_msg += '?????? ?????? ??? : ' + str(condition_tick) + '???\n'
                                self.telegram_msg += '?????? ?????? ??? : ' + str(return_tick) + '???\n'
                                self.telegram_msg += '????????? : ' + str(self.enter_price) + '\n'
                                self.telegram_msg += '????????? : ' + str(self.current_price) + '\n'
                                self.telegram_msg += '?????? ??? : ' + str(
                                    int((self.enter_price - self.current_price) / self.tick_unit)) + '\n'

                                self.clear_by_preserver_profit = True

                                return self.CONDITION_MEET

                        else:
                            if self.current_price <= self.enter_price - (self.tick_unit * condition_tick):
                                self.preserve_profit_price = self.current_price
                                self.preserve_profit_on = True

                                temp_msg = '!!!??????????????? ???????????????!!!\n' if self.is_simulation_strategy else ''
                                temp_msg += '!!!???????????? ????????????!!!\n' if self.is_virtual_trade() else ''

                                temp_msg += '?????? ?????? : ' + self.strategy_name + '\n'
                                temp_msg += '?????? ?????? ????????? ?????????????????????.\n'
                                temp_msg += '?????? ?????? ??? : ' + str(condition_tick) + '\n'
                                temp_msg += '????????? : ' + str(self.enter_price) + '\n'
                                temp_msg += '????????? : ' + str(self.current_price) + '\n'

                                self.parent.send_telegram(temp_msg)

                return self.CONDITION_PASS


            elif info['name'] == '??? ??????':
                start_hour = int(info['start_hour'])
                start_min = int(info['start_min'])
                end_hour = int(info['end_hour'])
                end_min = int(info['end_min'])

                if self.is_time_between(datetime.time(int(start_hour % 24), int(start_min % 60), 0), datetime.time(int(end_hour % 24), int(end_min % 60), 0)):

                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)
                    if (self.enter_type == '??????' and self.enter_price > self.current_price) or (self.enter_type == '??????' and self.enter_price < self.current_price):
                        profit = profit * -1


                    profit_tick = int(info['profit_tick'])
                    loss_tick = int(info['loss_tick'])

                    if profit <= loss_tick * -1 or profit_tick <= profit:
                        self.telegram_msg += '==============\n'

                        self.telegram_msg += '????????? : ' + info['name'] + '\n'

                        self.telegram_msg += '?????? ??? ??? : ' + str(profit_tick) + '???\n'
                        self.telegram_msg += '?????? ??? ??? : ' + str(loss_tick) + '???\n'
                        self.telegram_msg += '????????? : ' + str(self.enter_price) + '\n'
                        self.telegram_msg += '????????? : ' + str(self.current_price) + '\n'
                        self.telegram_msg += '?????? ??? : ' + str(profit) + '\n'

                        return self.CONDITION_MEET

                return self.CONDITION_PASS


        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, fname, exc_tb.tb_lineno)

    def ai_indicator_check(self, info):
        try:
            if info['name'] == '??????????????????':
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

                        if self.enter_type == '??????':
                            if self.stop_trailing_on:
                                if self.current_price >= self.stop_trailing_price:
                                    self.stop_trailing_price = self.current_price
                                    # print('?????? ????????? : ', self.stop_trailing_price)

                                elif self.current_price <= self.stop_trailing_price - (self.tick_unit * return_tick):
                                    self.stop_trailing_on = False

                                    self.telegram_msg += '==============\n'
                                    self.telegram_msg += '!!!AI ?????? ???????????????.!!!\n'
                                    self.telegram_msg += '????????? : ' + info['name'] + '\n'

                                    self.telegram_msg += '?????? ?????? ??? : ' + str(condition_tick) + '???\n'
                                    self.telegram_msg += '?????? ?????? ??? : ' + str(return_tick) + '???\n'
                                    self.telegram_msg += '????????? : ' + str(self.enter_price) + '\n'
                                    self.telegram_msg += '????????? : ' + str(self.current_price) + '\n'
                                    self.telegram_msg += '?????? ?????? ??? : ' + str(
                                        int((self.stop_trailing_price - self.enter_price) / self.tick_unit)) + '\n'
                                    self.telegram_msg += '?????? ??? : ' + str(
                                        int((self.current_price - self.enter_price) / self.tick_unit)) + '\n'

                                    self.stop_trailing_price = 0

                                    return self.CONDITION_MEET

                            else:
                                if self.current_price >= self.enter_price + (self.tick_unit * condition_tick):
                                    self.stop_trailing_price = self.current_price
                                    self.stop_trailing_on = True

                                    temp_msg = '!!!??????????????? ???????????????!!!\n' if self.is_simulation_strategy else ''
                                    temp_msg += '!!!???????????? ????????????!!!\n' if self.is_virtual_trade() else ''
                                    temp_msg += '!!!AI ?????? ???????????????.!!!\n'

                                    temp_msg += '?????? ?????? : ' + self.strategy_name + '\n'
                                    temp_msg += '?????????????????? ????????? ?????????????????????.\n'
                                    temp_msg += '?????? ?????? ??? : ' + str(condition_tick) + '\n'

                                    temp_msg += '????????? : ' + str(self.enter_price) + '\n'
                                    temp_msg += '????????? : ' + str(self.current_price) + '\n'

                                    self.parent.send_telegram(temp_msg)

                                    # print(temp)

                        else:
                            if self.stop_trailing_on:
                                if self.current_price <= self.stop_trailing_price:
                                    self.stop_trailing_price = self.current_price

                                elif self.current_price > self.stop_trailing_price + (self.tick_unit * return_tick):
                                    self.stop_trailing_on = False

                                    self.telegram_msg += '==============\n'
                                    self.telegram_msg += '!!!AI ?????? ???????????????.!!!\n'
                                    self.telegram_msg += '????????? : ' + info['name'] + '\n'

                                    self.telegram_msg += '?????? ?????? ??? : ' + str(condition_tick) + '???\n'
                                    self.telegram_msg += '?????? ?????? ??? : ' + str(return_tick) + '???\n'
                                    self.telegram_msg += '????????? : ' + str(self.enter_price) + '\n'
                                    self.telegram_msg += '????????? : ' + str(self.current_price) + '\n'
                                    self.telegram_msg += '?????? ?????? ??? : ' + str(
                                        int((self.enter_price - self.stop_trailing_price) / self.tick_unit)) + '\n'
                                    self.telegram_msg += '?????? ??? : ' + str(
                                        int((self.enter_price - self.current_price) / self.tick_unit)) + '\n'

                                    self.stop_trailing_price = 0
                                    return self.CONDITION_MEET

                            else:
                                if self.current_price <= self.enter_price - (self.tick_unit * condition_tick):
                                    self.stop_trailing_price = self.current_price
                                    self.stop_trailing_on = True

                                    temp_msg = '!!!??????????????? ???????????????!!!\n' if self.is_simulation_strategy else ''
                                    temp_msg += '!!!???????????? ????????????!!!\n' if self.is_virtual_trade() else ''
                                    temp_msg += '!!!AI ?????? ???????????????.!!!\n'
                                    temp_msg += '?????? ?????? : ' + self.strategy_name + '\n'
                                    temp_msg += '?????????????????? ????????? ?????????????????????.\n'
                                    temp_msg += '?????? ?????? ??? : ' + str(condition_tick) + '\n'

                                    temp_msg += '????????? : ' + str(self.enter_price) + '\n'
                                    temp_msg += '????????? : ' + str(self.current_price) + '\n'

                                    self.parent.send_telegram(temp_msg)

                return self.CONDITION_PASS

            elif info['name'] == '????????????':
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

                        if self.enter_type == '??????':
                            if self.preserve_profit_on:
                                if self.current_price <= self.preserve_profit_price - (self.tick_unit * return_tick):
                                    self.preserve_profit_on = False
                                    self.preserve_profit_price = 0

                                    self.telegram_msg += '==============\n'
                                    self.telegram_msg += '!!!AI ?????? ???????????????.!!!\n'
                                    self.telegram_msg += '????????? : ' + info['name'] + '\n'

                                    self.telegram_msg += '?????? ?????? ??? : ' + str(condition_tick) + '???\n'
                                    self.telegram_msg += '?????? ?????? ??? : ' + str(return_tick) + '???\n'
                                    self.telegram_msg += '????????? : ' + str(self.enter_price) + '\n'
                                    self.telegram_msg += '????????? : ' + str(self.current_price) + '\n'
                                    self.telegram_msg += '?????? ??? : ' + str(
                                        int((self.current_price - self.enter_price) / self.tick_unit)) + '\n'

                                    self.clear_by_preserver_profit = True

                                    return self.CONDITION_MEET

                            else:
                                if self.current_price >= self.enter_price + (self.tick_unit * condition_tick):
                                    self.preserve_profit_price = self.current_price
                                    self.preserve_profit_on = True

                                    temp_msg = '!!!??????????????? ???????????????!!!\n' if self.is_simulation_strategy else ''
                                    temp_msg += '!!!???????????? ????????????!!!\n' if self.is_virtual_trade() else ''
                                    temp_msg += '!!!AI ?????? ???????????????.!!!\n'
                                    temp_msg += '?????? ?????? : ' + self.strategy_name + '\n'
                                    temp_msg += '?????? ?????? ????????? ?????????????????????.\n'
                                    temp_msg += '?????? ?????? ??? : ' + str(condition_tick) + '\n'
                                    temp_msg += '????????? : ' + str(self.enter_price) + '\n'
                                    temp_msg += '????????? : ' + str(self.current_price) + '\n'

                                    self.parent.send_telegram(temp_msg)


                        else:
                            if self.preserve_profit_on:
                                if self.current_price >= self.preserve_profit_price + (self.tick_unit * return_tick):
                                    self.preserve_profit_on = False
                                    self.preserve_profit_price = 0

                                    self.telegram_msg += '==============\n'
                                    self.telegram_msg += '!!!AI ?????? ???????????????.!!!\n'
                                    self.telegram_msg += '????????? : ' + info['name'] + '\n'

                                    self.telegram_msg += '?????? ?????? ??? : ' + str(condition_tick) + '???\n'
                                    self.telegram_msg += '?????? ?????? ??? : ' + str(return_tick) + '???\n'
                                    self.telegram_msg += '????????? : ' + str(self.enter_price) + '\n'
                                    self.telegram_msg += '????????? : ' + str(self.current_price) + '\n'
                                    self.telegram_msg += '?????? ??? : ' + str(
                                        int((self.enter_price - self.current_price) / self.tick_unit)) + '\n'

                                    self.clear_by_preserver_profit = True

                                    return self.CONDITION_MEET

                            else:
                                if self.current_price <= self.enter_price - (self.tick_unit * condition_tick):
                                    self.preserve_profit_price = self.current_price
                                    self.preserve_profit_on = True

                                    temp_msg = '!!!??????????????? ???????????????!!!\n' if self.is_simulation_strategy else ''
                                    temp_msg += '!!!???????????? ????????????!!!\n' if self.is_virtual_trade() else ''
                                    temp_msg += '!!!AI ?????? ???????????????.!!!\n'
                                    temp_msg += '?????? ?????? : ' + self.strategy_name + '\n'
                                    temp_msg += '?????? ?????? ????????? ?????????????????????.\n'
                                    temp_msg += '?????? ?????? ??? : ' + str(condition_tick) + '\n'
                                    temp_msg += '????????? : ' + str(self.enter_price) + '\n'
                                    temp_msg += '????????? : ' + str(self.current_price) + '\n'

                                    self.parent.send_telegram(temp_msg)

                return self.CONDITION_PASS


            elif info['name'] == '??? ??????':
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
                        if (self.enter_type == '??????' and self.enter_price > self.current_price) or (self.enter_type == '??????' and self.enter_price < self.current_price):
                            profit = profit * -1


                        profit_tick = int(info['profit_tick'])
                        loss_tick = int(info['loss_tick'])

                        if profit <= loss_tick * -1 or profit_tick <= profit:
                            self.telegram_msg += '==============\n'
                            self.telegram_msg += '!!!AI ?????? ???????????????.!!!\n'
                            self.telegram_msg += '????????? : ' + info['name'] + '\n'

                            self.telegram_msg += '?????? ??? ??? : ' + str(profit_tick) + '???\n'
                            self.telegram_msg += '?????? ??? ??? : ' + str(loss_tick) + '???\n'
                            self.telegram_msg += '????????? : ' + str(self.enter_price) + '\n'
                            self.telegram_msg += '????????? : ' + str(self.current_price) + '\n'
                            self.telegram_msg += '?????? ??? : ' + str(profit) + '\n'

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

                        temp_msg = '!!!??????????????? ???????????????!!!\n' if self.is_simulation_strategy else ''
                        temp_msg += '?????? ?????? : ' + self.strategy_name + '\n'
                        temp_msg += '???????????? (????????????)??? ???????????????.\n'

                        word_dict = {'tick': '???', 'times': '???'}

                        temp_msg += '????????? ?????? ??? : ' + str(self.virtual_rerun_unit) + \
                                    word_dict[str(self.virtual_rerun_type)] + ' ?????? ??? ?????????' + '\n'

                        temp_msg += '?????? ?????? ?????? ?????? : ' + str(self.virtual_loss_total_tick) + '\n'
                        temp_msg += '?????? ?????? ?????? ?????? : ' + str(
                            self.virtual_current_loss_total_tick) + '\n\n'

                        temp_msg += '?????? ?????? ?????? ?????? : ' + str(self.virtual_total_enter_times) + '\n'
                        temp_msg += '?????? ?????? ?????? ?????? : ' + str(
                            self.virtual_current_total_enter_times) + '\n\n'

                        temp_msg += '?????? ?????? ?????? ?????? : ' + str(
                            self.virtual_consecutive_loss_times) + '\n'
                        temp_msg += '?????? ?????? ?????? ?????? : ' + str(
                            self.virtual_current_consecutive_loss_times) + '\n\n'

                        temp_msg += '?????? ?????? ?????? ?????? ?????? : ' + str(
                            self.virtual_consecutive_profit_preserve_times) + '\n'
                        temp_msg += '?????? ?????? ?????? ?????? ?????? : ' + str(
                            self.virtual_current_consecutive_profit_preserve_times) + '\n\n'

                        temp_msg += '?????? ?????? (??????+????????????) ?????? : ' + str(
                            self.virtual_consecutive_loss_and_profit_preserve_times) + '\n'
                        temp_msg += '?????? ?????? (??????+????????????) ?????? : ' + str(
                            self.virtual_current_consecutive_loss_and_profit_preserve_times) + '\n'

                        self.parent.send_telegram(temp_msg)
                else:
                    if (self.virtual_rerun_type == 'tick' and self.virtual_rerun_unit <= self.current_total_tick_for_virtual_trade) or \
                        (self.virtual_rerun_type == 'times' and self.virtual_rerun_unit <= self.current_total_profit_enter_times):
                        self.is_first_meet_virtual_indicator_running = True

                        temp_msg = '!!!??????????????? ???????????????!!!\n' if self.is_simulation_strategy else ''
                        temp_msg += '?????? ?????? : ' + self.strategy_name + '\n'
                        temp_msg += '???????????? (????????????)??? ????????? ?????????.\n'

                        word_dict = {'tick': '???', 'times': '???'}

                        temp_msg += '????????? ?????? ??? : ' + str(self.virtual_rerun_unit) + \
                                    word_dict[str(self.virtual_rerun_type)] + ' ?????? ??? ?????????' + '\n'

                        temp_msg += '?????? ?????? ?????? ?????? : ' + str(
                            self.current_total_profit_enter_times) + '\n\n'

                        temp_msg += '?????? ??? ?????? ?????? : ' + str(
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

                            temp_msg = '!!!??????????????? ???????????????!!!\n' if self.is_simulation_strategy else ''
                            temp_msg += '?????? ?????? : ' + self.strategy_name + '\n'
                            temp_msg += '???????????? (???????????????)??? ???????????????.\n'

                            word_dict = {'tick': '???', 'times': '???'}

                            temp_msg += '????????? ?????? ??? : ' + str(self.virtual_rerun_unit) + \
                                        word_dict[str(self.virtual_rerun_type)] + ' ?????? ??? ?????????' + '\n'

                            temp_msg += '?????? ?????? ?????? : ' + str(self.virtual_pending_min) + '??? \n'
                            temp_msg += '?????? ?????? ?????? : ' + str(int(current_pending_min)) + '??? \n\n'

                            temp_msg += '?????? ?????? ?????? ?????? : ' + str(self.virtual_total_enter_times) + '\n'
                            temp_msg += '?????? ?????? ?????? ?????? : ' + str(self.virtual_current_total_enter_times) + '\n\n'

                            self.parent.send_telegram(temp_msg)

                    else:
                        if (self.virtual_last_enter_time - self.virtual_first_enter_time).total_seconds() // 60.0 == 0:
                            self.virtual_first_enter_time = datetime.datetime.now()
                            self.current_total_profit_enter_times = 0
                            self.current_total_tick_for_virtual_trade = 0

                            self.virtual_current_total_enter_times = 0

                            temp_msg = '!!!??????????????? ???????????????!!!\n' if self.is_simulation_strategy else ''
                            temp_msg += '?????? ?????? : ' + self.strategy_name + '\n'
                            temp_msg += '???????????? (???????????????)??? ????????? ???????????? ???????????????.\n'

                            word_dict = {'tick': '???', 'times': '???'}

                            temp_msg += '????????? ?????? ??? : ' + str(self.virtual_rerun_unit) + \
                                        word_dict[str(self.virtual_rerun_type)] + ' ?????? ??? ?????????' + '\n'

                            temp_msg += '?????? ?????? ?????? : ' + str(self.virtual_pending_min) + '??? \n'
                            temp_msg += '?????? ?????? ?????? : ' + str(int(current_pending_min)) + '??? \n\n'

                            self.parent.send_telegram(temp_msg)

                        else:
                            self.virtual_first_enter_time == self.virtual_last_enter_time

                else:
                    if (self.virtual_rerun_type == 'tick' and self.virtual_rerun_unit <= self.current_total_tick_for_virtual_trade) or \
                            (self.virtual_rerun_type == 'times' and self.virtual_rerun_unit <= self.current_total_profit_enter_times):
                        self.is_box_virtual_indicator_running = True

                        temp_msg = '!!!??????????????? ???????????????!!!\n' if self.is_simulation_strategy else ''
                        temp_msg += '?????? ?????? : ' + self.strategy_name + '\n'
                        temp_msg += '???????????? (???????????????)??? ????????? ?????????.\n'

                        word_dict = {'tick': '???', 'times': '???'}

                        temp_msg += '????????? ?????? ??? : ' + str(self.virtual_rerun_unit) + \
                                    word_dict[str(self.virtual_rerun_type)] + ' ?????? ??? ?????????' + '\n'

                        temp_msg += '?????? ?????? ?????? ?????? : ' + str(
                            self.current_total_profit_enter_times) + '\n\n'

                        temp_msg += '?????? ??? ?????? ?????? : ' + str(
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

                temp_msg = '!!!??????????????? ???????????????!!!\n' if self.is_simulation_strategy else ''
                temp_msg += '?????? ?????? : ' + self.strategy_name + '\n'
                temp_msg += '????????? ?????? ??????/?????? ?????? ???????????? ????????? ???????????????.\n'

                temp_msg += '?????? ?????? ?????? ???: ' + str(int(self.current_total_profit_tick)) + '\n'
                temp_msg += '?????? ?????? ?????? ??? : ' + str(self.max_loss) + '\n'
                temp_msg += '?????? ?????? ?????? ??? : ' + str(self.max_profit) + '\n'

                self.parent.send_telegram(temp_msg)

            return True
        return False

    def enter_position_req(self, enter_type=''):
        if self.is_simulation_strategy or self.is_virtual_trade():
            if self.is_virtual_trade():
                self.telegram_msg = '!!!???????????? ????????????!!!\n' + self.telegram_msg
            if self.is_simulation_strategy:
                self.telegram_msg = '!!!??????????????? ???????????????!!!\n' + self.telegram_msg

            self.has_position = True
            self.last_enter_type = enter_type
            self.enter_type = enter_type
            self.enter_price = self.parent.get_current_price()

            now = datetime.datetime.now()
            self.enter_time_for_excel = now.strftime('%Y-%m-%d %H:%M:%S.%f')

        else:
            self.need_to_load_position = True

            checking_real_position_thread = threading.Thread(target=self.set_real_position)
            checking_real_position_thread.start()

        self.enter_id = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(10))

        now = datetime.datetime.now()
        self.telegram_msg += '==============\n'
        self.telegram_msg += '?????? ?????? ?????? ??? ?????? ??? : \n' + str(self.current_total_profit_tick) + '\n'
        self.telegram_msg += '==============\n'
        self.telegram_msg += '?????? ?????? ?????? ?????? : \n' + now.strftime('%Y-%m-%d %H:%M:%S.%f') + '\n'

        print('?????? ?????? ?????? ?????? : ', now.strftime('%Y-%m-%d %H:%M:%S.%f'))

        self.excel_enter_indicator = self.telegram_msg
        self.parent.send_telegram(self.telegram_msg)

        self.reset_cross_check()
        self.last_parabolic_enter_value = self.last_parabolic_enter_value_temp

        if self.last_parabolic_enter_time == self.last_parabolic_enter_time_temp or self.last_parabolic_enter_time == '':
            self.parabolic_same_bar_enter_times += 1

        self.last_parabolic_enter_time = self.last_parabolic_enter_time_temp

        if self.is_simulation_strategy or self.is_virtual_trade():
            info = {}

            info['enter_id'] = self.enter_id
            info['trade_type'] = '????????????' if self.is_virtual_trade() else '???????????????'
            info['strategy_name'] = self.strategy_name
            info['acc_num'] = self.trade_account
            info['quant'] = self.quant
            info['enter_type'] = '??????' if self.enter_type == '??????' else '??????'
            info['enter_time'] = self.enter_time_for_excel
            info['enter_price'] = self.enter_price
            info['order_send_time'] = self.enter_time_for_excel
            info['order_complete_time'] = self.enter_time_for_excel
            info['enter_indicator'] = self.excel_enter_indicator

            self.parent.add_trade_info_to_excel('enter', info)

    def clear_position_req(self, from_user=False, profit_total_clear=False, all_clear=False):
        try:
            if profit_total_clear:
                self.profit_total_clear_flag = True

            if from_user:
                self.excel_clear_indicator = ''

                if self.is_virtual_trade():
                    self.excel_clear_indicator += '!!!???????????? ????????????!!!\n'
                if self.is_simulation_strategy:
                    self.excel_clear_indicator += '!!!??????????????? ???????????????!!!\n'

                self.excel_clear_indicator += '????????? ?????? ?????? ?????? ???????????????.\n'

            else:
                if self.is_virtual_trade():
                    self.telegram_msg = '!!!???????????? ????????????!!!\n' + self.telegram_msg
                if self.is_simulation_strategy:
                    self.telegram_msg = '!!!??????????????? ???????????????!!!\n' + self.telegram_msg

                now = datetime.datetime.now()
                self.telegram_msg += '==============\n'
                self.telegram_msg += '?????? ?????? ?????? ??? ?????? ??? : \n' + str(self.current_total_profit_tick) + '\n'
                self.telegram_msg += '==============\n'
                self.telegram_msg += '?????? ?????? ?????? ?????? : \n' + now.strftime('%Y-%m-%d %H:%M:%S.%f') + '\n'

                self.excel_clear_indicator = self.telegram_msg

                self.parent.send_telegram(self.telegram_msg)

            if self.is_simulation_strategy or self.is_virtual_trade():
                if self.has_position:
                    #self.current_price = self.parent.get_current_price()
                    profit = abs(self.current_price - self.enter_price)
                    profit = int(profit // self.tick_unit)
                    if self.enter_type == '??????':
                        if self.enter_price < self.current_price:
                            result = '??????'
                        else:
                            result = '??????'
                            profit = profit * -1
                    elif self.enter_type == '??????':
                        if self.enter_price > self.current_price:
                            result = '??????'
                        else:
                            result = '??????'
                            profit = profit * -1

                    if not self.is_virtual_trade():
                        self.current_total_profit_tick += profit * self.quant

                    now = datetime.datetime.now()
                    self.clear_time_for_excel = now.strftime('%Y-%m-%d %H:%M:%S.%f')
                    #
                    # self.telegram_msg = '!!!??????????????? ???????????????!!!\n' if self.is_simulation_strategy else ''
                    # self.telegram_msg += '!!!???????????? ????????????!!!\n' if self.is_virtual_trade() else ''
                    # self.telegram_msg += '!!!AI ???????????????!!!\n' if self.is_there_ai_clear else ''
                    # self.telegram_msg += '?????? ???????????? ???????????????. (' + result + ')\n'
                    # self.telegram_msg += '?????? ?????? : ' + self.strategy_name + '\n'
                    # self.telegram_msg += '?????? ??? : ' + str(self.quant) + '\n'
                    # self.telegram_msg += '????????? : ' + str(self.enter_price) + '\n'
                    # self.telegram_msg += '????????? : ' + str(current_price) + '\n'
                    # self.telegram_msg += '?????? ?????? ??? : ' + str(profit) + '\n'
                    # self.telegram_msg += '?????? ?????? ?????? ?????? ??? : ' + str(self.current_total_profit_tick) + '\n'
                    #
                    # self.parent.send_telegram(self.telegram_msg)

                    if profit_total_clear:
                        self.telegram_msg = '?????? ?????? ???????????????.\n'
                        self.telegram_msg += '?????? ?????? : ' + self.strategy_name + '\n'
                        self.telegram_msg += '?????? ?????? ?????? ??? ?????? ??? : \n' + str(self.current_total_profit_tick) + '\n'

                        self.excel_clear_indicator = self.telegram_msg



                    info = {}

                    info['enter_id'] = self.enter_id
                    info['trade_type'] = '????????????' if self.is_virtual_trade() else '???????????????'
                    info['strategy_name'] = self.strategy_name
                    info['acc_num'] = self.trade_account
                    info['quant'] = self.quant
                    info['clear_type'] = '??????' if self.enter_type == '??????' else '??????'
                    info['clear_time'] = self.clear_time_for_excel
                    info['clear_price'] = self.current_price
                    info['order_send_time'] = self.clear_time_for_excel
                    info['order_complete_time'] = self.clear_time_for_excel
                    info['clear_indicator'] = self.excel_clear_indicator

                    # self.parent.add_trade_info_to_excel('clear', info)

                    info['enter_type'] = '??????' if self.enter_type == '??????' else '??????'
                    info['enter_time'] = self.enter_time_for_excel
                    info['enter_price'] = self.enter_price
                    info['enter_indicator'] = self.excel_enter_indicator

                    info['program_price_profit_tick'] = str(profit) + '(' + str(profit * self.quant) + ')'
                    info['real_price_profit_tick'] = profit
                    info['real_price_total_profit_tick'] = profit * self.quant
                    info['total_profit_dollar'] = profit * self.tick_value * self.quant

                    self.parent.add_trade_info_to_excel('clear', info)

                    self.update_virtual_trade(profit * self.quant)

                    self.has_position = False
                    self.enter_type = ''
                    self.enter_price = 0

                    if from_user:
                        if not all_clear:
                            temp = {}
                            temp['command'] = 'clear_position_from_auto_trader'
                            temp['result'] = '0'

                            self.parent.aws_mqtt.publish_message(temp)
                        else:
                            self.parent.num_of_all_clear += 1
                elif from_user:
                    if not all_clear:
                        temp = {}
                        temp['command'] = 'clear_position_from_auto_trader'
                        temp['result'] = '-1'

                        self.parent.aws_mqtt.publish_message(temp)

            else:
                if self.has_position:
                    self.need_to_load_position = True

                    checking_real_position_thread = threading.Thread(target=self.set_real_position)
                    checking_real_position_thread.start()

                    if from_user or profit_total_clear:
                        print('???????????? : ', self.position)

                        if self.enter_type == '??????':
                            self.waiting_enter_type = '??????'
                            self.parent.order_queue.append({'type': self.CLEAR_BUY_SIGNAL, 'acc_num': self.trade_account, 'quant': self.quant,'position': self.position})
                        else:
                            self.waiting_enter_type = '??????'
                            self.parent.order_queue.append({'type': self.CLEAR_SELL_SIGNAL, 'acc_num': self.trade_account, 'quant': self.quant,'position': self.position})

                        if from_user:
                            if not all_clear:
                                self.telegram_msg = '?????? ???????????? ?????? ???????????????.\n'
                                self.telegram_msg += '?????? ?????? : ' + self.strategy_name + '\n'
                                self.telegram_msg += '?????? ?????? ?????? ??? ?????? ??? : \n' + str(self.current_total_profit_tick) + '\n'

                                self.parent.send_telegram(self.telegram_msg)

                                temp = {}
                                temp['command'] = 'clear_position_from_auto_trader'
                                temp['result'] = '0'

                                self.parent.aws_mqtt.publish_message(temp)
                            else:
                                self.parent.num_of_all_clear += 1

                        if profit_total_clear:

                            self.telegram_msg = '?????? ?????? ???????????????.\n'
                            self.telegram_msg += '?????? ?????? : ' + self.strategy_name + '\n'
                            self.telegram_msg += '?????? ?????? ?????? ??? ?????? ??? : \n' + str(self.current_total_profit_tick) + '\n'

                        self.excel_clear_indicator = self.telegram_msg

                elif from_user:
                    if not all_clear:
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

                    temp_msg = '?????? ?????? : ' + self.strategy_name + '\n'
                    temp_msg += '?????? ???????????? ???????????? ???????????? ????????? ??? ????????????.\n'
                    temp_msg += '????????? ?????? ???????????????.\n'

                    self.need_to_load_position = False

                    self.parent.send_telegram(temp_msg)

                elif data['type'] == self.waiting_enter_type and self.has_position and int(data['sum_of_clear_quant']) == int(self.quant):
                    real_profit = int((data['sum_of_profit'] // self.tick_value) // int(data['sum_of_clear_quant']))

                    #self.current_price = self.parent.get_current_price()

                    program_profit = abs(self.current_price - self.enter_price)
                    program_profit = int(program_profit // self.tick_unit)


                    if (self.enter_type == '??????' and self.enter_price > self.current_price) or (
                            self.enter_type == '??????' and self.enter_price < self.current_price):
                        program_profit = program_profit * -1

                    now = datetime.datetime.now()
                    self.clear_time_for_excel = now.strftime('%Y-%m-%d %H:%M:%S.%f')

                    info = {}

                    info['enter_id'] = self.enter_id
                    info['trade_type'] = '??????'
                    info['strategy_name'] = self.strategy_name

                    info['acc_num'] = self.trade_account
                    info['quant'] = self.quant
                    info['clear_type'] = '??????' if self.enter_type == '??????' else '??????'
                    info['clear_time'] = self.clear_time_for_excel
                    if self.enter_type == '??????':
                        info['clear_price'] = round(self.enter_price + (real_profit * self.tick_unit), 2)
                    else:
                        info['clear_price'] = round(self.enter_price - (real_profit * self.tick_unit), 2)

                    info['order_send_time'] = data['order_send_time']
                    info['order_complete_time'] = data['order_complete_time']
                    info['clear_indicator'] = self.excel_clear_indicator

                    # self.parent.add_trade_info_to_excel('clear', info)

                    info['enter_type'] = '??????' if self.enter_type == '??????' else '??????'
                    info['enter_time'] = self.enter_time_for_excel
                    info['enter_price'] = self.enter_price
                    info['enter_indicator'] = self.excel_enter_indicator

                    info['program_price_profit_tick'] = str(program_profit) + '(' + str(program_profit * self.quant) + ')'
                    info['real_price_profit_tick'] = real_profit
                    info['real_price_total_profit_tick'] = real_profit * self.quant
                    info['total_profit_dollar'] = data['sum_of_profit']

                    self.parent.add_trade_info_to_excel('clear', info)

                    self.current_total_profit_tick += real_profit

                    print('??? ?????? ?????? : ', self.current_total_profit_tick)
                    self.update_virtual_trade(data['sum_of_profit'])

                    temp = {}

                    temp['acc_num'] = self.trade_account
                    temp['position'] = self.position
                    temp['quant'] = self.quant * -1 if self.enter_type == '??????' else self.quant
                    temp['enter_id'] = self.enter_id

                    self.parent.process_complete_order(temp)

                    self.set_position_info()

                    self.need_to_load_position = False

                elif data['type'] == self.waiting_enter_type and not self.has_position and int(data['sum_of_enter_quant']) == int(self.quant):

                    self.enter_id = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(10))

                    temp = {}

                    temp['acc_num'] = self.trade_account
                    temp['avg_price'] = float(data['avg_price'])
                    temp['position'] = self.position
                    temp['quant'] = int(data['sum_of_enter_quant']) if data['type'] == '??????' else int(data['sum_of_enter_quant']) * -1
                    temp['enter_id'] = self.enter_id

                    self.parent.process_complete_order(temp)

                    self.set_position_info()

                    now = datetime.datetime.now()
                    self.enter_time_for_excel = now.strftime('%Y-%m-%d %H:%M:%S.%f')


                    info = {}

                    info['enter_id'] = self.enter_id
                    info['trade_type'] = '??????'
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

                    self.need_to_load_position = False
                else:
                    print('putback')
                    self.parent.complete_order_queue_dict[self.trade_account].append(data)
                    time.sleep(0.1)
            else:
                time.sleep(0.01)

    def set_position_info(self):
        try:
            with open("position.json", "r", encoding="UTF8") as st_json:
                json_data = json.load(st_json)

            if json_data[self.trade_account][str(self.position)]['quant'] == 0:
                self.has_position = False
                self.enter_type = ''
                self.enter_price = 0
                self.enter_id = ''
            else:
                self.has_position = True

                self.enter_type = '??????' if json_data[self.trade_account][str(self.position)]['quant'] < 0 else '??????'
                self.last_enter_type = self.enter_type
                self.enter_price = json_data[self.trade_account][str(self.position)]['avg_price']
                self.quant = abs(json_data[self.trade_account][str(self.position)]['quant'])
                self.enter_id = json_data[self.trade_account][str(self.position)]['enter_id']

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, fname, exc_tb.tb_lineno)

    def get_current_profit(self):
        if self.has_position and not self.is_virtual_trade() and not self.is_simulation_strategy:
            #self.current_price = self.parent.get_current_price()

            profit = abs(self.current_price - self.enter_price)
            profit = int(profit // self.tick_unit) * self.quant
            if (self.enter_type == '??????' and self.enter_price > self.current_price) or (
                    self.enter_type == '??????' and self.enter_price < self.current_price):
                profit = profit * -1

            return profit + self.current_total_profit_tick
        else:
            if self.is_simulation_strategy:
                return 0
            else:
                return self.current_total_profit_tick

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
                if (self.enter_type == '??????' and self.enter_price > self.current_price) or (
                        self.enter_type == '??????' and self.enter_price < self.current_price):
                    profit = profit * -1


                if self.current_total_profit_tick + profit <= self.max_loss or self.max_profit <= self.current_total_profit_tick + profit:
                    self.profit_limit_flag = True

                    self.telegram_msg += '==============\n'
                    self.telegram_msg += '????????? ?????? ??????/?????? ?????? ???????????? ?????? ??? ????????? ???????????????.\n'

                    self.telegram_msg += '?????? ?????? ?????? ???: ' + str(int(self.current_total_profit_tick)) + '\n'
                    self.telegram_msg += '?????? ?????? ?????? ???: ' + str(int(profit)) + '\n'
                    self.telegram_msg += '?????? ?????? ?????? ??? : ' + str(self.max_loss) + '\n'
                    self.telegram_msg += '?????? ?????? ?????? ??? : ' + str(self.max_profit) + '\n'

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
                            self.telegram_msg = '!!!??????????????? ???????????????!!!\n' if self.is_simulation_strategy else ''
                            self.telegram_msg += '?????? ?????? : ' + self.strategy_name + '\n'
                            self.telegram_msg += '????????? ?????? ????????? ???????????? ????????? ???????????????.\n\n'
                            self.parent.send_telegram(self.telegram_msg)

                            self.time_range_in_msg_sent = True

                            self.reset_cross_check()

                        self.time_range_out_msg_sent = False
                        is_in_time = True
                        break

                if not is_in_time and not self.time_range_out_msg_sent:
                    self.time_range_out_msg_sent = True
                    self.time_range_in_msg_sent = False
                    self.telegram_msg = '!!!??????????????? ???????????????!!!\n' if self.is_simulation_strategy else ''
                    self.telegram_msg += '?????? ?????? : ' + self.strategy_name + '\n'
                    self.telegram_msg += '????????? ?????? ????????? ????????? ????????? ???????????????.\n'
                    if self.is_there_first_meet_virtual_indicator or self.is_there_box_virtual_indicator:
                        self.telegram_msg += '??????????????? ????????? ?????? ????????????.\n'
                    self.parent.send_telegram(self.telegram_msg)

                    self.reset_cross_check()

                if not is_in_time and self.has_position and not self.is_virtual_trade() and not self.need_to_load_position:
                    print('clear by time limit!')
                    if self.enter_type == '??????':
                        self.waiting_enter_type = '??????'
                        self.parent.order_queue.append({'type': self.CLEAR_BUY_SIGNAL, 'acc_num': self.trade_account, 'quant': self.quant,'position': self.position})

                    else:
                        self.waiting_enter_type = '??????'
                        self.parent.order_queue.append({'type': self.CLEAR_SELL_SIGNAL, 'acc_num': self.trade_account, 'quant': self.quant,'position': self.position})

                    self.clear_position_req()

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
            self.parabolic_high_low_dict = {}

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

                elif k == 'PARABOLIC_HIGH_LOW':
                    for kk, vv in v.items():
                        if k + '_' + kk not in self.parent.already_calced_list:
                            indicator_time_type, indicator_unit, af, af_max = kk.split('_')

                            df = self.parent.get_df(indicator_time_type, int(indicator_unit))
                            if 'PARABOLIC_' + kk not in self.parent.already_calced_list:
                                df = self.indicator.get_parabolic(df, af=float(af), af_max=float(af_max), calc_only_last=self.indicator_dict[k][kk])
                                self.indicator_dict['PARABOLIC'][kk] = True
                                self.parent.already_calced_list.append('PARABOLIC_' + kk)

                            df = self.indicator.get_parabolic_high_low(df, af=float(af), af_max=float(af_max))

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

    def stop_strategy(self, msg):
        self.need_to_load_position = False
        self.running_status = False

        with open("setting.json", "r", encoding='utf-8') as st_json:
            json_data = json.load(st_json)

        json_data['strategy_list'][self.position]['running_status'] = 'false'

        with open('setting.json', 'w', encoding="UTF8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

        with open("log.txt", "a", encoding="UTF8") as log:
            try:
                now = datetime.datetime.now()

                log.write("!!!!!!!!!!!!! ?????? ?????? !!!!!!!!!!!!!\n")
                log.write("????????? : " + str(self.strategy_name) + '\n')
                log.write("???????????? : " + str(self.trade_account) + '\n')
                log.write("???????????? : " + str(msg) + '\n')
                log.write("?????????????????? : " + str(now.strftime('%Y-%m-%d %H:%M:%S.%f')) + '\n')

            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(e, fname, exc_tb.tb_lineno)

        return json_data

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