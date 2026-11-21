#!/usr/bin/env python3
"""夯到拉排行榜：建任务目录 / 校验打分 / 出 PNG / 写依据表。

  python3 tierlist.py new "主题" [--out 目录]     默认建在 ./夯到拉/<日期>-<主题>/，环境变量 TIERLIST_OUT 可改根目录
  python3 tierlist.py check data.json [--strict]
  python3 tierlist.py build data.json [--size 3:4] [--theme ink|paper] [--layout auto|tile|pill|compact]
                                      [--hd | --scale 2] [--out 目录] [--strict] [--keep-html]

--size 可选：3:4（默认）4:5 1:1 9:16 2:3 4:3 16:9 all，或 1242x1660 这样的像素尺寸。
"""
import argparse
import datetime as dt
import decimal
import json
import math
import os
import pathlib
import re
import sys
import unicodedata
import urllib.parse

SKILL = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = SKILL / 'assets' / 'template.html'
# 禁用词：forbid.txt 随 skill 发布（默认只有说明），forbid.local.txt 放自己长期用的词，不入库
FORBID_FILES = [SKILL / 'forbid.txt', SKILL / 'forbid.local.txt']

TIERS = [
    {'name': '夯', 'note': '封神'},
    {'name': '顶级', 'note': '强推'},
    {'name': '人上人', 'note': '能打'},
    {'name': 'NPC', 'note': '路人'},
    {'name': '拉完了', 'note': '避雷'},
]
CUTS = [9.0, 8.0, 7.0, 5.5]  # 加权分 ≥ 9.0 夯，≥ 8.0 顶级，≥ 7.0 人上人，≥ 5.5 NPC，其余拉完了

# 比例: (画布宽, 画布高, 默认出图宽)。画布短边固定 1080，排版只调一套；出图时按倍率放大。
SIZES = {
    '3:4': (1080, 1440, 1200),
    '4:5': (1080, 1350, 1080),
    '1:1': (1080, 1080, 1080),
    '9:16': (1080, 1920, 1080),
    '2:3': (1080, 1620, 1200),
    '4:3': (1440, 1080, 1600),
    '16:9': (1920, 1080, 1920),
}
EV_TYPES = ['官方', '榜单', '评测', '市场', '媒体', '口碑']
FONT_CANDIDATES = [
    os.environ.get('TIERLIST_FONT', ''),
    '~/Library/Fonts/SourceHanSerifSC-VF.ttf',
    '/Library/Fonts/SourceHanSerifSC-VF.ttf',
    '~/Library/Fonts/SourceHanSerifSC-Regular.otf',
    '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',
]


# ---------------------------------------------------------------- 工具

def fmt(x, nd=2):
    """分数四舍五入到 nd 位，逢五进一（直接用 :.1f 会把 8.25 显示成 8.2）。"""
    q = decimal.Decimal(1).scaleb(-nd)
    return str(decimal.Decimal(repr(round(float(x), 3))).quantize(q, rounding=decimal.ROUND_HALF_UP))


def vlen(s):
    """显示宽度，汉字记 1。"""
    n = 0.0
    for ch in str(s):
        if ord(ch) > 0x2E80:
            n += 1
        elif ch.isupper() or ch.isdigit():
            n += 0.68
        elif ch == ' ':
            n += 0.3
        else:
            n += 0.55
    return n


def cols(s):
    """终端列宽。"""
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in str(s))


def pad(s, w, right=False):
    s = str(s)
    gap = max(0, w - cols(s))
    return (' ' * gap + s) if right else (s + ' ' * gap)


def safe_name(s):
    s = re.sub(r'[\\/:*?"<>|\s]+', '-', str(s).strip())
    return s.strip('-')[:40] or 'tierlist'


def norm_url(u):
    try:
        p = urllib.parse.urlsplit(u.strip())
    except Exception:
        return u
    if not p.scheme:
        return u.strip()
    return urllib.parse.urlunsplit((p.scheme.lower(), p.netloc.lower().removeprefix('www.'), p.path.rstrip('/'), '', ''))


def domain(u):
    try:
        return urllib.parse.urlsplit(u).netloc.lower().removeprefix('www.')
    except Exception:
        return ''


def font_url():
    for c in FONT_CANDIDATES:
        if c and pathlib.Path(c).expanduser().exists():
            return pathlib.Path(c).expanduser().resolve().as_uri()
    return ''


