#!/usr/bin/python3

import pandas as pd
import akshare as ak
import tushare as ts
import sys, os
import numpy as np
from pathlib import Path
import argparse
from p_name import p_list
from my_name import buy_list
import requests
import time
from datetime import datetime as dt, date, timedelta
from typing import List
from my_name import black_list

k_limit = 30
rsi_limit = 30
start_date = '2010-01-01'
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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

session = requests.Session()
session.trust_env = False
ak.session = session
original_get = requests.get
requests.get = session.get

ts.set_token('f56d02fa39d85879dd2ce855faee78641ca923da5d6ebe978ad8affa')
pro = ts.pro_api()

# def get_all_stocks_today() -> List[str]:
#     try:
#         today_dt = dt.now()
#         today_str = today_dt.strftime('%Y%m%d')
#         today_int = int(today_str)
#         df = pro.daily(trade_date=today_int)
#         if df is None or df.empty:
#             print(f"今天({today_str})没有交易数据")
#             return []
#         stock_sns = [code.split('.')[0] for code in df['ts_code'].unique()]
#         print(f"获取到 {len(stock_sns)} 只股票的SN号")
#         return stock_sns
#     except Exception as e:
#         print(f"获取当天股票数据失败: {e}")
#         return []
    
def get_all_stocks_today(max_retry_days: int = 10) -> List[str]:
    try:
        current_date = dt.now()
        attempts = 0
        while attempts < max_retry_days:
            check_date = current_date - timedelta(days=attempts)
            trade_date_str = check_date.strftime('%Y%m%d')
            trade_date_int = int(trade_date_str)
            try:
                df = pro.daily(trade_date=trade_date_int)
                if df is not None and not df.empty:
                    stock_sns = [code.split('.')[0] for code in df['ts_code'].unique()]
                    date_str = check_date.strftime('%Y-%m-%d')
                    if attempts == 0:
                        print(f"获取到当天({date_str}) {len(stock_sns)} 只股票")
                    else:
                        print(f"\n当天无交易，找到最近交易日: {date_str}")
                        print(f"获取到 {len(stock_sns)} 只股票")
                        
                        while True:
                            user_input = input("是否使用最近交易日数据？(y/n): ").strip().lower()
                            
                            if user_input == 'y':
                                return stock_sns
                            elif user_input == 'n':
                                print("用户选择退出，返回空列表")
                                return []
                            else:
                                print("请输入 y 或 n")
                    return stock_sns
                else:
                    attempts += 1
            except Exception as api_error:
                attempts += 1
                continue
        print(f"在最近 {max_retry_days} 天内未找到有效交易数据")
        return []
    except Exception as e:
        print(f"获取股票数据失败: {e}")
        return []

import threading

# 使用线程锁
_rate_lock = threading.Lock()
_last_call_time = None
_call_count = 0
_CALL_LIMIT = 49
_WINDOW = 61  # 60秒窗口

def wait_for_rate_limit():
    """等待直到可以调用API"""
    global _last_call_time, _call_count
    with _rate_lock:
        current_time = dt.now()
        if _last_call_time is None:
            _last_call_time = current_time
            _call_count = 1
            return
        elapsed = (current_time - _last_call_time).total_seconds()
        if elapsed >= _WINDOW:
            _last_call_time = current_time
            _call_count = 1
        else:
            _call_count += 1
            if _call_count > _CALL_LIMIT:
                wait_time = _WINDOW - elapsed
                if wait_time > 0:
                    print(f"达到频率限制，等待 {wait_time:.1f} 秒...")
                    time.sleep(wait_time)
                _last_call_time = dt.now()
                _call_count = 1

