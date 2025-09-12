#!/bin/python

import pandas as pd
import akshare as ak
import datetime as dt
import matplotlib.pyplot as plt
import sys
import numpy as np
from mplfinance.original_flavor import candlestick2_ohlc
from matplotlib.ticker import FormatStrFormatter
import argparse

# 天齐锂业 - 002466
p_list = '''
股票代码 股票名字
002466 天齐锂业
'''

class stock:
    def __init__(self, p_SN):
        pd.set_option('display.unicode.ambiguous_as_wide', True)
        pd.set_option('display.unicode.east_asian_width', True)
        pd.set_option('display.width', 180)
        self.p_SN = p_SN
        self.p_name = "xxx"
        for i in p_list.split('\n')[2:]:
            if self.p_SN == i.split(' ')[0]:
                self.p_name = i.split(' ')[1]
        today = dt.date.today()
        start_day = today - dt.timedelta(days = 30)
        self.data = ak.stock_zh_a_hist(symbol=p_SN, period='daily', adjust='', start_date=start_day.strftime('%Y%m%d'), end_date=today.strftime('%Y%m%d'))
        # print(self.data)
        # 获取单个股票的近30日数据
        self.df3 = self.data.reset_index().iloc[-30:,:7]  #取过去30天数据
        self.df3 = self.df3.dropna(how='any').reset_index(drop=True) #去除空值且从零开始编号索引
        self.df3 = self.df3.sort_values(by='日期', ascending=True)
        # print(df3.info())
        #添加均线
        self.df3['5'] = self.df3.收盘.rolling(5).mean()
        self.df3['10'] = self.df3.收盘.rolling(10).mean()
        print(self.df3.tail())

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
    
    def Get_KDJ(self, K_Ptr, date):
        # 计算短期RSV（相对强弱值）：RSV = (C - Ln) / (Hn - Ln) * 100 其中，C是当前收盘价，Ln是n天内的最低价，Hn是n天内的最高价。
        today = dt.date.today()
        data = pd.DataFrame({
            'Date': pd.date_range(start=today - dt.timedelta(days = date-1), periods=date, freq='D'),
            'High': [10 + i * 0.5 for i in range(date)],
            'Low': [8 + i * 0.4 for i in range(date)],
            'Close': [9 + i * 0.45 for i in range(date)],
        })
        print(data)
        low_min = data['Low'].rolling(window=date, min_periods=1).min()
        high_max = data['High'].rolling(window=date, min_periods=1).max()

        data['RSV'] = (data['Close'] - low_min) / (high_max - low_min) * 100
        data['K'] = data['RSV'].ewm(alpha=2/3, adjust=False).mean()
        data['D'] = data['K'].ewm(alpha=1/3, adjust=False).mean()
        data['J'] = 3 * data['K'] - 2 * data['D']
        return data

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--sn', type=str, default = '000001')
    parser.add_argument('--dd', type=int, default = 15)
    parser.add_argument('--kp', type=int, default = 9)
    args = parser.parse_args()
    st = stock(args.sn)
    # st.Show_plt()
    st.Get_KDJ(args.kp, args.dd)