def load_forbid(data):
    words = []
    for f in FORBID_FILES:
        if f.exists():
            words += [w.strip() for w in f.read_text(encoding='utf-8').splitlines() if w.strip() and not w.startswith('#')]
    words += [w for w in data.get('forbid', []) if w]
    return sorted(set(words))


def tier_index(v, tiers):
    """接受 0-4、't0'、'夯' 这几种写法。"""
    if v is None or v == '':
        return None
    if isinstance(v, int) and 0 <= v < len(tiers):
        return v
    s = str(v).strip()
    if re.fullmatch(r't?\d', s, re.I):
        i = int(s.lstrip('tT'))
        return i if 0 <= i < len(tiers) else None
    for i, t in enumerate(tiers):
        if s == t['name']:
            return i
    return None


def by_cut(total, cuts):
    for i, c in enumerate(cuts):
        if total >= c - 1e-9:
            return i
    return len(cuts)


def fmt_date(s, month_only=False):
    m = re.match(r'(\d{4})-(\d{1,2})(?:-(\d{1,2}))?', s or '')
    if not m:
        return s or ''
    y, mo, d = m.group(1), int(m.group(2)), m.group(3)
    if month_only or not d:
        return f'{y}.{mo:02d}'
    return f'{y}.{mo:02d}.{int(d):02d}'


# ---------------------------------------------------------------- 校验 + 打分

class Result:
    pass


