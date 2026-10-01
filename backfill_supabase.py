# -*- coding: utf-8 -*-
"""
backfill_supabase.py — Supabase content_packages 补同步脚本（收尾诊断产出）

两部分操作（共 10 条写入 + 1 次只读查询）：
  A. 6 条 INSERT：早期手动发布、未进库的 6 篇官网文章
  B. 4 条 UPDATE：sync_status=pending 的 4 条历史记录 -> synced

安全设计：
  - 默认 DRY_RUN：只打印将执行的操作清单，不写入任何数据（GET 只读查询允许执行，用于定位 pending 行）
  - 命令行带 --execute 才真正 POST/PATCH
  - 与 publish_b2b_package_v2.py 的 CONFIG 保持一致（URL / anon key / proxy）

用法：
  python backfill_supabase.py           # DRY_RUN，仅打印
  python backfill_supabase.py --execute # 真正写入
"""
import os
import re
import sys
import requests

# ---- 与 publish_b2b_package_v2.py CONFIG 保持一致 ----
SUPA_URL = 'https://whnmtkrmvqayfhpmrdiq.supabase.co'
SUPA_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indobm10a3JtdnFheWZocG1yZGlxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcwNDU5MjEsImV4cCI6MjEwMjYyMTkyMX0.MHTyZOGYd5KvnwGclq2oI2xua2rbXPHJ--AGmZOGhoE'
PROXY = 'http://127.0.0.1:7897'
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
ENDPOINT = SUPA_URL + '/rest/v1/content_packages'

# ---- A. 6 条 INSERT：(html 文件, 建议 product_id, 日期取 git 首提交) ----
INSERTS = [
    ('article_discharge_calculation.html', 'hv-wirewound',  '2026-09-22'),
    # 修复(2026-08-21)：键 (2026-09-22, hv-wirewound) 已被「泄放电阻计算指南」占用 -> HTTP 409。
    # 充电桩泄放电阻属既有类目 product_id='bleeder'（库内 2026-09-15 已有该类目行），日期保持 git 真实发布日 2026-09-22。
    ('article_ev_pile_bleeder.html',       'bleeder',       '2026-09-22'),
    ('article_ig_s_patent.html',           'ig-s',          '2026-09-22'),
    ('article_otp_vs_fuse.html',           'rxf-otp-1w',    '2026-09-22'),
    ('article_rxf_charger_protection.html','rxf-otp-1w',    '2026-09-14'),
    ('article_wirewound_vs_thickfilm.html','hv-wirewound',  '2026-09-25'),
]

HEADERS = {
    'apikey': SUPA_KEY,
    'Authorization': 'Bearer ' + SUPA_KEY,
    'Content-Type': 'application/json',
}
PROXIES = {'http': PROXY, 'https': PROXY}


def extract_title(html_file):
    html = open(os.path.join(REPO_DIR, html_file), encoding='utf-8').read()
    m = re.search(r'<title>(.*?)</title>', html, re.S)
    return m.group(1).strip() if m else '(title not found)'


def build_insert_payload(html_file, product_id, date):
    content = open(os.path.join(REPO_DIR, html_file), encoding='utf-8').read()
    return {
        'date': date,
        'product_id': product_id,
        'title': extract_title(html_file),
        'content_md': content,          # 与 v2 一致：存 HTML 全文
        'source': 'supplementary_sync',
        'status': 'published',
        'sync_status': 'synced',
    }


def get_pending_rows():
    """只读查询：定位 sync_status=pending 的行（用于 B 部分按 id 精准 UPDATE）"""
    r = requests.get(ENDPOINT, params={'sync_status': 'eq.pending', 'select': 'id,title,source,date'},
                      headers=HEADERS, proxies=PROXIES, timeout=30)
    if r.status_code != 200:
        print('  [WARN] GET pending 失败: HTTP {} {}'.format(r.status_code, r.text[:200]))
        return None
    return r.json()


def row_exists(date, product_id):
    """只读检查：键 (date, product_id) 是否已有行。True/False；查询失败返回 None。"""
    r = requests.get(ENDPOINT,
                     params={'date': 'eq.' + date, 'product_id': 'eq.' + product_id, 'select': 'id'},
                     headers=HEADERS, proxies=PROXIES, timeout=30)
    if r.status_code != 200:
        return None
    return len(r.json()) > 0