def get_A_data_from_python(p_SN):
    data = pd.DataFrame(columns=['date', 'now', 'close', 'high', 'low', 'open', 'vol', 'vor', 'tor'])
    # try:
    #     wait_for_rate_limit()
    #     dt_data = ak.stock_zh_a_hist(symbol=p_SN)
    #     data['date'] = pd.to_datetime(dt_data['日期'])
    #     data['now'] = dt_data['收盘']
    #     data['close'] = dt_data['收盘']
    #     data['high'] = dt_data['最高']
    #     data['low'] = dt_data['最低']
    #     data['open'] = dt_data['开盘']
    #     data['vol'] = dt_data['成交量']
    #     data['vor'] = dt_data['成交额']
    #     data['tor'] = dt_data['换手率']
    #     data = data[data['date'] >= start_date]
    # except Exception as e:
    wait_for_rate_limit()
    try:
        ts_code = f"{p_SN}.SH" if p_SN.startswith('6') else f"{p_SN}.BJ" if p_SN.startswith('9') else f"{p_SN}.SZ"
        dt_data = pro.daily(ts_code=ts_code)
        dt_data = dt_data.sort_values(by='trade_date', ascending=True)
        dt_data = dt_data.reset_index(drop=True)
        data['date'] = pd.to_datetime(dt_data['trade_date'].astype(str), format='%Y%m%d')
        data['now'] = dt_data['close']
        data['close'] = dt_data['close']
        data['high'] = dt_data['high']
        data['low'] = dt_data['low']
        data['open'] = dt_data['open']
        data['vol'] = dt_data['vol']
        data['vor'] = dt_data['amount']
        data['tor'] = dt_data['pct_chg']
        data = data[data['date'] >= start_date]
        # time.sleep(0.5)
    except Exception as e2:
        print(f"tushare获取{p_SN}失败: {e2}")
        return None
    if not data.empty and 'date' in data.columns:
        data['date'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')
    return data


def get_D_data_from_python(p_time):
    data = pd.DataFrame(columns=['sn', 'date', 'now', 'close', 'high', 'low', 'open', 'vol', 'vor', 'tor'])
    dt_data = pro.daily(trade_date=p_time)
    dt_data = dt_data.sort_values(by='trade_date', ascending=True)
    dt_data = dt_data.reset_index(drop=True)
    data['sn'] = dt_data['ts_code'].apply(lambda x: x.split('.')[0])
    data['date'] = pd.to_datetime(dt_data['trade_date'].astype(str), format='%Y%m%d')
    data['now'] = dt_data['close']
    data['close'] = dt_data['close']
    data['high'] = dt_data['high']
    data['low'] = dt_data['low']
    data['open'] = dt_data['open']
    data['vol'] = dt_data['vol']
    data['vor'] = dt_data['amount']
    data['tor'] = dt_data['pct_chg']

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
                # print(self.res['date'].iloc[-1] , str(date.today()), file_name)
                self.data = get_A_data_from_python(self.p_SN)
                if self.data is None or self.data.empty:
                    return
                update_size = self.res.index.size
                # print(update_size, len(self.data))
                for i in range(update_size, len(self.data)):
                    self.res.loc[i,'date'] = self.data.date.iloc[i]
                    self.res.loc[i,'value'] = self.data.close.iloc[i]
                    self.res.loc[i,'10-day'] = self.data.close.iloc[i-9:i+1].mean()
                    self.res.loc[i,'vol'] = self.data.vol.iloc[i]
                    self.res.loc[i,'vor'] = self.data.vor.iloc[i]
                    self.res.loc[i,'tor'] = self.data.tor.iloc[i]
                self.res['K'], self.res['D'], self.res['J'] = self.Get_KDJ()
                self.res['macd'], self.res['diff'], self.res['dea'] = self.Get_MACD()
                self.res['boll_u'], self.res['boll_m'], self.res['boll_l'] = self.Get_BOLL()
                self.res['rsi'] = self.Get_Rsi()
                self.res['obv'] = self.Get_OBV()
                self.calculate_cross_indicators()
                self.res.to_csv(file_name, index=False, encoding='utf-8-sig')
                if update_size != len(self.data):
                    print(self.res['date'].iloc[-1], self.p_SN, self.p_name ,' update csv ', len(self.data) - update_size)
        else:
            self.data = get_A_data_from_python(self.p_SN)
            if self.data is None or self.data.empty:
                return
            self.res = pd.DataFrame()
            self.res['date'] = self.data['date']
            self.res['value'] = self.data['close']
            self.res['10-day'] = self.data.close.rolling(10).mean()
            self.res['vol'] = self.data.vol
            self.res['vor'] = self.data.vor
            self.res['tor'] = self.data.tor
            self.res['K'], self.res['D'], self.res['J'] = self.Get_KDJ()
            self.res['macd'], self.res['diff'], self.res['dea'] = self.Get_MACD()
            self.res['boll_u'], self.res['boll_m'], self.res['boll_l'] = self.Get_BOLL()
            self.res['rsi'] = self.Get_Rsi()
            self.res['obv'] = self.Get_OBV()
            self.calculate_cross_indicators()
            self.res.to_csv(file_name, index=False, encoding='utf-8-sig')
    
    def update_all(self):
        s1 = 1

    def find_point(self, start_date, end_date = None):
        if end_date is None:
            end_date = date.today()
        self.Get_Data(True)
        mask = (self.res['date'] >= start_date)# & (self.res['date'] <= end_date)
        filtered_data = self.res.loc[mask]
        
        self.max_v = filtered_data['value'].max()
        self.min_v = filtered_data['value'].min()
        try:
            self.buy_v = filtered_data['value'].iloc[0]
        except:
            self.buy_v = filtered_data['value'].min()

    def Read_import(self):
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

    def Get_SomeData(self, p_CT):
        if len(self.res) < 30:
            return
        if p_CT == 'kdj':
            n_val = self.res.iloc[-1]
            if n_val.K > k_limit > self.res.iloc[-2]['K']:
                print(f"{self.p_SN:6}\t{self.p_name:6}\tdata:{n_val.date:12}\tvalue:{n_val.value:.2f}\tBOLL_m:{n_val.boll_m:.2f}\tMACD:{n_val.macd:.2f}"
                    + f"\tK:{n_val.K:6.2f}\tRSI:{n_val.rsi:6.2f}\tCross:{n_val.MA_Cross:2}, {n_val.MACD_Cross:2}, {n_val.KDJ_Cross:2}")

    def Get_KDJ(self, N=KDJ_N, M1=KDJ_M1, M2=KDJ_M2):
        data = self.data.copy()
        low_min = data['low'].rolling(N, min_periods=1).min()
        high_max = data['high'].rolling(N, min_periods=1).max()
        data['RSV'] = (data['close'] - low_min) / (high_max - low_min) * 100
        data['K'] = data['RSV'].ewm(alpha=1/M1, adjust=False).mean()
        data['D'] = data['K'].ewm(alpha=1/M2, adjust=False).mean()
        data['J'] = 3 * data['K'] - 2 * data['D']
        return data['K'],data['D'],data['J']

    def Get_MACD(self, n_fast=MACD_FAST, n_slow=MACD_SLOW, n_signal=MACD_SIGNAL):
        ema12 = self.data['close'].ewm(span=n_fast, adjust=False).mean()
        ema26 = self.data['close'].ewm(span=n_slow, adjust=False).mean()
        diff = ema12 - ema26
        dea = diff.ewm(span=n_signal, adjust=False).mean()
        macd = 2 * (diff - dea)
        return macd, diff, dea

    def Get_BOLL(self, n = BOLL_N, k = BOLL_K):
        mid = self.data['close'].rolling(n).mean()
        upper = mid + k * self.data['close'].rolling(n).std()
        lower = mid - k * self.data['close'].rolling(n).std()
        return upper, mid, lower
    
    def Get_Rsi(self, window=RSI_WINDOW):
        delta = self.data['close'].diff()
        gain = delta.copy()
        loss = delta.copy()
        gain[gain < 0] = 0
        loss[loss > 0] = 0
        loss = abs(loss)
        avg_gain = gain.rolling(window=window, min_periods=1).mean()
        avg_loss = loss.rolling(window=window, min_periods=1).mean()
        rs = avg_gain / (avg_loss + 1e-6)
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def Get_OBV(self):
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
    
    def calculate_cross_indicators(self):
        """向量化计算交叉指标"""
        if self.res is None or len(self.res) < 20:
            return
        
        data = self.res.copy()
        
        # 1. MA交叉 (价格上穿/下穿10日均线)
        data['MA_Cross'] = 0
        ma_cross_up = (data['value'] > data['10-day']) & (data['value'].shift(1) <= data['10-day'].shift(1))
        ma_cross_down = (data['value'] < data['10-day']) & (data['value'].shift(1) >= data['10-day'].shift(1))
        data.loc[ma_cross_up, 'MA_Cross'] = 1
        data.loc[ma_cross_down, 'MA_Cross'] = -1
        
        # 2. MACD交叉
        data['MACD_Cross'] = 0
        macd_cross_up = (data['diff'] > data['dea']) & (data['diff'].shift(1) <= data['dea'].shift(1))
        macd_cross_down = (data['diff'] < data['dea']) & (data['diff'].shift(1) >= data['dea'].shift(1))
        data.loc[macd_cross_up, 'MACD_Cross'] = 1
        data.loc[macd_cross_down, 'MACD_Cross'] = -1
        
        # 3. KDJ交叉
        data['KDJ_Cross'] = 0
        kdj_cross_up = (data['K'] > data['D']) & (data['K'].shift(1) <= data['D'].shift(1))
        kdj_cross_down = (data['K'] < data['D']) & (data['K'].shift(1) >= data['D'].shift(1))
        data.loc[kdj_cross_up, 'KDJ_Cross'] = 1
        data.loc[kdj_cross_down, 'KDJ_Cross'] = -1
        
        # 更新到self.res
        self.res['MA_Cross'] = data['MA_Cross']
        self.res['MACD_Cross'] = data['MACD_Cross']
        self.res['KDJ_Cross'] = data['KDJ_Cross']

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--sn', type=str, default = '')
    parser.add_argument('--ck', type=str, default = '')
    parser.add_argument('--ct', type=str, default = 'kdj')
    parser.add_argument('--st', type=bool, default = False)
    parser.add_argument('--dw', type=bool, default = False)
    parser.add_argument('--rd', action="store_const", const=True, default = False)
    parser.add_argument('--fd', type=str, default = '')
    parser.add_argument("--flag", action="store_const", const=True, default = False)
    args = parser.parse_args()
    
    if args.rd:
        rd_res = pd.DataFrame(columns=['sn', 'name', 'buy', 'last', 'high', 'open', 'now', 'boll_m', 'K', 'rsi', 'xx', 'err'])
        count = 0
        for i in buy_list.split('\n')[1:-1]:
            sn = i.split(' ')[0]
            name = i.split(' ')[1]
            date_str = i.split(' ')[2].strip("'")
            # start_date = dt.datetime.strptime(date_str, '%Y-%m-%d').date()
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
            st.find_point(date_str)
            rd_res.loc[count, 'buy'] = st.buy_v
            rd_res.loc[count, 'err'] = False
            if d_now < boll_m and d_now < st.max_v * 0.9: rd_res.loc[count, 'err'] = True
            if d_now < st.buy_v * 0.9: rd_res.loc[count, 'err'] = True
            if d_now < d_last * 0.92: rd_res.loc[count, 'err'] = True
            count += 1
        rd_res['xx'] = list(map(lambda x: f"{x:.2%}", rd_res['xx']))
        rd_res['K'] = list(map(lambda x: f"{x:.2f}", rd_res['K']))
        rd_res['rsi'] = list(map(lambda x: f"{x:.2f}", rd_res['rsi']))
        rd_res['boll_m'] = list(map(lambda x: f"{x:.2f}", rd_res['boll_m']))
        print(rd_res)
    
    if args.ck:
        folder_path = "/opt/zack/master/data"
        if os.path.exists(folder_path):
            all_names = os.listdir(folder_path)
            for file_ in all_names:
                if args.ck == 'all' or f"{args.ck}.csv" == file_:
                    print(file_)
                    ck_handle = pd.read_csv(f"{folder_path}/{file_}", encoding="utf-8-sig")
                    if ck_handle['date'].iloc[1] < start_date:
                        os.system(f"rm {folder_path}/{file_}")
                        print(f"rm {file_}")
    
    if args.sn:
        p_list = get_all_stocks_today()
        count = 0
        count_all = len(p_list)
        printed_percents = set()
        for i in p_list:
            if i in black_list:
                continue
            p_SN = None
            if args.sn == 'allall':
                p_SN = i
                # 显示进度
                percent = int((count / count_all) * 100)
                if percent in [5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100] and percent not in printed_percents:
                    print(f"\n🎯 {percent}% 完成\n")
                    printed_percents.add(percent)
                count += 1
            elif args.sn == 'all' and i in p_list.split('\n')[2:-1]:
                p_SN = i
                # p_name = i.split(' ')[1]
            elif args.sn == i:
                p_SN = i
            if p_SN is not None:
                st = stock(p_SN, '')
                st.Get_Data(flag=args.flag)
                st.Get_SomeData(args.ct)
    
    if args.fd:
        from mystrategy import mystrategy
        sum,count,win_count, win_all = 0,0,0,0
        sum2,count2,win_count2 = 0,0,0
        tm_all,tm_all2 = 0,0
        folder_path = "/opt/zack/master/data"
        if os.path.exists(folder_path):
            all_names = os.listdir(folder_path)
            for file_ in all_names:
                if args.fd == 'allall' or f"{args.fd}.csv" == file_:
                    i = file_.split('.csv')[0]
                    p_SN = i
                    st = mystrategy(p_SN)
                    res, win_count, tm = st.find_buy_point()
                    count += 1
                    win_all += win_count
                    sum += res
                    tm_all += tm
            if args.fd == 'all':
                for i in p_list.split('\n')[2:-1]:
                    p_SN = i.split(' ')[0]
                    p_name = i.split(' ')[1]
                    st = mystrategy(p_SN, p_name)
                    res, win_count, tm = st.find_buy_point()
                    count += 1
                    win_all += win_count
                    sum += res
                    tm_all += tm
            print(f"\ntotal:{count}, avg:{sum/count}, win:{win_all/tm_all*100:.2f}, tm_all:{tm_all/count:.2f}")
            sys.exit()
