#!/usr/bin/python3

import pandas as pd
import akshare as ak
import tushare as ts
import matplotlib.pyplot as plt
import sys, os
import numpy as np
from pathlib import Path
from mplfinance.original_flavor import candlestick2_ohlc
from matplotlib.ticker import FormatStrFormatter
import argparse
from p_name import p_list
from my_name import buy_list
from my_name import imp_list
from my_name import way1_list
from my_name import way2_list
from strategy import signal
from mystrategy import mystrategy
import requests
import time
from datetime import datetime as dt, date
from typing import List

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

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}
# 禁用 requests 的代理
session = requests.Session()
session.trust_env = False  # 忽略系统代理

ak.session = session

# 临时替换 requests 的默认行为
original_get = requests.get
requests.get = session.get
# print(f"akshare版本: {ak.__version__}")
# print(dir(ak))
# ak.set_config(headers=headers)

ts.set_token('5c940b85806741e9a4aedd3495a9fd43c11a0542d4b3ad641c1ef949')
pro = ts.pro_api()

def get_all_stocks_today() -> List[str]:
    try:
        today_dt = dt.now()  # dt是datetime的别名
        today_str = today_dt.strftime('%Y%m%d')
        today_int = int(today_str)
        df = pro.daily(trade_date=today_int)
        if df is None or df.empty:
            print(f"今天({today_str})没有交易数据")
            return []
        stock_sns = []
        for ts_code in df['ts_code'].unique():
            # 去除交易所后缀，只保留纯数字代码
            if '.' in ts_code:
                sn = ts_code.split('.')[0]
            else:
                sn = ts_code
            stock_sns.append(sn)
        print(f"获取到 {len(stock_sns)} 只股票的SN号")
        return stock_sns
        
    except Exception as e:
        print(f"获取当天股票数据失败: {e}")
        return []

