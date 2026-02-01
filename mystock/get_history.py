#!/usr/bin/python3

import pandas as pd
import tushare as ts
from datetime import datetime as dt, timedelta
import sys
import time
import argparse

ts.set_token('5c940b85806741e9a4aedd3495a9fd43c11a0542d4b3ad641c1ef949')
pro = ts.pro_api()

date_add_one = lambda d: (dt.strptime(d, '%Y%m%d') + timedelta(days=1)).strftime('%Y%m%d')

class GetHistory:
    def __init__(self, start_date, end_date):
        self.res = []
        file_name = f'history_{start_date}_{end_date}.csv'
        self.get_history(start_date, end_date)
        
        # 修复：正确合并数据
        all_dfs = []
        for date_str, df in self.res:
            if df is not None and not df.empty:
                all_dfs.append(df)
        
        if all_dfs:
            result_df = pd.concat(all_dfs, ignore_index=True)
            result_df.to_csv(file_name, index=False, encoding='utf-8-sig')
            print(f"数据已保存到 {file_name}，共 {len(result_df)} 条记录")
        else:
            print("没有获取到数据")

    def get_history(self, start_date, end_date):
        current_date = start_date
        day_count = 0
        printed_percents = set()
        date_all = (dt.strptime(end_date, '%Y%m%d') - dt.strptime(start_date, '%Y%m%d')).days
        while current_date <= end_date:
            try:
                # 显示进度
                percent = int((day_count / date_all) * 100)
                if percent in [5, 10, 20, 40, 60, 80, 100] and percent not in printed_percents:
                    print(f"🎯 {percent}% 完成: 第 {day_count}/{date_all} 天")
                    printed_percents.add(percent)
                df = pro.daily(trade_date=current_date)
                if df is not None and not df.empty:
                    # 修复：先保存当前日期的数据，再递增日期
                    self.res.append([current_date, df])
            except Exception as e:
                print(f"  {current_date}: 获取失败 - {e}")
            
            # 修复：日期递增应该在获取数据之后
            current_date = date_add_one(current_date)
            day_count += 1
            time.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_date', '-s', type=str, default = '20240101')
    parser.add_argument('--end_date', '-e', type=str, default = str(dt.now().date()).replace('-', ''))
    args = parser.parse_args()
    print(f"获取 {args.start_date} 到 {args.end_date} 的数据")
    history = GetHistory(args.start_date, args.end_date)