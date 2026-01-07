#!/usr/bin/python3

import pandas as pd
import akshare as ak
import datetime as dt
import matplotlib.pyplot as plt
import sys, os
import numpy as np
from pathlib import Path
from mplfinance.original_flavor import candlestick2_ohlc
from matplotlib.ticker import FormatStrFormatter
import argparse
from p_name import p_list
from strategy import signal

k_limit = 20
rsi_limit = 20

KDJ_N = 9
KDJ_M1 = 3
KDJ_M2 = 3
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BOLL_N = 20
BOLL_K = 2
RSI_WINDOW = 14

class stock:
    def __init__(self, p_SN, p_name):
        pd.set_option('display.unicode.ambiguous_as_wide', True)
        pd.set_option('display.unicode.east_asian_width', True)
        pd.set_option('display.width', 180)
        self.p_SN = p_SN
        self.p_name = p_name
        # today = dt.date.today()
        # start_day = today - dt.timedelta(days = p_count)
        # self.data = ak.stock_zh_a_hist(symbol=p_SN)
        # self.data = ak.stock_zh_a_hist(symbol=p_SN, period='daily', adjust='', start_date=start_day.strftime('%Y%m%d'), end_date=today.strftime('%Y%m%d'))
        # print(self.data)

    def Get_Data(self):
        file_name = f'data/{self.p_SN}.csv'
        if Path(file_name).is_file():
            self.res = pd.read_csv(file_name, encoding="utf-8-sig")
            if self.res['date'][self.res.index.size-1] != str(dt.date.today()):
                self.data = ak.stock_zh_a_hist(symbol=self.p_SN)
                update_size = self.res.index.size
                # macd, diff = self.Get_MACD()
                # boll_u, boll_m, boll_l = self.Get_BOLL()
                # K, D, J = self.Get_KDJ()
                # rsi = self.Get_Rsi()
                for i in range(self.res.index.size, len(self.data)):
                    self.res.loc[i,'date'] = self.data.日期[i]
                    self.res.loc[i,'value'] = self.data.收盘[i]
                    self.res.loc[i,'5--day'] = self.data.收盘[i-5:].rolling(5).mean()[i]
                    self.res.loc[i,'10-day'] = self.data.收盘[i-10:].rolling(10).mean()[i]
                    # self.res.loc[i,'macd'] = macd[i]
                    # self.res.loc[i,'diff'] = diff[i]
                    # self.res.loc[i,'boll_u'] = boll_u[i]
                    # self.res.loc[i,'boll_m'] = boll_m[i]
                    # self.res.loc[i,'boll_l'] = boll_l[i]
                    # self.res.loc[i,'K'] = K[i]
                    # self.res.loc[i,'D'] = D[i]
                    # self.res.loc[i,'J'] = J[i]
                    # self.res.loc[i,'rsi'] = rsi[i]
                self.res['macd'], self.res['diff'] = self.Get_MACD()
                self.res['boll_u'], self.res['boll_m'], self.res['boll_l'] = self.Get_BOLL()
                self.res['K'], self.res['D'], self.res['J'] = self.Get_KDJ()
                self.res['rsi'] = self.Get_Rsi()
                self.res.to_csv(file_name, index=False, encoding='utf-8-sig')
                if update_size != len(self.data):
                    print(self.p_SN, self.p_name ,' update csv')
        else:
            self.data = ak.stock_zh_a_hist(symbol=self.p_SN)
            self.res = pd.DataFrame()
            self.res['date'] = self.data['日期']
            self.res['value'] = self.data['收盘']
            self.res['5--day'] = self.data.收盘.rolling(5).mean()
            self.res['10-day'] = self.data.收盘.rolling(10).mean()
            self.res['macd'], self.res['diff'] = self.Get_MACD()
            self.res['boll_u'], self.res['boll_m'], self.res['boll_l'] = self.Get_BOLL()
            self.res['K'], self.res['D'], self.res['J'] = self.Get_KDJ()
            self.res['rsi'] = self.Get_Rsi()
            self.res.to_csv(file_name, index=False, encoding='utf-8-sig')

        # 获取单个股票的近30日数据
        # self.df3 = self.data.reset_index().iloc[-p_count:,:7]  #取过去30天数据
        # self.df3 = self.df3.dropna(how='any').reset_index(drop=True) #去除空值且从零开始编号索引
        # self.df3 = self.df3.sort_values(by='日期', ascending=True)

    def Check_Data(self):
        file_name = f'data/{self.p_SN}.csv'
        if Path(file_name).is_file():
            self.data = ak.stock_zh_a_hist(symbol=self.p_SN)
            # with pd.read_csv(file_name, encoding="utf-8-sig") as res:
            res = pd.read_csv(file_name, encoding="utf-8-sig")
            rsi = self.Get_Rsi()
            if not set(self.data['收盘']) == set(res.value):
                user_input = input("if rm the csv : y / n: ")
                if user_input.lower() == 'y':
                    os.system('rm %s'%file_name)

    def Get_SomeData(self, p_CT):
        if p_CT == 'kdj':
            n_val = self.res.loc[self.res.index == self.res.index.size-1]
            if n_val.K.values < k_limit:
                print(self.p_SN, self.p_name)
                print(n_val)

        if p_CT == 'rsi':
            n_val = self.res.loc[self.res.index == self.res.index.size-1]
            if n_val.rsi.values < rsi_limit:
                print(self.p_SN, self.p_name)
                print(n_val)

    def Show_plt(self):
        fig, ax = plt.subplots(1, 1, figsize=(8,3), dpi=200)
        candlestick2_ohlc(ax,
                        opens = self.df3[ '开盘'].values,
                        highs = self.df3['最高'].values,
                        lows = self.df3[ '最低'].values,
                        closes = self.df3['收盘'].values,
                        width=0.5, colorup="r",colordown="g")

        # 显示最高点和最低点
        ax.text(self.df3.最高.idxmax(), self.df3.最高.max(),   s = self.df3.最高.max(), fontsize=8)
        ax.text(self.df3.最高.idxmin(), self.df3.最高.min() - 2, s = self.df3.最高.min(), fontsize=8)

        ax.set_facecolor("white")
        plt.rc("font",family="")
        ax.set_title(self.p_SN + ' ' + self.p_name, fontproperties="SimHei")

        # 画均线
        plt.plot(self.df3['5'].values, alpha = 0.5, label='MA5')
        plt.plot(self.df3['10'].values, alpha = 0.5, label='MA10')

        ax.legend(facecolor='white', edgecolor='white', fontsize=6)

        # 修改x轴坐标
        plt.xticks(ticks = np.arange(0,len(self.df3)), labels = self.df3.日期.to_numpy() )
        plt.xticks(rotation=90, size=7)

        # 修改y轴坐标
        ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))

        plt.show()
    
    def Get_KDJ(self, N=KDJ_N, M1=KDJ_M1, M2=KDJ_M2):
        # 计算短期RSV（相对强弱值）：RSV = (C - Ln) / (Hn - Ln) * 100 其中，C是当前收盘价，Ln是n天内的最低价，Hn是n天内的最高价。
        data = self.data.copy()
        today = dt.date.today()
        low_min = data['最低'].rolling(N, min_periods=1).min()
        high_max = data['最高'].rolling(N, min_periods=1).max()
        data['RSV'] = (data['收盘'] - low_min) / (high_max - low_min) * 100
        data['K'] = data['RSV'].ewm(alpha=1/M1, adjust=False).mean()
        data['D'] = data['K'].ewm(alpha=1/M2, adjust=False).mean()
        data['J'] = 3 * data['K'] - 2 * data['D']
        # self.res['K'] = data['K']
        # self.res['D'] = data['D']
        # self.res['J'] = data['J']
        return data['K'],data['D'],data['J']

    def Get_MACD(self, n_fast=MACD_FAST, n_slow=MACD_SLOW, n_signal=MACD_SIGNAL):
        ema12 = self.data['收盘'].ewm(span=n_fast, adjust=False).mean()
        ema26 = self.data['收盘'].ewm(span=n_slow, adjust=False).mean()
        diff = ema12 - ema26
        dea = diff.ewm(span=n_signal, adjust=False).mean()
        macd = 2 * (diff - dea)
        # self.res['macd'] = macd
        # self.res['diff'] = diff
        return macd, diff

    def Get_BOLL(self, n = BOLL_N, k = BOLL_K):
        mid = self.data['收盘'].rolling(n).mean()
        upper = mid + k * self.data['收盘'].rolling(n).std()
        lower = mid - k * self.data['收盘'].rolling(n).std()
        # self.res['boll_u'] = upper
        # self.res['boll_m'] = mid
        # self.res['boll_l'] = lower
        return upper, mid, lower
    
    def Get_Rsi(self, window=RSI_WINDOW):
        """Compute RSI indicator with proper handling of initial values"""
        delta = self.data['收盘'].diff()
        gain = delta.copy()
        loss = delta.copy()

        gain[gain < 0] = 0
        loss[loss > 0] = 0
        loss = abs(loss)

        # First value is sum of gains or losses
        avg_gain = gain.rolling(window=window, min_periods=1).mean()
        avg_loss = loss.rolling(window=window, min_periods=1).mean()

        rs = avg_gain / (avg_loss + 1e-6)  # Avoid division by zero
        rsi = 100 - (100 / (1 + rs))

        return rsi

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--sn', type=str, default = '000001')
    parser.add_argument('--ck', type=str, default = '000001')
    # parser.add_argument('--cnt', type=int, default = 90)
    # parser.add_argument('--dd', type=int, default = 15)
    # parser.add_argument('--kp', type=int, default = 9)
    parser.add_argument('--ct', type=str, default = '')
    parser.add_argument('--st', type=bool, default = False)
    parser.add_argument('--dw', type=bool, default = False)
    args = parser.parse_args()
    for i in p_list.split('\n')[2:-1]:
        if args.sn == 'all' or args.sn == i.split(' ')[0]:
            p_SN = i.split(' ')[0]
            p_name = i.split(' ')[1]
            st = stock(p_SN, p_name)
            # print(self.p_SN, self.p_name)
            st.Get_Data()
            st.Get_SomeData(args.ct)
            if (not args.sn == 'all') and args.st:
                print(st.p_name)
                sig = signal()
                sig.generate_signals(st.res)
                print(sig.res)
                sig.backtest_strategy(sig.res)
                print(sig.res)
                sig.calculate_performance_metrics(sig.res)
                print(sig.metrics)
                if args.dw:
                    sig.plot_price_and_macd(sig.res)
                    sig.plot_returns_comparison(sig.res)
                    sig.plot_returns_distribution(sig.res)
        if args.ck == 'all' or args.ck == i.split(' ')[0]:
            p_SN = i.split(' ')[0]
            p_name = i.split(' ')[1]
            st = stock(p_SN, p_name)
            # print(self.p_SN, self.p_name)
            st.Check_Data()
    # st = stock(args.sn, args.ct, args.st)
    # st.Show_plt()
    # st.Get_MACD()
    # st.Get_BOLL()
    # st.Get_KDJ(args.kp, args.dd)