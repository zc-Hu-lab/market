#!/usr/bin/python3

import argparse
import pandas as pd
import tushare as ts
import sys
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

CONFIG = {
    'START_DATE_WEEKLY': '20100101',
    'KDJ_N': 9,
    'KDJ_M1': 3,
    'KDJ_M2': 3,
    'MACD_FAST': 12,
    'MACD_SLOW': 26,
    'MACD_SIGNAL': 9,
    'BOLL_N': 20,
    'BOLL_K': 2,
    'RSI_WINDOW': 14,
    'WEEKLY_DIR': '/opt/zack/master/week_data',
    'TUSHARE_TOKEN': 'f56d02fa39d85879dd2ce855faee78641ca923da5d6ebe978ad8affa',
}

class RateLimiter:
    """API调用频率限制器"""
    _last_call_time = None
    _call_count = 0
    _CALL_LIMIT = 50
    _WINDOW = 20  # 15秒窗口
    
    @classmethod
    def wait_if_needed(cls):
        """如果需要，等待直到可以继续调用API"""
        current_time = datetime.now()
        if cls._last_call_time is None:
            cls._last_call_time = current_time
            cls._call_count = 1
        else:
            elapsed = (current_time - cls._last_call_time).total_seconds()
            if elapsed < cls._WINDOW:
                cls._call_count += 1
                if cls._call_count > cls._CALL_LIMIT:
                    wait_time = cls._WINDOW - elapsed
                    print(f"达到API频率限制，等待 {wait_time:.1f} 秒...")
                    time.sleep(wait_time)
                    cls._last_call_time = datetime.now()
                    cls._call_count = 1
            else:
                cls._last_call_time = current_time
                cls._call_count = 1