def get_A_data_from_python(p_SN):
    data = pd.DataFrame(columns=['date', 'now', 'close', 'high', 'low', 'open', 'vol', 'vor', 'tor'])
    try:
        dt = ak.stock_zh_a_hist(symbol=p_SN)
        data['date'] = pd.to_datetime(dt['日期'])  # 立即转换为datetime
        data['now'] = dt['收盘']
        data['close'] = dt['收盘']
        data['high'] = dt['最高']
        data['low'] = dt['最低']
        data['open'] = dt['开盘']
        data['vol'] = dt['成交量']
        data['vor'] = dt['成交额']
        data['tor'] = dt['换手率']
        
        # 筛选2010年以后的数据
        data = data[data['date'] >= '2010-01-01']
        
    except Exception as e:
        if p_SN.startswith('6'):
            dt = pro.daily(ts_code=p_SN+'.SH')
        elif p_SN.startswith('9'):
            dt = pro.daily(ts_code=p_SN+'.BJ')
        else:
            dt = pro.daily(ts_code=p_SN+'.SZ')
        dt = dt.sort_values(by='trade_date', ascending=True)
        dt = dt.reset_index(drop=True)
        
        # 直接创建datetime格式的日期
        data['date'] = pd.to_datetime(dt['trade_date'].astype(str), format='%Y%m%d')
        data['now'] = dt['close']
        data['close'] = dt['close']
        data['high'] = dt['high']
        data['low'] = dt['low']
        data['open'] = dt['open']
        data['vol'] = dt['vol']
        data['vor'] = dt['amount']
        data['tor'] = dt['pct_chg']
        
        # 筛选2010年以后的数据
        data = data[data['date'] >= '2010-01-01']
        
        time.sleep(1)
    except:
        print(f"获取{p_SN}数据失败")
    if not data.empty and 'date' in data.columns:
        data['date'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')
    return data

class stock:
    def __init__(self, p_SN, p_name):
        pd.set_option('display.unicode.ambiguous_as_wide', True)
        pd.set_option('display.unicode.east_asian_width', True)
        pd.set_option('display.width', 180)
        self.p_SN = p_SN
        self.p_name = p_name
        pd.set_option('display.max_columns', None)

    def Get_Data(self, flag=False):
        file_name = f'/opt/zack/master/data/{self.p_SN}.csv'
        if Path(file_name).is_file():
            self.res = pd.read_csv(file_name, encoding="utf-8-sig")
            if (self.res['date'].iloc[-1] != str(date.today())) and not flag:
                print(self.res['date'].iloc[-1] , str(date.today()), file_name)
                self.data = get_A_data_from_python(self.p_SN)
                update_size = self.res.index.size
                # macd, diff = self.Get_MACD()
                # boll_u, boll_m, boll_l = self.Get_BOLL()
                # K, D, J = self.Get_KDJ()
                # rsi = self.Get_Rsi()
                print(self.res.index.size, len(self.data))
                for i in range(self.res.index.size, len(self.data)):
                    self.res.loc[i,'date'] = self.data.date[i]
                    self.res.loc[i,'value'] = self.data.close[i]
                    # self.res.loc[i,'5--day'] = self.data.close[i-5:].rolling(5).mean()[i]
                    self.res.loc[i,'10-day'] = self.data.close[i-10:].rolling(10).mean()[i]
                    self.res.loc[i,'vol'] = self.data.vol[i]
                    self.res.loc[i,'vor'] = self.data.vor[i]
                    self.res.loc[i,'tor'] = self.data.tor[i]
                    # self.res.loc[i,'macd'] = macd[i]
                    # self.res.loc[i,'diff'] = diff[i]
                    # self.res.loc[i,'boll_u'] = boll_u[i]
                    # self.res.loc[i,'boll_m'] = boll_m[i]
                    # self.res.loc[i,'boll_l'] = boll_l[i]
                    # self.res.loc[i,'K'] = K[i]
                    # self.res.loc[i,'D'] = D[i]
                    # self.res.loc[i,'J'] = J[i]
                    # self.res.loc[i,'rsi'] = rsi[i]
                self.res['macd'], self.res['diff'], self.res['dea'] = self.Get_MACD()
                self.res['boll_u'], self.res['boll_m'], self.res['boll_l'] = self.Get_BOLL()
                self.res['K'], self.res['D'], self.res['J'] = self.Get_KDJ()
                self.res['rsi'] = self.Get_Rsi()
                self.res['obv'] = self.Get_OBV()
                self.res.to_csv(file_name, index=False, encoding='utf-8-sig')
                if update_size != len(self.data):
                    print(self.p_SN, self.p_name ,' update csv')
        else:
            self.data = get_A_data_from_python(self.p_SN)
            self.res = pd.DataFrame()
            self.res['date'] = self.data['date']
            self.res['value'] = self.data['close']
            # self.res['5--day'] = self.data.close.rolling(5).mean()
            self.res['10-day'] = self.data.close.rolling(10).mean()
            self.res['vol'] = self.data.vol
            self.res['vor'] = self.data.vor
            self.res['tor'] = self.data.tor
            self.res['macd'], self.res['diff'], self.res['dea'] = self.Get_MACD()
            self.res['boll_u'], self.res['boll_m'], self.res['boll_l'] = self.Get_BOLL()
            self.res['K'], self.res['D'], self.res['J'] = self.Get_KDJ()
            self.res['rsi'] = self.Get_Rsi()
            self.res['obv'] = self.Get_OBV()
            self.res.to_csv(file_name, index=False, encoding='utf-8-sig')

    def Read_import(self):
        # data = get_A_data_from_python(self.p_SN)
        # n_val = data.loc[data.index == data.index.size-1].copy()
        data = ts.get_realtime_quotes(self.p_SN)
        n_val = pd.DataFrame(columns=['last', 'high', 'open', 'close'])
        n_val['last'] = data['pre_close']
        n_val['high'] = data['high']
        n_val['open'] = data['open']
        n_val['close'] = data['price']
        for col in n_val:
            if col in n_val.columns:
                n_val[col] = pd.to_numeric(n_val[col], errors='coerce')
        return n_val

    def Check_Data(self):
        file_name = f'/opt/zack/master/data/{self.p_SN}.csv'
        if Path(file_name).is_file():
            self.data = get_A_data_from_python(self.p_SN)
            # with pd.read_csv(file_name, encoding="utf-8-sig") as res:
            res = pd.read_csv(file_name, encoding="utf-8-sig")
            if not (set(self.data['close']) == set(res.value)):
                user_input = input("if rm the csv : y / n: ")
                if user_input.lower() == 'y':
                    os.system('rm %s'%file_name)

    def Get_SomeData(self, p_CT):
        if p_CT == 'kdj':
            n_val = self.res.loc[self.res.index == self.res.index.size-1]
            if n_val.K.values < k_limit and n_val.rsi.values < rsi_limit:
                print(self.p_SN, self.p_name)
                print(n_val)

        # if p_CT == 'rsi':
        #     n_val = self.res.loc[self.res.index == self.res.index.size-1]
        #     if n_val.rsi.values < rsi_limit:
        #         print(self.p_SN, self.p_name)
        #         print(n_val)

    def Show_plt(self):
        fig, ax = plt.subplots(1, 1, figsize=(8,3), dpi=200)
        candlestick2_ohlc(ax,
                        opens = self.df3[ 'open'].values,
                        highs = self.df3['high'].values,
                        lows = self.df3[ 'low'].values,
                        closes = self.df3['close'].values,
                        width=0.5, colorup="r",colordown="g")

        # 显示最高点和最低点
        ax.text(self.df3.high.idxmax(), self.df3.high.max(),   s = self.df3.high.max(), fontsize=8)
        ax.text(self.df3.high.idxmin(), self.df3.high.min() - 2, s = self.df3.high.min(), fontsize=8)

        ax.set_facecolor("white")
        plt.rc("font",family="")
        ax.set_title(self.p_SN + ' ' + self.p_name, fontproperties="SimHei")

        # 画均线
        plt.plot(self.df3['5'].values, alpha = 0.5, label='MA5')
        plt.plot(self.df3['10'].values, alpha = 0.5, label='MA10')

        ax.legend(facecolor='white', edgecolor='white', fontsize=6)

        # 修改x轴坐标
        plt.xticks(ticks = np.arange(0,len(self.df3)), labels = self.df3.date.to_numpy() )
        plt.xticks(rotation=90, size=7)

        # 修改y轴坐标
        ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))

        plt.show()
    
    def Get_KDJ(self, N=KDJ_N, M1=KDJ_M1, M2=KDJ_M2):
        # 计算短期RSV（相对强弱值）：RSV = (C - Ln) / (Hn - Ln) * 100 其中，C是当前close价，Ln是n天内的最低价，Hn是n天内的最高价。
        data = self.data.copy()
        today = dt.now()
        low_min = data['low'].rolling(N, min_periods=1).min()
        high_max = data['high'].rolling(N, min_periods=1).max()
        data['RSV'] = (data['close'] - low_min) / (high_max - low_min) * 100
        data['K'] = data['RSV'].ewm(alpha=1/M1, adjust=False).mean()
        data['D'] = data['K'].ewm(alpha=1/M2, adjust=False).mean()
        data['J'] = 3 * data['K'] - 2 * data['D']
        # self.res['K'] = data['K']
        # self.res['D'] = data['D']
        # self.res['J'] = data['J']
        return data['K'],data['D'],data['J']

    def Get_MACD(self, n_fast=MACD_FAST, n_slow=MACD_SLOW, n_signal=MACD_SIGNAL):
        ema12 = self.data['close'].ewm(span=n_fast, adjust=False).mean()
        ema26 = self.data['close'].ewm(span=n_slow, adjust=False).mean()
        diff = ema12 - ema26
        dea = diff.ewm(span=n_signal, adjust=False).mean()
        macd = 2 * (diff - dea)
        # self.res['macd'] = macd
        # self.res['diff'] = diff
        return macd, diff, dea

    def Get_BOLL(self, n = BOLL_N, k = BOLL_K):
        mid = self.data['close'].rolling(n).mean()
        upper = mid + k * self.data['close'].rolling(n).std()
        lower = mid - k * self.data['close'].rolling(n).std()
        # self.res['boll_u'] = upper
        # self.res['boll_m'] = mid
        # self.res['boll_l'] = lower
        return upper, mid, lower
    
    def Get_Rsi(self, window=RSI_WINDOW):
        """Compute RSI indicator with proper handling of initial values"""
        delta = self.data['close'].diff()
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
    
    def Get_OBV(self):
        """计算OBV指标"""
        if self.res is None or len(self.res) < 2:
            return pd.Series([0] * len(self.res) if self.res is not None else [])
        
        data = self.res.copy()
        obv = [0.0] * len(data)
        
        for i in range(1, len(data)):
            try:
                current_close = data.iloc[i]['close']
                prev_close = data.iloc[i-1]['close']
                current_vol = data.iloc[i]['vol']
                
                if current_close > prev_close:
                    obv[i] = obv[i-1] + current_vol
                elif current_close < prev_close:
                    obv[i] = obv[i-1] - current_vol
                else:
                    obv[i] = obv[i-1]
            except:
                obv[i] = obv[i-1]
        
        return pd.Series(obv)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--sn', type=str, default = '')
    parser.add_argument('--ck', type=str, default = '')
    # parser.add_argument('--cnt', type=int, default = 90)
    # parser.add_argument('--dd', type=int, default = 15)
    # parser.add_argument('--kp', type=int, default = 9)
    parser.add_argument('--ct', type=str, default = 'kdj')
    #kdj
    parser.add_argument('--st', type=bool, default = False)
    parser.add_argument('--dw', type=bool, default = False)
    parser.add_argument('--rd', action="store_const", const=True, default = False)
    parser.add_argument('--fd', type=str, default = '')
    parser.add_argument("--flag", action="store_const", const=True, default = False)
    args = parser.parse_args()
    if args.rd:
        if args.rd:
            # with open('/Users/zack-pc/zack/market/market/mystock/import', 'r', encoding='utf-8') as file:
                # fp = file.read()
                rd_res = pd.DataFrame(columns=['sn', 'name', 'last', 'high', 'open', 'now', 'boll_m', 'K', 'rsi', 'xx', 'err'])
                count = 0
                # for i in fp.split('\n'):
                for i in buy_list.split('\n')[1:-1]:
                    sn = i.split(' ')[0]
                    name = i.split(' ')[1]
                    st = stock(sn, name)
                    file_name = f'/opt/zack/master/data/{sn}.csv'
                    file_data = pd.read_csv(file_name, encoding="utf-8-sig")
                    res = st.Read_import()
                    rd_res.loc[count, 'sn'] = sn
                    rd_res.loc[count, 'name'] = name
                    rd_res.loc[count, 'last'] = d_last = res['last'].values
                    rd_res.loc[count, 'high'] = res['high'].values
                    rd_res.loc[count, 'open'] =  res['open'].values
                    rd_res.loc[count, 'now'] = d_now = res['close'].values
                    rd_res.loc[count, 'xx'] = (d_now - d_last) / d_last
                    rd_res.loc[count, 'boll_m'] = boll_m = file_data.iloc[-1]['boll_m']
                    rd_res.loc[count, 'K'] = K = file_data.iloc[-1]['K']
                    rd_res.loc[count, 'rsi'] = rsi = file_data.iloc[-1]['rsi']
                    rd_res.loc[count, 'err'] = d_now < boll_m and K > 50
                    count += 1
                rd_res['xx'] = list(map(lambda x: f"{x:.2%}", rd_res['xx']))
                rd_res['K'] = list(map(lambda x: f"{x:.2f}", rd_res['K']))
                rd_res['rsi'] = list(map(lambda x: f"{x:.2f}", rd_res['rsi']))
                rd_res['boll_m'] = list(map(lambda x: f"{x:.2f}", rd_res['boll_m']))
                print(rd_res)
    if args.sn or args.ck:
        if args.sn == 'all':
            p_list = get_all_stocks_today()
            for i in p_list:
                # print(i)
                p_SN = i
                st = stock(p_SN, '')
                st.Get_Data(flag=args.flag)
                st.Get_SomeData(args.ct)
            sys.exit()
        for i in p_list.split('\n')[2:-1]:
            if args.sn == 'group1' or args.sn == i.split(' ')[0]:
                p_SN = i.split(' ')[0]
                p_name = i.split(' ')[1]
                st = stock(p_SN, p_name)
                # print(self.p_SN, self.p_name)
                st.Get_Data(flag=args.flag)
                st.Get_SomeData(args.ct)
                if args.st:
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
    if args.fd:
        sum,count,win_count = 0,0,0
        tm_all = 0
        for i in p_list.split('\n')[2:-1]:
            if args.fd == 'all' or args.fd == i.split(' ')[0]:
                p_SN = i.split(' ')[0]
                p_name = i.split(' ')[1]
                st = mystrategy(p_SN, p_name)
                # res = st.find_buy_point()
                res,tm = st.find_min_point()
                if res > 5:
                    win_count += 1
                count += 1
                sum += res
                tm_all += tm
        print(f"\ntotal:{count}, avg:{sum/count}, win:{win_count/count*100:.2f}")
        print(f"\ntotal:{count}, avg:{sum/count}, win:{win_count/count*100:.2f}, tm_all:{tm_all/count:.2f}")
    # st = stock(args.sn, args.ct, args.st)
    # st.Show_plt()
    # st.Get_MACD()
    # st.Get_BOLL()
    # st.Get_KDJ(args.kp, args.dd)