#!/usr/bin/python3
# -*- coding: utf-8 -*-
# stock_analysis_system.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
import os
import warnings
warnings.filterwarnings('ignore')

class HistoryDataReader:
    """历史数据读取器"""
    
    def __init__(self, file_path='history_20260101_20260201.csv'):
        """
        初始化历史数据读取器
        
        参数:
        file_path: 历史数据文件路径
        """
        self.file_path = file_path
        self.data = None
        self.load_history_data()
    
    def load_history_data(self):
        """加载历史数据"""
        print(f"📂📂 正在加载历史数据文件: {self.file_path}")
        
        try:
            # 读取CSV文件
            self.data = pd.read_csv(self.file_path, encoding='utf-8-sig')
            print(f"✅ 数据加载成功!")
            print(f"   文件形状: {self.data.shape}")
            print(f"   时间范围: {self.data['trade_date'].min()} 到 {self.data['trade_date'].max()}")
            print(f"   股票数量: {self.data['ts_code'].nunique()}")
            
            # 数据清洗和预处理
            self.preprocess_data()
            
        except FileNotFoundError:
            print(f"❌❌ 文件不存在: {self.file_path}")
            print("请确保文件路径正确")
        except Exception as e:
            print(f"❌❌ 加载数据失败: {e}")
    
    def preprocess_data(self):
        """数据预处理"""
        if self.data is None or self.data.empty:
            return
        
        print(f"\n🧹🧹🧹🧹 数据预处理...")
        
        # 1. 确保日期格式正确
        if 'trade_date' in self.data.columns:
            # 从图片看，trade_date是YYYYMMDD格式
            self.data['trade_date'] = pd.to_datetime(self.data['trade_date'].astype(str), format='%Y%m%d')
        
        # 2. 重命名列以确保一致性
        column_mapping = {
            'ts_code': 'symbol',
            'trade_date': 'date',
            'open': 'open',
            'high': 'high', 
            'low': 'low',
            'close': 'close',
            'pre_close': 'pre_close',
            'change': 'change',
            'pct_chg': 'pct_change',
            'vol': 'volume',
            'amount': 'amount'
        }
        
        # 只重命名存在的列，避免重复列名
        rename_dict = {}
        for old, new in column_mapping.items():
            if old in self.data.columns and new not in self.data.columns:
                rename_dict[old] = new
        
        self.data = self.data.rename(columns=rename_dict)
        
        # 3. 如果date列不存在，但trade_date存在，则使用trade_date作为date
        if 'date' not in self.data.columns and 'trade_date' in self.data.columns:
            self.data['date'] = self.data['trade_date']
        
        # 4. 处理缺失值
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount', 'pct_change']
        for col in numeric_cols:
            if col in self.data.columns:
                # 用前向填充处理缺失值
                self.data[col] = self.data[col].ffill()
        
        # 5. 按日期和股票代码排序
        if 'symbol' in self.data.columns and 'date' in self.data.columns:
            self.data = self.data.sort_values(['symbol', 'date']).reset_index(drop=True)
        
        print(f"✅ 预处理完成")
        print(f"   处理后形状: {self.data.shape}")
        print(f"   可用列: {list(self.data.columns)}")

    def get_stock_data(self, symbol, start_date=None, end_date=None):
        """
        获取单只股票的历史数据
        
        参数:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        """
        if self.data is None:
            return None
        
        # 过滤指定股票
        stock_data = self.data[self.data['symbol'] == symbol].copy()
        
        if stock_data.empty:
            print(f"⚠️ 未找到股票 {symbol} 的数据")
            return None
        
        # 按日期过滤
        if start_date:
            if isinstance(start_date, str):
                start_date = pd.to_datetime(start_date)
            stock_data = stock_data[stock_data['date'] >= start_date]
        
        if end_date:
            if isinstance(end_date, str):
                end_date = pd.to_datetime(end_date)
            stock_data = stock_data[stock_data['date'] <= end_date]
        
        # 设置日期为索引
        if not stock_data.empty and 'date' in stock_data.columns:
            # 确保date列是唯一的
            if stock_data['date'].duplicated().any():
                print(f"⚠️ 警告: 股票 {symbol} 存在重复日期，将去重处理")
                stock_data = stock_data.drop_duplicates(subset=['date'], keep='last')
            
            stock_data = stock_data.set_index('date').sort_index()
        
        return stock_data

    def get_multi_stock_data(self, symbols=None, start_date=None, end_date=None):
        """
        获取多只股票数据
        
        返回:
        dict: {股票代码: DataFrame}
        """
        if self.data is None:
            return {}
        
        if symbols is None:
            # 获取所有股票
            symbols = self.data['symbol'].unique()[:10]  # 限制数量避免内存问题
        
        stock_data_dict = {}
        for symbol in symbols:
            df = self.get_stock_data(symbol, start_date, end_date)
            if df is not None and not df.empty:
                stock_data_dict[symbol] = df
        
        return stock_data_dict
    
    def get_date_range(self):
        """获取数据的时间范围"""
        if self.data is None or 'date' not in self.data.columns:
            return None, None
        
        min_date = self.data['date'].min()
        max_date = self.data['date'].max()
        
        return min_date, max_date
    
    def get_stock_list(self):
        """获取股票列表"""
        if self.data is None or 'symbol' not in self.data.columns:
            return []
        
        return sorted(self.data['symbol'].unique())
    
    def get_daily_market_data(self, date):
        """
        获取指定日期的全市场数据
        
        参数:
        date: 日期字符串或datetime对象
        """
        if self.data is None:
            return None
        
        if isinstance(date, str):
            date = pd.to_datetime(date)
        
        daily_data = self.data[self.data['date'] == date].copy()
        
        return daily_data
    