def analyze(data):
    r = Result()
    r.errors, r.warns, r.notes = [], [], []
    custom = data.get('tiers') or []
    tiers = [dict(TIERS[i], **(custom[i] if i < len(custom) else {})) for i in range(5)]
    r.tiers = tiers
    cuts = data.get('cuts') or CUTS
    if len(cuts) != 4 or any(cuts[i] <= cuts[i + 1] for i in range(3)):
        r.errors.append(f'cuts 要从高到低写 4 个分档线，现在是 {cuts}')
        cuts = CUTS
    r.cuts = cuts

    dims = data.get('dimensions') or []
    if not dims:
        r.errors.append('没有 dimensions（评分维度）')
    keys = [d.get('key') for d in dims]
    if any(not k for k in keys) or len(set(keys)) != len(keys):
        r.errors.append('dimensions 里的 key 缺失或重复')
    wsum = sum(float(d.get('weight', 0)) for d in dims)
    if dims and abs(wsum - 100) > 0.01:
        r.errors.append(f'维度权重加起来是 {wsum:g}，要等于 100')
    for d in dims:
        if not d.get('rubric'):
            r.warns.append(f'[打分锚点] 维度「{d.get("name")}」没写 rubric（10/7/4/1 分分别是什么样）')
    r.dims = dims
    wsum = wsum or 1

    items = data.get('items') or []
    if len(items) < 3:
        r.errors.append(f'候选只有 {len(items)} 个，至少 3 个')
    if len(items) > 40:
        r.warns.append(f'[太多] 候选 {len(items)} 个，一张图会很挤，建议控制在 30 个以内或拆成两张')
    seen = set()
    r.items = []
    urls, doms, types = set(), set(), set()
    for raw in items:
        name = (raw.get('name') or '').strip()
        if not name:
            r.errors.append('有候选没写 name')
            continue
        if name in seen:
            r.errors.append(f'候选重名：{name}')
        seen.add(name)
        it = Result()
        it.raw, it.name = raw, name
        it.disp = (raw.get('short') or name).strip()
        it.verdict = (raw.get('verdict') or '').strip()
        sc = raw.get('scores') or {}
        miss = [d['name'] for d in dims if d.get('key') not in sc]
        if miss:
            r.errors.append(f'{name}：缺维度分 {"、".join(miss)}')
        bad = [k for k, v in sc.items() if not isinstance(v, (int, float)) or v < 0 or v > 10]
        if bad:
            r.errors.append(f'{name}：分数要在 0-10 之间（{"、".join(bad)}）')
        extra = [k for k in sc if k not in keys]
        if extra:
            r.warns.append(f'[多余分数] {name} 有不在维度表里的分数：{"、".join(extra)}')
        it.scores = {d['key']: float(sc.get(d['key'], 0) or 0) for d in dims if d.get('key')}
        it.total = round(sum(it.scores[d['key']] * float(d['weight']) for d in dims if d.get('key')) / wsum, 3)
        it.auto = by_cut(it.total, cuts)
        ov = raw.get('tier')
        oi = tier_index(ov, tiers)
        if ov not in (None, '') and oi is None:
            r.errors.append(f'{name}：tier 写成了「{ov}」，认不出是哪一档')
        it.tier = oi if oi is not None else it.auto
        it.override = oi is not None and oi != it.auto
        if it.override and not (raw.get('override_reason') or '').strip():
            r.errors.append(f'{name}：按分数是「{tiers[it.auto]["name"]}」，手动改成「{tiers[oi]["name"]}」必须写 override_reason')

        ev = raw.get('evidence') or []
        it.evidence = ev
        if len(ev) < 2:
            r.warns.append(f'[证据不足] {name} 只有 {len(ev)} 条证据，至少 2 条')
        if it.tier == 0 and len(ev) < 3:
            r.warns.append(f'[夯要硬] {name} 进了「{tiers[0]["name"]}」，证据少于 3 条')
        if ev and not any(e.get('url') for e in ev):
            r.warns.append(f'[没链接] {name} 的证据都没有 url')
        if ev and not any(re.search(r'\d', e.get('text', '')) for e in ev):
            r.warns.append(f'[没数字] {name} 的证据里没有一个硬数字')
        if it.tier == 4 and not any(e.get('neg') for e in ev):
            r.warns.append(f'[拉完了要实锤] {name} 进了「{tiers[4]["name"]}」，但没有标 neg 的负面证据')
        for e in ev:
            if e.get('url'):
                urls.add(norm_url(e['url']))
                doms.add(domain(e['url']))
            if e.get('type'):
                types.add(e['type'])
                if e['type'] not in EV_TYPES:
                    r.warns.append(f'[信源类型] {name} 的证据类型「{e["type"]}」不在 {"/".join(EV_TYPES)} 里')
            if not e.get('text'):
                r.warns.append(f'[空证据] {name} 有一条证据没写 text')
        if not it.verdict:
            r.warns.append(f'[没锐评] {name} 没写 verdict')
        elif vlen(it.verdict) > 12.5:
            r.warns.append(f'[锐评太长] {name}「{it.verdict}」约 {vlen(it.verdict):.0f} 字，上图建议 ≤ 12 字')
        if vlen(it.disp) > 13:
            r.warns.append(f'[名字太长] {it.disp} 上图会被截断，写个 short')
        # 压线提醒
        for i, c in enumerate(cuts):
            if abs(it.total - c) < 0.15 and oi is None:
                r.notes.append(f'[压线] {name} {fmt(it.total)} 离「{tiers[i]["name"]}」线 {c} 不到 0.15，再核一遍分数')
        r.items.append(it)

    for s in data.get('sources') or []:
        if s.get('url'):
            urls.add(norm_url(s['url']))
            doms.add(domain(s['url']))
        if s.get('type'):
            types.add(s['type'])
    doms.discard('')
    r.urls, r.domains, r.types = urls, doms, types
    n = len(r.items)
    if n:
        if len(urls) < max(10, math.ceil(n * 0.8)):
            r.warns.append(f'[来源偏少] 独立链接 {len(urls)} 个，建议 ≥ {max(10, math.ceil(n * 0.8))}')
        if len(doms) < 6:
            r.warns.append(f'[来源单一] 只来自 {len(doms)} 个网站，建议 ≥ 6')
        if len(types) < 3:
            r.warns.append(f'[信源类型少] 只用了 {len(types)} 类信源（{"/".join(sorted(types)) or "未标注"}），建议 ≥ 3 类')

    r.ranked = sorted(r.items, key=lambda x: (x.tier, -x.total, x.name))
    counts = [sum(1 for it in r.items if it.tier == i) for i in range(5)]
    r.counts = counts
    if n:
        if counts[0] > max(3, math.ceil(n * 0.2)):
            r.warns.append(f'[夯太多] 「{tiers[0]["name"]}」有 {counts[0]} 个，夯要稀缺，一般 1-3 个')
        if max(counts) > n * 0.6:
            r.warns.append(f'[扎堆] 有一档占了 {max(counts)}/{n}，分数可能没拉开，回看 rubric 是否用满了 0-10')

    if not data.get('asof'):
        r.warns.append('[日期] 没写 asof，按今天算')
    r.asof = data.get('asof') or dt.date.today().isoformat()

    forbid = load_forbid(data)
    blob = json.dumps({k: v for k, v in data.items() if k not in ('forbid', '__dir')}, ensure_ascii=False)
    for w in forbid:
        if w in blob:
            r.errors.append(f'出现禁用词「{w}」，改掉再生成')
    return r