class WeeklyDataUpdater:
    def __init__(self):
        ts.set_token(CONFIG['TUSHARE_TOKEN'])
        self.pro = ts.pro_api()
        
    def _call_with_rate_limit(self, func_name, *args, **kwargs):
        """带频率限制的API调用"""
        RateLimiter.wait_if_needed()
        try:
            func = getattr(self.pro, func_name)
            return func(*args, **kwargs)
        except Exception as e:
            print(f"调用API {func_name} 失败: {e}")
            return None
    
    def _get_ts_code(self, symbol):
        """根据股票代码生成tushare代码格式"""
        if symbol.startswith('6'):
            return f"{symbol}.SH"
        elif symbol.startswith('9'):
            return f"{symbol}.BJ"
        else:
            return f"{symbol}.SZ"
    
    def _calculate_all_indicators(self, df):
        """计算所有技术指标"""
        df = df.copy()
        
        # 计算KDJ
        if len(df) >= CONFIG['KDJ_N']:
            close = df['value']
            high = df['high']
            low = df['low']
            low_min = low.rolling(CONFIG['KDJ_N'], min_periods=1).min()
            high_max = high.rolling(CONFIG['KDJ_N'], min_periods=1).max()
            rsv = (close - low_min) / (high_max - low_min + 1e-8) * 100
            k = rsv.ewm(alpha=1/CONFIG['KDJ_M1'], adjust=False).mean()
            d = k.ewm(alpha=1/CONFIG['KDJ_M2'], adjust=False).mean()
            df['K_weekly'] = k
            df['D_weekly'] = d
            df['J_weekly'] = 3 * k - 2 * d
        else:
            df['K_weekly'] = np.nan
            df['D_weekly'] = np.nan
            df['J_weekly'] = np.nan
        
        # 计算MACD
        close = df['value']
        ema12 = close.ewm(span=CONFIG['MACD_FAST'], adjust=False).mean()
        ema26 = close.ewm(span=CONFIG['MACD_SLOW'], adjust=False).mean()
        diff = ema12 - ema26
        dea = diff.ewm(span=CONFIG['MACD_SIGNAL'], adjust=False).mean()
        df['macd_weekly'] = 2 * (diff - dea)
        df['diff_weekly'] = diff
        df['dea_weekly'] = dea
        
        # 计算BOLL
        if len(df) >= CONFIG['BOLL_N']:
            close = df['value']
            mid = close.rolling(CONFIG['BOLL_N']).mean()
            std = close.rolling(CONFIG['BOLL_N']).std()
            df['boll_u_weekly'] = mid + CONFIG['BOLL_K'] * std
            df['boll_m_weekly'] = mid
            df['boll_l_weekly'] = mid - CONFIG['BOLL_K'] * std
        else:
            df['boll_u_weekly'] = np.nan
            df['boll_m_weekly'] = np.nan
            df['boll_l_weekly'] = np.nan
        
        # 计算RSI
        close = df['value']
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=CONFIG['RSI_WINDOW'], min_periods=1).mean()
        avg_loss = loss.rolling(window=CONFIG['RSI_WINDOW'], min_periods=1).mean()
        rs = avg_gain / (avg_loss + 1e-8)
        df['rsi_weekly'] = 100 - (100 / (1 + rs))
        
        return df
    
    def _weekly_needs_update(self, weekly_data):
        """检查周线数据是否需要更新"""
        if weekly_data is None or weekly_data.empty:
            return True
        
        last_date = weekly_data['date'].iloc[-1]
        today = datetime.now()
        
        # 检查最近7天是否有新的交易周
        for days_ago in range(7):
            check_date = today - timedelta(days=days_ago)
            date_str = check_date.strftime('%Y-%m-%d')
            if date_str > last_date:
                return True
        
        return False
    
    def update_weekly_data(self, symbol, name=""):
        """更新单个股票的周线数据"""
        print(f"更新 {symbol} {name} 的周线数据...")
        
        weekly_path = Path(CONFIG['WEEKLY_DIR']) / f"{symbol}.csv"
        weekly_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 尝试读取现有数据
        existing_data = None
        if weekly_path.exists():
            try:
                existing_data = pd.read_csv(weekly_path, encoding="utf-8-sig")
                print(f"  读取到现有数据: {len(existing_data)} 行")
                
                # 检查是否需要更新
                if not self._weekly_needs_update(existing_data):
                    print(f"  {symbol} 周线数据已是最新，跳过")
                    return True, "已是最新"
            except Exception as e:
                print(f"  读取现有数据失败: {e}")
                existing_data = None
        
        # 获取周线数据
        ts_code = self._get_ts_code(symbol)
        
        try:
            # 如果有现有数据，只获取增量数据
            if existing_data is not None and not existing_data.empty:
                last_date = existing_data['date'].iloc[-1]
                start_date = (datetime.strptime(last_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y%m%d')
                print(f"  获取增量数据，起始日期: {start_date}")
                
                df_new = self._call_with_rate_limit(
                    'weekly',
                    ts_code=ts_code,
                    start_date=start_date,
                    fields='trade_date,open,high,low,close,vol,amount'
                )
                
                if df_new is None or df_new.empty:
                    print(f"  {symbol} 无新数据")
                    return True, "无新数据"
                
                # 处理新数据
                df_new = df_new.sort_values('trade_date')
                df_new['date'] = pd.to_datetime(df_new['trade_date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')
                df_new = df_new.rename(columns={'close': 'value', 'vol': 'volume'})
                
                # 计算新数据的指标
                df_new_calculated = self._calculate_all_indicators(df_new)
                
                # 合并数据
                combined_data = pd.concat([existing_data, df_new_calculated], ignore_index=True)
                combined_data = combined_data.drop_duplicates(subset=['date'], keep='last')
                combined_data = combined_data.sort_values('date').reset_index(drop=True)
                
                # 重新计算所有指标以确保一致性
                combined_data = self._calculate_all_indicators(combined_data)
                
                final_data = combined_data
                update_type = "增量更新"
                
            else:
                # 获取全部数据
                print(f"  获取全部历史数据")
                df_weekly = self._call_with_rate_limit(
                    'weekly',
                    ts_code=ts_code,
                    start_date=CONFIG['START_DATE_WEEKLY'],
                    fields='trade_date,open,high,low,close,vol,amount'
                )
                
                if df_weekly is None or df_weekly.empty:
                    print(f"  {symbol} 获取数据失败")
                    return False, "获取数据失败"
                
                # 处理数据
                df_weekly = df_weekly.sort_values('trade_date')
                df_weekly['date'] = pd.to_datetime(df_weekly['trade_date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')
                df_weekly = df_weekly.rename(columns={'close': 'value', 'vol': 'volume'})
                
                # 计算指标
                final_data = self._calculate_all_indicators(df_weekly)
                update_type = "全量更新"
            
            # 保存数据
            final_data.to_csv(weekly_path, index=False, encoding='utf-8-sig')
            print(f"  {symbol} 周线数据{update_type}完成: {len(final_data)} 行，最后日期: {final_data['date'].iloc[-1]}")
            
            return True, f"{update_type}成功"
            
        except Exception as e:
            print(f"  {symbol} 更新失败: {e}")
            return False, f"更新失败: {str(e)}"

def update_all_weekly_data(sn):
    """更新所有股票的周线数据"""
    updater = WeeklyDataUpdater()

    if sn != '':
        print(f"更新股票代码 {sn} 的周线数据...")
        success, message = updater.update_weekly_data(sn)
        print(f"更新 {sn} {message}")
        return
    
    # 从数据目录获取所有股票代码
    data_dir = Path('/opt/zack/master/data')
    if not data_dir.exists():
        print(f"数据目录不存在: {data_dir}")
        return
    
    csv_files = list(data_dir.glob("*.csv"))
    print(f"找到 {len(csv_files)} 个股票数据文件")
    
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    for i, csv_file in enumerate(csv_files, 1):
        symbol = csv_file.stem
        
        print(f"\n[{i}/{len(csv_files)}] ", end="")
        success, message = updater.update_weekly_data(symbol)
        
        if success:
            if "已是最新" in message:
                skip_count += 1
            else:
                success_count += 1
        else:
            fail_count += 1
        
        # 避免API调用过于频繁
        if i < len(csv_files):
            time.sleep(0.5)
    
    print(f"\n{'='*50}")
    print(f"更新完成:")
    print(f"  成功更新: {success_count} 个")
    print(f"  跳过(已最新): {skip_count} 个")
    print(f"  失败: {fail_count} 个")
    print(f"  总计: {len(csv_files)} 个")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--sn', type=str, default = '')
    args = parser.parse_args()
    print("开始更新所有股票的周线数据...")
    print("=" * 50)

    update_all_weekly_data(args.sn)

    print("\n周线数据更新完成！")
