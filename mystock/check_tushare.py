#!/usr/bin/env python3
# check_tushare.py

import tushare as ts
import inspect
import os

print("=" * 60)
print("Tushare深度检查")
print("=" * 60)

# 1. 基本信息
print(f"版本: {ts.__version__}")
print(f"文件路径: {ts.__file__}")

# 2. 检查pro.daily函数的签名
print("\n检查pro.daily函数:")
try:
    sig = inspect.signature(ts.pro_api().daily)
    print(f"函数签名: {sig}")
except Exception as e:
    print(f"获取签名失败: {e}")

# 3. 查看模块的所有属性
print(f"\n模块包含的属性数量: {len(dir(ts))}")

# 4. 测试调用
print("\n测试调用pro.daily:")
try:
    pro = ts.pro_api()
    # 使用正确的参数格式
    data = pro.daily(ts_code='000001.SZ', trade_date='20240130')
    print(f"返回数据类型: {type(data)}")
    if hasattr(data, 'shape'):
        print(f"数据形状: {data.shape}")
    print(f"列名: {list(data.columns) if hasattr(data, 'columns') else '无columns属性'}")
    print(f"前几行数据:")
    print(data.head() if not data.empty else "空数据")
except Exception as e:
    print(f"调用失败: {e}")
    import traceback
    traceback.print_exc()

# 5. 检查是否是官方版本
print("\n检查版本特征:")
official_features = ['pro_api', 'get_hist_data', '__version__', '__author__']
for feature in official_features:
    has_feature = hasattr(ts, feature)
    print(f"  {feature}: {'✓' if has_feature else '✗'}")
