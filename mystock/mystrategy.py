import pandas as pd
import numpy as np
from pathlib import Path
from my_name import group1_list

class mystrategy:
    def __init__(self, p_SN, p_name):
        self.p_SN = p_SN
        self.p_name = p_name
        file_name = f'/opt/zack/master/data/{self.p_SN}.csv'
        self.rd = pd.DataFrame()
        if Path(file_name).is_file():
            self.rd = pd.read_csv(file_name, encoding="utf-8-sig")
            # print(rd.loc[rd.index == 0])
            # self.res = self.rd.loc[self.rd.index == 0]
            self.res = pd.DataFrame()

    def get_macd_money_flow_signal(self, dt = -1):
        """
        money flow signal analysis
        """
        
        latest = self.rd.iloc[dt]
        prev = self.rd.iloc[dt-1]
        
        signals = []
        
        if latest['diff'] > 0 and latest['dea'] > 0:
            signals.append(("zero axis above bullish", 1))
        elif latest['diff'] < 0 and latest['dea'] < 0:
            signals.append(("zero axis below bearish", -1))
        
        if prev['diff'] <= prev['dea'] and latest['diff'] > latest['dea']:
            signals.append(("golden cross", 2))
        elif prev['diff'] >= prev['dea'] and latest['diff'] < latest['dea']:
            signals.append(("dead cross", -2))
        
        if latest['macd'] > 0 and latest['macd'] > prev['macd']:
            signals.append(("red bar increase", 0.5))
        elif latest['macd'] < 0 and latest['macd'] < prev['macd']:
            signals.append(("green bar increase", -0.5))
        
        if latest['diff'] > prev['diff']:
            signals.append(("diff up", 0.5))
        else:
            signals.append(("diff down", -0.5))
        
        total_score = sum([score for _, score in signals])
        
        if total_score >= 2:
            result = "buy signal（money flow large in）"
        elif total_score >= 0.5:
            result = "buy signal（money flow in）"
        elif total_score <= -2:
            result = "sell signal（money flow large out）"
        elif total_score <= -0.5:
            result = "sell signal（money flow out）"
        else:
            result = "wait for a signal"
        
        # return {
        #     '最新DIF': round(latest['diff'], 4),
        #     '最新DEA': round(latest['dea'], 4),
        #     '最新MACD柱': round(latest['macd'], 4),
        #     '检测信号': signals,
        #     '综合评分': total_score,
        #     '资金流向判断': result
        # }
        return total_score, result
    
    def comprehensive_money_flow_analysis(self, dt = -1):
        """
        money flow analysis
        """
        data = self.rd.copy()
        data['VWAP'] = (data['vol'] * data['value']).cumsum() / data['vol'].cumsum()
        
        latest = data.iloc[dt]
        macd_bullish = latest['diff'] > latest['dea']
        obv_trend = data['obv'].iloc[dt-4:].mean() > data['obv'].iloc[dt-9:dt-4].mean()
        volume_confirm = latest['vol'] > data['vol'].iloc[dt-19:dt].mean()
        
        if macd_bullish and obv_trend and volume_confirm:
            total_score = 1
            result = "money is flowing in"
        elif not macd_bullish and not obv_trend:
            total_score = -1
            result = "money is flowing out"
        else:
            total_score = 0
            result = "wait for a signal"
        return total_score, result

    def find_buy_point(self):
        # if self.sn in group1_list:
        #     return self.way3()
        return self.way3()

    def way1(self):
        count_res = 0
        money_all = money = 10000
        pick = 0
        flag_sell = 0
        max_v = 0
        if self.rd.empty:
            return 0
        for index, row in self.rd.iterrows():
            if row['date'] < '2024':
                continue
            money_all = money + pick * row['value']
            if row['K'] < 20 and row['rsi'] < 30 and pick == 0:
                self.res.loc[count_res, 'date'] = row['date']
                self.res.loc[count_res, 'value'] = row['value']
                self.res.loc[count_res, 'K'] = row['K']
                self.res.loc[count_res, 'rsi'] = row['rsi']
                pick += 1 * money / row['value']
                money = 0
                self.res.loc[count_res, 'money_all'] = money_all
                self.res.loc[count_res, 'money'] = money
                self.res.loc[count_res, 'pick'] = pick
                self.res.loc[count_res, 'buy'] = 1
                count_res += 1
                max_v = row['value']
            # elif row['K'] < 10 and row['rsi'] < 20 and pick * row['value'] < 0.9 * money:
            #     self.res.loc[count_res, 'date'] = row['date']
            #     self.res.loc[count_res, 'value'] = row['value']
            #     self.res.loc[count_res, 'K'] = row['K']
            #     self.res.loc[count_res, 'rsi'] = row['rsi']
            #     pick += money / row['value']
            #     money = 0
            #     self.res.loc[count_res, 'money_all'] = money_all
            #     self.res.loc[count_res, 'money'] = money
            #     self.res.loc[count_res, 'pick'] = pick
            #     self.res.loc[count_res, 'buy'] = 1
            #     count_res += 1
            elif row['K'] > 80 and row['rsi'] > 80:
                flag_sell = 1
            elif ((row['K'] > 50 and row['value'] < row['boll_m']) or row['value'] < 0.9 * max_v) and pick > 0 and flag_sell == 1:
                self.res.loc[count_res, 'date'] = row['date']
                self.res.loc[count_res, 'value'] = row['value']
                self.res.loc[count_res, 'K'] = row['K']
                self.res.loc[count_res, 'rsi'] = row['rsi']
                money += pick * row['value']
                pick = 0
                self.res.loc[count_res, 'money_all'] = money_all
                self.res.loc[count_res, 'money'] = money
                self.res.loc[count_res, 'pick'] = pick
                self.res.loc[count_res, 'sell'] = 1
                flag_sell = 0
                count_res += 1
            if pick > 0:
                max_v = max(max_v, row['value'])
            # else:
            #     self.res.loc[count_res, 'date'] = row['date']
            #     self.res.loc[count_res, 'value'] = row['value']
            #     count_res += 1
        if money_all < 8500:
            print('\n',self.p_SN, self.p_name)
            print(self.res) 
            print("all money = ",money_all)
        # self.res.to_csv("res.csv", index=False, encoding='utf-8-sig')
        return money_all
    
    def way2(self):
        count_res = 0
        money_all = money = 10000
        pick = 0
        flag_sell = 0
        max_v = 0
        for index, row in self.rd.iterrows():
            if row['date'] < '2025':
                continue
            signal = self.get_macd_money_flow_signal(index)
            signal2 = self.comprehensive_money_flow_analysis(index)
            money_all = money + pick * row['value']
            if row['macd'] > 0 and row['diff'] > 0 and row['dea'] > 0 and pick == 0 and row['value'] > row['boll_u']:
                self.res.loc[count_res, 'date'] = row['date']
                self.res.loc[count_res, 'value'] = row['value']
                self.res.loc[count_res, 'K'] = row['K']
                self.res.loc[count_res, 'rsi'] = row['rsi']
                pick += 1 * money / row['value']
                money = 0
                self.res.loc[count_res, 'money_all'] = money_all
                self.res.loc[count_res, 'money'] = money
                self.res.loc[count_res, 'pick'] = pick
                self.res.loc[count_res, 'buy'] = 1
                count_res += 1
                max_v = row['value']
            # elif pick * row['value'] < 0.9 * money and signal[0] > 0 and signal2[0] > 0:
            #     self.res.loc[count_res, 'date'] = row['date']
            #     self.res.loc[count_res, 'value'] = row['value']
            #     self.res.loc[count_res, 'K'] = row['K']
            #     self.res.loc[count_res, 'rsi'] = row['rsi']
            #     pick += money / row['value']
            #     money = 0
            #     self.res.loc[count_res, 'money_all'] = money_all
            #     self.res.loc[count_res, 'money'] = money
            #     self.res.loc[count_res, 'pick'] = pick
            #     self.res.loc[count_res, 'buy'] = 1
            #     count_res += 1
            elif ((row['value'] < row['boll_m']) or (0.9 * max_v < row['value'])) and pick > 0 :
                self.res.loc[count_res, 'date'] = row['date']
                self.res.loc[count_res, 'value'] = row['value']
                self.res.loc[count_res, 'K'] = row['K']
                self.res.loc[count_res, 'rsi'] = row['rsi']
                money += pick * row['value']
                pick = 0
                self.res.loc[count_res, 'money_all'] = money_all
                self.res.loc[count_res, 'money'] = money
                self.res.loc[count_res, 'pick'] = pick
                self.res.loc[count_res, 'sell'] = 1
                flag_sell = 0
                count_res += 1
            # elif row['value'] < row['boll_m'] and pick > 0 and flag_sell == 1:
            #     self.res.loc[count_res, 'date'] = row['date']
            #     self.res.loc[count_res, 'value'] = row['value']
            #     self.res.loc[count_res, 'K'] = row['K']
            #     self.res.loc[count_res, 'rsi'] = row['rsi']
            #     money += pick * row['value']
            #     pick = 0
            #     self.res.loc[count_res, 'money_all'] = money_all
            #     self.res.loc[count_res, 'money'] = money
            #     self.res.loc[count_res, 'pick'] = pick
            #     self.res.loc[count_res, 'sell'] = 1
            #     flag_sell = 0
            #     count_res += 1
            if pick > 0:
                max_v = max(max_v, row['value'])
            # else:
            #     self.res.loc[count_res, 'date'] = row['date']
            #     self.res.loc[count_res, 'value'] = row['value']
            #     count_res += 1
        if money_all < 10000:
            print('\n',self.p_SN, self.p_name)
            print(self.res) 
            print("all money = ",money_all)
        # self.res.to_csv("res.csv", index=False, encoding='utf-8-sig')
        return money_all
    
    def way3(self):
        count_res = 0
        money_all = money = 10000
        pick = 0
        flag_sell = 0
        max_v = 0
        min_v = 999999
        if self.rd.empty:
            return 0
        for index, row in self.rd.iterrows():
            if row['date'] < '2025':
                continue
            money_all = money + pick * row['value']
            # if row['K'] < 20 and row['rsi'] < 30 and pick == 0 and row['value'] < row['boll_l']:
            if row['K'] < 20 and row['rsi'] < 30 and pick == 0:
                self.res.loc[count_res, 'date'] = row['date']
                self.res.loc[count_res, 'value'] = row['value']
                self.res.loc[count_res, 'K'] = row['K']
                self.res.loc[count_res, 'rsi'] = row['rsi']
                pick += 1 * money / row['value']
                money = 0
                self.res.loc[count_res, 'money_all'] = money_all
                self.res.loc[count_res, 'money'] = money
                self.res.loc[count_res, 'pick'] = pick
                self.res.loc[count_res, 'buy'] = 1
                self.res.loc[count_res, 'min'] = row['value']
                count_res += 1
                max_v = row['value']
            elif row['K'] > 80 and row['rsi'] > 80:
                flag_sell = 1
            elif ((row['K'] > 50 and row['value'] < row['boll_m']) or row['value'] < 0.9 * max_v) and pick > 0 and flag_sell == 1:
                self.res.loc[count_res, 'date'] = row['date']
                self.res.loc[count_res, 'value'] = row['value']
                self.res.loc[count_res, 'K'] = row['K']
                self.res.loc[count_res, 'rsi'] = row['rsi']
                money += pick * row['value']
                pick = 0
                self.res.loc[count_res, 'money_all'] = money_all
                self.res.loc[count_res, 'money'] = money
                self.res.loc[count_res, 'pick'] = pick
                self.res.loc[count_res, 'sell'] = 1
                self.res.loc[count_res, 'min'] = min_v
                flag_sell = 0
                if self.res.loc[count_res-1, 'money_all'] > self.res.loc[count_res, 'money_all']:
                    print(self.p_SN, self.p_name)
                    print(self.res[count_res-1:count_res+1]) 
                count_res += 1
            if pick > 0:
                max_v = max(max_v, row['value'])
                min_v = min(min_v, row['value'])
            else:
                min_v = 999999
            # else:
            #     self.res.loc[count_res, 'date'] = row['date']
            #     self.res.loc[count_res, 'value'] = row['value']
            #     count_res += 1
        # if money_all > 50000:
        #     print('\n',self.p_SN, self.p_name)
        #     print(self.res) 
        #     print("all money = ",money_all)
        # self.res.to_csv("res.csv", index=False, encoding='utf-8-sig')
        return money_all
    

    def sum_revenue(self):
        return