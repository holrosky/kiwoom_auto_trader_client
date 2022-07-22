class Parabolic():
    def __init__(self):
        self.max_af = 0
        self.af_step = 0
        self.af = 0
        self.ep = 0
        self.pars = 0
        self.trend = ''

    def setup_psar(self, df, af_step=0.02, max_af=0.2, calc_only_last=False):
        self.max_af = max_af
        self.af_step = af_step

        PSAR_name = 'PSAR_' + str(af_step) + '_' + str(max_af)
        EP_name = 'EP_' + str(af_step) + '_' + str(max_af)
        AF_name = 'AF_' + str(af_step) + '_' + str(max_af)

        if calc_only_last:
            self.af = df[AF_name].iloc[-2]
            self.ep = df[EP_name].iloc[-2]
            self.pars = df[PSAR_name].iloc[-2]
            self.trend = 'bull' if df[PSAR_name].iloc[-2] < df['close'].iloc[-2] else 'bear'
        else:
            self.af = af_step
            self.ep = df['low'].iloc[0]
            self.pars = df['high'].iloc[0]
            self.trend = 'bull'

    def get_psar(self, high, low):
        if self.trend == 'bull':
            self.pars = round(self.pars + (self.af * (self.ep - self.pars)), 2)
            #self.trend = 'bull'

            if low <= self.pars:
                self.trend = "bear"
                self.pars = self.ep
                self.ep = low
                self.af = self.af_step

            else:
                if high > self.ep:
                    self.ep = high
                    self.af = min(self.af + self.af_step, self.max_af)

        elif self.trend == 'bear':
            self.pars = round(self.pars - (self.af * (self.pars - self.ep)), 2)
            #self.trend = 'bear'

            if high >= self.pars:
                self.trend = "bull"
                self.pars = self.ep
                self.ep = high
                self.af = self.af_step

            else:
                if low < self.ep:
                    self.ep = low
                    self.af = min(self.af + self.af_step, self.max_af)


        return self.pars, self.ep, self.af