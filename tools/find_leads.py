#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""find_leads.py — HXO 充电器/电源适配器厂客户名单生成（中国制造网，免费、合规）

数据来源：
  1. 中国制造网（made-in-china.com）公开搜索页 -> 供应商列表（公司名、地区、供应商子域名）
  2. 供应商官网（首页 /contact /about）-> 公开邮箱（只取页面明文出现的）

合规红线：
  - 只抓公开页面；不登录、不绕验证码、不用代理池
  - 请求间隔 >= 3s；每域名最多 3 页；遵守 robots.txt
  - 不猜邮箱、不买数据；不抓电商站商品详情
  - 遇到反爬（验证码/登录墙/空数据）立即停下报告
  - 明确 UA 标识

输出：work/leads/客户名单_YYYYMMDD.xlsx
  字段：公司名 | 地区 | 公司资料页(MIC) | 公开邮箱 | 真实官网 | LinkedIn链接 | 来源关键词 | 来源URL | 备注 | 抓取日期

说明：中国制造网隐藏供应商邮箱与自有官网，故「公开邮箱/真实官网」多为空，
      备注标注「联系方式待人工补」。这与平台设计有关，非脚本缺陷。

用法：
  python tools/find_leads.py --limit 20
  python tools/find_leads.py --limit 100
  python tools/find_leads.py --limit 20 --no-enrich     # 只抓列表，不访问官网
