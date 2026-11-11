#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""self_optimize.py — 自我升级（Self-Optimizing）反馈闭环

每次发帖后记录「内容类型 → 效果分数」，据此：
    1. 动态调整各类内容权重；
    2. 输出「提示词调优 hint」——把表现最好的内容类型的风格注入下一次翻译；
    3. 每日复盘，输出设计模式分析。

状态落盘 work/optimization_state.json（gitignored，运行时不污染仓库）。
"""
import datetime as dt
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent.parent
STATE = REPO / "work" / "optimization_state.json"

CTYPE_HINTS = {
    "compare": "Prioritize data comparison, measured curves, and parameter tables.",
    "certification": "Prioritize certification standards, test items, and compliance credentials.",
    "pain": "Open from a real failure/pain point: state the problem first, then the solution.",
    "selection": "Prioritize selection formulas, decision trees, and comparison tables.",
}

DEFAULT_STATE = {"weights": {}, "history": [], "prompt_hint": ""}


def load() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT_STATE))


def save(s: dict):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")


def record_result(ctype: str, outcome: float) -> dict:
    """记录一次发布效果。outcome: 0~1 归一化效果分（曝光/互动）。"""
    s = load()
    w = s.setdefault("weights", {})
    cur = w.get(ctype, {"n": 0, "score": 0.5})
    n = cur["n"] + 1
    score = (cur["score"] * cur["n"] + max(0.0, min(1.0, outcome))) / n
    w[ctype] = {"n": n, "score": round(score, 4)}
    s.setdefault("history", []).append({
        "ts": dt.datetime.now().isoformat(timespec="seconds"),
        "ctype": ctype, "outcome": round(outcome, 3),
    })
    s["history"] = s["history"][-200:]
    # 选出当前表现最好的内容类型，注入调优 hint
    if w:
        best = max(w, key=lambda k: w[k]["score"])
        s["prompt_hint"] = CTYPE_HINTS.get(best, "")
    save(s)
    return s


def prompt_profile() -> str:
    return load().get("prompt_hint", "")


def daily_review() -> str:
    """每日复盘：按权重排序输出设计模式分析（供日志/看板）。"""
    s = load()
    w = s.get("weights", {})
    if not w:
        return "尚无反馈数据，维持默认风格。"
    ranked = sorted(w.items(), key=lambda kv: kv[1]["score"], reverse=True)
    lines = ["内容类型效果排名（分越高越该多用）："]
    for ctype, d in ranked:
        lines.append(f"  {ctype:<13} score={d['score']}  n={d['n']}")
    best = ranked[0][0]
    lines.append(f"当前主推风格：{best} —— {CTYPE_HINTS.get(best, '')}")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", help="record_result <ctype>:<outcome>，如 pain:0.8")
    ap.add_argument("--review", action="store_true", help="打印复盘")
    args = ap.parse_args()
    if args.record:
        ctype, _, outcome = args.record.partition(":")
        s = record_result(ctype.strip(), float(outcome))
        print(json.dumps(s["weights"], ensure_ascii=False))
    else:
        print(daily_review())
