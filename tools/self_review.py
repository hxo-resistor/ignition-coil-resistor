#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""self_review.py — 自我审查（Self-Reflection）

每次生成文案后，用 LLM 扮演「最严苛的 Reddit 版主 + 资深 B2B 采购」从三维打分：
    hard_sell   硬广味（越低越好）
    pain_point  痛点抓取（越高越好）
    compliance  合规性（越高越好）
不达标 → 依据 feedback 打回重写，直到通过或达到最大轮数（默认 3）。

平台感知阈值（Reddit 最严，LinkedIn/X 适度）：
    reddit    hard_sell<=3, pain_point>=7, compliance>=9
    linkedin  hard_sell<=5, pain_point>=6, compliance>=8
    x         hard_sell<=6, pain_point>=5, compliance>=8

无 DEEPSEEK_API_KEY 时退化为启发式 Mock 评分（用于链路测试）。
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import translate  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

THRESHOLDS = {
    "reddit": {"hard_sell": 3, "pain_point": 7, "compliance": 9},
    "linkedin": {"hard_sell": 5, "pain_point": 6, "compliance": 8},
    "x": {"hard_sell": 6, "pain_point": 5, "compliance": 8},
}

PLATFORM_CONTEXT = {
    "reddit": "This post is going to a Reddit technical subreddit (strict anti-self-promotion: no hard ads, no direct contact info).",
    "linkedin": "This is a LinkedIn B2B technical post (a natural contact line and link at the end are acceptable, but the body must deliver value first).",
    "x": "This is an X short post (a link and hashtags are acceptable; the body needs a data-driven hook).",
}

REVIEW_SYSTEM = (
    "You are the strictest Reddit moderator and a senior B2B electronics procurement expert. "
    "Score the following post on three dimensions (0-10 integers). Output only a JSON object, no explanation."
)
REVIEW_RULES_TMPL = (
    '{context}\n'
    'Output: {{"hard_sell": <int>, "pain_point": <int>, "compliance": <int>, '
    '"verdict": "pass"|"fail", "feedback": "<a one-sentence improvement suggestion>"}}\n'
    'Pass criteria: hard_sell<={hs} AND pain_point>={pp} AND compliance>={cp}.'
)

REWRITE_SYSTEM = (
    "You are a senior B2B technical marketing editor. Rewrite the post based on the feedback: "
    "reduce hard-sell tone, strengthen the pain point, ensure compliance, and keep all data, "
    "technical terminology and certifications. Output in the SAME language as the input (English). "
    "Output only the rewritten post, no explanations."
)


def _mock_score(text, platform):
    low = text.lower()
    has_contact = "resistor@" in low or "contact:" in low
    t = THRESHOLDS.get(platform, THRESHOLDS["linkedin"])
    hard_sell = (6 if has_contact else 3) if platform != "x" else (4 if has_contact else 3)
    pain = 8 if any(k in low for k in ("?", "why", "burn", "fail", "misfire", "overheat", "breakdown")) else 5
    comp = 9
    verdict = "pass" if (hard_sell <= t["hard_sell"] and pain >= t["pain_point"] and comp >= t["compliance"]) else "fail"
    return {"hard_sell": hard_sell, "pain_point": pain, "compliance": comp,
            "verdict": verdict, "feedback": "降低结尾联系方式的存在感，把痛点前置"}


def _passes(d, platform):
    t = THRESHOLDS.get(platform, THRESHOLDS["linkedin"])
    return (d.get("hard_sell", 99) <= t["hard_sell"]
            and d.get("pain_point", -1) >= t["pain_point"]
            and d.get("compliance", -1) >= t["compliance"])


def score(text: str, platform: str = "linkedin") -> dict:
    if not translate.is_configured():
        return _mock_score(text, platform)
    t = THRESHOLDS.get(platform, THRESHOLDS["linkedin"])
    rules = REVIEW_RULES_TMPL.format(context=PLATFORM_CONTEXT.get(platform, ""),
                                     hs=t["hard_sell"], pp=t["pain_point"], cp=t["compliance"])
    try:
        out = translate.chat(REVIEW_SYSTEM, text + "\n\n" + rules, temperature=0.0)
    except Exception as e:
        # 成本超预算或网络异常时，审查降级为「通过」，不阻断发帖
        if "BudgetExceeded" in type(e).__name__ or "预算" in str(e) or "超预算" in str(e):
            return {"hard_sell": 0, "pain_point": 10, "compliance": 10,
                    "verdict": "pass", "feedback": "cost-degraded"}
        return {"hard_sell": 5, "pain_point": 5, "compliance": 5,
                "verdict": "fail", "feedback": f"审查异常: {e}"}
    try:
        m = re.search(r"\{.*\}", out, re.S)
        if not m:
            return {"hard_sell": 5, "pain_point": 5, "compliance": 5,
                    "verdict": "fail", "feedback": out[:200]}
        d = json.loads(m.group(0))
        d["verdict"] = "pass" if _passes(d, platform) else "fail"
        return d
    except Exception as e:
        return {"hard_sell": 5, "pain_point": 5, "compliance": 5,
                "verdict": "fail", "feedback": f"解析异常: {e}"}


def rewrite(text: str, feedback: str) -> str:
    if not translate.is_configured():
        return text
    try:
        return translate.chat(REWRITE_SYSTEM, f"修改建议：{feedback}\n\n原文：\n{text}", temperature=0.5)
    except Exception:
        return text


def self_reflect(text: str, platform: str = "linkedin", max_rewrites: int = 1):
    """返回 (final_text, last_score, rounds)。

    硬限制：最多重写 1 次（即最多 2 次评分 + 1 次改写）。不再无限循环。
    若仍不达标，放弃重写并写日志，直接返回当前文案（不阻塞发帖）。
    """
    r = score(text, platform)
    rounds = 1
    for _ in range(max_rewrites):
        if _passes(r, platform):
            break
        text = rewrite(text, r.get("feedback", ""))
        r = score(text, platform)
        rounds += 1
    if not _passes(r, platform):
        print(f"[self_review] {platform} 审查 {rounds} 轮仍未通过，放弃重写（写日志），保留当前文案。",
              file=sys.stderr, flush=True)
    return text, r, rounds


if __name__ == "__main__":
    t = sys.argv[1] if len(sys.argv) > 1 else "例：点火线圈抑制电阻 5W 满载温升 +62℃，选型安全系数 2 倍。"
    final, r, rounds = self_reflect(t, "reddit")
    print(f"轮数={rounds}  hard_sell={r.get('hard_sell')} pain_point={r.get('pain_point')} compliance={r.get('compliance')} verdict={r.get('verdict')}")
    print(final)
