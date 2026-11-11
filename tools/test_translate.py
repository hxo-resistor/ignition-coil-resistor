#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_translate.py — 全自动英文发帖链路端到端测试（DeepSeek 真翻译）

链路：选题 → content_factory（中文差异化正文）→ DeepSeek 翻译 → LinkedIn/X 英文文案
前置：需已配置 DEEPSEEK_API_KEY 环境变量。

用法：
    python tools/test_translate.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import content_factory  # noqa: E402
import translate  # noqa: E402


def main():
    if not translate.is_configured():
        print("=" * 70)
        print("未检测到 DEEPSEEK_API_KEY。")
        print("请到 https://platform.deepseek.com 申请 key，然后设置：")
        print('    setx DEEPSEEK_API_KEY "sk-..."')
        print("设置后重跑本脚本。")
        print("=" * 70)
        raise SystemExit(2)

    print("=" * 70)
    print("全自动英文发帖链路测试（DeepSeek 真实翻译）")
    print("=" * 70)

    for num in ("1", "5", "15"):
        spec = content_factory.spec_by_num(num)
        s = content_factory.build_social(spec)
        print(f"\n【选题 #{num}】")
        print(f"  中文标题: {spec['title']}")
        print(f"  英文标题: {s['title_en']}")
        print("-" * 60)
        print("[LinkedIn 长文]")
        print(s["linkedin"])
        print("\n[X 短文]")
        print(s["x"])
        n = len(s["x"])
        print(f"\n  X 长度校验: {n} 字符  {'✅ ≤280' if n <= 280 else '❌ 超长'}")

    print("\n" + "=" * 70)
    print("链路验证：选题 → 内容工厂 → DeepSeek 翻译 → LinkedIn/X 文案 全部生成 ✅")
    print("=" * 70)


if __name__ == "__main__":
    main()
