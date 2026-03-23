import pandas as pd
import numpy as np
from pathlib import Path
from my_name import group1_list
from my_name import buy_list
from my_name import week_macd_list
from my_name import week_macd_list2
from my_name import day_diff_dea_list

def second_order_diff_pandas(series):
    # pandas的diff()方法
    first_diff = series.diff()  # 一阶差分
    second_diff = first_diff.diff()  # 二阶差分
    
    return second_diff

def has_up_cross_in_past_n_days(values_series, limit):
    for i in range(1, len(values_series)):
        if values_series.iloc[i-1] < limit <= values_series.iloc[i]:
            return True
    return False

def has_up_boll_in_past_n_days(values_series, limit):
    for i in range(1, len(values_series)):
        if values_series.iloc[i-1] < limit.iloc[i-1]  and limit.iloc[i] <= values_series.iloc[i]:
            return True
    return False

def has_up_boll_still_n_days(values_series):
    res = True
    for i in range(1, len(values_series)):
        if values_series.iloc[i-1] > values_series.iloc[i]:
            res = False
    return res

def has_boll_v_shape_recent(boll_series):
    v = boll_series.tolist()
    return len(v)>=3 and (m:=v.index(min(v))) not in (0,len(v)-1) and all(v[i]>v[i+1] for i in range(m)) and all(v[i]<v[i+1] for i in range(m,len(v)-1))

def daily_to_weekly(daily_array, window=10):
    week_day = 5  # 每周最多5个交易日
    if daily_array is None or len(daily_array) == 0:
        return np.array([])
    daily_array = np.asarray(daily_array)
    if len(daily_array) <= week_day:
        if len(daily_array) > 0:
            return np.array([np.nanmean(daily_array)])
        else:
            return np.array([])
    n_weeks_total = (len(daily_array) + week_day - 1) // week_day
    weekly_means = []
    for i in range(n_weeks_total):
        start_idx = i * week_day
        end_idx = min((i + 1) * week_day, len(daily_array))
        week_data = daily_array[start_idx:end_idx]
        if len(week_data) > 0:
            weekly_mean = np.nanmean(week_data)  # 取每周平均值
            weekly_means.append(weekly_mean)
        else:
            weekly_means.append(np.nan)
    weekly_means = np.array(weekly_means)
    if len(weekly_means) > window:
        return weekly_means[-window:]
    else:
        return weekly_means

def find_previous_weekly_data(input_date, weekly_df):
    if not pd.api.types.is_datetime64_any_dtype(weekly_df['date']):
        weekly_df['date'] = pd.to_datetime(weekly_df['date'])
    input_date = pd.to_datetime(input_date)

    previous_weeks = weekly_df[weekly_df['date'] < input_date]

    if previous_weeks.empty:
        return None, None
    else:
        latest_previous_week = previous_weeks.loc[previous_weeks['date'].idxmax()]
        latest_index = latest_previous_week.name
        return latest_previous_week, latest_index

def judge_trend_by_regression(prices, std = 'value', window=10):
    if len(prices) < window:
        return 0
    
    # recent_prices = prices[-window:]
    recent_prices = prices[std].values[-window:].astype(float)
    x = np.arange(len(recent_prices))
    
    slope = np.polyfit(x, recent_prices, 1)[0]
    
    return slope

def predict_trend(prices):
    window = len(prices)
    
    x = np.arange(len(prices))
    y = np.array(prices)
    
    A = np.vstack([x, np.ones(len(x))]).T
    slope, _ = np.linalg.lstsq(A, y, rcond=None)[0]
    
    return slope

def my_mean(prices):
    return np.mean(prices)

def my_range(prices, low, high):
    return (prices >= low) & (prices <= high)

class jiaoyi:
    def __init__(self, all_money = 10000):
        self.all_money = all_money
        self.pick = 0

    def buy(self, price, num):
        self.all_money -= price * num
        self.pick += num

    def sell(self, price, num):
        self.all_money += price * num
        self.pick -= num

