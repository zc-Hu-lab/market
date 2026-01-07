#!/usr/bin/python3

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

class signal:
    def __init__(self):
        self.res = pd.DataFrame()
        return
        
    def generate_signals(self, df):
        """
        生成MACD交易信号
        """
        df = df.copy()
        
        # 初始化信号列
        df['signal'] = 0
        df['signal_type'] = ''
        
        # 金叉信号（买入）
        golden_cross = (df['diff'] > df['macd']) & (df['diff'].shift(1) <= df['macd'].shift(1))
        df.loc[golden_cross, 'signal'] = 1
        df.loc[golden_cross, 'signal_type'] = '金叉买入'
        
        # 死叉信号（卖出）
        death_cross = (df['diff'] < df['macd']) & (df['diff'].shift(1) >= df['macd'].shift(1))
        df.loc[death_cross, 'signal'] = -1
        df.loc[death_cross, 'signal_type'] = '死叉卖出'
        
        # 零轴突破信号（辅助参考）
        zero_cross_up = (df['diff'] > 0) & (df['diff'].shift(1) <= 0)
        zero_cross_down = (df['diff'] < 0) & (df['diff'].shift(1) >= 0)
        
        df.loc[zero_cross_up, 'zero_cross'] = 1
        df.loc[zero_cross_down, 'zero_cross'] = -1
        df['zero_cross'] = df['zero_cross'].fillna(0)
        
        # 统计信号数量
        buy_signals = len(df[df['signal'] == 1])
        sell_signals = len(df[df['signal'] == -1])
        
        print(f"交易信号统计：")
        print(f"买入信号：{buy_signals} 次")
        print(f"卖出信号：{sell_signals} 次")

        self.res['date'] = df['date']
        self.res['value'] = df['value']
        self.res['signal'] = df['signal']
        self.res['signal_type'] = df['signal_type']
        self.res['zero_cross'] = df['zero_cross']
        
        return
    # df = generate_signals(df)
    
    def backtest_strategy(self, df, initial_capital=100000, commission_rate=0.001):
        """
        回测MACD策略
        """
        df = df.copy()
        
        # 建立仓位（1持仓，0空仓）
        df['position'] = 0
        current_position = 0
        
        for i in range(len(df)):
            if df.loc[i,'signal'] == 1:  # 买入信号
                current_position = 1
            elif df.loc[i,'signal'] == -1:  # 卖出信号
                current_position = 0
            df.loc[i, df.columns.get_loc('position')] = current_position
        
        # 计算收益率
        df['returns'] = df['value'].pct_change()
        df['strategy_returns'] = df['returns'] * df['position'].shift(1)
        
        # 考虑交易成本
        df['trades'] = df['position'].diff().abs()
        df['commission'] = df['trades'] * commission_rate
        df['strategy_returns_net'] = df['strategy_returns'] - df['commission']
        
        # 累计收益
        df['cum_strategy_returns'] = (1 + df['strategy_returns_net']).cumprod() - 1
        df['cum_market_returns'] = (1 + df['returns']).cumprod() - 1
        
        self.res = df
        return df
    # df = backtest_strategy(df)
    
    def calculate_performance_metrics(self, df):
        """
        计算策略绩效指标
        """
        # 基本收益指标
        strategy_total_return = df['cum_strategy_returns'].iloc[-1]
        market_total_return = df['cum_market_returns'].iloc[-1]
        
        # 年化收益率
        trading_days = len(df)
        years = trading_days / 252
        strategy_annual_return = (1 + strategy_total_return) ** (1/years) - 1
        market_annual_return = (1 + market_total_return) ** (1/years) - 1
        
        # 波动率
        strategy_volatility = df['strategy_returns_net'].std() * np.sqrt(252)
        market_volatility = df['returns'].std() * np.sqrt(252)
        
        # 夏普比率（假设无风险利率为3%）
        risk_free_rate = 0.03
        strategy_sharpe = (strategy_annual_return - risk_free_rate) / strategy_volatility
        market_sharpe = (market_annual_return - risk_free_rate) / market_volatility
        
        # 最大回撤
        def calculate_max_drawdown(returns):
            cum_returns = (1 + returns).cumprod()
            rolling_max = cum_returns.expanding().max()
            drawdown = (cum_returns - rolling_max) / rolling_max
            return drawdown.min()
        
        strategy_max_dd = calculate_max_drawdown(df['strategy_returns_net'])
        market_max_dd = calculate_max_drawdown(df['returns'])
        
        # 胜率
        winning_trades = len(df[(df['strategy_returns_net'] > 0) & (df['trades'] > 0)])
        total_trades = len(df[df['trades'] > 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        metrics = {
            '策略总收益率': f"{strategy_total_return:.2%}",
            '市场总收益率': f"{market_total_return:.2%}",
            '策略年化收益率': f"{strategy_annual_return:.2%}",
            '市场年化收益率': f"{market_annual_return:.2%}",
            '策略年化波动率': f"{strategy_volatility:.2%}",
            '市场年化波动率': f"{market_volatility:.2%}",
            '策略夏普比率': f"{strategy_sharpe:.3f}",
            '市场夏普比率': f"{market_sharpe:.3f}",
            '策略最大回撤': f"{strategy_max_dd:.2%}",
            '市场最大回撤': f"{market_max_dd:.2%}",
            '交易胜率': f"{win_rate:.2%}",
            '总交易次数': total_trades
        }
        
        self.metrics = metrics
        return metrics

    # # 计算绩效指标
    # performance = calculate_performance_metrics(df)
    # print("=== 策略绩效分析 ===")
    # for key, value in performance.items():
    #     print(f"{key}: {value}")

    def plot_price_and_macd(self, df, figsize=(15, 10)):
        """
        绘制价格走势和MACD指标图
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)
        
        # 价格走势图
        ax1.plot(df.index, df['close'], label='收盘价', linewidth=1.5)
        
        # 标记买卖点
        buy_points = df[df['signal'] == 1]
        sell_points = df[df['signal'] == -1]
        
        ax1.scatter(buy_points.index, buy_points['close'], 
                color='red', marker='^', s=100, label='买入信号', zorder=5)
        ax1.scatter(sell_points.index, sell_points['close'], 
                color='green', marker='v', s=100, label='卖出信号', zorder=5)
        
        ax1.set_title('股价走势与MACD交易信号', fontsize=16)
        ax1.set_ylabel('价格（元）', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # MACD指标图
        ax2.plot(df.index, df['macd_dif'], label='DIF', linewidth=1.5)
        ax2.plot(df.index, df['macd_dea'], label='DEA', linewidth=1.5)
        ax2.bar(df.index, df['macd_hist'], label='MACD柱状图', alpha=0.6)
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        ax2.set_title('MACD指标', fontsize=14)
        ax2.set_xlabel('日期', fontsize=12)
        ax2.set_ylabel('MACD值', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig

    # plot_price_and_macd(df)
    # plt.show()

    def plot_returns_comparison(self, df, figsize=(12, 8)):
        """
        绘制策略收益与市场收益对比图
        """
        plt.figure(figsize=figsize)
        
        plt.plot(df.index, df['cum_strategy_returns'] * 100, 
                label='MACD策略收益', linewidth=2, color='blue')
        plt.plot(df.index, df['cum_market_returns'] * 100, 
                label='买入并持有收益', linewidth=2, color='orange')
        
        plt.title('平安银行：MACD策略 vs 买入并持有', fontsize=16)
        plt.xlabel('日期', fontsize=12)
        plt.ylabel('累计收益率（%）', fontsize=12)
        plt.legend(fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        return plt.gcf()

    # plot_returns_comparison(df)
    # plt.show()

    def plot_returns_distribution(self, df, figsize=(12, 5)):
        """
        绘制收益分布图
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        # 日收益率分布
        strategy_returns = df['strategy_returns_net'].dropna()
        market_returns = df['returns'].dropna()
        
        ax1.hist(strategy_returns * 100, bins=50, alpha=0.7, label='策略日收益率', density=True)
        ax1.hist(market_returns * 100, bins=50, alpha=0.7, label='市场日收益率', density=True)
        ax1.set_xlabel('日收益率（%）')
        ax1.set_ylabel('密度')
        ax1.set_title('日收益率分布')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 月度收益率对比
        monthly_strategy = df['strategy_returns_net'].resample('M').apply(lambda x: (1+x).prod()-1)
        monthly_market = df['returns'].resample('M').apply(lambda x: (1+x).prod()-1)
        
        months = range(len(monthly_strategy))
        width = 0.35
        ax2.bar([m - width/2 for m in months], monthly_strategy * 100, 
                width, label='策略月收益率', alpha=0.8)
        ax2.bar([m + width/2 for m in months], monthly_market * 100, 
                width, label='市场月收益率', alpha=0.8)
        ax2.set_xlabel('月份')
        ax2.set_ylabel('月收益率（%）')
        ax2.set_title('月度收益率对比')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig

    # plot_returns_distribution(df)
    # plt.show()