class PricePointAnalyzer:
    """点位分析器（基于历史数据）"""
    
    def __init__(self, data_reader, symbol):
        """
        初始化点位分析器
        
        参数:
        data_reader: HistoryDataReader实例
        symbol: 股票代码
        """
        self.data_reader = data_reader
        self.symbol = symbol
        self.stock_data = data_reader.get_stock_data(symbol)
        
    def calculate_all_levels(self, lookback_days=60):
        """计算所有技术点位"""
        if self.stock_data is None or self.stock_data.empty:
            print(f"⚠️ 没有 {self.symbol} 的数据")
            return None
        
        # 获取最近的数据
        recent_data = self.stock_data.tail(lookback_days)
        
        if recent_data.empty:
            return None
        
        # 计算当前价格
        current_price = recent_data['close'].iloc[-1]
        
        # 计算各种技术点位
        levels = {
            '股票代码': self.symbol,
            '分析日期': datetime.now().strftime('%Y-%m-%d'),
            '数据截止日期': recent_data.index[-1].strftime('%Y-%m-%d'),
            '当前价格': current_price,
            '今日开盘': recent_data['open'].iloc[-1] if 'open' in recent_data.columns else None,
            '今日最高': recent_data['high'].iloc[-1] if 'high' in recent_data.columns else None,
            '今日最低': recent_data['low'].iloc[-1] if 'low' in recent_data.columns else None,
            '昨日收盘': recent_data['pre_close'].iloc[-1] if 'pre_close' in recent_data.columns else None,
            '涨跌幅': recent_data['pct_change'].iloc[-1] if 'pct_change' in recent_data.columns else None,
        }
        
        # 计算均线
        levels.update(self.calculate_moving_averages(recent_data))
        
        # 计算支撑阻力
        levels.update(self.calculate_support_resistance(recent_data))
        
        # 计算斐波那契
        levels.update(self.calculate_fibonacci_levels(recent_data))
        
        # 计算布林带
        levels.update(self.calculate_bollinger_bands(recent_data))
        
        return levels
    
    def calculate_moving_averages(self, data):
        """计算移动平均线"""
        closes = data['close']
        
        ma_values = {}
        periods = [5, 10, 20, 30, 60, 120, 250]
        
        for period in periods:
            if len(closes) >= period:
                ma = closes.tail(period).mean()
                ma_values[f'{period}日均线'] = ma
        
        return ma_values
    
    def calculate_support_resistance(self, data, window=20):
        """计算支撑位和阻力位"""
        closes = data['close']
        highs = data['high']
        lows = data['low']
        
        # 计算支撑位（局部低点）
        support_levels = []
        for i in range(window, len(lows) - window):
            if lows.iloc[i] == lows.iloc[i-window:i+window].min():
                support_levels.append(lows.iloc[i])
        
        # 计算阻力位（局部高点）
        resistance_levels = []
        for i in range(window, len(highs) - window):
            if highs.iloc[i] == highs.iloc[i-window:i+window].max():
                resistance_levels.append(highs.iloc[i])
        
        # 去重并排序
        support_levels = sorted(list(set(support_levels)))
        resistance_levels = sorted(list(set(resistance_levels)))
        
        return {
            '支撑位1': support_levels[-1] if support_levels else None,
            '支撑位2': support_levels[-2] if len(support_levels) >= 2 else None,
            '支撑位3': support_levels[-3] if len(support_levels) >= 3 else None,
            '阻力位1': resistance_levels[-1] if resistance_levels else None,
            '阻力位2': resistance_levels[-2] if len(resistance_levels) >= 2 else None,
            '阻力位3': resistance_levels[-3] if len(resistance_levels) >= 3 else None,
        }
    
    def calculate_fibonacci_levels(self, data):
        """计算斐波那契回撤位"""
        highs = data['high']
        lows = data['low']
        
        if len(highs) < 2 or len(lows) < 2:
            return {}
        
        high_point = highs.max()
        low_point = lows.min()
        diff = high_point - low_point
        
        if diff == 0:
            return {}
        
        fib_levels = {
            '斐波那契0.0': high_point,
            '斐波那契0.236': high_point - diff * 0.236,
            '斐波那契0.382': high_point - diff * 0.382,
            '斐波那契0.5': high_point - diff * 0.5,
            '斐波那契0.618': high_point - diff * 0.618,
            '斐波那契0.786': high_point - diff * 0.786,
            '斐波那契1.0': low_point,
        }
        
        return fib_levels
    
    def calculate_bollinger_bands(self, data, window=20, std_dev=2):
        """计算布林带"""
        closes = data['close']
        
        if len(closes) < window:
            return {}
        
        sma = closes.rolling(window=window).mean()
        std = closes.rolling(window=window).std()
        
        return {
            '布林带中轨': sma.iloc[-1],
            '布林带上轨': sma.iloc[-1] + std.iloc[-1] * std_dev,
            '布林带下轨': sma.iloc[-1] - std.iloc[-1] * std_dev,
            '布林带宽度': (std.iloc[-1] * std_dev * 2) / sma.iloc[-1] if sma.iloc[-1] != 0 else 0
        }
    
    def generate_point_analysis_report(self):
        """生成点位分析报告"""
        levels = self.calculate_all_levels()
        
        if levels is None:
            return "无法生成分析报告"
        
        report = []
        report.append("=" * 60)
        report.append(f"📈📈 股票点位分析报告 - {self.symbol}")
        report.append("=" * 60)
        report.append(f"分析时间: {levels['分析日期']}")
        report.append(f"数据截止: {levels['数据截止日期']}")
        report.append(f"当前价格: {levels['当前价格']:.2f}")
        
        if levels.get('涨跌幅') is not None:
            report.append(f"今日涨跌: {levels['涨跌幅']:+.2f}%")
        
        # 价格水平
        report.append("\n💵💵 价格水平:")
        report.append(f"  开盘价: {levels.get('今日开盘', 'N/A'):.2f}")
        report.append(f"  最高价: {levels.get('今日最高', 'N/A'):.2f}")
        report.append(f"  最低价: {levels.get('今日最低', 'N/A'):.2f}")
        report.append(f"  昨日收盘: {levels.get('昨日收盘', 'N/A'):.2f}")
        
        # 均线
        report.append("\n📊📊 移动平均线:")
        for key, value in levels.items():
            if '日均线' in key and value is not None:
                diff = (levels['当前价格'] - value) / value * 100
                report.append(f"  {key}: {value:.2f} ({diff:+.2f}%)")
        
        # 支撑阻力
        report.append("\n📈📈 支撑阻力位:")
        for i in range(1, 4):
            support_key = f'支撑位{i}'
            resistance_key = f'阻力位{i}'
            if support_key in levels and levels[support_key] is not None:
                diff = (levels['当前价格'] - levels[support_key]) / levels['当前价格'] * 100
                report.append(f"  {support_key}: {levels[support_key]:.2f} ({diff:+.2f}%)")
        
        for i in range(1, 4):
            resistance_key = f'阻力位{i}'
            if resistance_key in levels and levels[resistance_key] is not None:
                diff = (levels[resistance_key] - levels['当前价格']) / levels['当前价格'] * 100
                report.append(f"  {resistance_key}: {levels[resistance_key]:.2f} ({diff:+.2f}%)")
        
        # 斐波那契
        report.append("\n🔢🔢 斐波那契回撤位:")
        fib_keys = ['斐波那契0.0', '斐波那契0.236', '斐波那契0.382', 
                   '斐波那契0.5', '斐波那契0.618', '斐波那契0.786', '斐波那契1.0']
        for key in fib_keys:
            if key in levels and levels[key] is not None:
                diff = (levels['当前价格'] - levels[key]) / levels[key] * 100
                report.append(f"  {key}: {levels[key]:.2f} ({diff:+.2f}%)")
        
        # 布林带
        report.append("\n📉📉 布林带:")
        if '布林带上轨' in levels and levels['布林带上轨'] is not None:
            bb_keys = ['布林带上轨', '布林带中轨', '布林带下轨']
            for key in bb_keys:
                if key in levels and levels[key] is not None:
                    diff = (levels['当前价格'] - levels[key]) / levels[key] * 100
                    report.append(f"  {key}: {levels[key]:.2f} ({diff:+.2f}%)")
        
        report.append("=" * 60)
        
        return "\n".join(report)