class mystrategy:
    def __init__(self, p_SN, p_name = 'xxx'):
        self.p_SN = p_SN
        self.p_name = p_name
        file_name = f'/opt/zack/master/data/{self.p_SN}.csv'
        file_week_name = f'/opt/zack/master/week_data/{self.p_SN}.csv'
        self.rd = pd.DataFrame()
        if Path(file_name).is_file():
            self.rd = pd.read_csv(file_name, encoding="utf-8-sig")
            # print(rd.loc[rd.index == 0])
            # self.res = self.rd.loc[self.rd.index == 0]
            self.res = pd.DataFrame()
        if Path(file_week_name).is_file():
            self.rd_week = pd.read_csv(file_week_name, encoding="utf-8-sig")

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
        # return self.find_min_point()
        # self.find_still_point()
        # return 1,1,1
        # if self.p_SN == '002466': return self.way_603099()
        # if self.p_SN == '002475': return self.way_603099()
        # if self.p_SN == '600660': return self.way_week_macd()
        # if self.p_SN == '601898': return self.way16()
        if self.p_SN == '603039': return self.way_603039()
        if self.p_SN in week_macd_list: return self.way_week_macd()
        if self.p_SN in week_macd_list2: return self.way_week_macd2()
        if self.p_SN in day_diff_dea_list: return self.way_diff_dea()
        return self.way14()
        # return self.fenxi()

    # macd > 0 and week_macd up
    def way_603039(self):
        if self.rd.empty:
            return 0
        jy = jiaoyi()
        status = 0
        jy_times = 0
        win_times = 0
        max_v, min_v, buy_v = 0, 0, 0
        still_day = 0
        still_days = []
        macd_low = []
        buy_flag = 0
        jie = 0
        huice = 0.0
        finall = ''
        for index, row in self.rd.iterrows():
            if row['date'] < '2024' or row['date'] > '2027':
                continue
            if index < 40:
                continue
            week_now, week_index = find_previous_weekly_data(row['date'], self.rd_week)
            if week_now is None:
                print(self.p_SN, 'no weekly data')
                return 10000, 0, 0
            if status == 0:
                if jy.all_money > 0:
                    if row['macd'] > 0 and row['macd'] > self.rd.iloc[index-1]['macd'] and \
                        row['value'] > row['boll_m'] and self.rd.iloc[index-2]['value'] < self.rd.iloc[index-2]['boll_m']:
                        status = 1
                    # if row['macd'] > self.rd.iloc[index-1]['macd'] > self.rd.iloc[index-2]['macd'] and \
                    #     len(macd_low) > 5 and min(macd_low) < -1:
                    #     status = 1
                    # if 10 < row['K'] < 30 and row['K'] > self.rd.iloc[index-1]['K'] and self.rd.iloc[index-1]['K'] < self.rd.iloc[index-2]['K'] < self.rd.iloc[index-3]['K']:
                    #     status = 1
                    # if row['macd'] > self.rd.iloc[index-1]['macd'] > 0 > self.rd.iloc[index-2]['macd']:
                    #     status = 1
                    # if 20 < k_low < 30 and row['K'] > 30 > self.rd.iloc[index-1]['K']:
                    #     status = 1
                    # if row['macd'] > self.rd.iloc[index-1]['macd'] > 0 and row['boll_m'] > self.rd.iloc[index-1]['boll_m']:
                    #     status = 1
                if jy.pick > 0:
                    still_day += 1
                    # if row['K'] < 30:
                    #     status = -2
                    if row['value'] < row['boll_m'] and row['value'] < max_v * 0.9:
                        status = -2
                    if row['value'] < buy_v * 0.9:
                        status = -2
                    if row['value'] < self.rd.iloc[index-1]['value'] * 0.92:
                        status = -2
                    # if row['macd'] < self.rd.iloc[index-1]['macd'] < self.rd.iloc[index-2]['macd'] and row['macd'] < 0:
                    #     status = -2
            
            if status == 1:
                status = 1
                if row['boll_m'] > self.rd.iloc[index-1]['boll_m']:
                    status = 2
                # if week_now['macd_weekly'] < self.rd_week.iloc[week_index-1]['macd_weekly']:
                #     status = 0
                if week_now['macd_weekly'] > self.rd_week.iloc[week_index-1]['macd_weekly']:
                    status = 2
                # if row['boll_m'] > self.rd.iloc[index-1]['boll_m']:
                #     status = 2

                # if row['macd'] < -1.5:
                #     status = 0

            if status == 2:
                status = 3
                if week_now['macd_weekly'] > self.rd_week.iloc[week_index-1]['macd_weekly']:
                    status = 3
                    
            if status > 2:
                if jy.all_money > 1:
                    if jy.all_money < 10000:
                        jie += 10000 - jy.all_money
                        jy.all_money = 10000
                    else:
                        if jie < jy.all_money - 10000:
                            jy.all_money -= jie
                            jie = 0
                        else:
                            jie -= jy.all_money - 10000
                            jy.all_money = 10000
                    buy_flag = 1
                    still_day = 0
                    # if index > len(self.rd)-2:
                    #     print(self.p_SN, 'buy')
                status = 0
            
            if status < -1:
                if jy.pick > 0:
                    buy_flag = -1
                    jy_times += 1
                status = 0
            # if jy.pick > 0:
            #     loop.append(row['value'])
            min_v = min(min_v, row['value'])
            max_v = max(max_v, row['value'])

            if jy.pick > 0:
                if row['value'] < max_v:
                    temp = 1 - row['value'] / max_v
                    huice = max(huice, temp)

            if buy_flag > 0:
                all_p = jy.all_money / row['value']
                jy.buy(row['value'], all_p)
                buy_v = max_v = min_v = row['value']
                buy_flag = 0
                still_day = 0
                print(row['date'], row['value'], len(macd_low))
                finall = row['date']
                if index > len(self.rd)-2:
                    money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                    if money_all > 9000 and win_times > 0.3 * jy_times:
                        print(self.p_SN, self.p_name, 'buy', row['date'] , win_times, ' / ', jy_times, money_all)
            if buy_flag < 0:
                if row['value'] > buy_v:
                    win_times += 1
                jy.sell(row['value'], jy.pick)
                buy_flag = 0
                still_days.append(still_day)
                print(row['date'], ' sell ' , f"{((row['value'] - buy_v) / buy_v)*100:.2f}%" , still_day, 'days \n')
                finall = ''
                if index > len(self.rd)-2 and self.p_SN in buy_list:
                    money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                    print(self.p_SN, self.p_name, 'sell', row['date'] , win_times, ' / ', jy_times, money_all)
            
            if row['macd'] < 0:
                macd_low.append(row['macd'])
            else:
                macd_low = []
        
        money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
        if not finall == '':
            print(self.p_SN, self.p_name, 'buy', finall , win_times, ' / ', jy_times, money_all)
        return money_all,win_times,jy_times
    
    # week_macd up and macd > 0
    def way_week_macd(self):
        if self.rd.empty:
            return 0
        jy = jiaoyi()
        loop = []
        status = 0
        jy_times = 0
        win_times = 0
        max_v, min_v, buy_v = 0, 0, 0
        still_day = 0
        still_days = []
        buy_flag = 0
        jie = 0
        huice = 0.0
        finall = ''
        for index, row in self.rd.iterrows():
            if row['date'] < '2021' or row['date'] > '2027':
                continue
            if index < 40:
                continue
            if self.rd_week is None:
                return 10000, 0, 0
            week_now, week_index = find_previous_weekly_data(row['date'], self.rd_week)
            if week_now is None:
                print(self.p_SN, 'no weekly data')
                return 10000, 0, 0
            if status == 0:
                if jy.all_money > 0:
                    if week_now['macd_weekly'] > self.rd_week.iloc[week_index-1]['macd_weekly'] > 0 > self.rd_week.iloc[week_index-2]['macd_weekly']:
                        status = 1
                        macd_all = self.rd_week.iloc[week_index-1]['macd_weekly']
                if jy.pick > 0:
                    still_day += 1
                    if row['value'] < row['boll_m'] and row['value'] < max_v * 0.9:
                        status = -2
                    if row['value'] < buy_v * 0.9:
                        status = -2
                    if row['value'] < self.rd.iloc[index-1]['value'] * 0.92:
                        status = -2

            if status == 1:
                status = 1
                if week_now['macd_weekly'] > 0:
                    macd_all += week_now['macd_weekly']
                else:
                    status = 0
                if macd_all > 0.1:
                    status = 2
                # if row['macd'] > self.rd.iloc[index-1]['macd'] > self.rd.iloc[index-2]['macd'] and row['macd'] > 0:
                #     status = 2

            if status == 2:
                status = 3
                if week_now['macd_weekly'] > self.rd_week.iloc[week_index-1]['macd_weekly'] > 0:
                    status = 3
                    
            if status > 2:
                if jy.all_money > 1:
                    if jy.all_money < 10000:
                        jie += 10000 - jy.all_money
                        jy.all_money = 10000
                    else:
                        if jie < jy.all_money - 10000:
                            jy.all_money -= jie
                            jie = 0
                        else:
                            jie -= jy.all_money - 10000
                            jy.all_money = 10000
                    buy_flag = 1
                    still_day = 0
                status = 0
            
            if status < -1:
                if jy.pick > 0:
                    buy_flag = -1
                    jy_times += 1
                status = 0
            min_v = min(min_v, row['value'])
            max_v = max(max_v, row['value'])

            if jy.pick > 0:
                if row['value'] < max_v:
                    temp = 1 - row['value'] / max_v
                    huice = max(huice, temp)

            if buy_flag > 0:
                all_p = jy.all_money / row['value']
                jy.buy(row['value'], all_p)
                loop.append([row['date'], row['value']])
                buy_v = max_v = min_v = row['value']
                buy_flag = 0
                still_day = 0
                print(row['date'], row['value'], week_now['macd_weekly'], self.rd_week.iloc[week_index-1]['macd_weekly'])
                money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                finall = row['date']
                if index > len(self.rd)-2 and money_all > 10000:
                    print(self.p_SN, self.p_name, 'buy', row['date'] , win_times, ' / ', jy_times, money_all)
            if buy_flag < 0:
                if row['value'] > buy_v:
                    win_times += 1
                jy.sell(row['value'], jy.pick)
                loop.append([row['date'], row['value'], row['K'], row['rsi'], jy.all_money])
                buy_flag = 0
                still_days.append(still_day)
                print(row['date'], ' sell ' , f"{((row['value'] - buy_v) / buy_v)*100:.2f}%" , still_day, 'days \n')
                finall = ''
                if index > len(self.rd)-3 and self.p_SN in buy_list:
                    money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                    print(self.p_SN, self.p_name, 'sell', row['date'] , win_times, ' / ', jy_times, money_all)
        
        money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
        # if not finall == '':
        #     print(self.p_SN, self.p_name, 'buy', finall , win_times, ' / ', jy_times, money_all)
        if money_all > 30000:
            print(self.p_SN, self.p_name, win_times, ' / ', jy_times, money_all)
        return money_all,win_times,jy_times
    
    # week_macd up and week_macd > 0
    def way_week_macd2(self):
        if self.rd.empty:
            return 0
        jy = jiaoyi()
        loop = []
        status = 0
        jy_times = 0
        win_times = 0
        max_v, min_v, buy_v = 0, 0, 0
        still_day = 0
        still_days = []
        buy_flag = 0
        jie = 0
        huice = 0.0
        finall = ''
        for index, row in self.rd.iterrows():
            if row['date'] < '2024' or row['date'] > '2027':
                continue
            if index < 40:
                continue
            if self.rd_week is None:
                return 10000, 0, 0
            week_now, week_index = find_previous_weekly_data(row['date'], self.rd_week)
            if week_now is None:
                print(self.p_SN, 'no weekly data')
                return 10000, 0, 0
            if status == 0:
                if jy.all_money > 0:
                    if week_now['macd_weekly'] > 0 and week_now['macd_weekly'] > self.rd_week.iloc[week_index-1]['macd_weekly'] > self.rd_week.iloc[week_index-2]['macd_weekly']:
                        status = 1
                        # macd_all = self.rd.iloc[index-1]['macd']
                    # if week_now['macd_weekly'] > self.rd_week.iloc[week_index-1]['macd_weekly'] > self.rd_week.iloc[week_index-2]['macd_weekly'] and week_now['macd_weekly'] > 0:
                    #     status = 1
                    #     macd_all = self.rd_week.iloc[week_index-1]['macd_weekly']
                if jy.pick > 0:
                    still_day += 1
                    if row['value'] < row['boll_m'] and row['value'] < max_v * 0.9:
                        status = -2
                    if row['value'] < buy_v * 0.9:
                        status = -2
                    if row['value'] < self.rd.iloc[index-1]['value'] * 0.92:
                        status = -2

            if status == 1:
                status = 2
                # if week_now['macd_weekly'] > 0:
                #     macd_all += week_now['macd_weekly']
                # else:
                #     status = 0
                # if macd_all > 0.1:
                #     status = 2
                # if row['macd'] > self.rd.iloc[index-1]['macd'] > self.rd.iloc[index-2]['macd'] and row['macd'] > 0:
                #     status = 2

            if status == 2:
                status = 3
                if week_now['macd_weekly'] > self.rd_week.iloc[week_index-1]['macd_weekly'] > 0:
                    status = 3
                    
            if status > 2:
                if jy.all_money > 1:
                    if jy.all_money < 10000:
                        jie += 10000 - jy.all_money
                        jy.all_money = 10000
                    else:
                        if jie < jy.all_money - 10000:
                            jy.all_money -= jie
                            jie = 0
                        else:
                            jie -= jy.all_money - 10000
                            jy.all_money = 10000
                    buy_flag = 1
                    still_day = 0
                status = 0
            
            if status < -1:
                if jy.pick > 0:
                    buy_flag = -1
                    jy_times += 1
                status = 0
            min_v = min(min_v, row['value'])
            max_v = max(max_v, row['value'])

            if jy.pick > 0:
                if row['value'] < max_v:
                    temp = 1 - row['value'] / max_v
                    huice = max(huice, temp)

            if buy_flag > 0:
                all_p = jy.all_money / row['value']
                jy.buy(row['value'], all_p)
                loop.append([row['date'], row['value']])
                buy_v = max_v = min_v = row['value']
                buy_flag = 0
                still_day = 0
                print(row['date'], row['value'], week_now['macd_weekly'], self.rd_week.iloc[week_index-1]['macd_weekly'])
                money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                finall = row['date']
                if index > len(self.rd)-2 and money_all > 10000:
                    print(self.p_SN, self.p_name, 'buy', row['date'] , win_times, ' / ', jy_times, money_all)
            if buy_flag < 0:
                if row['value'] > buy_v:
                    win_times += 1
                jy.sell(row['value'], jy.pick)
                loop.append([row['date'], row['value'], row['K'], row['rsi'], jy.all_money])
                buy_flag = 0
                still_days.append(still_day)
                print(row['date'], ' sell ' , f"{((row['value'] - buy_v) / buy_v)*100:.2f}%" , still_day, 'days \n')
                finall = ''
                if index > len(self.rd)-3 and self.p_SN in buy_list:
                    money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                    print(self.p_SN, self.p_name, 'sell', row['date'] , win_times, ' / ', jy_times, money_all)
        
        money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
        # if not finall == '':
        #     print(self.p_SN, self.p_name, 'buy', finall , win_times, ' / ', jy_times, money_all)
        return money_all,win_times,jy_times
    
    # diff < dea to diff > dea 
    def way_diff_dea(self):
        if self.rd.empty:
            return 0
        jy = jiaoyi()
        loop = []
        status = 0
        jy_times = 0
        win_times = 0
        max_v, min_v, buy_v = 0, 0, 0
        still_day = 0
        still_days = []
        buy_flag = 0
        jie = 0
        huice = 0.0
        finall = ''
        for index, row in self.rd.iterrows():
            if row['date'] < '2021' or row['date'] > '2027':
                continue
            if index < 40:
                continue
            if self.rd_week is None:
                return 10000, 0, 0
            week_now, week_index = find_previous_weekly_data(row['date'], self.rd_week)
            if week_now is None:
                print(self.p_SN, 'no weekly data')
                return 10000, 0, 0
            if status == 0:
                if jy.all_money > 0:
                    # if week_now['macd_weekly'] > 0 > self.rd_week.iloc[week_index-1]['macd_weekly']:
                    #     status = 1
                    #     macd_all = 0
                    if row['diff'] - row['dea'] > 0 > self.rd.iloc[index-1]['diff'] - self.rd.iloc[index-1]['dea']:
                        status = 1
                if jy.pick > 0:
                    still_day += 1
                    if row['value'] < row['boll_m'] and row['value'] < max_v * 0.9:
                        status = -2
                    if row['value'] < buy_v * 0.9:
                        status = -2
                    if row['value'] < self.rd.iloc[index-1]['value'] * 0.92:
                        status = -2
                    if row['boll_m'] < self.rd.iloc[index-1]['boll_m']:
                        if row['diff'] - row['dea'] < 0 < self.rd.iloc[index-1]['diff'] - self.rd.iloc[index-1]['dea']:
                            status = -2
                        if 0 < row['macd'] < self.rd.iloc[index-1]['macd'] < self.rd.iloc[index-2]['macd'] < self.rd.iloc[index-3]['macd']:
                            status = -2

            if status == 1:
                status = 2
                # if week_now['macd_weekly'] >= 0:
                #     macd_all += week_now['macd_weekly']
                # else:
                #     status = 0
                # if macd_all > 0.1 and row['macd'] > self.rd.iloc[index-1]['macd']:
                #     status = 2
                # if row['macd'] > self.rd.iloc[index-1]['macd'] > self.rd.iloc[index-2]['macd'] and row['macd'] > 0:
                #     status = 2

            if status == 2:
                status = 3
                if week_now['boll_m_weekly'] > self.rd_week.iloc[week_index-1]['boll_m_weekly']:
                    status = 3
                    
            if status > 2:
                if jy.all_money > 1:
                    if jy.all_money < 10000:
                        jie += 10000 - jy.all_money
                        jy.all_money = 10000
                    else:
                        if jie < jy.all_money - 10000:
                            jy.all_money -= jie
                            jie = 0
                        else:
                            jie -= jy.all_money - 10000
                            jy.all_money = 10000
                    buy_flag = 1
                    still_day = 0
                status = 0
            
            if status < -1:
                if jy.pick > 0:
                    buy_flag = -1
                    jy_times += 1
                status = 0
            min_v = min(min_v, row['value'])
            max_v = max(max_v, row['value'])

            if jy.pick > 0:
                if row['value'] < max_v:
                    temp = 1 - row['value'] / max_v
                    huice = max(huice, temp)

            if buy_flag > 0:
                all_p = jy.all_money / row['value']
                jy.buy(row['value'], all_p)
                loop.append([row['date'], row['value']])
                buy_v = max_v = min_v = row['value']
                buy_flag = 0
                still_day = 0
                # print(row['date'], row['value'], week_now['macd_weekly'], self.rd_week.iloc[week_index-1]['macd_weekly'])
                money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                finall = row['date']
                if index > len(self.rd)-5 and money_all > 10000:
                    print(self.p_SN, self.p_name, 'buy', row['date'] , win_times, ' / ', jy_times, money_all)
            if buy_flag < 0:
                if row['value'] > buy_v:
                    win_times += 1
                jy.sell(row['value'], jy.pick)
                loop.append([row['date'], row['value'], row['K'], row['rsi'], jy.all_money])
                buy_flag = 0
                still_days.append(still_day)
                # print(row['date'], ' sell ' , f"{((row['value'] - buy_v) / buy_v)*100:.2f}%" , still_day, 'days \n')
                finall = ''
                if index > len(self.rd)-3 and self.p_SN in buy_list:
                    money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                    print(self.p_SN, self.p_name, 'sell', row['date'] , win_times, ' / ', jy_times, money_all)
        
        money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
        if not finall == '':
            print(self.p_SN, self.p_name, 'buy his:', finall , win_times, ' / ', jy_times, money_all)
        return money_all,win_times,jy_times
    

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
            if row['date'] < '2021':
                continue
            money_all = money + pick * row['value']
            # if row['K'] < 20 and row['rsi'] < 30 and pick == 0 and row['value'] < row['boll_l']:
            if row['K'] < 20 and row['rsi'] < 30 and pick == 0:
                self.res.loc[count_res, 'date'] = row['date']
                self.res.loc[count_res, 'value'] = row['value']
                self.res.loc[count_res, 'K'] = row['K']
                self.res.loc[count_res, 'rsi'] = row['rsi']
                pick += 1 * money / row['value']
                money -= 1 * money
                self.res.loc[count_res, 'money_all'] = money_all
                self.res.loc[count_res, 'money'] = money
                self.res.loc[count_res, 'pick'] = pick
                self.res.loc[count_res, 'buy'] = 1
                # self.res.loc[count_res, 'min'] = row['value']
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
                # if self.res.loc[count_res-1, 'money_all'] > self.res.loc[count_res, 'money_all']:
                #     print(self.p_SN, self.p_name)
                #     print(self.res[count_res-1:count_res+1]) 
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
        if money_all > 5000:
            print('\n',self.p_SN, self.p_name)
            print(self.res) 
            print("all money = ",money_all)
        # self.res.to_csv("res.csv", index=False, encoding='utf-8-sig')
        return money_all
    
    def way4(self):
        if self.rd.empty:
            return 0
        jy = jiaoyi()
        loop = []
        min_v = 999999
        for index, row in self.rd.iterrows():
            if row['date'] < '2025':
                continue
            all_p = jy.all_money / row['value']
            if row['K'] < 20 and row['rsi'] < 20 and row['value'] < row['boll_l'] and jy.all_money > 0:
                jy.buy(row['value'], all_p)
                loop.append([row['date'], row['value'], row['K'], row['rsi']])
            if row['K'] > 80 and row['rsi'] > 80 and row['value'] > row['boll_m'] and jy.pick > 0:
                jy.sell(row['value'], jy.pick)
                loop.append([row['date'], row['value'], row['K'], row['rsi'], min_v])
                min_v = 999999
            if jy.pick > 0:
                min_v = min(min_v, row['value'])
        
        # self.res.to_csv("res.csv", index=False, encoding='utf-8-sig')
        money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value']
        # print(loop)
        return money_all
    
    def way5(self):
        if self.rd.empty:
            return 0
        jy = jiaoyi()
        loop = []
        status = 0
        jy_times = 0
        max_v, min_v, buy_v = 0, 0, 0
        still_day = 0
        for index, row in self.rd.iterrows():
            if row['date'] < '2023':
                continue
            all_p = jy.all_money / row['value']
            if status > 1:
                if jy.all_money > 0:
                    jy.buy(row['value'], all_p)
                    loop.append(row['date'])
                    loop.append(self.rd.iloc[index]['value'])
                    status = 0
                    buy_v = max_v = min_v = row['value']
            if status == 1:
                if row['value'] > row['boll_m']:
                    status = 2
            if status == 0:
                if row['K'] < 30 or row['rsi'] < 30:
                    status = 1
                if row['K'] > 80 and row['rsi'] > 80:
                    status = -1
                if row['value'] < buy_v * 0.9:
                    status = -2
                min_v = min(min_v, row['value'])
                max_v = max(max_v, row['value'])
            if status == -1:
                if row['value'] < row['boll_m']:
                    status = -2
                if row['value'] < max_v * 0.9:
                    status = -2
            if status < -1:
                if jy.pick > 0:
                    jy.sell(row['value'], jy.pick)
                    loop.append([row['date'], row['value'], row['K'], row['rsi']])
                    status = 0
                    jy_times += 1
            if jy.pick > 0:
                loop.append(self.rd.iloc[index]['value'])
        
        # self.res.to_csv("res.csv", index=False, encoding='utf-8-sig')
        money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value']
        # if money_all < 9500:
        #     print(self.p_SN, loop, money_all)
        return money_all,jy_times
    
    def way6(self):
        if self.rd.empty:
            return 0
        self.cross = [0] * len(self.rd)
        jy = jiaoyi()
        loop = []
        status = 0
        jy_times = 0
        max_v, min_v, buy_v = 0, 0, 0
        still_day = 0
        kdj_flag, macd_flag = 0, 0
        for index, row in self.rd.iterrows():
            if row['date'] < '2023':
                continue
            all_p = jy.all_money / row['value']
            if status > 2:
                if jy.all_money > 0:
                    jy.buy(row['value'], all_p)
                    loop.append(row['date'])
                    loop.append(row['value'])
                    status = 0
                    buy_v = max_v = min_v = row['value']
            if status == 2:
                if row['MACD_Cross'] > 0:
                    status = 3
                if row['MACD_Cross'] < 0 or row['KDJ_Cross'] < 0:
                    status = 1
            if status == 1:
                if row['KDJ_Cross'] > 0:
                    status = 2
                if row['KDJ_Cross'] < 0 or row['MACD_Cross'] < 0:
                    status = 0
            if status == 0:
                if row['K'] < 30 or row['rsi'] < 30:
                    status = 1
                if row['KDJ_Cross'] < 0 or row['MACD_Cross'] < 0:
                    status = -1
                min_v = min(min_v, row['value'])
                max_v = max(max_v, row['value'])
            if status == -1:
                if row['value'] < row['boll_m']:
                    status = -2
                if row['value'] < max_v * 0.9:
                    status = -2
            if status < -1:
                if jy.pick > 0:
                    jy.sell(row['value'], jy.pick)
                    loop.append(row['date'])
                    loop.append(row['value'])
                    loop.append(jy.all_money)
                    jy_times += 1
                status = 0
            if jy.pick > 0:
                if row['value'] < buy_v * 0.9:
                    status = -2
                self.cross[index] = 1
                loop.append(row['value'])
            # print(row['date'], status)
        
        # self.res.to_csv("res.csv", index=False, encoding='utf-8-sig')
        money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value']
        # if money_all < 9500:
        #     print(self.p_SN)
        # print(loop, money_all)
        return money_all,jy_times
    
    def way7(self):
        if self.rd.empty:
            return 0
        jy = jiaoyi()
        cross_flag = 0
        loop = []
        status = 0
        jy_times = 0
        max_v, min_v, buy_v = 0, 0, 0
        still_day = 0
        kdj_flag, macd_flag = 0, 0
        for index, row in self.rd.iterrows():
            if row['date'] < '2023':
                continue
            all_p = jy.all_money / row['value']
            cross_flag += row['MACD_Cross'] + row['KDJ_Cross']
            if status > 2:
                status = 0
                if jy.all_money > 0:
                    jy.buy(row['value'], all_p)
                    loop.append(row['date'])
                    loop.append(row['value'])
                    buy_v = max_v = min_v = row['value']
                    # print('\n',judge_trend_by_regression(self.rd.iloc[index-10:index+1]))
                cross_flag = 0
            elif status == 2:
                if row['MACD_Cross'] > 0:
                    status = 3
                if row['KDJ_Cross'] < 0 or row['MACD_Cross'] < 0:
                    status = 0
            elif status == 1:
                if row['KDJ_Cross'] > 0:
                    status = 2
                if row['KDJ_Cross'] < 0 or row['MACD_Cross'] < 0:
                    status = 0
            elif status == 0:
                if (row['K'] < 30 or row['rsi'] < 30):
                    status = 1
                # if row['K'] > 80 or row['rsi'] > 80:
                #     status = -1
                min_v = min(min_v, row['value'])
                max_v = max(max_v, row['value'])
            elif status < 0:
                status = 0
                if cross_flag > 1:
                    continue
                if row['KDJ_Cross'] > 0 and row['MACD_Cross'] > 0:
                    continue
                if jy.pick > 0:
                    jy.sell(row['value'], jy.pick)
                    # print(loop)
                    loop = []
                    loop.append(row['date'])
                    loop.append(row['value'])
                    loop.append(row['boll_m'])
                    loop.append(max_v)
                    loop.append(jy.all_money)
                    # print(loop)
                    loop = []
                    jy_times += 1
                cross_flag = 0
            if jy.pick > 0:
                if row['value'] < max_v * 0.9 and row['value'] < row['boll_m']:
                    status = -1
                if row['value'] < buy_v * 0.9:
                    status = -1
                # if row['KDJ_Cross'] < 0 and row['MACD_Cross'] < 0:
                if cross_flag < -1:
                    status = -1
                loop.append([row['value'], row['K']])
            # print(row['date'], cross_flag, status)
        
        money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value']
        if money_all < 7000:
            print(self.p_SN, money_all)
        # print(loop)
        return money_all,jy_times

    def way8(self):
        if self.rd.empty:
            return 0
        jy = jiaoyi()
        loop = []
        status = 0
        jy_times = 0
        win_times = 0
        max_v, min_v, buy_v = 0, 0, 0
        still_day = 0
        buy_flag = 0
        jie = 0
        huice = 0.0
        for index, row in self.rd.iterrows():
            if row['date'] < '2024' or row['date'] > '2027':
                continue
            if status == 0:
                if jy.all_money > 0:
                    if row['K'] < 30 or row['rsi'] < 30:
                        status = 1
                    if self.rd.iloc[index-1]['K'] < 30 or self.rd.iloc[index-1]['rsi'] < 30:
                        status = 1
                if jy.pick > 0:
                    if row['value'] < row['boll_m'] and row['value'] < max_v * 0.9:
                        status = -2
                    if row['value'] < buy_v * 0.9:
                        status = -2
                    if row['value'] < self.rd.iloc[index-1]['value'] * 0.92:
                        status = -2
            
            if status == 1:
                status = 0
                v_trend = predict_trend(self.rd['value'].iloc[index-2:index+1])
                k_trend = predict_trend(self.rd['K'].iloc[index-2:index+1])
                macd_trend = predict_trend(self.rd['macd'].iloc[index-2:index+1])
                if (v_trend > 0.0) and (k_trend > 1.0) and (macd_trend > 0.0) and my_mean(self.rd['value'].iloc[index-4:index+1]) > my_mean(self.rd['value'].iloc[index-5:index]):
                    status = 2
                    # print(v_trend, k_trend, macd_trend, my_mean(self.rd['value'].iloc[index-4:index+1]), my_mean(self.rd['value'].iloc[index-5:index]))

            if status == 2:
                status = 1
                if row['boll_l'] > self.rd.iloc[index-1]['boll_l'] or row['boll_m'] > self.rd.iloc[index-1]['boll_m']:
                    status = 3
                week_v = daily_to_weekly(self.rd['value'].iloc[index-20:index+1])
                week_boll_m = daily_to_weekly(self.rd['boll_m'].iloc[index-20:index+1])
                week_boll_l = daily_to_weekly(self.rd['boll_l'].iloc[index-20:index+1])
                if week_v[-1] > week_v[-2] or week_boll_m[-1] > week_boll_m[-2]:
                    status = 3

            if status > 2:
                if jy.all_money > 1:
                    if jy.all_money < 10000:
                        jie += 10000 - jy.all_money
                        jy.all_money = 10000
                    else:
                        if jie < jy.all_money - 10000:
                            jy.all_money -= jie
                            jie = 0
                        else:
                            jie -= jy.all_money - 10000
                            jy.all_money = 10000
                    buy_flag = 1
                    still_day = 0
                    # if index > len(self.rd)-2:
                    #     print(self.p_SN, 'buy')
                status = 0
            
            if status < -1:
                if jy.pick > 0:
                    buy_flag = -1
                    jy_times += 1
                status = 0
            # if jy.pick > 0:
            #     loop.append(row['value'])
            min_v = min(min_v, row['value'])
            max_v = max(max_v, row['value'])
            still_day += 1

            if jy.pick > 0:
                if row['value'] < max_v:
                    temp = 1 - row['value'] / max_v
                    huice = max(huice, temp)

            if buy_flag > 0:
                all_p = jy.all_money / row['value']
                jy.buy(row['value'], all_p)
                loop.append([row['date'], row['value']])
                # loop.append([v_trend, k_trend, macd_trend])
                buy_v = max_v = min_v = row['value']
                buy_flag = 0
                # if index < len(self.rd)-3:
                #     if row['value'] > self.rd.iloc[index+3]['value'] * 1.1:
                #         print(self.p_SN, row['date'], 'err buy')
                if index > len(self.rd)-2:
                    money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                    if money_all > 9000 and win_times > 0.3 * jy_times:
                        print(self.p_SN, self.p_name, 'buy', row['date'] , win_times, ' / ', jy_times, money_all)
            if buy_flag < 0:
                if row['value'] > buy_v:
                    win_times += 1
                jy.sell(row['value'], jy.pick)
                loop.append([row['date'], row['value'], row['K'], row['rsi'], jy.all_money])
                buy_flag = 0
                # if index < len(self.rd)-3:
                #     if row['value'] < self.rd.iloc[index+3]['value'] * 0.9:
                #         print(self.p_SN, row['date'], 'err sell')
                if index > len(self.rd)-2 and self.p_SN in buy_list:
                    money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                    print(self.p_SN, self.p_name, 'sell', row['date'] , win_times, ' / ', jy_times, money_all)
            # print(row['date'], status)
        
        money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
        # if money_all < 9000:
        #     print(self.p_SN, money_all)
        # for i in loop:
        #     print(*i)
        # print(self.p_SN, win_times, ' / ', jy_times, money_all)
        # print(f'max huice: {huice * 100:.2f} %')
        return money_all,win_times,jy_times
    
    def way9(self):
        if self.rd.empty:
            return 0
        jy = jiaoyi()
        loop = []
        status = 0
        jy_times = 0
        max_v, min_v, buy_v = 0, 0, 0
        still_day = 0
        buy_flag = 0
        win_times = 0
        for index, row in self.rd.iterrows():
            if row['date'] < '2023':
                continue
            all_p = jy.all_money / row['value']
            if status > 1:
                if jy.all_money > 0:
                    buy_flag = 1
                status = 0
            elif status == 1:
                if row['value'] > row['boll_m']:
                    status = 2
            elif status == 0:
                if jy.all_money>0 and row['value'] > row['boll_u']:
                    status = 2
                if jy.pick > 0:
                    if row['value'] < row['boll_m'] and row['value'] < max_v * 0.9:
                        status = -2
                    if row['value'] < buy_v * 0.9:
                        status = -2
            elif status == -1:
                if row['value'] < row['boll_m']:
                    status = -2
                if row['value'] < max_v * 0.9:
                    status = -2
            if status < -1:
                if jy.pick > 0:
                    buy_flag = -1
                    jy_times += 1
                status = 0

            min_v = min(min_v, row['value'])
            max_v = max(max_v, row['value'])

            if buy_flag > 0:
                jy.buy(row['value'], all_p)
                loop.append(row['date'])
                loop.append(self.rd.iloc[index]['value'])
                buy_v = max_v = min_v = row['value']
                buy_flag = 0
            if buy_flag < 0:
                if row['value'] > buy_v:
                    win_times += 1
                jy.sell(row['value'], jy.pick)
                loop.append([row['date'], row['value'], row['K'], row['rsi'], jy.all_money])
                buy_flag = 0
        
        money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value']
        # if money_all < 9500:
        #     print(self.p_SN, loop, money_all)
        print(self.p_SN, win_times, ' / ', jy_times, money_all)
        return money_all,jy_times
    
    def way10(self):
        if self.rd.empty:
            return 0
        jy = jiaoyi()
        loop = []
        status = 0
        jy_times = 0
        win_times = 0
        max_v, min_v, buy_v = 0, 0, 0
        buy_flag = 0
        jie = 0
        huice = 0.0
        for index, row in self.rd.iterrows():
            if row['date'] < '2024' or row['date'] > '2027':
                continue
            if status == 0:
                if jy.all_money > 0:
                    # if has_up_cross_in_past_n_days(self.rd['K'].iloc[index-4:index+1], 30) and has_up_cross_in_past_n_days(self.rd['macd'].iloc[index-4:index+1], 0) and \
                    # has_up_boll_in_past_n_days(self.rd['value'].iloc[index-4:index+1], self.rd['boll_m'].iloc[index-4:index+1]) and has_boll_v_shape_recent(self.rd['boll_m'].iloc[index-4:index+1]):
                    #     status = 1
                    if row['K'] < 30 or row['rsi'] < 30:
                        status = 1
                    if self.rd.iloc[index-1]['K'] < 30 or self.rd.iloc[index-1]['rsi'] < 30:
                        status = 1
                if jy.pick > 0:
                    if row['value'] < row['boll_m'] and row['value'] < max_v * 0.9:
                        status = -2
                    if row['value'] < buy_v * 0.9:
                        status = -2
                    if row['value'] < self.rd.iloc[index-1]['value'] * 0.92:
                        status = -2
            
            if status == 1:
                status = 0
                v_trend = predict_trend(self.rd['value'].iloc[index-2:index+1])
                k_trend = predict_trend(self.rd['K'].iloc[index-2:index+1])
                macd_trend = predict_trend(self.rd['macd'].iloc[index-2:index+1])
                if (v_trend > 0.0) and (k_trend > 1.0) and (macd_trend > 0.0) and my_mean(self.rd['value'].iloc[index-4:index+1]) > my_mean(self.rd['value'].iloc[index-5:index]):
                    status = 2
            if status > 1:
                if jy.all_money > 1:
                    if jy.all_money < 10000:
                        jie += 10000 - jy.all_money
                        jy.all_money = 10000
                    else:
                        if jie < jy.all_money - 10000:
                            jy.all_money -= jie
                            jie = 0
                        else:
                            jie -= jy.all_money - 10000
                            jy.all_money = 10000
                    buy_flag = 1
                    still_day = 0
                status = 0
            
            if status < -1:
                if jy.pick > 0:
                    buy_flag = -1
                    jy_times += 1
                status = 0

            if jy.pick > 0:
                if row['value'] < max_v:
                    temp = 1 - row['value'] / max_v
                    huice = max(huice, temp)

            if buy_flag > 0:
                all_p = jy.all_money / row['value']
                jy.buy(row['value'], all_p)
                loop.append([row['date'], row['value']])
                # loop.append([v_trend, k_trend, macd_trend])
                buy_v = max_v = min_v = row['value']
                buy_flag = 0
                if index > len(self.rd)-3:
                    money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                    print(self.p_SN, self.p_name, 'buy', row['date'] , win_times, ' / ', jy_times, money_all)
            if buy_flag < 0:
                if row['value'] > buy_v:
                    win_times += 1
                jy.sell(row['value'], jy.pick)
                loop.append([row['date'], row['value'], row['K'], row['rsi'], jy.all_money])
                buy_flag = 0
                if index > len(self.rd)-2 and self.p_SN in buy_list:
                    money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                    print(self.p_SN, self.p_name, 'sell', row['date'] , win_times, ' / ', jy_times, money_all)
        
        money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
        # for i in loop:
        #     print(*i)
        return money_all,jy_times
    
    def way11(self):
        if self.rd.empty:
            return 0
        jy = jiaoyi()
        loop = []
        status = 0
        jy_times = 0
        win_times = 0
        max_v, min_v, buy_v = 0, 0, 0
        still_day = 0
        still_days = []
        macd_low = 0
        buy_flag = 0
        jie = 0
        huice = 0.0
        for index, row in self.rd.iterrows():
            if row['date'] < '2024' or row['date'] > '2027':
                continue
            if index < 40:
                continue
            week_now, week_index = find_previous_weekly_data(row['date'], self.rd_week)
            if week_now is None:
                print(self.p_SN, 'no weekly data')
                return 10000, 0, 0
            # week_v = daily_to_weekly(self.rd['value'].iloc[index-40:index+1])
            # week_macd = daily_to_weekly(self.rd['macd'].iloc[index-40:index+1])
            # week_diff = daily_to_weekly(self.rd['diff'].iloc[index-40:index+1])
            # week_dea = daily_to_weekly(self.rd['dea'].iloc[index-40:index+1])
            # week_boll_m = daily_to_weekly(self.rd['boll_m'].iloc[index-40:index+1])
            # week_boll_l = daily_to_weekly(self.rd['boll_l'].iloc[index-40:index+1])
            if status == 0:
                if jy.all_money > 0:
                    if row['K'] < 30 or row['rsi'] < 30:
                        status = 1
                    
                if jy.pick > 0:
                    still_day += 1
                    if row['value'] < row['boll_m'] and row['value'] < max_v * 0.9:
                        status = -2
                    if row['value'] < buy_v * 0.9:
                        status = -2
                    if row['value'] < self.rd.iloc[index-1]['value'] * 0.92:
                        status = -2
                    # if row['macd'] < 0 and row['diff'] < row['dea']:
                    #     status = -2
                    if macd_low > 3:
                        status = -2
            
            if status == 1:
                status = 1
                if week_now['boll_m_weekly'] > self.rd_week.iloc[week_index-1]['boll_m_weekly'] and week_now['macd_weekly'] > 0 and week_now['diff_weekly'] > week_now['dea_weekly']:
                    status = 2

            if status == 2:
                status = 1
                if row['boll_m'] > self.rd.iloc[index-1]['boll_m'] and row['macd'] > self.rd.iloc[index-1]['macd'] and \
                row['K'] > self.rd.iloc[index-1]['K']:
                    status = 3
                    
            if status > 2:
                if jy.all_money > 1:
                    if jy.all_money < 10000:
                        jie += 10000 - jy.all_money
                        jy.all_money = 10000
                    else:
                        if jie < jy.all_money - 10000:
                            jy.all_money -= jie
                            jie = 0
                        else:
                            jie -= jy.all_money - 10000
                            jy.all_money = 10000
                    buy_flag = 1
                    still_day = 0
                    # if index > len(self.rd)-2:
                    #     print(self.p_SN, 'buy')
                status = 0
            
            if status < -1:
                if jy.pick > 0:
                    buy_flag = -1
                    jy_times += 1
                status = 0
            # if jy.pick > 0:
            #     loop.append(row['value'])
            min_v = min(min_v, row['value'])
            max_v = max(max_v, row['value'])
            still_day += 1

            if jy.pick > 0:
                if row['value'] < max_v:
                    temp = 1 - row['value'] / max_v
                    huice = max(huice, temp)

            if buy_flag > 0:
                all_p = jy.all_money / row['value']
                jy.buy(row['value'], all_p)
                loop.append([row['date'], row['value']])
                # loop.append([v_trend, k_trend, macd_trend])
                buy_v = max_v = min_v = row['value']
                buy_flag = 0
                still_day = 0
                print(row['date'], row['value'], self.rd_week.iloc[week_index]['macd_weekly'])
                if index > len(self.rd)-2:
                    money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                    if money_all > 9000 and win_times > 0.3 * jy_times:
                        print(self.p_SN, self.p_name, 'buy', row['date'] , win_times, ' / ', jy_times, money_all)
            if buy_flag < 0:
                if row['value'] > buy_v:
                    win_times += 1
                jy.sell(row['value'], jy.pick)
                loop.append([row['date'], row['value'], row['K'], row['rsi'], jy.all_money])
                buy_flag = 0
                still_days.append(still_day)
                print(row['date'], ' sell ' , f"{((row['value'] - buy_v) / buy_v)*100:.2f}%" , still_day, 'days \n')
                if index > len(self.rd)-2 and self.p_SN in buy_list:
                    money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                    print(self.p_SN, self.p_name, 'sell', row['date'] , win_times, ' / ', jy_times, money_all)
            # print(row['date'], status)
        
        money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
        # if money_all < 9000:
        #     print(self.p_SN, money_all)
        # for i in loop:
        #     print(*i)
        # print(self.p_SN, win_times, ' / ', jy_times, money_all)
        # print(f'max huice: {huice * 100:.2f} %')
        return money_all,win_times,jy_times
    
    def way12(self):
        if self.rd.empty:
            return 0
        jy = jiaoyi()
        loop = []
        status = 0
        jy_times = 0
        win_times = 0
        max_v, min_v, buy_v = 0, 0, 0
        still_day = 0
        still_days = []
        macd_low = 0
        k_low = 30
        buy_flag = 0
        jie = 0
        huice = 0.0
        for index, row in self.rd.iterrows():
            if row['date'] < '2024' or row['date'] > '2027':
                continue
            if index < 40:
                continue
            week_now, week_index = find_previous_weekly_data(row['date'], self.rd_week)
            if week_now is None:
                print(self.p_SN, 'no weekly data')
                return 10000, 0, 0
            # week_v = daily_to_weekly(self.rd['value'].iloc[index-40:index+1])
            # week_macd = daily_to_weekly(self.rd['macd'].iloc[index-40:index+1])
            # week_diff = daily_to_weekly(self.rd['diff'].iloc[index-40:index+1])
            # week_dea = daily_to_weekly(self.rd['dea'].iloc[index-40:index+1])
            # week_boll_m = daily_to_weekly(self.rd['boll_m'].iloc[index-40:index+1])
            # week_boll_l = daily_to_weekly(self.rd['boll_l'].iloc[index-40:index+1])
            if status == 0:
                if jy.all_money > 0:
                    if row['K'] < 30 or row['rsi'] < 30:
                        status = 1
                if jy.pick > 0:
                    still_day += 1
                    if row['K'] < 30:
                        status = -2
                    if row['value'] < row['boll_m'] and row['value'] < max_v * 0.9:
                        status = -2
                    if row['value'] < buy_v * 0.9:
                        status = -2
                    if row['value'] < self.rd.iloc[index-1]['value'] * 0.92:
                        status = -2
                    # if row['macd'] < 0 and row['diff'] < row['dea']:
                    #     status = -2
                    if macd_low > 3:
                        status = -2
                    # if status == -2:
                    #     k_low = 30
            
            if status == 1:
                status = 1
                if row['K'] > self.rd.iloc[index-1]['K'] and row['macd'] > self.rd.iloc[index-1]['macd'] \
                 and row['K'] > 30:
                    status = 2
                # if row['macd'] < -1.5:
                #     status = 0

            if status == 2:
                status = 1
                if row['boll_l'] > self.rd.iloc[index-1]['boll_l'] and row['macd'] > self.rd.iloc[index-1]['macd'] and row['macd'] > 0:
                    status = 3
                if week_now['boll_m_weekly'] > self.rd_week.iloc[week_index-1]['boll_m_weekly']:
                    status = 3
                    
            if status > 2:
                if jy.all_money > 1:
                    if jy.all_money < 10000:
                        jie += 10000 - jy.all_money
                        jy.all_money = 10000
                    else:
                        if jie < jy.all_money - 10000:
                            jy.all_money -= jie
                            jie = 0
                        else:
                            jie -= jy.all_money - 10000
                            jy.all_money = 10000
                    buy_flag = 1
                    still_day = 0
                    # if index > len(self.rd)-2:
                    #     print(self.p_SN, 'buy')
                status = 0
            
            if status < -1:
                if jy.pick > 0:
                    buy_flag = -1
                    jy_times += 1
                status = 0
            # if jy.pick > 0:
            #     loop.append(row['value'])
            min_v = min(min_v, row['value'])
            max_v = max(max_v, row['value'])
            still_day += 1

            if jy.pick > 0:
                if row['value'] < max_v:
                    temp = 1 - row['value'] / max_v
                    huice = max(huice, temp)

            if buy_flag > 0:
                all_p = jy.all_money / row['value']
                jy.buy(row['value'], all_p)
                loop.append([row['date'], row['value']])
                # loop.append([v_trend, k_trend, macd_trend])
                buy_v = max_v = min_v = row['value']
                buy_flag = 0
                still_day = 0
                print(row['date'], row['value'], week_now['boll_m_weekly'] - self.rd_week.iloc[week_index-1]['boll_m_weekly'])
                # print(row['date'], row['value'], self.rd_week.iloc[week_index]['macd_weekly'])
                if index > len(self.rd)-2:
                    money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                    if money_all > 9000 and win_times > 0.3 * jy_times:
                        print(self.p_SN, self.p_name, 'buy', row['date'] , win_times, ' / ', jy_times, money_all)
            if buy_flag < 0:
                if row['value'] > buy_v:
                    win_times += 1
                jy.sell(row['value'], jy.pick)
                loop.append([row['date'], row['value'], row['K'], row['rsi'], jy.all_money])
                buy_flag = 0
                still_days.append(still_day)
                print(row['date'], ' sell ' , f"{((row['value'] - buy_v) / buy_v)*100:.2f}%" , still_day, 'days \n')
                if index > len(self.rd)-2 and self.p_SN in buy_list:
                    money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                    print(self.p_SN, self.p_name, 'sell', row['date'] , win_times, ' / ', jy_times, money_all)
            # print(row['date'], status)
        
        money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
        # if money_all < 9000:
        #     print(self.p_SN, money_all)
        # for i in loop:
        #     print(*i)
        # print(self.p_SN, win_times, ' / ', jy_times, money_all)
        # print(f'max huice: {huice * 100:.2f} %')
        return money_all,win_times,jy_times
    
    def way13(self):
        if self.rd.empty:
            return 0
        jy = jiaoyi()
        loop = []
        status = 0
        jy_times = 0
        win_times = 0
        max_v, min_v, buy_v = 0, 0, 0
        still_day = 0
        still_days = []
        buy_flag = 0
        jie = 0
        huice = 0.0
        for index, row in self.rd.iterrows():
            if row['date'] < '2024' or row['date'] > '2027':
                continue
            if index < 40:
                continue
            week_now, week_index = find_previous_weekly_data(row['date'], self.rd_week)
            if week_now is None:
                print(self.p_SN, 'no weekly data')
                return 10000, 0, 0
            if status == 0:
                if jy.all_money > 0:
                    if row['macd'] > self.rd.iloc[index-1]['macd'] > self.rd.iloc[index-2]['macd']:
                        status = 1
                if jy.pick > 0:
                    still_day += 1
                    if row['value'] < row['boll_m'] and row['value'] < max_v * 0.9:
                        status = -2
                    if row['value'] < buy_v * 0.9:
                        status = -2
                    if row['value'] < self.rd.iloc[index-1]['value'] * 0.92:
                        status = -2

            if status == 1:
                status = 1
                if row['diff'] > row['dea'] and self.rd.iloc[index-1]['diff'] < self.rd.iloc[index-1]['dea']:
                    status = 2

            if status == 2:
                status = 3
                if row['boll_l'] > self.rd.iloc[index-1]['boll_l'] and row['macd'] > self.rd.iloc[index-1]['macd'] and row['macd'] > 0:
                    status = 3
                if week_now['boll_m_weekly'] > self.rd_week.iloc[week_index-1]['boll_m_weekly']:
                    status = 3
                    
            if status > 2:
                if jy.all_money > 1:
                    if jy.all_money < 10000:
                        jie += 10000 - jy.all_money
                        jy.all_money = 10000
                    else:
                        if jie < jy.all_money - 10000:
                            jy.all_money -= jie
                            jie = 0
                        else:
                            jie -= jy.all_money - 10000
                            jy.all_money = 10000
                    buy_flag = 1
                    still_day = 0
                    # if index > len(self.rd)-2:
                    #     print(self.p_SN, 'buy')
                status = 0
            
            if status < -1:
                if jy.pick > 0:
                    buy_flag = -1
                    jy_times += 1
                status = 0
            # if jy.pick > 0:
            #     loop.append(row['value'])
            min_v = min(min_v, row['value'])
            max_v = max(max_v, row['value'])
            still_day += 1

            if jy.pick > 0:
                if row['value'] < max_v:
                    temp = 1 - row['value'] / max_v
                    huice = max(huice, temp)

            if buy_flag > 0:
                all_p = jy.all_money / row['value']
                jy.buy(row['value'], all_p)
                loop.append([row['date'], row['value']])
                # loop.append([v_trend, k_trend, macd_trend])
                buy_v = max_v = min_v = row['value']
                buy_flag = 0
                still_day = 0
                print(row['date'], row['value'], week_now['boll_m_weekly'] - self.rd_week.iloc[week_index-1]['boll_m_weekly'])
                # print(row['date'], row['value'], self.rd_week.iloc[week_index]['macd_weekly'])
                if index > len(self.rd)-2:
                    money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                    if money_all > 9000 and win_times > 0.3 * jy_times:
                        print(self.p_SN, self.p_name, 'buy', row['date'] , win_times, ' / ', jy_times, money_all)
            if buy_flag < 0:
                if row['value'] > buy_v:
                    win_times += 1
                jy.sell(row['value'], jy.pick)
                loop.append([row['date'], row['value'], row['K'], row['rsi'], jy.all_money])
                buy_flag = 0
                still_days.append(still_day)
                print(row['date'], ' sell ' , f"{((row['value'] - buy_v) / buy_v)*100:.2f}%" , still_day, 'days \n')
                if index > len(self.rd)-2 and self.p_SN in buy_list:
                    money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                    print(self.p_SN, self.p_name, 'sell', row['date'] , win_times, ' / ', jy_times, money_all)
            # print(row['date'], status)
        
        money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
        # if money_all < 9000:
        #     print(self.p_SN, money_all)
        # for i in loop:
        #     print(*i)
        # print(self.p_SN, win_times, ' / ', jy_times, money_all)
        # print(f'max huice: {huice * 100:.2f} %')
        return money_all,win_times,jy_times
    
    # macd up and macd > 0
    def way14(self):
        if self.rd.empty:
            return 0
        jy = jiaoyi()
        loop = []
        status = 0
        jy_times = 0
        win_times = 0
        max_v, min_v, buy_v = 0, 0, 0
        still_day = 0
        still_days = []
        buy_flag = 0
        K_max = 0
        jie = 0
        huice = 0.0
        macd_now = []
        macd_last = []
        finall = ''
        for index, row in self.rd.iterrows():
            if row['date'] < '2024' or row['date'] > '2027':
                continue
            if index < 40:
                continue
            if self.rd_week is None:
                return 10000, 0, 0
            week_now, week_index = find_previous_weekly_data(row['date'], self.rd_week)
            if week_now is None:
                print(self.p_SN, 'no weekly data')
                return 10000, 0, 0
            if macd_now == []:
                macd_now.append(row['macd'])
            else:
                if row['macd'] * macd_now[-1] < 0:
                    macd_last = macd_now
                    macd_now = [row['macd']]
                else:
                    macd_now.append(row['macd'])
            if status == 0:
                if jy.all_money > 0:
                    # if row['macd'] > 0 > self.rd.iloc[index-1]['macd']:
                    #     status = 1
                    # if week_now['macd_weekly'] > self.rd_week.iloc[week_index-1]['macd_weekly']:
                    #     status = 1
                    if row['K'] < 30:
                        status = 1
                        K_max = 30
                if jy.pick > 0:
                    still_day += 1
                    K_max = max(K_max, row['K'])
                    if row['value'] < row['boll_m'] and row['value'] < max_v * 0.9:
                        status = -2
                    if row['value'] < buy_v * 0.9:
                        status = -2
                    if row['value'] < self.rd.iloc[index-1]['value'] * 0.92:
                        status = -2
                    if still_day < 10 and row['macd'] < self.rd.iloc[index-1]['macd'] < self.rd.iloc[index-2]['macd']:
                        status = -2
                    if K_max > 70 and row['macd'] < self.rd.iloc[index-1]['macd'] < self.rd.iloc[index-2]['macd']:
                        status = -2
                    if K_max > 70 and row['K'] < 70:
                        status = -2
                    if row['K'] < 30 < self.rd.iloc[index-1]['K'] < self.rd.iloc[index-2]['K']:
                        status = -2
                    # if row['macd'] < 0 and self.rd.iloc[index-1]['macd'] < 0:
                    #     status = -2
                    # if self.rd_week.iloc[week_index]['macd_weekly'] < self.rd_week.iloc[week_index-1]['macd_weekly']:
                    #     status = -2
                    # if 10 > still_day > 5 and row['value'] < buy_v:
                    #     status = -2
                    # if row['macd'] < self.rd.iloc[index-1]['macd'] < self.rd.iloc[index-2]['macd']:
                    #     status = -2

            if status == 1:
                status = 1
                # if row['boll_m'] > self.rd.iloc[index - len(macd_last)]['boll_m']:
                #     status = 2
                # if row['macd'] > self.rd.iloc[index-1]['macd'] > self.rd.iloc[index-2]['macd'] and row['macd'] > 0:
                #     status = 2
                if row['K'] > self.rd.iloc[index-1]['K'] > self.rd.iloc[index-2]['K'] and row['K'] > 30:
                    status = 2

            if status == 2:
                status = 3
                if week_now['macd_weekly'] > self.rd_week.iloc[week_index-1]['macd_weekly'] > 0:
                    status = 3
                    
            if status > 2:
                if jy.all_money > 1:
                    if jy.all_money < 10000:
                        jie += 10000 - jy.all_money
                        jy.all_money = 10000
                    else:
                        if jie < jy.all_money - 10000:
                            jy.all_money -= jie
                            jie = 0
                        else:
                            jie -= jy.all_money - 10000
                            jy.all_money = 10000
                    buy_flag = 1
                    still_day = 0
                    # if index > len(self.rd)-2:
                    #     print(self.p_SN, 'buy')
                status = 0
            
            if status < -1:
                if jy.pick > 0:
                    buy_flag = -1
                    jy_times += 1
                status = 0
            # if jy.pick > 0:
            #     loop.append(row['value'])
            min_v = min(min_v, row['value'])
            max_v = max(max_v, row['value'])

            if jy.pick > 0:
                if row['value'] < max_v:
                    temp = 1 - row['value'] / max_v
                    huice = max(huice, temp)

            if buy_flag > 0:
                all_p = jy.all_money / row['value']
                jy.buy(row['value'], all_p)
                loop.append([row['date'], row['value']])
                # loop.append([v_trend, k_trend, macd_trend])
                buy_v = max_v = min_v = row['value']
                buy_flag = 0
                still_day = 0
                # print(row['date'], row['value'], week_now['macd_weekly'], self.rd_week.iloc[week_index-1]['macd_weekly'])
                # print(row['date'], row['value'], self.rd_week.iloc[week_index]['macd_weekly'])
                finall = row['date']
                money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                if index > len(self.rd)-2 and money_all > 10000:
                    print(self.p_SN, self.p_name, 'buy', row['date'] , win_times, ' / ', jy_times, money_all)
            if buy_flag < 0:
                if row['value'] > buy_v:
                    win_times += 1
                jy.sell(row['value'], jy.pick)
                loop.append([row['date'], row['value'], row['K'], row['rsi'], jy.all_money])
                buy_flag = 0
                still_days.append(still_day)
                # print(row['date'], ' sell ' , f"{((row['value'] - buy_v) / buy_v)*100:.2f}%" , still_day, 'days \n')
                finall = ''
                if index > len(self.rd)-3 and self.p_SN in buy_list:
                    money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                    print(self.p_SN, self.p_name, 'sell', row['date'] , win_times, ' / ', jy_times, money_all)
            # print(row['date'], status)
        
        if not finall == '':
            print('\n', self.p_SN, self.p_name, 'buy', finall , win_times, '/', jy_times, money_all)
        money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
        # if money_all < 9000:
        #     print(self.p_SN, money_all)
        # for i in loop:
        #     print(*i)
        # print(self.p_SN, win_times, ' / ', jy_times, money_all)
        # print(f'max huice: {huice * 100:.2f} %')
        return money_all,win_times,jy_times
    
    def way15(self):
        if self.rd.empty:
            return 0
        jy = jiaoyi()
        status = 0
        jy_times = 0
        win_times = 0
        max_v, min_v, buy_v = 0, 0, 0
        still_day = 0
        buy_flag = 0
        jie = 0
        finall = ''
        for index, row in self.rd.iterrows():
            if row['date'] < '2024' or row['date'] > '2027':
                continue
            if index < 40:
                continue
            week_now, week_index = find_previous_weekly_data(row['date'], self.rd_week)
            if week_now is None:
                print(self.p_SN, 'no weekly data')
                return 10000, 0, 0
            if status == 0:
                if jy.all_money > 0:
                    # if 10 < row['K'] < 30 and row['K'] > self.rd.iloc[index-1]['K'] and self.rd.iloc[index-1]['K'] < self.rd.iloc[index-2]['K'] < self.rd.iloc[index-3]['K']:
                    #     status = 1
                    if row['macd'] > self.rd.iloc[index-1]['macd'] > 0 > self.rd.iloc[index-2]['macd']:
                        status = 1
                    # if 20 < k_low < 30 and row['K'] > 30 > self.rd.iloc[index-1]['K']:
                    #     status = 1
                    # if row['macd'] > self.rd.iloc[index-1]['macd'] > 0 and row['boll_m'] > self.rd.iloc[index-1]['boll_m']:
                    #     status = 1
                if jy.pick > 0:
                    still_day += 1
                    # if row['K'] < 30:
                    #     status = -2
                    if row['value'] < row['boll_m'] and row['value'] < max_v * 0.9:
                        status = -2
                    if row['value'] < buy_v * 0.9:
                        status = -2
                    if row['value'] < self.rd.iloc[index-1]['value'] * 0.92:
                        status = -2
                    if row['macd'] < self.rd.iloc[index-1]['macd'] < self.rd.iloc[index-2]['macd'] and self.rd.iloc[index-2]['macd'] > 1:
                        status = -2
                    # if week_now['macd_weekly'] < self.rd_week.iloc[week_index-1]['macd_weekly']:
                    #     status = -2
                    # if row['macd'] < 0:
                    #     status = -2
                    # if still_day < 3 and row['macd'] < self.rd.iloc[index-1]['macd']:
                    #     status = -2
                    # if 70 < row['K'] < self.rd.iloc[index-1]['K'] and self.rd.iloc[index-1]['K'] > self.rd.iloc[index-2]['K'] > 70:
                    #     status = -2
            
            if status == 1:
                status = 1
                if week_now['macd_weekly'] > self.rd_week.iloc[week_index-1]['macd_weekly']:
                    status = 2
                # if row['boll_m'] > self.rd.iloc[index-1]['boll_m']:
                #     status = 2

                # if row['macd'] < -1.5:
                #     status = 0

            if status == 2:
                status = 3
                if week_now['macd_weekly'] > self.rd_week.iloc[week_index-1]['macd_weekly']:
                    status = 3
                    
            if status > 2:
                if jy.all_money > 1:
                    if jy.all_money < 10000:
                        jie += 10000 - jy.all_money
                        jy.all_money = 10000
                    else:
                        if jie < jy.all_money - 10000:
                            jy.all_money -= jie
                            jie = 0
                        else:
                            jie -= jy.all_money - 10000
                            jy.all_money = 10000
                    buy_flag = 1
                    still_day = 0
                    # if index > len(self.rd)-2:
                    #     print(self.p_SN, 'buy')
                status = 0
            
            if status < -1:
                if jy.pick > 0:
                    buy_flag = -1
                    jy_times += 1
                status = 0
            # if jy.pick > 0:
            #     loop.append(row['value'])
            min_v = min(min_v, row['value'])
            max_v = max(max_v, row['value'])

            if jy.pick > 0:
                if row['value'] < max_v:
                    temp = 1 - row['value'] / max_v

            if buy_flag > 0:
                all_p = jy.all_money / row['value']
                jy.buy(row['value'], all_p)
                buy_v = max_v = min_v = row['value']
                buy_flag = 0
                still_day = 0
                print(row['date'], row['value'], week_now['macd_weekly'], self.rd_week.iloc[week_index-1]['macd_weekly'])
                finall = row['date']
                if index > len(self.rd)-2:
                    money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                    if money_all > 9000 and win_times > 0.3 * jy_times:
                        print(self.p_SN, self.p_name, 'buy', row['date'] , win_times, ' / ', jy_times, money_all)
            if buy_flag < 0:
                if row['value'] > buy_v:
                    win_times += 1
                jy.sell(row['value'], jy.pick)
                buy_flag = 0
                print(row['date'], ' sell ' , f"{((row['value'] - buy_v) / buy_v)*100:.2f}%" , still_day, 'days \n')
                finall = ''
                if index > len(self.rd)-2 and self.p_SN in buy_list:
                    money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                    print(self.p_SN, self.p_name, 'sell', row['date'] , win_times, ' / ', jy_times, money_all)
        
        if not finall == '':
            print(self.p_SN, self.p_name, 'buy', finall , win_times, ' / ', jy_times, money_all)
        money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
        return money_all,win_times,jy_times
    
    def way16(self):
        if self.rd.empty:
            return 0
        jy = jiaoyi()
        loop = []
        status = 0
        jy_times = 0
        win_times = 0
        max_v, min_v, buy_v = 0, 0, 0
        still_day = 0
        still_days = []
        buy_flag = 0
        jie = 0
        huice = 0.0
        finall = ''
        for index, row in self.rd.iterrows():
            if row['date'] < '2024' or row['date'] > '2027':
                continue
            if index < 40:
                continue
            if self.rd_week is None:
                return 10000, 0, 0
            week_now, week_index = find_previous_weekly_data(row['date'], self.rd_week)
            if week_now is None:
                print(self.p_SN, 'no weekly data')
                return 10000, 0, 0
            if status == 0:
                if jy.all_money > 0:
                    # if week_now['macd_weekly'] > 0 > self.rd_week.iloc[week_index-1]['macd_weekly']:
                    #     status = 1
                    #     macd_all = 0
                    if row['macd'] > self.rd.iloc[index-2]['macd'] > 0 > self.rd.iloc[index-5]['macd'] and \
                        row['value'] > row['boll_m'] and self.rd.iloc[index-2]['value'] < self.rd.iloc[index-2]['boll_m']:
                        status = 1
                if jy.pick > 0:
                    still_day += 1
                    if row['value'] < row['boll_m'] and row['value'] < max_v * 0.9:
                        status = -2
                    if row['value'] < buy_v * 0.9:
                        status = -2
                    if row['value'] < self.rd.iloc[index-1]['value'] * 0.92:
                        status = -2

            if status == 1:
                status = 2
                # if week_now['macd_weekly'] >= 0:
                #     macd_all += week_now['macd_weekly']
                # else:
                #     status = 0
                # if macd_all > 0.1 and row['macd'] > self.rd.iloc[index-1]['macd'] and row['boll_m'] > self.rd.iloc[index-1]['boll_m']:
                #     status = 2
                # if row['macd'] > self.rd.iloc[index-1]['macd'] > self.rd.iloc[index-2]['macd'] and row['macd'] > 0:
                #     status = 2

            if status == 2:
                status = 3
                if week_now['boll_m_weekly'] > self.rd_week.iloc[week_index-1]['boll_m_weekly']:
                    status = 3
                    
            if status > 2:
                if jy.all_money > 1:
                    if jy.all_money < 10000:
                        jie += 10000 - jy.all_money
                        jy.all_money = 10000
                    else:
                        if jie < jy.all_money - 10000:
                            jy.all_money -= jie
                            jie = 0
                        else:
                            jie -= jy.all_money - 10000
                            jy.all_money = 10000
                    buy_flag = 1
                    still_day = 0
                status = 0
            
            if status < -1:
                if jy.pick > 0:
                    buy_flag = -1
                    jy_times += 1
                status = 0
            min_v = min(min_v, row['value'])
            max_v = max(max_v, row['value'])

            if jy.pick > 0:
                if row['value'] < max_v:
                    temp = 1 - row['value'] / max_v
                    huice = max(huice, temp)

            if buy_flag > 0:
                all_p = jy.all_money / row['value']
                jy.buy(row['value'], all_p)
                loop.append([row['date'], row['value']])
                buy_v = max_v = min_v = row['value']
                buy_flag = 0
                still_day = 0
                print(row['date'], row['value'], week_now['macd_weekly'], self.rd_week.iloc[week_index-1]['macd_weekly'])
                money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                finall = row['date']
                if index > len(self.rd)-5 and money_all > 10000:
                    print(self.p_SN, self.p_name, 'buy', row['date'] , win_times, ' / ', jy_times, money_all)
            if buy_flag < 0:
                if row['value'] > buy_v:
                    win_times += 1
                jy.sell(row['value'], jy.pick)
                loop.append([row['date'], row['value'], row['K'], row['rsi'], jy.all_money])
                buy_flag = 0
                still_days.append(still_day)
                print(row['date'], ' sell ' , f"{((row['value'] - buy_v) / buy_v)*100:.2f}%" , still_day, 'days \n')
                finall = ''
                if index > len(self.rd)-3 and self.p_SN in buy_list:
                    money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
                    print(self.p_SN, self.p_name, 'sell', row['date'] , win_times, ' / ', jy_times, money_all)
        
        money_all = jy.all_money + jy.pick * self.rd.iloc[-1]['value'] - jie
        # if not finall == '':
        #     print(self.p_SN, self.p_name, 'buy his:', finall , win_times, ' / ', jy_times, money_all)
        return money_all,win_times,jy_times
    

    # 5%
    def fenxi(self):
        if self.rd.empty:
            return 0
        for index, row in self.rd.iterrows():
            if row['date'] < '2024' or row['date'] > '2027':
                continue
            if index < 40:
                continue
            week_now, week_index = find_previous_weekly_data(row['date'], self.rd_week)
            if week_now is None:
                print(self.p_SN, 'no weekly data')
                return 10000, 0, 0
            if row['value'] - self.rd.iloc[index-1]['value'] > row['value'] * 0.05:
                print(row['date'], row['value'], row['K'], row['macd'], row['diff']-row['dea'], row['boll_m'], row['10-day'], week_now['macd_weekly'], week_now['boll_m_weekly'])
                print(last['date'], last['value'], last['K'], last['macd'], last['diff']-last['dea'], last['boll_m'], last['10-day'], last_week['macd_weekly'], last_week['boll_m_weekly'])
                print('\n')
            last = row
            last_week = week_now
        return 10000, 0, 0

    def find_min_point(self):
        return 0,0
        if self.rd.empty:
            return 0,0
        status = 0
        loop = []
        day = 10
        score = 0
        score_all = 0
        jy_times = 0
        buy_v = min_v = max_v = 0
        for index, row in self.rd.iterrows():
            if row['date'] < '2023' or row['date'] > '2027':
                continue
            if status > 2:
                loop = []
                loop.append(row['date'])
                score = 0
                status = 0
                jy_times += 1
                buy_v = min_v = max_v = row['value']
                loop.append(row['value'])
                if index < len(self.rd)-day:
                    for i in range(1, day):
                        min_v = min(min_v, self.rd.iloc[index+i]['value'])
                        max_v = max(max_v, self.rd.iloc[index+i]['value'])
                        loop.append(self.rd.iloc[index+i]['value'])
                        if self.rd.iloc[index+i]['value'] > buy_v:
                            score += 1
                    if self.rd.iloc[index+day]['value'] > buy_v * 0.95:
                        score = max(score, day/2)
                    if self.rd.iloc[index+day]['value'] > buy_v * 1.1:
                        score = day
                    if self.rd.iloc[index+day]['value'] < buy_v * 0.9:
                        score = 0
                    score_all += score
                # if score < 3:
                #     print(self.p_SN, loop, score)
            # if status == 1:
            #     if row['value'] > row['boll_m']:
            #         status = 2
            # if status == 0:
            #     if row['MA_Cross'] > 0 and row['MACD_Cross'] > 0 and row['KDJ_Cross'] > 0:
            #         status = 2
            if status == 0:
                if row['K'] < 30 or row['rsi'] < 30:
                    status = 1
            if status == 1:
                # if row['MA_Cross'] > 0 or row['MACD_Cross'] > 0 or row['KDJ_Cross'] > 0:
                #     status = 2
                if row['K'] > 50 and row['rsi'] > 50:
                    status = 0
                if row['KDJ_Cross'] > 0:
                    status = 2
            if status == 2:
                if row['KDJ_Cross'] < 0 or row['MACD_Cross'] < 0 or row['MA_Cross'] < 0:
                    status = 1
                if row['MACD_Cross'] > 0:
                    status = 3
            loop = []
            if row['KDJ_Cross'] > 0:
                loop.append(row['date'])
                if index < len(self.rd)-day:
                    for i in range(1, day):
                        loop.append(self.rd['value'][index+i])
                # print(loop)
        if jy_times == 0:
            return day/2, 0
        return [score_all/jy_times, jy_times]

    def find_max_point(self):
        if self.rd.empty:
            return 0
        max_v = -1
        day = 10
        score = 0
        score_all = 0
        jy_times = 0
        rsi_flag = 0
        boll_flag = 0
        for index, row in self.rd.iterrows():
            if row['date'] < '2023' or row['date'] > '2027':
                continue
            aa = []
            if boll_flag > 0 and rsi_flag > 0 and 1:
                max_v = row['value']
                a_min = a_max = row['value']
                jy_times += 1
                rsi_flag = 0
                boll_flag = 0
            else:
                if row['K'] > 80 and row['rsi'] > 80:
                    rsi_flag += 1
                # else:
                #     rsi_flag = max(0, rsi_flag-1)
                if rsi_flag > 0 and row['value'] < row['boll_m']:
                    boll_flag += 1
                else:
                    boll_flag = max(0, boll_flag-1)
            if max_v > 0 and index < len(self.rd)-day:
                for i in range(1, day+1):
                    aa.append(self.rd.iloc[index+i]['value'])
                    if self.rd.iloc[index+i]['value'] < max_v:
                        score += 1
                    a_min = min(self.rd.iloc[index+i]['value'], a_min)
                    a_max = max(self.rd.iloc[index+i]['value'], a_max)
                if self.rd.iloc[index+day]['value'] < max_v * 0.9:
                    score = day
                score_all += score
                # if score == 0 and a_min < min_v * 0.9:
                # print(self.p_SN, aa, score)
                score = 0
                max_v = -1
        if jy_times == 0:
            return day/2, 0
        return [score_all/jy_times, jy_times]

    def find_still_point(self):
        if self.rd.empty:
            return
        continue_win = 0
        last_row = 0
        for index, row in self.rd.iterrows():
            if row['date'] < '2024' or row['date'] > '2027':
                continue
            if row['value'] > last_row:
                continue_win += 1
            else:
                if continue_win > 3:
                    print(self.p_SN, row['date'], continue_win, self.rd.iloc[index-continue_win]['value'], row['value'])
                continue_win = 0

            if index > 1:
                last_row = row['value']
                
        
    def sum_revenue(self):
        return
    
# analysis 1:
# buy:
# 1. K < 30 or rsi < 30 and value < boll_l
# sell:
# 1. K > 80 and rsi > 80 and value > boll_m
# 2023-2026 total:199, avg:6.830159914148974, win:77.89, tm_all:6.67    (10 days)

# analysis 2:
# buy:
# sell:

# analysis 3:
# buy:
# 1. K < 30 or rsi < 30 and value < boll_l
# if status == 1:
#     if row['value'] < row['boll_l']:
#         status = 2
# if status == 0:
#     if row['K'] < 30 or row['rsi'] < 30:
#         status = 1
# total:199, avg:5.801103678586807, win:82.41, tm_all:22.31
# kdj_low pinghuan macd > 0 

# 整体跌，下午入场，整体涨，上午入场。
# really buy: buy > sell chose best buy. if sell > buy : not buy.

#300866 2024-0808
#603039 2025-1223