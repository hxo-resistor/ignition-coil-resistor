#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cost_guard.py — 成本护栏（Cost Guard）

统计每日 Token 消耗，超过阈值自动降级，防止 API 被刷爆。

价格（元/千 token，可按 DeepSeek 实际价调整）：
    HXO_DAILY_BUDGET      每日预算上限，默认 2.0 元
    HXO_PRICE_INPUT_1K    输入价，默认 0.002 元/千 token（deepseek-chat ≈ ¥2/M）
    HXO_PRICE_OUTPUT_1K   输出价，默认 0.008 元/千 token（deepseek-chat ≈ ¥8/M）

状态落盘 work/cost_state.json（gitignored）。

用法：
    from cost_guard import record, today_cost, over_budget, summary
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent.parent
STATE = REPO / "work" / "cost_state.json"

DAILY_BUDGET_YUAN = float(os.environ.get("HXO_DAILY_BUDGET", "1.0"))
PRICE_INPUT_1K = float(os.environ.get("HXO_PRICE_INPUT_1K", "0.002"))
PRICE_OUTPUT_1K = float(os.environ.get("HXO_PRICE_OUTPUT_1K", "0.008"))


class BudgetExceeded(Exception):
    pass


def _today():
    return dt.date.today().isoformat()


def load() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"days": {}}


def save(s: dict):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    # 只保留最近 30 天
    s["days"] = dict(sorted(s["days"].items())[-30:])
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")


def _cost(prompt_tokens: int, completion_tokens: int) -> float:
    return (prompt_tokens / 1000.0) * PRICE_INPUT_1K + (completion_tokens / 1000.0) * PRICE_OUTPUT_1K


def record(prompt_tokens: int, completion_tokens: int) -> dict:
    """记录一次调用，返回今日累计。"""
    s = load()
    d = s["days"].setdefault(_today(), {"prompt_tokens": 0, "completion_tokens": 0, "cost": 0.0, "calls": 0})
    d["prompt_tokens"] += int(prompt_tokens or 0)
    d["completion_tokens"] += int(completion_tokens or 0)
    d["calls"] += 1
    d["cost"] = round(_cost(d["prompt_tokens"], d["completion_tokens"]), 6)
    save(s)
    return d


def today_stats() -> dict:
    return load()["days"].get(_today(), {"prompt_tokens": 0, "completion_tokens": 0, "cost": 0.0, "calls": 0})


def today_cost() -> float:
    return today_stats().get("cost", 0.0)


def over_budget() -> bool:
    return today_cost() >= DAILY_BUDGET_YUAN


def summary() -> str:
    d = today_stats()
    return (f"今日消耗：{d['cost']:.4f} 元 / 预算 {DAILY_BUDGET_YUAN} 元  "
            f"（{d['calls']} 次调用，输入 {d['prompt_tokens']} tok，输出 {d['completion_tokens']} tok）"
            f"{'  ⚠️ 已超预算，降级运行' if over_budget() else ''}")


def reset():
    if STATE.exists():
        STATE.unlink()


if __name__ == "__main__":
    ap = None
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", help="record <prompt_tokens>:<completion_tokens>")
    ap.add_argument("--reset", action="store_true")
    a = ap.parse_args()
    if a.reset:
        reset()
        print("已重置成本统计。")
    elif a.record:
        p, _, c = a.record.partition(":")
        record(int(p), int(c))
        print(summary())
    else:
        print(summary())
