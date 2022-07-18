import datetime
import os
import sys
import time

import numpy
import pandas
#import modin.pandas as pandas
import parabolic


class Indicator():
    def __init__(self):
        self.pars = parabolic.Parabolic()
        self.parabolic_high_low_dict = {}

    def get_ma(self, df, period = 5, calc_only_last=False):
        if calc_only_last:
            df['MA_' + str(period)].iloc[-1] = round(df['close'].iloc[period * -1 : ].rolling(period).mean().iloc[-1], 2)

        else:
            df['MA_' + str(period)] = round(df['close'].rolling(period).mean(), 2)

        return df

    def get_tema(self, df, period = 5, calc_only_last=False):
        if calc_only_last:
            df['EMA_ONE_' + str(period)].iloc[-1] = round(df['close'].iloc[len(df) - (period * 5):].ewm(span=period, adjust=False).mean().iloc[-1], 2)
            df['EMA_TWO_' + str(period)].iloc[-1] = round(df['EMA_ONE_' + str(period)].iloc[len(df) - (period * 5):].ewm(span=period, adjust=False).mean().iloc[-1], 2)
            df['TEMA_' + str(period)].iloc[-1] = round(df['EMA_TWO_' + str(period)].iloc[len(df) - (period * 5):].ewm(span=period, adjust=False).mean().iloc[-1], 2)

        else:
            df['EMA_ONE_' + str(period)] = round(df['close'].ewm(span=period, adjust=False).mean(), 2)
            df['EMA_TWO_' + str(period)] = round(df['EMA_ONE_' + str(period)].ewm(span=period, adjust=False).mean(), 2)
            df['TEMA_' + str(period)] = round(df['EMA_TWO_' + str(period)].ewm(span=period, adjust=False).mean(), 2)

        return df

    def get_pivot(self, df):
        if 'second_resistance' in df:
            return df
        else:
            pre_day_high = df['high'].iloc[-2]
            pre_day_low = df['low'].iloc[-2]
            pre_day_close = df['open'].iloc[-1]

            pivot_val = (pre_day_high + pre_day_low + pre_day_close) / 3

            df['second_resistance'] = 0
            df['first_resistance'] = 0
            df['pivot_point'] = 0
            df['first_support'] = 0
            df['second_support'] = 0

            df['second_resistance'].iloc[-1] = round(pivot_val + pre_day_high - pre_day_low, 2)
            df['first_resistance'].iloc[-1] = round((2 * pivot_val) - pre_day_low, 2)
            df['pivot_point'].iloc[-1] = round(pivot_val, 2)
            df['first_support'].iloc[-1] = round((2 * pivot_val) - pre_day_high, 2)
            df['second_support'].iloc[-1] = round(pivot_val - pre_day_high + pre_day_low, 2)

        return df

    def get_parabolic(self, df, af=0.02, af_max=0.2, calc_only_last=False):
        try:
            PSAR_name = 'PSAR_' + str(af) + '_' + str(af_max)
            EP_name = 'EP_' + str(af) + '_' + str(af_max)
            AF_name = 'AF_' + str(af) + '_' + str(af_max)

            self.pars.setup_psar(df, af_step=af, max_af=af_max, calc_only_last=calc_only_last)

            if calc_only_last:
                df[PSAR_name].iloc[-1], df[EP_name].iloc[-1], df[AF_name].iloc[-1] = self.pars.get_psar(df['high'].iloc[-1], df['low'].iloc[-1])

            else:
                df[PSAR_name] = None
                df[EP_name] = None
                df[AF_name] = None

                for i in range(len(df)):
                    df[PSAR_name].iloc[i], df[EP_name].iloc[i], df[AF_name].iloc[i] = self.pars.get_psar(df['high'].iloc[i], df['low'].iloc[i])

            return df
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, fname, exc_tb.tb_lineno)

    def get_parabolic_high_low(self, df, af=0.02, af_max=0.2):
        try:
            if 'H1_' + str(af) + '_' + str(af_max) not in df:
                df['H1_' + str(af) + '_' + str(af_max)] = numpy.nan
                df['H2_' + str(af) + '_' + str(af_max)] = numpy.nan
                df['M_' + str(af) + '_' + str(af_max)] = numpy.nan
                df['L2_' + str(af) + '_' + str(af_max)] = numpy.nan
                df['L1_' + str(af) + '_' + str(af_max)] = numpy.nan
                df['calced_' + str(af) + '_' + str(af_max)] = False

            PSAR_name = 'PSAR_' + str(af) + '_' + str(af_max)
            EP_name = 'EP_' + str(af) + '_' + str(af_max)

            current_trend = 'bull' if df[PSAR_name].iloc[-1] < df['close'].iloc[-1] else 'bear'
            last_trend = 'bull' if df[PSAR_name].iloc[-2] < df['close'].iloc[-2] else 'bear'

            if pandas.isna(df['H1_' + str(af) + '_' + str(af_max)].iloc[-1]) and not pandas.isna(df['H1_' + str(af) + '_' + str(af_max)].iloc[-2]):
                df['H1_' + str(af) + '_' + str(af_max)].iloc[-1] = df['H1_' + str(af) + '_' + str(af_max)].iloc[-2]
                df['H2_' + str(af) + '_' + str(af_max)].iloc[-1] = df['H2_' + str(af) + '_' + str(af_max)].iloc[-2]
                df['M_' + str(af) + '_' + str(af_max)].iloc[-1] = df['M_' + str(af) + '_' + str(af_max)].iloc[-2]
                df['L2_' + str(af) + '_' + str(af_max)].iloc[-1] = df['L2_' + str(af) + '_' + str(af_max)].iloc[-2]
                df['L1_' + str(af) + '_' + str(af_max)].iloc[-1] = df['L1_' + str(af) + '_' + str(af_max)].iloc[-2]
                df['calced_' + str(af) + '_' + str(af_max)].iloc[-1] = False

            if pandas.isna(df['H1_' + str(af) + '_' + str(af_max)].iloc[-1]) and pandas.isna(df['H1_' + str(af) + '_' + str(af_max)].iloc[-2]) or \
                    (current_trend != last_trend and (not df['calced_' + str(af) + '_' + str(af_max)].iloc[-1] or pandas.isna(df['calced_' + str(af) + '_' + str(af_max)].iloc[-1]))):

                df['calced_' + str(af) + '_' + str(af_max)].iloc[-1] = True

                if current_trend == 'bull':
                    idx = -1
                    while df[PSAR_name].iloc[idx] < df['close'].iloc[idx]:
                        idx -= 1

                    low = df[EP_name].iloc[idx]

                    while df[PSAR_name].iloc[idx] > df['close'].iloc[idx]:
                        idx -= 1

                    high = df[EP_name].iloc[idx]

                else:
                    idx = -1
                    while df[PSAR_name].iloc[idx] > df['close'].iloc[idx]:
                        idx -= 1

                    high = df[EP_name].iloc[idx]

                    while df[PSAR_name].iloc[idx] < df['close'].iloc[idx]:
                        idx -= 1

                    low = df[EP_name].iloc[idx]

                h1 = high
                l1 = low

                mid = round((h1 + l1) / 2, 2)

                h2 = round((h1 + mid) / 2, 2)
                l2 = round((mid + l1) / 2, 2)

                df['H1_' + str(af) + '_' + str(af_max)].iloc[-1] = h1
                df['H2_' + str(af) + '_' + str(af_max)].iloc[-1] = h2
                df['M_' + str(af) + '_' + str(af_max)].iloc[-1] = mid
                df['L2_' + str(af) + '_' + str(af_max)].iloc[-1] = l2
                df['L1_' + str(af) + '_' + str(af_max)].iloc[-1] = l1

            return df
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, fname, exc_tb.tb_lineno)

    def get_macd(self, df, macd_short, macd_long, macd_signal, calc_only_last=False):
        try:
            MACD_short_name = 'MACD_short_' + str(macd_short) + '_' + str(macd_long) + '_' + str(macd_signal)
            MACD_long_name = 'MACD_long_' + str(macd_short) + '_' + str(macd_long) + '_' + str(macd_signal)
            MACD_name = 'MACD_' + str(macd_short) + '_' + str(macd_long) + '_' + str(macd_signal)
            MACD_sinal_name =  'MACD_signal_' + str(macd_short) + '_' + str(macd_long) + '_' + str(macd_signal)
            MACD_Osc_name = 'MACD_Osc_' + str(macd_short) + '_' + str(macd_long) + '_' + str(macd_signal)

            if calc_only_last:
                df[MACD_short_name].iloc[-1] = round(df['close'].iloc[len(df) - (macd_short * 5):].ewm(span=macd_short).mean().iloc[-1], 2)
                df[MACD_long_name].iloc[-1] = round(df['close'].iloc[len(df) - (macd_long * 5):].ewm(span=macd_long).mean().iloc[-1], 2)
                df[MACD_name].iloc[-1] = round(df[MACD_short_name].iloc[-1] - df[MACD_long_name].iloc[-1], 2)
                df[MACD_sinal_name].iloc[-1] = round(df[MACD_name].iloc[len(df) - (macd_signal * 5):].ewm(span=macd_signal).mean().iloc[-1], 2)
                df[MACD_Osc_name].iloc[-1] = round(df[MACD_name].iloc[-1] - df[MACD_sinal_name].iloc[-1], 2)

            else:
                df[MACD_short_name] = df['close'].ewm(span=macd_short).mean()
                df[MACD_long_name] = df['close'].ewm(span=macd_long).mean()
                df[MACD_name] = df.apply(lambda x: (x[MACD_short_name] - x[MACD_long_name]), axis=1)
                df[MACD_sinal_name] = df[MACD_name].ewm(span=macd_signal).mean()
                df[MACD_Osc_name] = df.apply(lambda x: (x[MACD_name] - x[MACD_sinal_name]), axis=1)

                df[MACD_short_name] = round(df[MACD_short_name], 2)
                df[MACD_long_name] = round(df[MACD_long_name], 2)
                df[MACD_name] = round(df[MACD_name], 2)
                df[MACD_sinal_name] = round(df[MACD_sinal_name], 2)
                df[MACD_Osc_name] = round(df[MACD_Osc_name], 2)

            return df

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, fname, exc_tb.tb_lineno)

    def get_rsi(self, df, interval, calc_only_last=False):
        if calc_only_last:
            delta = df['close'].iloc[len(df) - interval * 5 :].diff()

            up, down = delta.copy(), delta.copy()
            up[up < 0] = 0
            down[down > 0] = 0

            _gain = up.ewm(com=(interval - 1), min_periods=interval).mean()
            _loss = down.abs().ewm(com=(interval - 1), min_periods=interval).mean()

            RS = _gain / _loss

            df['RSI_' + str(interval)].iloc[-1] = round(pandas.Series(100 - (100 / (1 + RS)), name="RSI").iloc[-1], 2)

        else:
            delta = df['close'].diff()

            up, down = delta.copy(), delta.copy()
            up[up < 0] = 0
            down[down > 0] = 0

            _gain = up.ewm(com=(interval - 1), min_periods=interval).mean()
            _loss = down.abs().ewm(com=(interval - 1), min_periods=interval).mean()

            RS = _gain / _loss

            df['RSI_' + str(interval)] = round(pandas.Series(100 - (100 / (1 + RS)), name="RSI"), 2)

        return df

    #
    # def get_bollinger_band(self, df):
    #     df['ma12'] = round(df['close'].rolling(window=20).mean(), 2)  # 12일 이동평균
    #     df['stddev'] = round(df['close'].rolling(window=20).std(), 2)  # 12일 이동표준편차
    #     df['upper'] = round(df['ma12'] + 2 * df['stddev'], 2)  # 상단밴드
    #     df['lower'] = round(df['ma12'] - 2 * df['stddev'], 2)  # 하단밴드
    #     df['bb_middle'] = round((df['upper'] + df['lower']) / 2, 2)  # 중앙밴드
    #
    #     return df
    #
    # def get_volume_avg(self, df, window):
    #     last_index = len(df) - 2
    #
    #     sum_of_volume = 0
    #
    #     for i in range(window):
    #         sum_of_volume += df['volume'].iloc[last_index - i]
    #
    #     mean_of_volume = sum_of_volume / window
    #
    #     self.vol_avg = int(mean_of_volume)


    # def get_parabolic(self, df, af=0.02, max=0.2):
    #     try:
    #         df['AF'] = None
    #         df['PSAR'] = None
    #         df['EP'] = None
    #         df['PSARdir'] = None
    #         df['cross'] = None
    #
    #         df['AF'].iloc[0] = af
    #         df['PSAR'].iloc[0] = df['low'].iloc[0]
    #         df['EP'].iloc[0] = df['high'].iloc[0]
    #         df['PSARdir'].iloc[0] = 'bull'
    #
    #         for a in range(1, len(df)):
    #             if df['PSARdir'].iloc[a - 1] == 'bull':
    #                 df['PSAR'].iloc[a] = round(df['PSAR'].iloc[a - 1] + (df['AF'].iloc[a - 1] * (df['EP'].iloc[a - 1] - df['PSAR'].iloc[a - 1])), 2)
    #                 df['PSARdir'].iloc[a] = "bull"
    #
    #                 if df['low'].iloc[a] < df['PSAR'].iloc[a]:
    #                     df['PSARdir'].iloc[a] = "bear"
    #                     df['PSAR'].iloc[a] = df['EP'].iloc[a - 1]
    #                     df['EP'].iloc[a] = df['low'].iloc[a]
    #                     df['AF'].iloc[a] = af
    #
    #                 else:
    #                     if df['high'].iloc[a] > df['EP'].iloc[a - 1]:
    #                         df['EP'].iloc[a] = df['high'].iloc[a]
    #                         if df['AF'].iloc[a - 1] + af <= max:
    #                             df['AF'].iloc[a] = df['AF'].iloc[a - 1] + af
    #                         else:
    #                             df['AF'].iloc[a] = df['AF'].iloc[a - 1]
    #                     elif df['high'].iloc[a] <= df['EP'].iloc[a - 1]:
    #                         df['AF'].iloc[a] = df['AF'].iloc[a - 1]
    #                         df['EP'].iloc[a] = df['EP'].iloc[a - 1]
    #
    #             elif df['PSARdir'].iloc[a - 1] == 'bear':
    #                 df['PSAR'].iloc[a] = round(df['PSAR'].iloc[a - 1] - (df['AF'].iloc[a - 1] * (df['PSAR'].iloc[a - 1] - df['EP'].iloc[a - 1])), 2)
    #                 df['PSARdir'].iloc[a] = "bear"
    #
    #                 if df['high'].iloc[a] > df['PSAR'].iloc[a]:
    #                     df['PSARdir'].iloc[a] = "bull"
    #                     df['PSAR'].iloc[a] = df['EP'].iloc[a - 1]
    #                     df['EP'].iloc[a] = df['high'].iloc[a]
    #                     df['AF'].iloc[a] = af
    #
    #                 else:
    #                     if df['low'].iloc[a] < df['EP'].iloc[a - 1]:
    #                         df['EP'].iloc[a] = df['low'].iloc[a]
    #                         if df['AF'].iloc[a - 1] + af <= max:
    #                             df['AF'].iloc[a] = df['AF'].iloc[a - 1] + af
    #                         else:
    #                             df['AF'].iloc[a] = df['AF'].iloc[a - 1]
    #                     elif df['low'].iloc[a] >= df['EP'].iloc[a - 1]:
    #                         df['AF'].iloc[a] = df['AF'].iloc[a - 1]
    #                         df['EP'].iloc[a] = df['EP'].iloc[a - 1]
    #
    #             if df['PSARdir'].iloc[a - 1] == 'bull' and df['PSARdir'].iloc[a] == 'bear':
    #                 df['cross'].iloc[a] = 'dead_cross'
    #             elif df['PSARdir'].iloc[a - 1] == 'bear' and df['PSARdir'].iloc[a] == 'bull':
    #                 df['cross'].iloc[a] = 'golden_cross'
    #
    #         print(df)
    #
    #         return df
    #
    #     except Exception as e:
    #         exc_type, exc_obj, exc_tb = sys.exc_info()
    #         fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    #         print(e, fname, exc_tb.tb_lineno)

    # def get_parabolic(self, df, af=0.02, max=0.2):
    #     psar = df.ta.psar(high=df['high'], low=df['low'], close=df['close'], af0=af, af=af, max_af=max)
    #
    #     df['PSARl'] = round(psar['PSARl_' + str(af) + '_' + str(max)], 2)
    #     df['PSARs'] = round(psar['PSARs_' + str(af) + '_' + str(max)], 2)
    #
    #     fn = lambda x: np.max(x)
    #     df["PSAR"] = df[["PSARl", "PSARs"]].apply(fn, axis=1)
    #
    #     print(df)
    #     return df


    # def get_parabolic(self, df, af=0.02, max=0.2):
    #     df['PSAR'] = round(talib.SAR(df.high, df.low, acceleration=af, maximum=max), 2)
    #
    #     return df
    #
    # def get_parabolic(self, df, af=0.02, max=0.2):
    #     df.loc[0, 'AF'] = af
    #
    #     df.loc[0, 'PSAR'] = df.loc[0, 'low']
    #     df.loc[0, 'EP'] = df.loc[0, 'high']
    #     df.loc[0, 'PSARdir'] = "bull"
    #
    #     highest_price = df.loc[0, 'high']
    #     lowest_price = df.loc[0, 'low']
    #
    #     for a in range(1, len(df)):
    #         if df.loc[a - 1, 'PSARdir'] == 'bull':
    #             df.loc[a, 'PSAR'] = df.loc[a - 1, 'PSAR'] + (df.loc[a - 1, 'AF'] * (df.loc[a - 1, 'EP'] - df.loc[a - 1, 'PSAR']))
    #             df.loc[a, 'PSARdir'] = "bull"
    #
    #             highest_price = max(highest_price, df.loc[a, 'high'])
    #
    #             if df.loc[a, 'low'] < df.loc[a, 'PSAR']:
    #                 df.loc[a, 'PSARdir'] = "bear"
    #                 df.loc[a, 'PSAR'] = highest_price
    #                 df.loc[a, 'EP'] = df.loc[a, 'low']
    #                 df.loc[a, 'AF'] = af
    #
    #                 highest_price = []
    #             else:
    #                 if df.loc[a, 'high'] > df.loc[a - 1, 'EP']:
    #                     df.loc[a, 'EP'] = df.loc[a, 'high']
    #                     if df.loc[a - 1, 'AF'] < max:
    #                         df.loc[a, 'AF'] = df.loc[a - 1, 'AF'] + af
    #                     else:
    #                         df.loc[a, 'AF'] = df.loc[a - 1, 'AF']
    #                 elif df.loc[a, 'high'] <= df.loc[a - 1, 'EP']:
    #                     df.loc[a, 'AF'] = df.loc[a - 1, 'AF']
    #                     df.loc[a, 'EP'] = df.loc[a - 1, 'EP']
    #
    #         elif df.loc[a - 1, 'PSARdir'] == 'bear':
    #             df.loc[a, 'PSAR'] = df.loc[a - 1, 'PSAR'] - (
    #                         df.loc[a - 1, 'AF'] * (df.loc[a - 1, 'PSAR'] - df.loc[a - 1, 'EP']))
    #             df.loc[a, 'PSARdir'] = "bear"
    #
    #             if df.loc[a, 'high'] > df.loc[a - 1, 'PSAR'] or df.loc[a, 'high'] > df.loc[a, 'PSAR']:
    #                 df.loc[a, 'PSARdir'] = "bull"
    #                 df.loc[a, 'PSAR'] = df.loc[a - 1, 'EP']
    #                 df.loc[a, 'EP'] = df.loc[a - 1, 'high']
    #                 df.loc[a, 'AF'] = af
    #             else:
    #                 if df.loc[a, 'low'] < df.loc[a - 1, 'EP']:
    #                     df.loc[a, 'EP'] = df.loc[a, 'low']
    #                     if df.loc[a - 1, 'AF'] < max:
    #                         df.loc[a, 'AF'] = df.loc[a - 1, 'AF'] + af
    #                     else:
    #                         df.loc[a, 'AF'] = df.loc[a - 1, 'AF']
    #
    #                 elif df.loc[a, 'low'] >= df.loc[a - 1, 'EP']:
    #                     df.loc[a, 'AF'] = df.loc[a - 1, 'AF']
    #                     df.loc[a, 'EP'] = df.loc[a - 1, 'EP']
    #     return df