def do_inserts(execute):
    print('\n===== A. INSERT 6 条（缺库文章，幂等：已存在则跳过）=====')
    ok = 0
    skipped = 0
    for i, (f, pid, date) in enumerate(INSERTS, 1):
        path = os.path.join(REPO_DIR, f)
        if not os.path.exists(path):
            print('  [{}/6] {} 文件缺失，跳过'.format(i, f))
            continue
        exists = row_exists(date, pid)
        if exists:
            print('  [{}/6] {} (date={}, product_id={}) 已存在 -> SKIP（幂等，不重复写入）'.format(i, f, date, pid))
            skipped += 1
            continue
        if exists is None:
            print('  [{}/6] [WARN] {} 存在性检查 GET 失败，按原逻辑直接 POST'.format(i, f))
        payload = build_insert_payload(f, pid, date)
        if execute:
            r = requests.post(ENDPOINT, json=payload, headers=dict(HEADERS, Prefer='return=minimal'),
                              proxies=PROXIES, timeout=60)
            good = r.status_code in (200, 201)
            print('  [{}/6] {} product_id={} date={} title={} -> HTTP {} {}'.format(
                i, f, pid, date, payload['title'][:40], r.status_code, 'OK' if good else r.text[:200]))
        else:
            print('  [{}/6] [DRY_RUN] POST content_packages | file={} | product_id={} | date={} | title={} | content={}chars'.format(
                i, f, pid, date, payload['title'][:50], len(payload['content_md'])))
        ok += 1
    print('  A 部分完成：将写入 {} 条，跳过已存在 {} 条'.format(ok, skipped))


def do_updates(execute):
    print('\n===== B. UPDATE 4 条（pending -> synced）=====')
    rows = get_pending_rows()
    if rows is None:
        # 回退：按诊断时记录到的 4 个库内标题做 title=eq 更新（execute 模式下仍会尝试）
        rows = None
        fallback = True
    else:
        fallback = False
        if len(rows) != 4:
            print('  [WARN] 期望 4 条 pending，实际查到 {} 条，请人工核对后再 --execute'.format(len(rows)))

    if not fallback:
        for i, row in enumerate(rows, 1):
            filt = 'id=eq.' + str(row['id']) if 'id' in row else 'title=eq.' + row['title']
            if execute:
                # 修复(2026-08-21)：过滤条件直接拼入 URL（原 params={filt:''} 产生空值参数 -> HTTP 400）
                r = requests.patch(ENDPOINT + '?' + filt, json={'sync_status': 'synced'},
                                   headers=HEADERS, proxies=PROXIES, timeout=30)
                tag = 'OK' if r.status_code in (200, 204) else r.text[:200]
                print('  [{}/{}] {} -> HTTP {} {}'.format(i, len(rows), row.get('title', '(?)')[:50], r.status_code, tag))
                if r.status_code in (200, 204):
                    rr = requests.get(ENDPOINT + '?' + filt + '&select=sync_status',
                                      headers=HEADERS, proxies=PROXIES, timeout=30)
                    print('       回查 sync_status =', rr.json() if rr.status_code == 200 else 'HTTP ' + str(rr.status_code))
            else:
                print('  [{}/{}] [DRY_RUN] PATCH content_packages?{} | title={} | source={} | date={} | sync_status: pending -> synced'.format(
                    i, len(rows), filt, row.get('title', '(?)')[:50], row.get('source'), row.get('date')))
    else:
        # 无法定位行时，按诊断记录的 4 条标题打印（execute 模式下逐个 PATCH title=eq）
        known = [
            'IG-C Ceramic Ignition Coil Resistor',
            'RXF 1W 12Ω 221°C OTP Temperature Fuse',
            'High-Value Wirewound Resistor - Capacitor',
            '点火系统的EMI干扰怎么抑制？三种抑制电阻选型指南 | HXO Resi',
        ]
        print('  [FALLBACK] GET 失败，按诊断记录标题匹配（title=eq，前缀需人工确认）')
        for i, t in enumerate(known, 1):
            filt = 'title=ilike.{}%'.format(t[:40])
            if execute:
                r = requests.patch(ENDPOINT + '?' + filt, json={'sync_status': 'synced'},
                                   headers=HEADERS, proxies=PROXIES, timeout=30)
                print('  [{}] {} -> HTTP {} {}'.format(i, t[:50], r.status_code,
                                                       'OK' if r.status_code in (200, 204) else r.text[:200]))
            else:
                print('  [{}/4] [DRY_RUN] PATCH content_packages?{} -> synced'.format(i, filt))


def main():
    execute = '--execute' in sys.argv
    print('backfill_supabase.py  |  mode = ' + ('EXECUTE (真正写入)' if execute else 'DRY_RUN (仅打印)'))
    if execute:
        print('  即将写入 6 条 INSERT + 4 条 UPDATE，Ctrl+C 可中止')
        import time
        time.sleep(3)
    do_inserts(execute)
    do_updates(execute)
    print('\n完成。' + (' 已写入 Supabase。' if execute else ' 未写入任何数据（DRY_RUN）。'))


if __name__ == '__main__':
    main()