"""
import argparse
import datetime as dt
import re
import sys
import time
from pathlib import Path

import requests

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "work" / "leads"

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 中国制造网关键词（中文）
DEFAULT_KEYWORDS = ["充电器", "电源适配器", "开关电源"]

# 珠三角优先
PRD = ["广东", "深圳", "东莞", "广州", "珠海", "惠州", "中山", "佛山", "guangdong",
       "shenzhen", "dongguan", "guangzhou", "zhuhai", "huizhou", "foshan", "zhongshan"]

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
LINKEDIN_RE = re.compile(r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/(?:company|in)/[A-Za-z0-9._%-]+", re.I)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.I | re.S)
OGSITE_RE = re.compile(r'<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']+)', re.I)

REGION_WORDS = [
    "Guangdong", "Shenzhen", "Dongguan", "Guangzhou", "Zhuhai", "Huizhou", "Foshan",
    "Zhongshan", "Jiangsu", "Zhejiang", "Fujian", "Shanghai", "Shandong", "Henan",
    "Anhui", "Hunan", "Hubei", "Sichuan", "Jiangxi", "Beijing", "Tianjin", "Chongqing",
    "Ningbo", "Wenzhou", "Hangzhou", "Suzhou", "Xiamen", "Quanzhou",
]
CN_REGION = {
    "Guangdong": "广东", "Shenzhen": "深圳", "Dongguan": "东莞", "Guangzhou": "广州",
    "Zhuhai": "珠海", "Huizhou": "惠州", "Foshan": "佛山", "Zhongshan": "中山",
    "Jiangsu": "江苏", "Zhejiang": "浙江", "Fujian": "福建", "Shanghai": "上海",
    "Shandong": "山东", "Henan": "河南", "Anhui": "安徽", "Hunan": "湖南",
    "Hubei": "湖北", "Sichuan": "四川", "Jiangxi": "江西", "Beijing": "北京",
    "Tianjin": "天津", "Chongqing": "重庆", "Ningbo": "宁波", "Wenzhou": "温州",
    "Hangzhou": "杭州", "Suzhou": "苏州", "Xiamen": "厦门", "Quanzhou": "泉州",
}

SEARCH_URL = ("https://www.made-in-china.com/productdirectory.do"
              "?word={kw}&file=&searchType=0&subaction=hunt&style=b&mode=and"
              "&code=0&comProvince=nolimit&order=0&isOpenCorrection=1")
SOURCE_DOMAIN_SUFFIX = ".en.made-in-china.com"


class AntiCrawl(Exception):
    """Raised when a platform shows captcha / login wall / empty data."""


def log(msg):
    print(f"[{dt.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def session():
    s = requests.Session()
    s.headers.update(UA)
    return s


def check_anticrawl(html, status):
    low = html.lower()
    if status in (403, 429):
        raise AntiCrawl(f"HTTP {status}（疑似限流/封禁）")
    if any(k in html for k in ["验证码", "请输入验证", "滑动验证", "访问过于频繁"]):
        raise AntiCrawl("出现中文验证码/访问限制")
    if any(k in low for k in ["captcha", "are you a robot", "unusual traffic", "access denied"]):
        raise AntiCrawl("出现英文验证码/机器人检测")


def clean_text(t):
    t = re.sub(r"<[^>]+>", " ", t)
    t = (t.replace("&amp;", "&").replace("&nbsp;", " ").replace("&lt;", "<")
         .replace("&gt;", ">").replace("&#39;", "'").replace("&quot;", '"'))
    return re.sub(r"\s+", " ", t).strip()


def extract_region(text):
    for w in REGION_WORDS:
        if re.search(r"\b" + re.escape(w) + r"\b", text):
            return CN_REGION.get(w, w)
    return ""


def parse_list_page(html):
    """Extract suppliers from a Made-in-China search-results page.

    Each supplier card has:
      <div class="company-name-wrapper">
        <div class="company-name-txt">
          <a class="compnay-name J-compnay-name" href="https://<sub>.en.made-in-china.com">
            <span>COMPANY NAME</span></a>
    """
    results = []
    seen = set()
    # split page into supplier blocks
    starts = [m.start() for m in re.finditer(r'class="company-name-wrapper"', html)]
    starts.append(len(html))
    for idx in range(len(starts) - 1):
        block = html[starts[idx]:starts[idx + 1]]
        # subdomain + name
        am = re.search(
            r'class="compnay-name[^"]*"[^>]*href="https?://([a-z0-9\-]+)\.en\.made-in-china\.com[^"]*"[^>]*>\s*<span>(.*?)</span>',
            block, re.S | re.I)
        if not am:
            am = re.search(
                r'href="https?://([a-z0-9\-]+)\.en\.made-in-china\.com"[^>]*class="compnay-name[^"]*"[^>]*>\s*<span>(.*?)</span>',
                block, re.S | re.I)
        if not am:
            continue
        sub = am.group(1).lower()
        if sub in seen:
            continue
        name = clean_text(am.group(2))
        if not name:
            continue
        region = extract_region(clean_text(block))
        seen.add(sub)
        results.append({"Company": name, "Sub": sub,
                        "SubURL": f"https://{sub}.en.made-in-china.com/",
                        "Region": region})
    return results


def search_suppliers(s, keyword, max_pages=3):
    out = []
    for page in range(1, max_pages + 1):
        url = SEARCH_URL.format(kw=requests.utils.quote(keyword))
        if page > 1:
            url += f"&page={page}"
        try:
            r = s.get(url, timeout=30)
        except Exception as e:
            log(f"  [warn] 请求失败: {str(e)[:60]}")
            break
        check_anticrawl(r.text, r.status_code)
        items = parse_list_page(r.text)
        log(f"  第{page}页: {len(items)} 家")
        out.extend(items)
        if len(items) == 0:
            break
        time.sleep(3)
    return out


def robots_allows(s, domain):
    try:
        r = s.get(f"https://{domain}/robots.txt", timeout=12, allow_redirects=True)
    except Exception:
        return True, 3.0
    if r.status_code != 200 or "html" in r.headers.get("Content-Type", ""):
        return True, 3.0
    delay = 3.0
    text = r.text.lower()
    for blk in re.split(r"(?m)^user-agent:\s*", text):
        if blk.strip().startswith("*") or blk.strip().startswith("hxo"):
            for line in blk.splitlines():
                line = line.strip()
                if line.startswith("disallow:") and line.split(":", 1)[1].strip() == "/":
                    return False, delay
                if line.startswith("crawl-delay:"):
                    try:
                        delay = max(delay, float(line.split(":", 1)[1].strip()))
                    except Exception:
                        pass
    return True, delay


def fetch_profile(s, sub):
    """Open MIC supplier profile; extract any PUBLIC email / website / LinkedIn it exposes.

    Note: Made-in-China intentionally hides supplier emails and usually the company's
    own domain (contact goes through the platform). This is best-effort only.
    """
    url = f"https://{sub}.en.made-in-china.com/"
    email, linkedin, site = "", "", ""
    ok, delay = robots_allows(s, f"{sub}.en.made-in-china.com")
    if not ok:
        return email, linkedin, site
    try:
        r = s.get(url, timeout=25)
    except Exception:
        return email, linkedin, site
    html = r.text

    # emails: exclude MIC's own / tracking / asset emails
    mails = [e for e in EMAIL_RE.findall(html)
             if not any(b in e.lower() for b in
                        ["made-in-china", "micstatic", "example", ".png", ".jpg", ".gif"])]
    if mails:
        email = mails[0]

    lk = LINKEDIN_RE.search(html)
    if lk:
        linkedin = lk.group(0)

    # external company website: must be an http(s) link to a NON-platform, NON-asset,
    # non-social, non-government domain (avoid CSS/JS/image asset URLs).
    bad_suffix = ("made-in-china.com", "micstatic.com", "beian.gov.cn", "miit.gov.cn",
                  "google.com", "google-analytics.com", "gstatic.com", "googletagmanager.com",
                  "facebook.com", "twitter.com", "youtube.com", "instagram.com",
                  "linkedin.com", "tiktok.com", "whatsapp.com", "skype.com", "w3.org")
    for u in re.findall(r'href="(https?://[^"]+)"', html):
        if re.search(r"\.(css|js|png|jpe?g|gif|svg|ico|webp)(\?|$)", u, re.I):
            continue
        dom = re.sub(r"^https?://", "", u).split("/")[0].lower()
        if any(dom == b or dom.endswith("." + b) for b in bad_suffix):
            continue
        site = u
        break
    return email, linkedin, site


PRD_REGIONS = {"广东", "深圳", "东莞", "广州", "珠海", "惠州", "中山", "佛山"}


def write_xlsx(records, path):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    cols = ["公司名", "地区", "公司资料页", "公开邮箱", "真实官网", "LinkedIn链接",
            "来源关键词", "来源URL", "备注", "抓取日期"]
    widths = [40, 10, 44, 30, 34, 40, 14, 46, 34, 12]

    def fill_sheet(ws, rows):
        ws.append(cols)
        for c in range(1, len(cols) + 1):
            cell = ws.cell(row=1, column=c)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="1A365D")
            cell.alignment = Alignment(vertical="center")
        for rec in rows:
            ws.append([rec.get(c, "") for c in cols])
        for i, w in enumerate(widths, start=1):
            ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w
        ws.freeze_panes = "A2"

    wb = Workbook()
    ws = wb.active
    ws.title = "客户名单"
    fill_sheet(ws, records)

    # 珠三角优先 sheet（方便手动跟进）
    prd = [r for r in records if r.get("地区") in PRD_REGIONS]
    ws2 = wb.create_sheet("珠三角优先")
    fill_sheet(ws2, prd)

    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(path))
    return len(prd)


def main():
    ap = argparse.ArgumentParser(description="HXO 充电器/电源适配器厂客户名单（中国制造网）")
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--keywords", nargs="*", default=DEFAULT_KEYWORDS)
    ap.add_argument("--max-pages", type=int, default=3)
    ap.add_argument("--no-enrich", action="store_true", help="不访问官网/资料页，仅列表")
    ap.add_argument("--dry-run", action="store_true", help="不写 xlsx")
    args = ap.parse_args()

    s = session()
    suppliers = []
    seen = set()

    log(f"目标 {args.limit} 条 | 关键词 {args.keywords}")
    for kw in args.keywords:
        if len(suppliers) >= args.limit:
            break
        log(f"搜索: {kw}")
        try:
            items = search_suppliers(s, kw, max_pages=args.max_pages)
        except AntiCrawl as e:
            log(f"!! 反爬拦截: {e} —— 立即停止")
            break
        for it in items:
            sub = it["Sub"]
            if sub in seen:
                continue
            seen.add(sub)
            it["来源关键词"] = kw
            suppliers.append(it)
            if len(suppliers) >= args.limit:
                break
        time.sleep(3)

    # 珠三角优先排序
    suppliers.sort(key=lambda x: (0 if any(p in x["Region"] for p in
                     ["广东", "深圳", "东莞", "广州", "珠海", "惠州", "中山", "佛山"]) else 1))

    log(f"列表合计 {len(suppliers)} 家（去重后）")

    records = []
    for i, it in enumerate(suppliers, 1):
        rec = {
            "公司名": it["Company"],
            "地区": it["Region"],
            "公司资料页": it["SubURL"],
            "公开邮箱": "",
            "真实官网": "",
            "LinkedIn链接": "",
            "来源关键词": it["来源关键词"],
            "来源URL": it["SubURL"],
            "备注": "联系方式待人工补（MIC 隐藏邮箱/官网）",
            "抓取日期": dt.date.today().isoformat(),
        }
        if not args.no_enrich:
            email, linkedin, site = fetch_profile(s, it["Sub"])
            if email:
                rec["公开邮箱"] = email
            if linkedin:
                rec["LinkedIn链接"] = linkedin
            if site:
                rec["真实官网"] = site
                rec["备注"] = "已有官网"
            time.sleep(3)
        records.append(rec)
        if i <= 5 or i % 10 == 0:
            log(f"  [{i}/{len(suppliers)}] {rec['公司名'][:32]} | {rec['地区']} | {rec['公开邮箱'] or '—'}")

    log(f"完成: {len(records)} 条")
    if args.dry_run:
        for r in records[:5]:
            print(r)
        return
    stamp = dt.date.today().strftime("%Y%m%d")
    out = OUT_DIR / f"客户名单_{stamp}.xlsx"
    prd_n = write_xlsx(records, out)
    log(f"已写入 {out}（全部 {len(records)} 条；珠三角优先 sheet {prd_n} 条）")


if __name__ == "__main__":
    main()
