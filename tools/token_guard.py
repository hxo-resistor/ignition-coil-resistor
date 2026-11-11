#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""token_guard.py — 强制 Token 计费拦截（硬闸）

每次调用 LLM 前，先估算本次成本：
    1. 单次请求预估 > HXO_SINGLE_LIMIT（默认 0.1 元）→ sys.exit(1) 强行退出
    2. 今日累计 + 本次预估 > HXO_HARD_DAILY_LIMIT（默认 1.0 元）→ sys.exit(1) 强行退出

这是硬闸：超限直接终止进程，绝不靠模型自己判断、绝不后台循环。
"""
import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cost_guard  # noqa: E402

SINGLE_LIMIT_YUAN = float(os.environ.get("HXO_SINGLE_LIMIT", "0.1"))
DAILY_HARD_LIMIT_YUAN = float(os.environ.get("HXO_HARD_DAILY_LIMIT", "1.0"))


def estimate_tokens(text: str) -> int:
    """粗略估算 token 数：CJK 字符≈1 token，其余≈4 字符/token。"""
    if not text:
        return 0
    cjk = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    other = len(text) - cjk
    return cjk + other // 4


def estimate_cost(text: str) -> float:
    """估算本次请求成本（输入 + 输出按同规模保守估算）。"""
    tokens = estimate_tokens(text)
    return tokens / 1000.0 * (cost_guard.PRICE_INPUT_1K + cost_guard.PRICE_OUTPUT_1K)


def guard(text: str) -> float:
    """发请求前调用。超限则 sys.exit 硬退出，返回本次估算成本。"""
    cost = estimate_cost(text)
    if cost > SINGLE_LIMIT_YUAN:
        print(f"[token_guard] 单次请求预估 {cost:.4f} 元，超过单次上限 {SINGLE_LIMIT_YUAN} 元，终止！",
              file=sys.stderr, flush=True)
        sys.exit(1)
    today = cost_guard.today_cost()
    if today + cost > DAILY_HARD_LIMIT_YUAN:
        print(f"[token_guard] 今日累计 {today:.4f} 元 + 本次 {cost:.4f} 元，"
              f"超过日硬上限 {DAILY_HARD_LIMIT_YUAN} 元，终止！", file=sys.stderr, flush=True)
        sys.exit(1)
    return cost


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default="")
    ap.add_argument("--dry", action="store_true", help="只估算不拦截")
    a = ap.parse_args()
    t = a.text or "点火线圈抑制电阻额定功率怎么选？1W/3W/5W/10W 选型陷阱与实测温升"
    print(f"字符数={len(t)}  估算 tokens={estimate_tokens(t)}  估算成本={estimate_cost(t):.5f} 元")
    print(f"今日累计={cost_guard.today_cost():.5f} 元 / 硬上限 {DAILY_HARD_LIMIT_YUAN} 元")
    if not a.dry:
        guard(t)
        print("未超限，放行。")
