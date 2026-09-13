import pandas as pd
import numpy as np
from pathlib import Path

from my_name import week_macd_list
from my_name import week_macd_list2
from my_name import day_diff_dea_list
from my_name import day3_macd_list


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

class get_buypoint:
    def __init__(self, p_SN, p_name = 'xxx', dt_start = '2026', dt_end = '2027'):
        self.p_SN = p_SN
        self.p_name = p_name
        if self.p_SN not in week_macd_list:
            return
        file_name = f'/opt/zack/master/data/{self.p_SN}.csv'
        self.rd = pd.DataFrame()
        if Path(file_name).is_file():
            self.rd = pd.read_csv(file_name, encoding="utf-8-sig")
            if not self.rd.empty:
                self.rd["date"] = pd.to_datetime(self.rd["date"])
                dt_start = pd.to_datetime(dt_start)
                dt_end = pd.to_datetime(dt_end)
                self.rd = self.rd[
                    (self.rd["date"] >= dt_start) &
                    (self.rd["date"] <= dt_end)
                ].reset_index(drop=True)
        self.res = pd.DataFrame()


    def get_buy_point(self):
        # if self.p_SN == '603039': return self.way_603039()
        if self.p_SN in week_macd_list: return self.way_macd()
        # if self.p_SN in week_macd_list2: return self.way_week_macd2()
        # if self.p_SN in day_diff_dea_list: return self.way_diff_dea()
        # if self.p_SN in day3_macd_list: return self.way_3day_macd()

    # macd up and macd > 0
    def way_macd(self):
        buy_flag = 0
        status = 0

        if self.rd.empty:
            return 0
        for index, row in self.rd.iterrows():
            n_val = self.rd.iloc[index-1]
            if status == 0:
                if buy_flag == 0:
                    if row['macd'] > n_val['macd'] and row['macd'] > 0:
                        status = 1
                if buy_flag > 0:
                    max_v = max(max_v, row['value'])
                    if row['value'] < row['boll_m'] and row['value'] < max_v * 0.9:
                        status = -2
                    if row['value'] < buy_v * 0.9:
                        status = -2
                    if row['value'] < self.rd.iloc[index-1]['value'] * 0.92:
                        status = -2

            if status == 1:
                status = 2

            if status == 2:
                status = 3
                    
            if status > 2:
                buy_flag = 1
                buy_v = max_v = row['value']
                status = 0
            
            if status < -1:
                buy_flag = 0
                status = 0

        return buy_flag
    