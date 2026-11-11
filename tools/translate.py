#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""translate.py — LLM 自动翻译（多 provider 可插拔）

按环境变量自动选择 provider：
    * OpenAI 兼容接口（DeepSeek / OpenAI / 豆包 / 智谱 / 月之暗面 等通用）
        HXO_LLM_BASE_URL   e.g. https://api.deepseek.com/v1
        HXO_LLM_API_KEY    your api key
        HXO_LLM_MODEL      e.g. deepseek-chat / gpt-4o-mini（默认 gpt-4o-mini）
    * DeepL（可选）
        HXO_DEEPL_AUTH_KEY your deepl key（默认 api-free 端点）
    * MOCK（无 key 时）—— 返回带 [MOCK] 标记的占位，仅用于链路测试

可选：
    HXO_LLM_PROXY         http://127.0.0.1:7897（访问海外 API 时用）

用法：
    python tools/translate.py --text "点火线圈抑制电阻怎么选？" --lang en
"""
import argparse
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

SYSTEM_PROMPT = (
    "You are a professional technical translator for electronics and B2B industrial content. "
    "Translate the given Chinese text into idiomatic, concise English. "
    "Keep numbers, units, formulas, and product codes (IG-C, IG-F, IG-S, RXF, HVW, CISPR, RoHS, REACH, AEC-Q200) unchanged. "
    "Keep any '#' hashtags unchanged. Output only the translation, with no explanations or quotes."
)


def is_configured() -> bool:
    return bool(os.environ.get("HXO_DEEPL_AUTH_KEY") or os.environ.get("HXO_LLM_API_KEY"))


def _proxies():
    p = os.environ.get("HXO_LLM_PROXY", "")
    if p:
        return {"http": p, "https": p}
    return None


def _openai_translate(text: str, target: str) -> str:
    base = os.environ.get("HXO_LLM_BASE_URL", "").rstrip("/")
    key = os.environ.get("HXO_LLM_API_KEY", "")
    model = os.environ.get("HXO_LLM_MODEL", "gpt-4o-mini")
    if not base or not key:
        raise RuntimeError("HXO_LLM_BASE_URL / HXO_LLM_API_KEY 未配置")
    url = base + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "temperature": 0.3,
    }
    r = requests.post(url, json=payload, timeout=60,
                      headers={"Authorization": f"Bearer {key}"},
                      proxies=_proxies())
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"].strip()


def _deepl_translate(text: str, target: str) -> str:
    key = os.environ.get("HXO_DEEPL_AUTH_KEY", "")
    if not key:
        raise RuntimeError("HXO_DEEPL_AUTH_KEY 未配置")
    is_pro = ":fx" in key
    host = "https://api.deepl.com/v2" if is_pro else "https://api-free.deepl.com/v2"
    r = requests.post(host + "/translate", timeout=60, data={
        "auth_key": key, "text": text,
        "target_lang": target.upper(), "source_lang": "ZH",
    }, proxies=_proxies())
    r.raise_for_status()
    return r.json()["translations"][0]["text"].strip()


def _mock_translate(text: str, target: str) -> str:
    return f"[MOCK-{target.upper()}] {text}"


def translate(text: str, target: str = "en") -> str:
    """翻译一段中文为英文。无 key 时走 mock（仅测试）。"""
    if not text or not text.strip():
        return text
    try:
        if os.environ.get("HXO_DEEPL_AUTH_KEY"):
            return _deepl_translate(text, target)
        if os.environ.get("HXO_LLM_API_KEY"):
            return _openai_translate(text, target)
    except Exception as e:
        print(f"[translate] 翻译失败，回退 mock：{e}", file=sys.stderr, flush=True)
    return _mock_translate(text, target)


def main():
    ap = argparse.ArgumentParser(description="LLM 自动翻译")
    ap.add_argument("--text", required=True)
    ap.add_argument("--lang", default="en")
    args = ap.parse_args()
    if not is_configured():
        print("[提示] 未配置 API key，使用 MOCK 翻译。", file=sys.stderr)
    print(translate(args.text, args.lang))


if __name__ == "__main__":
    main()