def report(data, r):
    dims = r.dims
    head = pad('排名', 5) + pad('档位', 8) + pad('加权', 7, True) + '  ' + ''.join(pad(d['name'][:4], 9) for d in dims) + pad('候选', 22) + '锐评'
    print(f'\n# {data.get("title") or data.get("topic", "")}  （截至 {r.asof}）')
    print('  分档线：' + ' / '.join(f'{r.tiers[i]["name"]} ≥ {c}' for i, c in enumerate(r.cuts)) + f' / {r.tiers[4]["name"]} < {r.cuts[-1]}')
    print('  维度：' + ' · '.join(f'{d["name"]} {float(d["weight"]):g}%' for d in dims))
    print()
    print(head)
    for k, it in enumerate(r.ranked, 1):
        flag = '*' if it.override else ''
        line = pad(k, 5) + pad(r.tiers[it.tier]['name'] + flag, 8) + pad(f'{fmt(it.total)}', 7, True) + '  '
        line += ''.join(pad(f'{it.scores.get(d["key"], 0):g}', 9) for d in dims)
        line += pad(it.disp, 22) + it.verdict
        print(line)
    print()
    print('  分布：' + ' · '.join(f'{r.tiers[i]["name"]} {c}' for i, c in enumerate(r.counts)))
    print(f'  来源：{len(r.urls)} 个独立链接，{len(r.domains)} 个网站，信源类型 {len(r.types)} 类（{"/".join(sorted(r.types))}）')
    if any(it.override for it in r.items):
        print('  * 手动调档：' + '；'.join(f'{it.name}（{it.raw.get("override_reason")}）' for it in r.items if it.override))
    for title, arr in (('错误', r.errors), ('提醒', r.warns), ('注意', r.notes)):
        if arr:
            print(f'\n  {title}（{len(arr)}）：')
            for a in arr:
                print('   - ' + a)
    print()


# ---------------------------------------------------------------- 出图

def parse_sizes(arg):
    arg = (arg or '3:4').strip().lower()
    if arg == 'all':
        return [(k, *v) for k, v in SIZES.items()]
    out = []
    for part in arg.split(','):
        part = part.strip()
        if part in SIZES:
            out.append((part, *SIZES[part]))
            continue
        m = re.fullmatch(r'(\d+)\s*[x×*]\s*(\d+)', part)
        if not m:
            sys.exit(f'认不出尺寸：{part}（可选 {" ".join(SIZES)} all，或 1242x1660）')
        w, h = int(m.group(1)), int(m.group(2))
        if w <= h:
            cw, ch = 1080, round(h * 1080 / w)
        else:
            cw, ch = round(w * 1080 / h), 1080
        out.append((f'{w}x{h}', cw, ch, w))
    return out


def icon_payload(raw, base):
    ic = dict(raw.get('icon') or {})
    img = ic.get('image')
    if img and not re.match(r'(https?|data|file):', img):
        p = pathlib.Path(img).expanduser()
        if not p.is_absolute():
            p = (base / p).resolve()
        ic['image'] = p.as_uri() if p.exists() else ''
        if not p.exists():
            print(f'  ! 图标文件不存在，改用字标：{img}')
    return ic


