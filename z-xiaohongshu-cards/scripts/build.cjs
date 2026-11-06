#!/usr/bin/env node
/*
 * 把内容 JSON 套进风格，生成可渲染的 cards.html。Agent 只写内容，版式全部来自风格。
 *
 *   node build.cjs <content.json> [--style 风格id] [--out cards.html]
 *
 * JSON 不合规时列出全部问题并退出 1，按提示改内容后重跑。
 */
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const LIMITS = {
  title: 20, coverTitle: 16, sub: 24, kicker: 16, tag: 8, tags: 4,
  head: 12, text: 30, minItems: 2, maxItems: 5, cmpItem: 14, cmpItems: 4,
  quote: 48, value: 6, unit: 4, statText: 30, statHead: 8, statItem: 12,
  verdict: 26, caption: 30, cta: 20,
};
const TYPES = ['cover', 'points', 'steps', 'compare', 'quote', 'stat', 'image', 'end'];

const plain = (s) => String(s == null ? '' : s).replace(/\*\*/g, '').replace(/\n/g, '');
/* 按版面宽度计字数：一个汉字算 1，一个西文字符算 0.55 */
const size = (s) => Math.ceil([...plain(s)].reduce((n, c) => n + (c.charCodeAt(0) < 128 ? 0.55 : 1), 0));
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const inline = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, '<mark>$1</mark>').replace(/\n/g, '<br>');

function validate(doc, baseDir) {
  const errs = [];
  const max = (where, v, n) => { if (size(v) > n) errs.push(`${where} 有 ${size(v)} 字，上限 ${n} 字：「${plain(v)}」`); };
  const need = (where, v) => { if (!plain(v)) errs.push(`${where} 不能为空`); };
  const img = (where, v) => {
    if (/^(https?:|\/|[A-Za-z]:\\)/.test(v)) errs.push(`${where} 要用相对路径，并把图片放进 assets/：${v}`);
    else if (!fs.existsSync(path.resolve(baseDir, v))) errs.push(`${where} 找不到图片：${v}`);
  };
  const items = (where, list) => {
    if (!Array.isArray(list) || list.length < LIMITS.minItems || list.length > LIMITS.maxItems) {
      errs.push(`${where}.items 要有 ${LIMITS.minItems}–${LIMITS.maxItems} 条，内容多就拆成两页`);
      return;
    }
    list.forEach((it, i) => {
      need(`${where}.items[${i}].head`, it.head);
      max(`${where}.items[${i}].head`, it.head, LIMITS.head);
      max(`${where}.items[${i}].text`, it.text, LIMITS.text);
    });
  };
  if (!Array.isArray(doc.pages) || !doc.pages.length) errs.push('pages 不能为空');
  (doc.pages || []).forEach((p, n) => {
    const at = `第 ${n + 1} 页（${p.type}）`;
    if (!TYPES.includes(p.type)) { errs.push(`${at} 类型未知，可用：${TYPES.join(' ')}`); return; }
    max(`${at} tag`, p.tag, LIMITS.tag);
    if (p.type !== 'quote') { need(`${at} title`, p.title); max(`${at} title`, p.title, p.type === 'cover' ? LIMITS.coverTitle : LIMITS.title); }
    if (p.type === 'cover') {
      max(`${at} kicker`, p.kicker, LIMITS.kicker);
      max(`${at} sub`, p.sub, LIMITS.sub);
      if (p.tags && p.tags.length > LIMITS.tags) errs.push(`${at} tags 最多 ${LIMITS.tags} 个`);
      if (p.image) img(`${at} image`, p.image);
    }
    if (p.type === 'points' || p.type === 'steps') items(at, p.items);
    if (p.type === 'end' && p.items) items(at, p.items);
    if (p.type === 'end') max(`${at} cta`, p.cta, LIMITS.cta);
    if (p.type === 'compare') {
      ['left', 'right'].forEach((k) => {
        const c = p[k] || {};
        need(`${at} ${k}.label`, c.label);
        max(`${at} ${k}.label`, c.label, 8);
        const l = c.items || [];
        if (l.length < 2 || l.length > LIMITS.cmpItems) errs.push(`${at} ${k}.items 要有 2–${LIMITS.cmpItems} 条`);
        l.forEach((s, i) => max(`${at} ${k}.items[${i}]`, s, LIMITS.cmpItem));
      });
      max(`${at} verdict`, p.verdict, LIMITS.verdict);
    }
    if (p.type === 'quote') { need(`${at} text`, p.text); max(`${at} text`, p.text, LIMITS.quote); max(`${at} source`, p.source, 16); }
    if (p.type === 'stat') {
      need(`${at} value`, p.value);
      max(`${at} value`, p.value, LIMITS.value);
      max(`${at} unit`, p.unit, LIMITS.unit);
      max(`${at} text`, p.text, LIMITS.statText);
      if (p.items) {
        if (p.items.length > 3) errs.push(`${at} items 最多 3 条`);
        p.items.forEach((it, i) => { need(`${at} items[${i}].head`, it.head); max(`${at} items[${i}].head`, it.head, LIMITS.statHead); max(`${at} items[${i}].text`, it.text, LIMITS.statItem); });
      }
    }
    if (p.type === 'image') {
      if (p.image) img(`${at} image`, p.image); else errs.push(`${at} 缺少 image`);
      max(`${at} caption`, p.caption, LIMITS.caption);
    }
  });
  return errs;
}

