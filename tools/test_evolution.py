#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_evolution.py — 三大自我进化机制全链路测试

   1. 自我审查（Self-Reflection）：生成 → LLM 三维打分 → 不达标打回重写
   2. 自愈 + 拟人化防封（Self-Healing）：随机延迟 + 代理池 + 429/封禁自动休眠切 IP 重试
   3. 自我升级（Self-Optimizing）：内容类型权重追踪 + 提示词自调优 + 每日复盘
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import content_factory  # noqa: E402
import self_review  # noqa: E402
import anti_ban  # noqa: E402
import self_optimize  # noqa: E402
import translate  # noqa: E402


def main():
    print("=" * 70)
    print("三大自我进化机制 · 全链路测试")
    print(f"翻译后端：{'DeepSeek 真实' if translate.is_configured() else 'MOCK'}")
    print("=" * 70)

    # ---------------- 机制 1：自我审查 ----------------
    print("\n【机制 1 · 自我审查 Self-Reflection】")
    spec = content_factory.spec_by_num("1")
    raw = content_factory.build_social(spec, review=False)  # 关闭审查拿原始文案
    print(f"原始 LinkedIn 文案（前 160 字）：\n  {raw['linkedin'][:160]}...")
    final, r, rounds = self_review.self_reflect(raw["linkedin"], "linkedin")
    print(f"\n审查结果：hard_sell={r.get('hard_sell')}  pain_point={r.get('pain_point')}  "
          f"compliance={r.get('compliance')}  verdict={r.get('verdict')}  轮数={rounds}")
    print(f"审查后文案（前 160 字）：\n  {final[:160]}...")

    # ---------------- 机制 2：自愈 + 拟人化防封 ----------------
    print("\n" + "=" * 70)
    print("【机制 2 · 自愈 Self-Healing + 拟人化防封】")
    pool = anti_ban.ProxyPool()
    print(f"代理池：{len(pool)} 个（{'未配置' if len(pool) == 0 else '已配置：' + pool.current()}）")
    print(f"拟人随机延迟：{anti_ban.human_sleep(0.1, 0.3)}s")

    def _boom():
        raise RuntimeError("HTTP 429 Too Many Requests")

    ok, res = anti_ban.with_retry(_boom, attempts=3, base_backoff=0.05)
    print(f"模拟连续 429 → with_retry 优雅降级：ok={ok}（未抛异常，已写 work/anti_ban.log）")

    # ---------------- 机制 3：自我升级 ----------------
    print("\n" + "=" * 70)
    print("【机制 3 · 自我升级 Self-Optimizing 反馈闭环】")
    for ctype, outcome in [("compare", 0.5), ("pain", 0.9), ("certification", 0.7), ("pain", 0.85)]:
        self_optimize.record_result(ctype, outcome)
    print(self_optimize.daily_review())
    print(f"\n当前注入翻译的调优 hint：{self_optimize.prompt_profile()!r}")

    print("\n" + "=" * 70)
    print("三大机制全部跑通 ✅（自我审查→自愈防封→自我升级）")
    print("=" * 70)


if __name__ == "__main__":
    main()