def make_payload(data, r, cw, ch, theme, layout):
    base = pathlib.Path(data['__dir'])
    tiers = []
    for i, t in enumerate(r.tiers):
        items = [it for it in r.ranked if it.tier == i]
        tiers.append({
            'key': f't{i}', 'name': t['name'], 'note': t.get('note', ''),
            'items': [{'name': it.disp, 'verdict': it.verdict, 'scoreText': f'{fmt(it.total, 1)}',
                       'icon': icon_payload(it.raw, base)} for it in items],
        })
    n, m, k = len(r.items), len(r.urls), len(r.dims)
    freq = {}
    for it in r.items:
        for e in it.evidence:
            s = (e.get('source') or '').strip()
            if s:
                freq[s] = freq.get(s, 0) + 1
    for s in data.get('sources') or []:
        nm = (s.get('name') or '').strip()
        if nm:
            freq[nm] = freq.get(nm, 0) + 1
    top = [s for s, _ in sorted(freq.items(), key=lambda x: (-x[1], x[0]))][:4]
    src_line = data.get('footer_sources') or ('、'.join(top) + f' 等 {m} 个独立来源' if top else f'{m} 个独立来源')
    dims_line = ' · '.join(f'{d["name"]} {float(d["weight"]):g}%' for d in r.dims)
    footer = [
        {'k': '评分', 'v': dims_line, 'r': data.get('byline', ''), 'kind': 'dims'},
        {'k': '来源', 'v': src_line, 'r': f'截至 {fmt_date(r.asof)}'},
    ]
    return {
        'canvas': {'w': cw, 'h': ch},
        'theme': theme, 'layout': layout,
        'kicker': data.get('kicker') or f'TIER LIST · {fmt_date(r.asof, month_only=True)}',
        'title': data.get('title') or data.get('topic', ''),
        'subtitle': data.get('subtitle') if data.get('subtitle') is not None else f'{n} 个候选 · {m} 个独立来源 · {k} 维加权打分',
        'seal': data.get('seal', '从夯到拉'),
        'showScore': data.get('show_score', True),
        'showNotes': data.get('show_notes', True),
        'ghost': data.get('ghost', True),
        'emptyText': data.get('empty_text', '虚位以待'),
        'tiers': tiers,
        'footer': footer,
        'dims': [{'name': d['name'], 'weight': float(d['weight'])} for d in r.dims],
    }


def render_all(jobs, keep_html=False):
    from playwright.sync_api import sync_playwright
    from PIL import Image
    tpl = TEMPLATE.read_text(encoding='utf-8')
    furl = font_url()
    if not furl:
        print('  ! 没找到思源宋体，退回系统宋体（Songti SC）。可用环境变量 TIERLIST_FONT 指定字体文件')
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for payload, png, cw, ch, ow, oh in jobs:
            html = tpl.replace('__FONT_URL__', furl).replace('/*__DATA__*/null', json.dumps(payload, ensure_ascii=False))
            tmp = png.with_name(png.stem + '.render.html')
            tmp.write_text(html, encoding='utf-8')
            page = browser.new_page(viewport={'width': cw, 'height': ch}, device_scale_factor=ow / cw)
            page.goto(tmp.as_uri())
            page.wait_for_function('window.__done === true', timeout=60000)
            lay = page.evaluate('window.__layout')
            page.screenshot(path=str(png), clip={'x': 0, 'y': 0, 'width': cw, 'height': ch}, type='png')
            page.close()
            im = Image.open(png)
            if im.size != (ow, oh):
                im = im.convert('RGB').resize((ow, oh), Image.LANCZOS)
                im.save(png)
            if not keep_html:
                tmp.unlink(missing_ok=True)
            results.append((png, lay))
        browser.close()
    return results


# ---------------------------------------------------------------- 依据表

def md_cell(s):
    return str(s).replace('|', '\\|').replace('\n', ' ')


