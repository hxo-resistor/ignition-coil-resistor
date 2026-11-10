#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tz.py — 多时区黄金发布窗口判断

国内（CN）：北京时间上午 9:00~11:00（工作日）发布。
海外（INTL）：目标「美东 9:00~11:00 AM（工作日）」黄金窗口，
            自动用 zoneinfo 换算成北京时间，跟随美国冬夏令时（EST/EDT）自动切换。

用法：
    python tools/tz.py                # 打印当前各区域黄金窗口状态 + 下次触发时间
"""
import datetime as dt
import sys
from zoneinfo import ZoneInfo

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CN_TZ = ZoneInfo("Asia/Shanghai")
US_EAST = ZoneInfo("America/New_York")
US_WEST = ZoneInfo("America/Los_Angeles")

# 黄金窗口（当地时区的小时范围）
CN_GOLDEN = (9, 11)          # 北京时间 9~11 点
US_EAST_GOLDEN = (9, 11)     # 美东 9~11 AM
US_WEST_GOLDEN = (8, 11)     # 美西 8~11 AM（与美东重叠的合理时段）

WEEKDAYS = {0, 1, 2, 3, 4}   # 周一~周五


def _local_hour(now: dt.datetime, tz) -> int:
    return now.astimezone(tz).hour


def cn_golden(now: dt.datetime | None = None) -> bool:
    """北京时间工作日 9~11 点。"""
    now = now or dt.datetime.now(CN_TZ)
    lo, hi = CN_GOLDEN
    return now.weekday() in WEEKDAYS and lo <= now.hour < hi


def us_east_golden(now: dt.datetime | None = None) -> bool:
    """当前时刻的美东时间是否落在 9~11 AM 工作日。"""
    now = now or dt.datetime.now(CN_TZ)
    local = now.astimezone(US_EAST)
    lo, hi = US_EAST_GOLDEN
    return local.weekday() in WEEKDAYS and lo <= local.hour < hi


def us_west_golden(now: dt.datetime | None = None) -> bool:
    """当前时刻的美西时间是否落在 8~11 AM 工作日。"""
    now = now or dt.datetime.now(CN_TZ)
    local = now.astimezone(US_WEST)
    lo, hi = US_WEST_GOLDEN
    return local.weekday() in WEEKDAYS and lo <= local.hour < hi


def intl_golden(now: dt.datetime | None = None) -> bool:
    """海外黄金窗口：美东或美西任一落在窗口即可（覆盖两海岸）。"""
    return us_east_golden(now) or us_west_golden(now)


def _next_weekday_trigger(now: dt.datetime, tz, target_hour: int) -> dt.datetime:
    """返回「下一个工作日、当地 target_hour 点」对应的时刻（aware）。"""
    local = now.astimezone(tz)
    # 今天 target_hour 已经过了 → 明天开始找
    start = local.date()
    if local.hour >= target_hour:
        start = start + dt.timedelta(days=1)
    d = start
    while d.weekday() not in WEEKDAYS:
        d = d + dt.timedelta(days=1)
    return dt.datetime(d.year, d.month, d.day, target_hour, 0, tzinfo=tz)


def next_intl_trigger(now: dt.datetime | None = None) -> dt.datetime:
    """下一次海外发布触发时间（美东 9:00 换算到北京时间）。"""
    now = now or dt.datetime.now(CN_TZ)
    trigger_et = _next_weekday_trigger(now, US_EAST, 9)
    return trigger_et.astimezone(CN_TZ)


def next_cn_trigger(now: dt.datetime | None = None) -> dt.datetime:
    """下一次国内发布触发时间（北京时间 10:00）。"""
    now = now or dt.datetime.now(CN_TZ)
    return _next_weekday_trigger(now, CN_TZ, 10)


def status_report():
    now = dt.datetime.now(CN_TZ)
    now_et = now.astimezone(US_EAST)
    now_pt = now.astimezone(US_WEST)
    lines = [
        f"现在（北京）: {now:%Y-%m-%d %H:%M %a}",
        f"现在（美东）: {now_et:%Y-%m-%d %H:%M %a}",
        f"现在（美西）: {now_pt:%Y-%m-%d %H:%M %a}",
        f"国内黄金窗口: {'✅ 命中' if cn_golden(now) else '❌ 未命中'}",
        f"海外黄金窗口: {'✅ 命中' if intl_golden(now) else '❌ 未命中'}",
        f"下次国内触发（北京）: {next_cn_trigger(now):%Y-%m-%d %H:%M}",
        f"下次海外触发（北京）: {next_intl_trigger(now):%Y-%m-%d %H:%M}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print(status_report())