/* 模板语法：{{x}} 输出转义文本，{{#x}}…{{/x}} 条件或循环，{{.}} 循环里的字符串。 */
function get(stack, key) {
  if (key === '.') return stack[stack.length - 1];
  const parts = key.split('.');
  for (let i = stack.length - 1; i >= 0; i--) {
    let v = stack[i];
    if (v === null || typeof v !== 'object' || !(parts[0] in v)) continue;
    for (const k of parts) v = v == null ? undefined : v[k];
    return v;
  }
  return undefined;
}

function fill(tpl, stack) {
  const open = /\{\{#([\w.]+)\}\}/;
  let out = '';
  let rest = tpl;
  for (;;) {
    const m = open.exec(rest);
    if (!m) { out += rest; break; }
    out += rest.slice(0, m.index);
    const tagOpen = `{{#${m[1]}}}`;
    const tagClose = `{{/${m[1]}}}`;
    let depth = 1;
    let pos = m.index + tagOpen.length;
    while (depth) {
      const a = rest.indexOf(tagOpen, pos);
      const b = rest.indexOf(tagClose, pos);
      if (b < 0) throw new Error(`模板缺少 ${tagClose}`);
      if (a >= 0 && a < b) { depth++; pos = a + tagOpen.length; } else { depth--; pos = b + tagClose.length; }
    }
    const inner = rest.slice(m.index + tagOpen.length, pos - tagClose.length);
    const v = get(stack, m[1]);
    if (Array.isArray(v)) {
      v.forEach((it, i) => {
        const ctx = typeof it === 'object' ? { ...it } : { '.': it };
        ctx.i = String(i + 1).padStart(2, '0');
        ctx.n1 = i + 1;
        ctx.cn = '一二三四五'[i] || String(i + 1);
        ctx.last = i === v.length - 1;
        out += fill(inner, typeof it === 'object' ? [...stack, ctx] : [...stack, ctx, it]);
      });
    } else if (v) {
      out += fill(inner, typeof v === 'object' ? [...stack, v] : stack);
    }
    rest = rest.slice(pos);
  }
  return out.replace(/\{\{([\w.]+)\}\}/g, (_, k) => {
    const v = get(stack, k);
    return v == null || typeof v === 'object' ? '' : inline(v);
  });
}

function parts(file) {
  const res = {};
  if (!fs.existsSync(file)) return res;
  const text = fs.readFileSync(file, 'utf8');
  const re = /<template data-(page|part)="([\w-]+)">([\s\S]*?)<\/template>/g;
  let m;
  while ((m = re.exec(text))) res[m[2]] = m[3].trim();
  return res;
}

function main() {
  const argv = process.argv.slice(2);
  const opt = { file: null, style: null, out: null };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--style') opt.style = argv[++i];
    else if (argv[i] === '--out') opt.out = argv[++i];
    else if (!opt.file) opt.file = argv[i];
  }
  if (!opt.file) { console.error('用法：node build.cjs <content.json> [--style 风格id] [--out cards.html]'); process.exit(2); }
  const file = path.resolve(opt.file);
  const baseDir = path.dirname(file);
  let doc;
  try { doc = JSON.parse(fs.readFileSync(file, 'utf8')); } catch (e) { console.error(`JSON 解析失败：${e.message}`); process.exit(1); }
  const id = opt.style || doc.style;
  const dir = path.join(root, 'styles', id || '');
  if (!id || !fs.existsSync(path.join(dir, 'style.css'))) {
    const ok = fs.readdirSync(path.join(root, 'styles')).filter((d) => fs.existsSync(path.join(root, 'styles', d, 'style.css')));
    console.error(`风格不存在：${id}。可用：${ok.join(' ')}`);
    process.exit(1);
  }
  const errs = validate(doc, baseDir);
  if (errs.length) { console.error(`内容有 ${errs.length} 处要改：\n- ${errs.join('\n- ')}`); process.exit(1); }

  const tpl = { ...parts(path.join(root, 'styles/_base/pages.html')), ...parts(path.join(dir, 'pages.html')) };
  const total = doc.pages.length;
  const cards = doc.pages.map((p, i) => {
    const n = p.items ? p.items.length : 0;
    const ctx = {
      brand: doc.brand || '', note: '', tag: '', ...p,
      no: String(i + 1).padStart(2, '0'), total: String(total).padStart(2, '0'),
      seq: i + 1, count: n, hasItems: !!n, hasTags: !!(p.tags && p.tags.length),
      textChars: p.type === 'quote' ? [...plain(p.text)] : undefined,
    };
    const tl = size(p.title || p.text);
    const len = tl <= 8 ? 's' : tl <= 14 ? 'm' : 'l';
    const name = p.name || p.type;
    const body = [tpl.decor, tpl.head, `<main class="main">${tpl[p.type]}</main>`, tpl.foot].map((t) => fill(t, [ctx])).join('\n');
    return `<section class="card p-${p.type}" data-name="${esc(name)}" data-n="${n}" data-tl="${len}" data-vl="${[...plain(p.value)].length}">\n${body}\n</section>`;
  });
  const css = [fs.readFileSync(path.join(root, 'styles/_base/base.css'), 'utf8'), fs.readFileSync(path.join(dir, 'style.css'), 'utf8')].join('\n');
  const html = `<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8"><title>${esc(id)}</title><style>\n${css}\n</style></head>\n<body>\n${cards.join('\n')}\n</body></html>\n`;
  const out = path.resolve(opt.out || path.join(baseDir, 'cards.html'));
  fs.writeFileSync(out, html);
  console.log(`已生成 ${path.relative(process.cwd(), out)}：${total} 页，风格 ${id}`);
}

main();