def write_evidence(data, r, pngs, out_dir):
    dims = r.dims
    L = []
    title = data.get('title') or data.get('topic', '')
    L.append(f'# {title}｜夯到拉排行榜·评分依据\n')
    for p in pngs:
        L.append(f'![]({p.name})\n')
    L.append(f'截至 {r.asof} · {len(r.items)} 个候选 · {len(r.urls)} 个独立来源（{len(r.domains)} 个网站）· {len(dims)} 维加权打分\n')
    if data.get('scope'):
        L.append(f'**范围**：{data["scope"]}\n')
    L.append('## 评分维度\n')
    L.append('| 维度 | 权重 | 怎么打分 |\n|---|---|---|')
    for d in dims:
        L.append(f'| {md_cell(d["name"])} | {float(d["weight"]):g}% | {md_cell(d.get("rubric", ""))} |')
    L.append('')
    L.append('分档线（加权分，满分 10）：' + '，'.join(f'{r.tiers[i]["name"]} ≥ {c}' for i, c in enumerate(r.cuts)) + f'，低于 {r.cuts[-1]} 为{r.tiers[4]["name"]}。\n')
    L.append('## 排名总表\n')
    L.append('| 排名 | 档位 | 候选 | ' + ' | '.join(md_cell(d['name']) for d in dims) + ' | 加权分 | 锐评 |')
    L.append('|' + '---|' * (len(dims) + 5))
    for k, it in enumerate(r.ranked, 1):
        t = r.tiers[it.tier]['name'] + ('*' if it.override else '')
        L.append(f'| {k} | {t} | {md_cell(it.name)} | ' + ' | '.join(f'{it.scores.get(d["key"], 0):g}' for d in dims) + f' | {fmt(it.total)} | {md_cell(it.verdict)} |')
    ov = [it for it in r.items if it.override]
    if ov:
        L.append('')
        L.append('\\* 手动调档：' + '；'.join(f'{it.name}，按分数应为「{r.tiers[it.auto]["name"]}」，{it.raw.get("override_reason")}' for it in ov))
    L.append('\n## 逐个说依据\n')
    for i, t in enumerate(r.tiers):
        group = [it for it in r.ranked if it.tier == i]
        L.append(f'### {t["name"]}\n')
        if not group:
            L.append('（空缺）\n')
            continue
        for it in group:
            L.append(f'**{it.name}** · {fmt(it.total)} · {it.verdict}\n')
            if it.raw.get('summary'):
                L.append(it.raw['summary'] + '\n')
            for e in it.evidence:
                tag = '【负面】' if e.get('neg') else ''
                src = e.get('source') or domain(e.get('url', '')) or '来源'
                link = f'[{src}]({e["url"]})' if e.get('url') else src
                meta = '，'.join(x for x in [link, e.get('date', ''), e.get('type', '')] if x)
                L.append(f'- {tag}{e.get("text", "")}（{meta}）')
            L.append('')
    srcs = data.get('sources') or []
    if srcs:
        L.append('## 资料来源\n')
        for k, s in enumerate(srcs, 1):
            nm = s.get('name') or domain(s.get('url', ''))
            meta = ' · '.join(x for x in [s.get('type', ''), s.get('date', ''), s.get('note', '')] if x)
            L.append(f'{k}. [{nm}]({s.get("url", "")})' + (f' · {meta}' if meta else ''))
        L.append('')
    path = out_dir / 'evidence.md'
    path.write_text('\n'.join(L), encoding='utf-8')
    return path


# ---------------------------------------------------------------- 命令

SKELETON = {
    'topic': '',
    'scope': '时间 / 地域 / 品类边界，写清哪些算、哪些不算',
    'asof': '',
    'title': '',
    'subtitle': None,
    'theme': 'ink',
    'layout': 'auto',
    'dimensions': [
        {'key': 'd1', 'name': '维度一', 'weight': 40, 'rubric': '10=…；7=…；4=…；1=…'},
        {'key': 'd2', 'name': '维度二', 'weight': 30, 'rubric': '10=…；7=…；4=…；1=…'},
        {'key': 'd3', 'name': '维度三', 'weight': 30, 'rubric': '10=…；7=…；4=…；1=…'},
    ],
    'items': [
        {
            'name': '候选名',
            'short': '',
            'icon': {'emoji': '', 'mono': '', 'color': '', 'image': ''},
            'scores': {'d1': 0, 'd2': 0, 'd3': 0},
            'verdict': '≤12 字锐评',
            'summary': '',
            'evidence': [
                {'text': '带数字的事实', 'source': '来源名', 'url': 'https://', 'date': 'YYYY-MM', 'type': '榜单'},
                {'text': '负面事实示例', 'source': '来源名', 'url': 'https://', 'date': 'YYYY-MM', 'type': '口碑', 'neg': True},
            ],
        }
    ],
    'sources': [],
}


def load(path):
    p = pathlib.Path(path).expanduser().resolve()
    if not p.exists():
        sys.exit(f'找不到 {p}')
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        sys.exit(f'{p.name} 不是合法 JSON：第 {e.lineno} 行第 {e.colno} 列，{e.msg}')
    data['__dir'] = str(p.parent)
    return p, data


