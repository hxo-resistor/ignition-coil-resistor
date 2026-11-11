#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_proxy.py — 代理池 IP 连通性测试

逐个测试 HXO_PROXY_POOL（逗号分隔）或 HXO_PROXY 里的代理，
检测连通性 + 延迟 + 出口 IP，识别已被目标站拉黑/失效的 IP。

用法：
    python tools/test_proxy.py
    python tools/test_proxy.py --target https://www.reddit.com
    python tools/test_proxy.py --target https://httpbin.org/ip
"""
import argparse
import os
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    import requests
except ImportError:
    requests = None


def get_proxies():
    raw = os.environ.get("HXO_PROXY_POOL", "") or os.environ.get("HXO_PROXY", "")
    return [p.strip() for p in raw.split(",") if p.strip()]


def test_proxy(proxy, target, timeout):
    proxies = {"http": proxy, "https": proxy}
    t0 = time.time()
    try:
        r = requests.get(target, proxies=proxies, timeout=timeout, allow_redirects=True)
        dur = time.time() - t0
        body = r.text[:80].replace("\n", " ").replace("\r", "")
        return True, r.status_code, round(dur, 2), body
    except Exception as e:
        return False, None, round(time.time() - t0, 2), str(e)[:80]


def main():
    ap = argparse.ArgumentParser(description="代理池 IP 连通性测试")
    ap.add_argument("--target", default="https://www.reddit.com")
    ap.add_argument("--timeout", type=float, default=12.0)
    args = ap.parse_args()

    if requests is None:
        print("缺少 requests 库：pip install requests")
        sys.exit(2)

    proxies = get_proxies()
    if not proxies:
        print("未配置 HXO_PROXY_POOL / HXO_PROXY。请先设置，例如：")
        print('  setx HXO_PROXY_POOL "http://ip1:port,http://ip2:port"')
        sys.exit(0)

    print(f"测试目标：{args.target}")
    print(f"代理数量：{len(proxies)}")
    print("-" * 70)
    ok_cnt = 0
    for p in proxies:
        ok, status, dur, detail = test_proxy(p, args.target, args.timeout)
        flag = "✅ 可用" if ok else "❌ 失效"
        if ok:
            ok_cnt += 1
        print(f"[{flag}] {p:<28} {'HTTP '+str(status) if ok else '失败':<12} {dur}s  {detail}")
    print("-" * 70)
    print(f"结论：{ok_cnt}/{len(proxies)} 个代理可用")
    if ok_cnt == 0:
        print("⚠️ 所有代理均无法连通目标站，Reddit/X 会秒封。请更换高质量住宅/移动 IP。")


if __name__ == "__main__":
    main()