class PositionManager:
    """仓位管理器（基于历史回测）"""
    
    def __init__(self, initial_capital=1000000, data_reader=None):
        """
        初始化仓位管理器
        
        参数:
        initial_capital: 初始资金
        data_reader: HistoryDataReader实例
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.data_reader = data_reader
        
        # 持仓记录
        self.positions = {}  # {symbol: 持仓信息}
        self.trade_history = []  # 交易记录
        self.portfolio_history = []  # 组合历史
        
        # 参数设置
        self.params = {
            'max_position_ratio': 0.3,  # 最大仓位比例
            'max_stock_ratio': 0.1,     # 单只股票最大比例
            'stop_loss_pct': 0.08,      # 止损比例
            'take_profit_pct': 0.20,    # 止盈比例
            'commission_rate': 0.0003,  # 佣金率
        }
    
    def calculate_position_size(self, symbol, price, signal_strength=0.5):
        """
        计算仓位大小（基于历史波动率）
        
        参数:
        signal_strength: 信号强度 0-1
        """
        if self.data_reader is None:
            return 0
        
        # 获取股票历史数据
        stock_data = self.data_reader.get_stock_data(symbol)
        if stock_data is None or stock_data.empty:
            return 0
        
        # 计算历史波动率
        returns = stock_data['close'].pct_change().dropna()
        if len(returns) < 20:
            volatility = 0.02  # 默认波动率
        else:
            volatility = returns.std() * np.sqrt(252)  # 年化波动率
        
        # 基于波动率计算风险
        risk_amount = self.current_capital * 0.02 * signal_strength  # 2%基础风险
        
        # 计算止损距离
        stop_loss_distance = price * self.params['stop_loss_pct']
        
        # 计算股数
        if stop_loss_distance > 0:
            shares = risk_amount / stop_loss_distance
        else:
            shares = 0
        
        # 检查仓位限制
        position_value = shares * price
        max_position_value = self.current_capital * self.params['max_stock_ratio'] * signal_strength
        
        if position_value > max_position_value:
            shares = max_position_value / price
        
        return int(shares)
    
    def execute_backtest_trade(self, date, symbol, action, price, shares, reason=""):
        """
        执行回测交易
        
        参数:
        date: 交易日期
        action: 'BUY' 或 'SELL'
        """
        if action == 'BUY':
            return self.execute_backtest_buy(date, symbol, price, shares, reason)
        elif action == 'SELL':
            return self.execute_backtest_sell(date, symbol, price, shares, reason)
    
    def execute_backtest_buy(self, date, symbol, price, shares, reason=""):
        """执行回测买入"""
        # 计算买入金额（含佣金）
        buy_amount = shares * price
        commission = buy_amount * self.params['commission_rate']
        total_cost = buy_amount + commission
        
        # 检查资金是否足够
        if total_cost > self.current_capital:
            print(f"❌❌ {date} 买入失败: 资金不足")
            return False
        
        # 检查仓位限制
        current_position_value = sum(pos['current_value'] for pos in self.positions.values())
        if current_position_value + buy_amount > self.current_capital * self.params['max_position_ratio']:
            print(f"❌❌ {date} 买入失败: 超过总仓位限制")
            return False
        
        # 记录交易
        trade_record = {
            'date': date,
            'action': 'BUY',
            'symbol': symbol,
            'price': price,
            'shares': shares,
            'amount': buy_amount,
            'commission': commission,
            'reason': reason
        }
        self.trade_history.append(trade_record)
        
        # 更新资金
        self.current_capital -= total_cost
        
        # 更新持仓
        if symbol in self.positions:
            # 加仓
            pos = self.positions[symbol]
            total_shares = pos['shares'] + shares
            avg_price = ((pos['avg_price'] * pos['shares']) + (price * shares)) / total_shares
            
            self.positions[symbol] = {
                'shares': total_shares,
                'avg_price': avg_price,
                'current_price': price,
                'current_value': total_shares * price,
                'buy_count': pos['buy_count'] + 1,
                'last_buy_date': date
            }
        else:
            # 新建持仓
            self.positions[symbol] = {
                'shares': shares,
                'avg_price': price,
                'current_price': price,
                'current_value': shares * price,
                'buy_count': 1,
                'last_buy_date': date
            }
        
        print(f"✅ {date} 买入 {symbol} {shares}股 @ {price:.2f}")
        return True
    
    def execute_backtest_sell(self, date, symbol, price, shares, reason=""):
        """执行回测卖出"""
        if symbol not in self.positions:
            print(f"❌❌ {date} 卖出失败: 没有持仓")
            return False
        
        position = self.positions[symbol]
        
        if shares > position['shares']:
            print(f"❌❌ {date} 卖出失败: 卖出数量超过持仓")
            return False
        
        # 计算卖出金额（含佣金）
        sell_amount = shares * price
        commission = sell_amount * self.params['commission_rate']
        net_amount = sell_amount - commission
        
        # 计算盈亏
        buy_value = position['avg_price'] * shares
        profit_loss = net_amount - buy_value
        profit_pct = (profit_loss / buy_value) * 100 if buy_value > 0 else 0
        
        # 记录交易
        trade_record = {
            'date': date,
            'action': 'SELL',
            'symbol': symbol,
            'price': price,
            'shares': shares,
            'amount': sell_amount,
            'commission': commission,
            'profit_loss': profit_loss,
            'profit_pct': profit_pct,
            'reason': reason
        }
        self.trade_history.append(trade_record)
        
        # 更新资金
        self.current_capital += net_amount
        
        # 更新持仓
        if shares == position['shares']:
            # 清仓
            del self.positions[symbol]
        else:
            # 减仓
            position['shares'] -= shares
            position['current_value'] = position['shares'] * price
        
        print(f"✅ {date} 卖出 {symbol} {shares}股 @ {price:.2f}")
        print(f"   盈亏: {profit_loss:+.2f} ({profit_pct:+.2f}%)")
        
        return True
    
    def update_portfolio_value(self, date, market_data=None):
        """更新组合价值"""
        total_value = self.current_capital
        
        # 如果有持仓，更新持仓价值
        for symbol, position in self.positions.items():
            if market_data is not None and symbol in market_data:
                # 使用市场数据更新价格
                current_price = market_data[symbol]
                position['current_price'] = current_price
                position['current_value'] = position['shares'] * current_price
            
            total_value += position['current_value']
        
        # 记录组合价值
        portfolio_record = {
            'date': date,
            'cash': self.current_capital,
            'positions_value': total_value - self.current_capital,
            'total_value': total_value,
            'positions_count': len(self.positions)
        }
        self.portfolio_history.append(portfolio_record)
        
        return total_value
    
    def get_portfolio_summary(self):
        """获取组合摘要"""
        if not self.portfolio_history:
            return {
                'initial_capital': self.initial_capital,
                'current_capital': self.current_capital,
                'total_value': self.current_capital,
                'positions_count': 0,
                'positions': []
            }
        
        latest = self.portfolio_history[-1]
        
        positions_list = []
        for symbol, pos in self.positions.items():
            positions_list.append({
                'symbol': symbol,
                'shares': pos['shares'],
                'avg_price': pos['avg_price'],
                'current_price': pos['current_price'],
                'current_value': pos['current_value'],
                'profit_loss': (pos['current_price'] - pos['avg_price']) * pos['shares'],
                'profit_pct': (pos['current_price'] - pos['avg_price']) / pos['avg_price'] * 100
            })
        
        summary = {
            'initial_capital': self.initial_capital,
            'current_capital': latest['cash'],
            'positions_value': latest['positions_value'],
            'total_value': latest['total_value'],
            'positions_count': latest['positions_count'],
            'positions': positions_list,
            'total_return': (latest['total_value'] - self.initial_capital) / self.initial_capital * 100
        }
        
        return summary


class RiskManager:
    """风险管理系统（基于历史数据）"""
    
    def __init__(self, data_reader):
        """
        初始化风险管理系统
        
        参数:
        data_reader: HistoryDataReader实例
        """
        self.data_reader = data_reader
        
        # 风险参数
        self.risk_params = {
            'max_drawdown_limit': 0.20,  # 最大回撤限制
            'var_confidence': 0.95,      # VaR置信度
            'position_concentration_limit': 0.2,  # 单票仓位集中度限制
            'sector_concentration_limit': 0.4,    # 行业集中度限制
        }
    
    def analyze_stock_risk(self, symbol, lookback_days=252):
        """分析单只股票风险"""
        stock_data = self.data_reader.get_stock_data(symbol)
        if stock_data is None or stock_data.empty:
            return None
        
        # 获取最近数据
        recent_data = stock_data.tail(lookback_days)
        if len(recent_data) < 20:
            return None
        
        # 计算收益率
        returns = recent_data['close'].pct_change().dropna()
        
        # 计算风险指标
        risk_metrics = {
            'symbol': symbol,
            'analysis_days': len(recent_data),
            'current_price': recent_data['close'].iloc[-1],
            'volatility_daily': returns.std(),
            'volatility_annual': returns.std() * np.sqrt(252),
            'sharpe_ratio': self.calculate_sharpe_ratio(returns),
            'max_drawdown': self.calculate_max_drawdown(recent_data['close']),
            'var_95': self.calculate_var(returns, confidence=0.95),
            'var_99': self.calculate_var(returns, confidence=0.99),
            'skewness': returns.skew(),
            'kurtosis': returns.kurtosis(),
        }
        
        return risk_metrics
    
    def calculate_sharpe_ratio(self, returns, risk_free_rate=0.02):
        """计算夏普比率"""
        if len(returns) < 2:
            return 0
        
        excess_returns = returns - risk_free_rate / 252
        sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        
        return sharpe
    
    def calculate_max_drawdown(self, prices):
        """计算最大回撤"""
        if len(prices) < 2:
            return 0
        
        peak = prices.iloc[0]
        max_dd = 0
        
        for price in prices:
            if price > peak:
                peak = price
            
            drawdown = (peak - price) / peak
            max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def calculate_var(self, returns, confidence=0.95):
        """计算风险价值 (VaR)"""
        if len(returns) < 30:
            return 0
        
        sorted_returns = np.sort(returns)
        var_index = int((1 - confidence) * len(sorted_returns))
        
        if var_index >= len(sorted_returns):
            var_index = len(sorted_returns) - 1
        
        var = sorted_returns[var_index]
        return var
    
    def analyze_portfolio_risk(self, portfolio_positions, current_prices):
        """分析组合风险"""
        if not portfolio_positions:
            return None
        
        # 计算组合价值
        portfolio_value = sum(pos['current_value'] for pos in portfolio_positions.values())
        
        # 计算集中度风险
        concentration_risk = 0
        for symbol, position in portfolio_positions.items():
            position_ratio = position['current_value'] / portfolio_value
            concentration_risk = max(concentration_risk, position_ratio)
        
        # 计算相关性风险（简化的）
        correlation_risk = self.estimate_correlation_risk(portfolio_positions.keys())
        
        risk_report = {
            'portfolio_value': portfolio_value,
            'positions_count': len(portfolio_positions),
            'concentration_risk': concentration_risk,
            'correlation_risk': correlation_risk,
            'is_concentrated': concentration_risk > self.risk_params['position_concentration_limit']
        }
        
        return risk_report
    
    def estimate_correlation_risk(self, symbols):
        """估计相关性风险（简化的）"""
        if len(symbols) <= 1:
            return 0
        
        # 这里可以扩展为计算实际的相关性矩阵
        # 现在返回一个估计值
        if len(symbols) < 3:
            return 0.7  # 相关性较高
        elif len(symbols) < 5:
            return 0.5  # 中等相关性
        else:
            return 0.3  # 相关性较低
    
    def generate_risk_report(self, symbol=None, portfolio_positions=None):
        """生成风险报告"""
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("⚠️ 风险分析报告")
        report_lines.append("=" * 60)
        
        if symbol:
            # 单只股票风险分析
            risk_metrics = self.analyze_stock_risk(symbol)
            if risk_metrics:
                report_lines.append(f"📈📈 股票: {symbol}")
                report_lines.append(f"   当前价格: {risk_metrics['current_price']:.2f}")
                report_lines.append(f"   分析天数: {risk_metrics['analysis_days']}")
                report_lines.append(f"   日波动率: {risk_metrics['volatility_daily']:.2%}")
                report_lines.append(f"   年化波动率: {risk_metrics['volatility_annual']:.2%}")
                report_lines.append(f"   夏普比率: {risk_metrics['sharpe_ratio']:.2f}")
                report_lines.append(f"   最大回撤: {risk_metrics['max_drawdown']:.2%}")
                report_lines.append(f"   VaR(95%): {risk_metrics['var_95']:.2%}")
                report_lines.append(f"   VaR(99%): {risk_metrics['var_99']:.2%}")
                report_lines.append(f"   偏度: {risk_metrics['skewness']:.2f}")
                report_lines.append(f"   峰度: {risk_metrics['kurtosis']:.2f}")
        
        if portfolio_positions:
            # 组合风险分析
            portfolio_risk = self.analyze_portfolio_risk(portfolio_positions, {})
            if portfolio_risk:
                report_lines.append(f"\n📊📊 组合风险:")
                report_lines.append(f"   组合价值: {portfolio_risk['portfolio_value']:,.2f}")
                report_lines.append(f"   持仓数量: {portfolio_risk['positions_count']}")
                report_lines.append(f"   集中度风险: {portfolio_risk['concentration_risk']:.2%}")
                report_lines.append(f"   相关性风险: {portfolio_risk['correlation_risk']:.2f}")
                
                if portfolio_risk['is_concentrated']:
                    report_lines.append(f"   ⚠⚠⚠️ 警告: 持仓过于集中!")
        
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)


class TradingBacktestSystem:
    """综合交易回测系统"""
    
    def __init__(self, data_reader, initial_capital=1000000):
        """
        初始化回测系统
        
        参数:
        data_reader: HistoryDataReader实例
        initial_capital: 初始资金
        """
        self.data_reader = data_reader
        self.initial_capital = initial_capital
        
        # 初始化各个模块
        self.position_manager = PositionManager(initial_capital, data_reader)
        self.risk_manager = RiskManager(data_reader)
        
        # 回测参数
        self.backtest_params = {
            'start_date': None,
            'end_date': None,
            'trade_frequency': 'daily',  # daily, weekly, monthly
            'signal_method': 'technical',  # technical, trend, mean_reversion
        }
        
        # 回测结果
        self.backtest_results = {}
    
    def run_backtest(self, strategy_func, start_date=None, end_date=None, strategy_type='technical'):
        """
        运行回测
        
        参数:
        strategy_func: 策略函数，接收(date, data)返回交易信号
        strategy_type: 策略类型 technical/trend/mean_reversion/momentum
        """
        print(f"🔧🔧 开始回测...")
        print(f"   初始资金: {self.initial_capital:,.2f}")
        print(f"   策略类型: {strategy_type}")
        
        # 获取日期范围 - 使用文件中的完整时间范围
        if start_date is None or end_date is None:
            min_date, max_date = self.data_reader.get_date_range()
            start_date = start_date or min_date
            end_date = end_date or max_date
        
        print(f"   回测期间: {start_date} 到 {end_date}")
        
        # 生成交易日列表
        trade_dates = self.generate_trade_dates(start_date, end_date)
        
        print(f"   回测天数: {len(trade_dates)}")
        print("-" * 60)
        
        # 策略上下文，用于保存状态
        strategy_context = {
            'previous_signals': {},
            'position_days': {},  # 持仓天数记录
            'trade_count': 0,
            'last_trade_date': None,
            'strategy_type': strategy_type
        }
        
        # 逐日回测
        for i, date in enumerate(trade_dates, 1):
            if i % 50 == 0 or i == len(trade_dates) or i <= 10:
                print(f"   进度: {i}/{len(trade_dates)} ({i/len(trade_dates)*100:.1f}%)")
            
            # 获取当日市场数据
            daily_data = self.data_reader.get_daily_market_data(date)
            if daily_data is None or daily_data.empty:
                continue
            
            try:
                # 执行策略，传入上下文
                signals = strategy_func(date, daily_data, strategy_context, strategy_type)
                
                # 过滤和验证信号
                validated_signals = self.validate_signals(date, signals, daily_data, strategy_context)
                
                # 执行交易
                self.execute_signals(date, validated_signals, daily_data, strategy_context)
                
                # 检查风险控制
                self.check_risk_control(date, strategy_context)
                
                # 更新组合价值
                self.position_manager.update_portfolio_value(date)
                
                # 更新策略上下文
                self.update_strategy_context(date, strategy_context, validated_signals)
                
            except Exception as e:
                print(f"❌ 策略执行错误 {date}: {e}")
                continue
        
        print("-" * 60)
        print(f"✅ 回测完成!")
        
        # 生成回测报告
        self.generate_backtest_report()
    
    def generate_trade_dates(self, start_date, end_date):
        """生成交易日列表"""
        # 获取所有日期并过滤出有数据的交易日
        all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
        trade_dates = []
        
        for date in all_dates:
            daily_data = self.data_reader.get_daily_market_data(date)
            if daily_data is not None and not daily_data.empty:
                trade_dates.append(date)
        
        return trade_dates
    
    def validate_signals(self, date, signals, daily_data, context):
        """验证交易信号的有效性"""
        validated_signals = []
        
        if not signals:
            return validated_signals
        
        for signal in signals:
            # 基本验证
            if not self.validate_signal_basics(signal):
                continue
            
            symbol = signal['symbol']
            action = signal['action']
            price = signal['price']
            
            # 价格验证
            if not self.validate_price(symbol, price, daily_data):
                continue
            
            # 频率控制验证
            if not self.validate_trade_frequency(symbol, action, date, context):
                continue
            
            # 风险验证
            if not self.validate_risk(symbol, action, price, context):
                continue
            
            validated_signals.append(signal)
        
        return validated_signals
    
    def validate_signal_basics(self, signal):
        """验证信号基本格式"""
        required_fields = ['symbol', 'action', 'price']
        
        for field in required_fields:
            if field not in signal or signal[field] is None:
                return False
        
        if signal['action'] not in ['BUY', 'SELL', 'HOLD']:
            return False
        
        if signal['price'] <= 0:
            return False
        
        return True
    
    def validate_price(self, symbol, price, daily_data):
        """验证价格合理性"""
        try:
            # 获取该股票的当日数据
            symbol_data = daily_data[daily_data['symbol'] == symbol]
            if symbol_data.empty:
                return False
            
            daily_info = symbol_data.iloc[0]
            high, low = daily_info['high'], daily_info['low']
            
            # 价格应该在当日高低点范围内（允许小幅误差）
            if price < low * 0.99 or price > high * 1.01:
                return False
            
            return True
        except:
            return False
    
    def validate_trade_frequency(self, symbol, action, date, context):
        """验证交易频率"""
        if action == 'HOLD':
            return True
        
        # 检查最小持仓天数
        if action == 'SELL':
            if symbol in context.get('position_days', {}):
                hold_days = context['position_days'][symbol]
                if hold_days < 3:  # 至少持仓3天
                    return False
        
        # 检查交易频率
        last_trade_date = context.get('last_trade_date')
        if last_trade_date and action == 'BUY':
            days_since_last = (date - last_trade_date).days
            if days_since_last < 1:  # 至少间隔1天
                return False
        
        return True
    
    def validate_risk(self, symbol, action, price, context):
        """风险验证"""
        portfolio_summary = self.position_manager.get_portfolio_summary()
        
        if action == 'BUY':
            # 检查单票仓位限制
            current_positions = portfolio_summary['positions']
            symbol_position = next((p for p in current_positions if p['symbol'] == symbol), None)
            
            if symbol_position:
                current_value = symbol_position['current_value']
                if current_value > self.initial_capital * 0.1:  # 单票不超过10%
                    return False
            
            # 检查总仓位限制
            total_position_value = portfolio_summary['positions_value']
            if total_position_value > self.initial_capital * 0.8:  # 总仓位不超过80%
                return False
        
        return True
    
    def execute_signals(self, date, signals, daily_data, context):
        """执行交易信号"""
        if not signals:
            return
        
        for signal in signals:
            symbol = signal.get('symbol')
            action = signal.get('action')
            price = signal.get('price')
            reason = signal.get('reason', '')
            
            if action == 'HOLD':
                continue  # 持有信号不执行交易
            
            # 获取仓位信息
            portfolio_summary = self.position_manager.get_portfolio_summary()
            
            if action == 'BUY':
                # 计算买入数量
                signal_strength = signal.get('strength', 0.5)
                shares = self.position_manager.calculate_position_size(
                    symbol, price, signal_strength
                )
                
                if shares > 0:
                    success = self.position_manager.execute_backtest_buy(
                        date, symbol, price, shares, reason
                    )
                    if success:
                        context['trade_count'] += 1
                        context['last_trade_date'] = date
            
            elif action == 'SELL':
                # 检查是否有持仓
                has_position = any(p['symbol'] == symbol 
                                 for p in portfolio_summary['positions'])
                
                if has_position:
                    # 卖出全部持仓
                    for position in portfolio_summary['positions']:
                        if position['symbol'] == symbol:
                            shares = position['shares']
                            success = self.position_manager.execute_backtest_sell(
                                date, symbol, price, shares, reason
                            )
                            if success:
                                context['trade_count'] += 1
                                context['last_trade_date'] = date
                            break
    
    def check_risk_control(self, date, context):
        """检查风险控制"""
        portfolio_summary = self.position_manager.get_portfolio_summary()
        
        # 检查止损
        for position in portfolio_summary['positions']:
            symbol = position['symbol']
            current_price = position['current_price']
            avg_price = position['avg_price']
            
            # 止损检查（亏损超过8%）
            if (avg_price - current_price) / avg_price > 0.08:
                print(f"⚠️ 触发止损: {symbol} 亏损超过8%")
                # 这里可以添加自动止损逻辑
    
    def update_strategy_context(self, date, context, signals):
        """更新策略上下文"""
        # 更新持仓天数
        portfolio_summary = self.position_manager.get_portfolio_summary()
        for position in portfolio_summary['positions']:
            symbol = position['symbol']
            if symbol in context['position_days']:
                context['position_days'][symbol] += 1
            else:
                context['position_days'][symbol] = 1
        
        # 清理已清仓的股票
        current_symbols = [p['symbol'] for p in portfolio_summary['positions']]
        for symbol in list(context['position_days'].keys()):
            if symbol not in current_symbols:
                del context['position_days'][symbol]
    
    def generate_backtest_report(self):
        """生成回测报告"""
        portfolio_summary = self.position_manager.get_portfolio_summary()
        trade_history = self.position_manager.trade_history
        portfolio_history = self.position_manager.portfolio_history
        
        if not portfolio_history:
            print("❌❌ 没有回测数据")
            return
        
        # 计算回测指标
        initial_value = self.initial_capital
        final_value = portfolio_summary['total_value']
        total_return = portfolio_summary['total_return']
        
        # 计算年化收益率
        if portfolio_history:
            start_date = portfolio_history[0]['date']
            end_date = portfolio_history[-1]['date']
            days = (end_date - start_date).days
            
            if days > 0:
                years = days / 365.25
                cagr = ((final_value / initial_value) ** (1 / years) - 1) * 100
            else:
                cagr = 0
        else:
            cagr = 0
        
        # 计算最大回撤
        equity_curve = [h['total_value'] for h in portfolio_history]
        max_dd = self.risk_manager.calculate_max_drawdown(pd.Series(equity_curve))
        
        # 计算夏普比率
        returns = []
        for i in range(1, len(portfolio_history)):
            ret = (portfolio_history[i]['total_value'] - 
                  portfolio_history[i-1]['total_value']) / portfolio_history[i-1]['total_value']
            returns.append(ret)
        
        if returns:
            returns_series = pd.Series(returns)
            sharpe = np.mean(returns_series) / np.std(returns_series) * np.sqrt(252)
        else:
            sharpe = 0
        
        # 交易统计
        buy_trades = [t for t in trade_history if t['action'] == 'BUY']
        sell_trades = [t for t in trade_history if t['action'] == 'SELL']
        
        winning_trades = [t for t in sell_trades if t.get('profit_loss', 0) > 0]
        losing_trades = [t for t in sell_trades if t.get('profit_loss', 0) <= 0]
        
        win_rate = len(winning_trades) / len(sell_trades) if sell_trades else 0
        
        # 平均盈亏
        avg_win = np.mean([t.get('profit_loss', 0) for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.get('profit_loss', 0) for t in losing_trades]) if losing_trades else 0
        
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # 生成报告
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("📊📊 回测结果报告")
        report_lines.append("=" * 60)
        report_lines.append(f"📅📅 回测期间: {start_date} 到 {end_date}")
        report_lines.append(f"📅📅 回测天数: {days} 天 ({years:.1f} 年)")
        report_lines.append("")
        report_lines.append("💰 收益表现:")
        report_lines.append(f"   初始资金: {initial_value:,.2f}")
        report_lines.append(f"   最终资金: {final_value:,.2f}")
        report_lines.append(f"   总收益率: {total_return:.2f}%")
        report_lines.append(f"   年化收益率: {cagr:.2f}%")
        report_lines.append("")
        report_lines.append("📈📈 风险指标:")
        report_lines.append(f"   最大回撤: {max_dd:.2%}")
        report_lines.append(f"   夏普比率: {sharpe:.2f}")
        report_lines.append("")
        report_lines.append("🔄🔄 交易统计:")
        report_lines.append(f"   总交易次数: {len(trade_history)}")
        report_lines.append(f"   买入交易: {len(buy_trades)}")
        report_lines.append(f"   卖出交易: {len(sell_trades)}")
        report_lines.append(f"   胜率: {win_rate:.1%}")
        report_lines.append(f"   平均盈利: {avg_win:.2f}")
        report_lines.append(f"   平均亏损: {avg_loss:.2f}")
        report_lines.append(f"   盈亏比: {profit_factor:.2f}")
        report_lines.append("")
        report_lines.append("📊📊 当前持仓:")
        for position in portfolio_summary['positions']:
            report_lines.append(f"   {position['symbol']}: {position['shares']}股, " +
                               f"价值: {position['current_value']:,.2f}, " +
                               f"盈亏: {position['profit_loss']:+,.2f} ({position['profit_pct']:+.2f}%)")
        
        report_lines.append("=" * 60)
        
        report = "\n".join(report_lines)
        print(report)


# 策略函数示例
def example_technical_strategy(date, daily_data, context, strategy_type='technical'):
    """示例技术策略：均线交叉策略"""
    signals = []
    
    # 对每只股票进行分析
    symbols = daily_data['symbol'].unique()[:20]  # 限制数量
    
    for symbol in symbols:
        symbol_data = daily_data[daily_data['symbol'] == symbol]
        if len(symbol_data) < 20:  # 需要足够数据
            continue
        
        # 获取历史数据
        all_data = context['data_reader'].get_stock_data(symbol)
        if all_data is None or len(all_data) < 20:
            continue
        
        # 计算技术指标
        closes = all_data['close']
        ma5 = closes.rolling(5).mean()
        ma20 = closes.rolling(20).mean()
        
        current_price = closes.iloc[-1]
        current_ma5 = ma5.iloc[-1]
        current_ma20 = ma20.iloc[-1]
        prev_ma5 = ma5.iloc[-2] if len(ma5) > 1 else current_ma5
        prev_ma20 = ma20.iloc[-2] if len(ma20) > 1 else current_ma20
        
        # 生成交易信号
        if current_ma5 > current_ma20 and prev_ma5 <= prev_ma20:
            # 5日均线上穿20日均线，买入信号
            signals.append({
                'symbol': symbol,
                'action': 'BUY',
                'price': current_price,
                'strength': 0.7,
                'reason': '5日均线上穿20日均线'
            })
        elif current_ma5 < current_ma20 and prev_ma5 >= prev_ma20:
            # 5日均线下穿20日均线，卖出信号
            signals.append({
                'symbol': symbol,
                'action': 'SELL',
                'price': current_price,
                'reason': '5日均线下穿20日均线'
            })
    
    return signals


def trend_following_strategy(date, daily_data, context, strategy_type='trend'):
    """趋势跟踪策略"""
    signals = []
    
    symbols = daily_data['symbol'].unique()[:20]
    
    for symbol in symbols:
        symbol_data = daily_data[daily_data['symbol'] == symbol]
        if len(symbol_data) < 50:
            continue
        
        all_data = context['data_reader'].get_stock_data(symbol)
        if all_data is None or len(all_data) < 50:
            continue
        
        closes = all_data['close']
        ma20 = closes.rolling(20).mean()
        ma50 = closes.rolling(50).mean()
        
        current_price = closes.iloc[-1]
        current_ma20 = ma20.iloc[-1]
        current_ma50 = ma50.iloc[-1]
        
        # 趋势判断
        if current_ma20 > current_ma50 and current_price > current_ma20:
            # 上升趋势，买入
            signals.append({
                'symbol': symbol,
                'action': 'BUY',
                'price': current_price,
                'strength': 0.8,
                'reason': '上升趋势确认'
            })
        elif current_ma20 < current_ma50:
            # 下降趋势，卖出
            signals.append({
                'symbol': symbol,
                'action': 'SELL',
                'price': current_price,
                'reason': '下降趋势确认'
            })
    
    return signals


def mean_reversion_strategy(date, daily_data, context, strategy_type='mean_reversion'):
    """均值回归策略"""
    signals = []
    
    symbols = daily_data['symbol'].unique()[:20]
    
    for symbol in symbols:
        symbol_data = daily_data[daily_data['symbol'] == symbol]
        if len(symbol_data) < 20:
            continue
        
        all_data = context['data_reader'].get_stock_data(symbol)
        if all_data is None or len(all_data) < 20:
            continue
        
        closes = all_data['close']
        ma20 = closes.rolling(20).mean()
        std20 = closes.rolling(20).std()
        
        current_price = closes.iloc[-1]
        current_ma20 = ma20.iloc[-1]
        current_std = std20.iloc[-1]
        
        # 计算z-score
        if current_std > 0:
            z_score = (current_price - current_ma20) / current_std
            
            # 均值回归信号
            if z_score > 2:  # 超过2倍标准差，卖出
                signals.append({
                    'symbol': symbol,
                    'action': 'SELL',
                    'price': current_price,
                    'reason': f'价格偏离均值{z_score:.2f}倍标准差'
                })
            elif z_score < -2:  # 低于2倍标准差，买入
                signals.append({
                    'symbol': symbol,
                    'action': 'BUY',
                    'price': current_price,
                    'strength': 0.6,
                    'reason': f'价格低于均值{abs(z_score):.2f}倍标准差'
                })
    
    return signals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_file', '-f', type=str, default='history_20260101_20260201.csv')
    parser.add_argument('--sn', type=str, default='000001')
    parser.add_argument('--strategy', type=str, default='technical', 
                       choices=['technical', 'trend', 'mean_reversion'])
    parser.add_argument('--backtest', action='store_true', help='是否运行回测')
    parser.add_argument('--capital', type=float, default=1000000, help='初始资金')
    args = parser.parse_args()
    
    # 1. 加载数据
    data_file = args.data_file
    data_reader = HistoryDataReader(data_file)
    
    if data_reader.data is None:
        print("❌❌ 无法加载数据，程序退出")
        return
    
    # 2. 获取股票列表
    stock_list = data_reader.get_stock_list()
    print(f"📊📊 可分析股票: {len(stock_list)} 只")
    
    # 3. 选择要分析的股票
    if args.sn.startswith('6'):
        selected_stock = args.sn + '.SZ'
    elif args.sn.startswith('9'):
        selected_stock = args.sn + '.BJ'
    else:
        selected_stock = args.sn + '.SH'
    
    if selected_stock not in stock_list:
        # 尝试其他格式
        if args.sn + '.SH' in stock_list:
            selected_stock = args.sn + '.SH'
        elif args.sn + '.SZ' in stock_list:
            selected_stock = args.sn + '.SZ'
        else:
            selected_stock = stock_list[0] if stock_list else None
    
    if not selected_stock:
        print("❌❌ 没有可分析的股票数据")
        return
    
    print(f"\n🎯🎯 选择分析股票: {selected_stock}")
    
    # 4. 点位分析
    analyzer = PricePointAnalyzer(data_reader, selected_stock)
    report = analyzer.generate_point_analysis_report()
    print(report)
    
    # 5. 风险分析
    print("\n" + "=" * 60)
    print("⚠️ 风险分析")
    print("=" * 60)
    
    risk_manager = RiskManager(data_reader)
    risk_report = risk_manager.generate_risk_report(selected_stock)
    print(risk_report)
    
    # 6. 回测演示
    if args.backtest:
        print("\n" + "=" * 60)
        print("🔧🔧 回测演示")
        print("=" * 60)
        
        # 创建回测系统
        backtest_system = TradingBacktestSystem(data_reader, initial_capital=args.capital)
        
        # 选择策略
        strategy_map = {
            'technical': example_technical_strategy,
            'trend': trend_following_strategy,
            'mean_reversion': mean_reversion_strategy
        }
        
        strategy_func = strategy_map.get(args.strategy, example_technical_strategy)
        
        # 为策略函数添加数据读取器引用
        def strategy_with_data(date, daily_data, context, strategy_type):
            context['data_reader'] = data_reader
            return strategy_func(date, daily_data, context, strategy_type)
        
        # 运行回测
        try:
            # 获取数据日期范围 - 使用文件中的完整时间范围
            min_date, max_date = data_reader.get_date_range()
            
            if min_date and max_date:
                # 使用文件中的完整时间范围进行回测
                demo_start_date = min_date
                demo_end_date = max_date
                
                print(f"回测期间: {demo_start_date.date()} 到 {demo_end_date.date()}")
                print(f"策略类型: {args.strategy}")
                print(f"初始资金: {args.capital:,.2f}")
                
                # 运行策略
                backtest_system.run_backtest(
                    strategy_func=strategy_with_data,
                    start_date=demo_start_date,
                    end_date=demo_end_date,
                    strategy_type=args.strategy
                )
        except Exception as e:
            print(f"回测过程中出错: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ 分析完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()