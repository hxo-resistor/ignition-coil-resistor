#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""translate.py — DeepSeek 自动翻译（中 → 英，B2B 电子专业语境）

默认使用 DeepSeek（国内直连、便宜、质量高）：
    DEEPSEEK_API_KEY   必填。API Key（申请：https://platform.deepseek.com）
    DEEPSEEK_BASE_URL  可选。默认 https://api.deepseek.com/v1
    DEEPSEEK_MODEL     可选。默认 deepseek-chat

也可用通用 OpenAI 兼容变量覆盖（接其它厂商时用）：
    HXO_LLM_API_KEY / HXO_LLM_BASE_URL / HXO_LLM_MODEL

用法：
    python tools/translate.py --text "点火线圈抑制电阻怎么选？" --lang en
"""
import argparse
import os
import sys

import requests

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-chat"

# 强调：高转化 B2B 文案，不是机翻；保留专业术语、单位、公式、Hashtag
SYSTEM_PROMPT = (
    "You are a senior B2B electronics copywriter and technical translator. "
    "Translate the Chinese text into punchy, native, professional English suitable for LinkedIn/X marketing posts. "
    "Keep the hook engaging and sales-relevant. Keep numbers, units, formulas and product codes "
    "(IG-C, IG-F, IG-S, RXF, HVW, CISPR, RoHS, REACH, AEC-Q200, etc.) unchanged. "
    "Keep any '#' hashtags unchanged. "
    "Output only the translated text — no explanations, no quotation marks, no extra commentary."
)


def is_configured() -> bool:
    return bool(_api_key())


def _api_key() -> str:
    return os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("HXO_LLM_API_KEY") or ""


def _base_url() -> str:
    return os.environ.get("HXO_LLM_BASE_URL") or os.environ.get("DEEPSEEK_BASE_URL") or DEFAULT_BASE_URL


def _model() -> str:
    return os.environ.get("HXO_LLM_MODEL") or os.environ.get("DEEPSEEK_MODEL") or DEFAULT_MODEL


def translate(text: str, target: str = "en") -> str:
    """翻译一段中文为英文。未配置 key 时抛出明确错误。"""
    if not text or not text.strip():
        return text
    key = _api_key()
    if not key:
        raise RuntimeError(
            "未配置 DEEPSEEK_API_KEY。请到 https://platform.deepseek.com 申请，"
            "然后用 `setx DEEPSEEK_API_KEY \"sk-...\"` 设置。"
        )
    url = _base_url().rstrip("/") + "/chat/completions"
    payload = {
        "model": _model(),
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "temperature": 0.3,
    }
    r = requests.post(url, json=payload, timeout=120,
                      headers={"Authorization": f"Bearer {key}"})
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"].strip()


def main():
    ap = argparse.ArgumentParser(description="DeepSeek 自动翻译")
    ap.add_argument("--text", required=True)
    ap.add_argument("--lang", default="en")
    args = ap.parse_args()
    if not is_configured():
        print("未配置 DEEPSEEK_API_KEY，无法翻译。", file=sys.stderr)
        raise SystemExit(2)
    print(translate(args.text, args.lang))


if __name__ == "__main__":
    main()
