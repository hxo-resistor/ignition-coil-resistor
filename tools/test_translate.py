#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_translate.py — 全自动英文发帖链路端到端测试

链路：选题 → content_factory（中文差异化正文）→ translate（LLM 翻译）→ LinkedIn/X 英文文案
    * 配好 HXO_LLM_API_KEY / HXO_DEEPL_AUTH_KEY 时走真实翻译
    * 未配 key 时自动切 MOCK 翻译，验证整条链路可用（配好 key 即真实）

用法：
    python tools/test_translate.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import content_factory  # noqa: E402
import translate  # noqa: E402


def main():
    if translate.is_configured():
        mode = "真实 LLM 翻译"
    else:
        os.environ["HXO_LLM_MOCK"] = "1"
        mode = "MOCK 翻译（未配 API key）"

    print("=" * 70)
    print(f"全自动英文发帖链路测试  模式={mode}")
    print("=" * 70)

    for num in ("1", "5", "15"):
        spec = content_factory.spec_by_num(num)
        s = content_factory.build_social(spec)
        print(f"\n【选题 #{num}】{spec['title']}")
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
    print("链路验证：选题 → 内容工厂 → 翻译 → LinkedIn/X 文案 全部生成成功 ✅")
    if not translate.is_configured():
        print("提示：当前为 MOCK 翻译。配置 HXO_LLM_API_KEY（+BASE_URL/MODEL）或")
        print("      HXO_DEEPL_AUTH_KEY 后，重跑本脚本即为真实英文翻译。")
    print("=" * 70)


if __name__ == "__main__":
    main()