def cmd_new(a):
    topic = a.topic.strip()
    today = dt.date.today().isoformat()
    root = pathlib.Path(os.environ.get('TIERLIST_OUT') or '夯到拉').expanduser().resolve()
    run = pathlib.Path(a.out).expanduser().resolve() if a.out else root / f'{today}-{safe_name(topic)}'
    run.mkdir(parents=True, exist_ok=True)
    dp = run / 'data.json'
    if dp.exists():
        print(f'已存在，不覆盖：{dp}')
    else:
        sk = json.loads(json.dumps(SKELETON))
        sk['topic'], sk['asof'] = topic, today
        dp.write_text(json.dumps(sk, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'已建：{dp}')
    print(run)


def cmd_check(a):
    _, data = load(a.data)
    r = analyze(data)
    report(data, r)
    if r.errors or (a.strict and r.warns):
        sys.exit(1)


def cmd_build(a):
    dp, data = load(a.data)
    r = analyze(data)
    report(data, r)
    if r.errors:
        sys.exit('有错误，先改 data.json')
    if a.strict and r.warns:
        sys.exit('--strict：还有提醒没处理')
    out = pathlib.Path(a.out).expanduser().resolve() if a.out else dp.parent
    out.mkdir(parents=True, exist_ok=True)
    theme = a.theme or data.get('theme') or 'ink'
    layout = a.layout or data.get('layout') or 'auto'
    stem = safe_name(data.get('file_stem') or (data.get('topic') or 'tierlist') + '-夯到拉')
    jobs = []
    for tag, cw, ch, ow in parse_sizes(a.size):
        scale = a.scale if a.scale else (2.0 if a.hd else None)
        if scale:
            ow = round(cw * scale)
        oh = round(ow * ch / cw)
        suffix = tag.replace(':', 'x') + (f'@{scale:g}x' if scale else '')
        png = out / f'{stem}-{suffix}.png'
        jobs.append((make_payload(data, r, cw, ch, theme, layout), png, cw, ch, ow, oh))
    results = render_all(jobs, keep_html=a.keep_html)
    bad = False
    for png, lay in results:
        from PIL import Image
        w, h = Image.open(png).size
        print(f'  ✓ {png}  {w}×{h}')
        if lay.get('error'):
            print('    ! 页面脚本出错：' + lay['error'])
            bad = True
            continue
        print(f'    排版：{lay["mode"]}，缩放 {lay["u"]}，标题 {lay["titleSize"]}px' + ('（已折行）' if lay.get('titleWrapped') else ''))
        tips = []
        if lay.get('overflow'):
            tips.append('[溢出] 最紧凑排版也放不下：减少候选、缩短名字，或换 9:16 / 16:9')
        if lay.get('truncName'):
            tips.append('[名字被截] ' + '、'.join(lay['truncName']) + ' → 写 short')
        if lay.get('truncVerdict'):
            tips.append('[锐评被截] ' + '、'.join(lay['truncVerdict']) + ' → 缩短 verdict')
        if lay.get('truncFoot'):
            tips.append('[页脚被截] ' + ' / '.join(lay['truncFoot']) + ' → 缩短维度名或写 footer_sources')
        if lay.get('subtitleCut'):
            tips.append('[副标题被截] 缩短 subtitle')
        for t in tips:
            print('    ! ' + t)
        bad = bad or bool(tips)
    ev = write_evidence(data, r, [p for p, _ in results], out)
    print(f'  ✓ {ev}')
    if bad and a.strict:
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description='夯到拉排行榜')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('new', help='建任务目录和 data.json 骨架')
    p.add_argument('topic')
    p.add_argument('--out')
    p.set_defaults(fn=cmd_new)
    p = sub.add_parser('check', help='校验 + 打分表 + 提醒')
    p.add_argument('data')
    p.add_argument('--strict', action='store_true')
    p.set_defaults(fn=cmd_check)
    p = sub.add_parser('build', help='出 PNG + evidence.md')
    p.add_argument('data')
    p.add_argument('--size', default='3:4')
    p.add_argument('--theme', choices=['ink', 'paper'])
    p.add_argument('--layout', choices=['auto', 'tile', 'pill', 'compact'])
    p.add_argument('--hd', action='store_true', help='按画布 2 倍出图（3:4 为 2160×2880）')
    p.add_argument('--scale', type=float, help='按画布 N 倍出图，优先于 --hd')
    p.add_argument('--out')
    p.add_argument('--strict', action='store_true')
    p.add_argument('--keep-html', action='store_true')
    p.set_defaults(fn=cmd_build)
    a = ap.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
