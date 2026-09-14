#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
A股个股/指数 周线数据更新器 —— Baostock 版（最终完整可运行版）
================================================================
数据：Baostock（免费、匿名登录、不限频）
  日线 -> resample("W-FRI") 聚合成周线
  个股前复权(adjustflag=2)，指数不复权(adjustflag=3)

输出列（与原 Tushare 版一致）：
  date, value(收盘), open, high, low, volume, amount,
  K_weekly, D_weekly, J_weekly,
  diff_weekly, dea_weekly, macd_weekly,
  boll_u_weekly, boll_m_weekly, boll_l_weekly, rsi_weekly

用法：
  python main_week.py --limit 5            # 先试 5 只
  python main_week.py                      # 全量（从 STOCK_DIR 读代码清单）
  python main_week.py --resume             # 跳过已存在文件（断点续传）
  python main_week.py --symbol 000001      # 单只（sz.000001 = 平安银行）
  python main_week.py --include-indices    # 同时更新指数
"""
import argparse
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import baostock as bs
import pandas as pd

# ============================ 配置（按需修改） ============================
CONFIG = {
    "STOCK_DIR": "/opt/zack/master/data",         # 代码清单：该目录下 *.csv，文件名=6位代码
    "WEEKLY_DIR": "/opt/zack/master/week_data",    # 周线输出目录
    "START_DATE": "2010-01-01",                    # 全量起始日
    "ADJUST_STOCK": "2",                           # 个股：2=前复权
    "ADJUST_INDEX": "3",                           # 指数：3=不复权
    "FREQUENCY": "d",                              # 日线
    "FIELDS": "date,open,high,low,close,volume,amount",
    "REQUEST_GAP": 0.3,                            # 每只间隔（秒），礼貌限速
    "RELOGIN_EVERY": 300,                          # 每处理多少只重新登录一次（防长连接失效）
    "BATCH_SIZE": 50,                              # 每多少只打印一次汇总
}

# 指数完整代码（走不复权，避免把指数当个股）
INDICES = [
    "sh.000001",  # 上证综指
    "sz.399001",  # 深证成指
    "sz.399006",  # 创业板指
    "sh.000300",  # 沪深300
    "sh.000905",  # 中证500
]


# ============================ 工具函数 ============================
def to_bs_code(symbol: str) -> str:
    """6位代码 -> Baostock 格式（带市场前缀）"""
    s = symbol.strip()
    if s.startswith(("60", "68", "69", "9", "000")):
        return f"sh.{s}"   # 上交所 + 上证指数(000xxx)
    if s.startswith(("00", "30", "31", "002", "003", "001")):
        return f"sz.{s}"   # 深市 + 创业板
    if s.startswith(("43", "83", "87", "88", "89", "92")):
        return f"bj.{s}"   # 北交所
    print(f"  [警告] 无法识别市场前缀: {s}，默认 sz", flush=True)
    return f"sz.{s}"


def is_index(symbol: str) -> bool:
    """是否是指数（用完整 bs_code 判断）"""
    return to_bs_code(symbol) in INDICES


def _validate_date(d: str):
    """Baostock 要求 YYYY-MM-DD，否则返回 None 导致 AttributeError"""
    if not (len(d) == 10 and d[4] == "-" and d[7] == "-"):
        raise ValueError(f"日期必须是 YYYY-MM-DD，实际: {d}")


# ============================ 数据合并（兼容新旧 pandas） ============================
def safe_concat(dfs):
    """兼容 pandas <2.0(append) 与 >=2.0(concat only)"""
    if not isinstance(dfs, list):
        dfs = list(defs := dfs)
    return pd.concat(defs, ignore_index=True)


def merge_weekly(old_path: Path, wk: pd.DataFrame) -> pd.DataFrame:
    """把增量周线与磁盘旧文件合并、去重、重算指标"""
    if not old_path.exists():
        return wk
    old = pd.read_csv(old_path, encoding="utf-8-sig")
    if old.empty:
        return wk
    merged = pd.concat([old, wk], ignore_index=True)
    merged = merged.drop_duplicates(subset=["date"], keep="last")
    merged = merged.sort_values("date").reset_index(drop=True)
    return calc_indicators(merged)


# ============================ 数据获取 ============================
def fetch_daily(bs_code: str, start: str, end: str, adjustflag: str) -> pd.DataFrame:
    """拉取日线，返回 DataFrame"""
    _validate_date(start)
    _validate_date(end)

    rs = bs.query_history_k_data_plus(
        bs_code, CONFIG["FIELDS"],
        start_date=start, end_date=end,
        frequency=CONFIG["FREQUENCY"], adjustflag=adjustflag,
    )
    if rs is None:
        raise RuntimeError("Baostock 返回 None（几乎都是日期格式错误）")
    if rs.error_code != "0":
        raise RuntimeError(f"Baostock error {rs.error_code}: {rs.error_msg}")

    df = rs.get_data()
    if df.empty:
        return df

    for col in ["open", "high", "low", "close", "volume", "amount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["close"]).copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


# ============================ 日线 -> 周线 ============================
def daily_to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """resample 成周线（每周五收盘，W-FRI）"""
    df = df.copy().set_index("date")
    w = df.resample("W-FRI").agg({
        "open": "first", "high": "max", "low": "min",
        "close": "last", "volume": "sum", "amount": "sum",
    })
    w = w.dropna(subset=["close"]).reset_index()
    w["date"] = w["date"].dt.strftime("%Y-%m-%d")
    w = w.rename(columns={"close": "value"})
    return w


# ============================ 技术指标 ============================
def calc_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """KDJ / MACD / BOLL / RSI"""
    df = df.copy()
    close, high, low = df["value"], df["high"], df["low"]

    # KDJ(9,3,3)
    low_min = low.rolling(9, min_periods=1).min()
    high_max = high.rolling(9, min_periods=1).max()
    rsv = (close - low_min) / (high_max - low_min + 1e-8) * 100
    df["K_weekly"] = rsv.ewm(alpha=1/3, adjust=False).mean()
    df["D_weekly"] = df["K_weekly"].ewm(alpha=1/3, adjust=False).mean()
    df["J_weekly"] = 3 * df["K_weekly"] - 2 * df["D_weekly"]

    # MACD(12,26,9)
    diff = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
    dea = diff.ewm(span=9, adjust=False).mean()
    df["diff_weekly"] = diff
    df["dea_weekly"] = dea
    df["macd_weekly"] = 2 * (diff - dea)

    # BOLL(20, 2)
    mid = close.rolling(20).mean()
    std = close.rolling(20).std()
    df["boll_m_weekly"] = mid
    df["boll_u_weekly"] = mid + 2 * std
    df["boll_l_weekly"] = mid - 2 * std

    # RSI(14)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    ag = gain.rolling(14, min_periods=1).mean()
    al = loss.rolling(14, min_periods=1).mean()
    df["rsi_weekly"] = 100 - (100 / (1 + ag / (al + 1e-8)))

    return df


# ============================ 单只更新 ============================
def update_one(symbol: str, out_dir: Path) -> str:
    """更新单只，返回状态字符串"""
    out_path = out_dir / f"{symbol}.csv"
    bs_code = to_bs_code(symbol)
    adjustflag = CONFIG["ADJUST_INDEX"] if is_index(symbol) else CONFIG["ADJUST_STOCK"]

    # 增量起始日
    start = CONFIG["START_DATE"]
    if out_path.exists():
        try:
            old = pd.read_csv(out_path, encoding="utf-8-sig")
            if not old.empty and "date" in old.columns:
                last = pd.to_datetime(old["date"]).max()
                if last >= pd.Timestamp(datetime.now().date() - timedelta(days=7)):
                    return "latest"   # 一周内已更新，跳过
                start = (last + timedelta(days=1)).strftime("%Y-%m-%d")
        except Exception as e:
            print(f"  [警告] 读旧文件失败，全量重拉: {e}", flush=True)

    end = datetime.now().strftime("%Y-%m-%d")
    if start > end:
        return "latest"

    time.sleep(CONFIG["REQUEST_GAP"])
    df = fetch_daily(bs_code, start, end, adjustflag)
    if df.empty:
        return "no_data"

    wk = daily_to_weekly(df)
    if wk.empty:
        return "no_data"
    wk = calc_indicators(wk)

    # 合并旧数据（兼容 pandas 2.0+，无 .append）
    try:
        merged = merge_weekly(out_path, wk)
        merged.to_csv(out_path, index=False, encoding="utf-8-sig")
    except Exception as e:
        return f"fail:merge:{e}"

    return f"ok:{len(wk)}"


# ============================ 登录探针 ============================
def probe_login():
    """启动时先验证 Baostock 连通性 + 代码前缀是否正确"""
    print("正在登录 Baostock ...", flush=True)
    lg = bs.login()
    print(f"登录: {lg.error_code} {lg.error_msg}", flush=True)
    if lg.error_code != "0":
        print("登录失败，请检查网络/代理。", flush=True)
        sys.exit(1)

    print("连通性探针（验证代码前缀 + 日期格式）...", flush=True)
    for code in ["sz.000001", "sh.600000", "sz.300268"]:
        rs = bs.query_history_k_data_plus(
            code, CONFIG["FIELDS"],
            start_date="2026-09-01", end_date="2026-09-12",
            frequency="d", adjustflag="2",
        )
        if rs is None or rs.error_code != "0":
            print(f"  {code}: FAIL ({rs.error_msg if rs else 'None'})", flush=True)
            continue
        d = rs.get_data()
        last_close = pd.to_numeric(d["close"], errors="coerce").iloc[-1] if not d.empty else None
        print(f"  {code}: OK  最新收盘={last_close}", flush=True)
    print("探针完成。\n", flush=True)


# ============================ 主流程 ============================
def collect_symbols(limit: int) -> list:
    """从 STOCK_DIR 收集代码清单（不含指数）"""
    src = Path(CONFIG["STOCK_DIR"])
    if not src.exists():
        print(f"代码清单目录不存在: {src}", flush=True)
        sys.exit(1)
    codes = sorted(f.stem for f in src.glob("*.csv"))
    if limit:
        codes = codes[:limit]
    return codes


def main():
    ap = argparse.ArgumentParser(description="A股周线更新器 (Baostock)")
    ap.add_argument("--limit", type=int, default=0, help="只处理前 N 只（调试）")
    ap.add_argument("--resume", action="store_true", help="跳过已存在文件")
    ap.add_argument("--symbol", type=str, default="", help="只更新指定代码")
    ap.add_argument("--include-indices", action="store_true", help="同时更新指数")
    args = ap.parse_args()

    out_dir = Path(CONFIG["WEEKLY_DIR"])
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60, flush=True)
    print("Baostock 周线更新器", flush=True)
    print(f"  代码源目录 : {CONFIG['STOCK_DIR']}", flush=True)
    print(f"  输出目录   : {CONFIG['WEEKLY_DIR']}", flush=True)
    print(f"  个股复权   : 前复权(2)  |  指数复权 : 不复权(3)", flush=True)
    print("=" * 60, flush=True)

    # 登录 + 探针
    probe_login()

    # 组装任务列表（统一用 symbols 列表，结构唯一）
    symbols = []
    if args.symbol:
        symbols = [args.symbol]
    else:
        symbols = collect_symbols(args.limit)
        if args.include_indices:
            idx_codes = [c.split(".")[-1] for c in INDICES]
            symbols = idx_codes + symbols

    print(f"共 {len(symbols)} 只待处理\n", flush=True)

    ok = latest = no_data = fail = 0
    t0 = time.time()
    failed_log = open(out_dir / "failed.txt", "a", buffering=1)

    try:
        for i, sym in enumerate(symbols, 1):
            sym = sym.strip()

            # resume 模式：已存在则跳过
            if args.resume and (out_dir / f"{sym}.csv").exists() and not args.symbol:
                latest += 1
                if i % CONFIG["BATCH_SIZE"] == 0:
                    print(f"  [{i}/{len(symbols)}] 跳过已存在，累计 latest={latest}", flush=True)
                continue

            # 👇 进度打印（每只用，不缓冲，卡住也能看到）
            print(f"[{i}/{len(symbols)}] 正在拉 {sym} ...", flush=True)

            try:
                r = update_one(sym, out_dir)
            except Exception as e:
                r = f"fail:{type(e).__name__}:{e}"
                # 网络类错误打印详情，方便排错
                print(f"  -> 异常: {r}", flush=True)

            if r.startswith("ok"):
                ok += 1
            elif r == "latest":
                latest += 1
            elif r == "no_data":
                no_data += 1
            else:
                fail += 1
                failed_log.write(f"{sym}\t{r}\n")

            print(f"  -> {r}", flush=True)

            # 每 BATCH_SIZE 只打印汇总 + 自动重登（防长连接失效）
            if i % CONFIG["RELOGIN_EVERY"] == 0:
                print(f"  [重登] 已处理 {i} 只，重新登录 Baostock ...", flush=True)
                bs.logout()
                lg = bs.login()
                print(f"  [重登] {lg.error_code} {lg.error_msg}", flush=True)
            if i % CONFIG["BATCH_SIZE"] == 0:
                el = time.time() - t0
                print(
                    f"  --- 进度 [{i}/{len(symbols)}] "
                    f"ok={ok} latest={latest} no_data={no_data} fail={fail} "
                    f"耗时={el:.0f}s ---",
                    flush=True,
                )

        el = time.time() - t0
        print(f"\n{'='*60}", flush=True)
        print(f"完成: 成功={ok} 已最新={latest} 无数据={no_data} 失败={fail}", flush=True)
        print(f"总耗时: {el:.0f}s ({el/60:.1f}min)", flush=True)
        print(f"失败列表: {out_dir/'failed.txt'}", flush=True)
        print(f"{'='*60}", flush=True)

    except KeyboardInterrupt:
        print("\n\n[中断] 用户 Ctrl-C，已处理部分已保存到磁盘。", flush=True)
        print(f"  当前进度: ok={ok} latest={latest} no_data={no_data} fail={fail}", flush=True)
        print("  下次用 --resume 继续。", flush=True)
    finally:
        try:
            bs.logout()
        except Exception:
            pass
        failed_log.close()
        print("Baostock 已登出，退出。", flush=True)


if __name__ == "__main__":
    main()
