#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""anti_ban.py — 自愈（Self-Healing）+ 拟人化防封

针对 Reddit / X 的高风控，提供：
    1. 拟人化：随机延迟、操作轨迹抖动、打字节奏
    2. 环境隔离：代理池（HXO_PROXY_POOL，逗号分隔；回退 HXO_PROXY）
    3. 自愈：捕获 429/403/封禁类错误 → 指数+随机休眠（可数小时）→ 切 IP → 重试
    4. 绝不抛异常崩溃：统一 with_retry 包裹，失败优雅降级，日志落盘 work/anti_ban.log
"""
import logging
import os
import random
import time
from pathlib import Path

try:
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

LOG_FILE = Path(__file__).resolve().parent.parent / "work" / "anti_ban.log"

_logger = None


def log():
    global _logger
    if _logger is None:
        _logger = logging.getLogger("anti_ban")
        if not _logger.handlers:
            _logger.setLevel(logging.INFO)
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            h = logging.FileHandler(LOG_FILE, encoding="utf-8")
            h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
            _logger.addHandler(h)
    return _logger


# ---------------------------------------------------------------------------
# 拟人化
# ---------------------------------------------------------------------------
def human_sleep(lo: float, hi: float) -> float:
    """随机均匀延迟（秒），返回实际睡眠时长。"""
    d = random.uniform(lo, hi)
    time.sleep(d)
    return round(d, 2)


def jitter(base: float, spread: float = 0.4) -> float:
    """以 base 为中心 ±spread 比例的随机抖动。"""
    return base * random.uniform(1 - spread, 1 + spread)


def human_trace(text: str) -> None:
    """模拟人工输入轨迹：按字符数累计小延迟。"""
    delay = 0.02 + random.uniform(0, 0.05)
    time.sleep(delay * min(len(text), 200))


# ---------------------------------------------------------------------------
# 代理池 / IP 隔离
# ---------------------------------------------------------------------------
class ProxyPool:
    def __init__(self):
        raw = os.environ.get("HXO_PROXY_POOL", "") or os.environ.get("HXO_PROXY", "")
        self.proxies = [p.strip() for p in raw.split(",") if p.strip()]
        self.i = 0

    def current(self):
        return self.proxies[self.i] if self.proxies else None

    def rotate(self):
        if self.proxies:
            self.i = (self.i + 1) % len(self.proxies)
        return self.current()

    def __len__(self):
        return len(self.proxies)


# ---------------------------------------------------------------------------
# 自愈重试
# ---------------------------------------------------------------------------
_BAN_KEYWORDS = ("429", "403", "rate limit", "banned", "blocked", "too many requests",
                 "temporarily", "forbidden", "suspended")


def is_ban(err) -> bool:
    s = str(err).lower()
    return any(k in s for k in _BAN_KEYWORDS)


def with_retry(fn, *, attempts: int = 3, base_backoff: float = 60.0,
               max_backoff: float = 6 * 3600, proxies=None):
    """执行 fn()，遇封禁/限流自动休眠切 IP 重试，绝不抛异常。

    返回 (ok: bool, result)。失败时优雅降级并写日志。
    """
    pool = proxies if proxies is not None else ProxyPool()
    for i in range(attempts):
        try:
            return True, fn()
        except Exception as e:
            if is_ban(e):
                backoff = min(max_backoff, base_backoff * (2 ** i)) + random.uniform(0, base_backoff)
                log().warning(f"封禁/限流：{e} → 休眠 {backoff:.0f}s 后切 IP 重试 ({i + 1}/{attempts})")
                time.sleep(backoff)
                log().info(f"切换代理 -> {pool.rotate()}")
            else:
                backoff = jitter(5.0, 0.5)
                log().error(f"非封禁错误（短暂重试）：{e}")
                time.sleep(backoff)
    log().error(f"重试 {attempts} 次仍失败，优雅降级（不抛异常）")
    return False, None


if __name__ == "__main__":
    print("代理池：", len(ProxyPool()), "个代理")
    print("拟人延迟演示：", human_sleep(0.1, 0.3), "s")
    # 演示：模拟连续封禁，最终优雅降级
    def _boom():
        raise RuntimeError("429 Too Many Requests")
    ok, result = with_retry(_boom, attempts=3, base_backoff=0.05)
    print("with_retry 结果：", ok, result, "（未崩溃）")
