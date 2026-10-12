import re, json, sys
sys.stdout.reconfigure(encoding='utf-8')
html = open('arw-series.html', encoding='utf-8').read()
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
print('JSON-LD blocks:', len(blocks))
for i, b in enumerate(blocks):
    try:
        d = json.loads(b)
        print(f'  block {i+1}: OK @type={d.get("@type")}')
    except Exception as e:
        print(f'  block {i+1}: INVALID -> {e}')
for tag in ['div', 'table', 'section', 'nav', 'ul', 'tbody', 'tr', 'td', 'th']:
    o = len(re.findall(r'<' + tag + r'[ >]', html))
    c = len(re.findall(r'</' + tag + r'>', html))
    print(f'  <{tag}> open={o} close={c}', 'OK' if o == c else 'MISMATCH')
print('img derating ref:', 'images/uploads/derating_curve.png' in html)

idx = open('articles.html', encoding='utf-8').read()
print('articles links arw:', 'arw-series.html' in idx)
sm = open('sitemap.xml', encoding='utf-8').read()
print('sitemap has arw:', 'arw-series.html' in sm)
