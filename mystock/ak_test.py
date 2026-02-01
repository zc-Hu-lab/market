import time
import akshare as ak

# 在连续请求间增加延时
data = ak.stock_zh_a_hist(symbol="000001", period="daily")
time.sleep(1)  # 延时1秒