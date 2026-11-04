/* z-wanghong-handwritten-ppt :: runtime.js
 * 同一份运行时服务两种成品：
 *   data-mode="static"  每页完整呈现，翻页即看全貌
 *   data-mode="steps"   逐步书写：文字按行写出、荧光扫过、红框红线描出、标注箭头画出
 * URL 参数：?export 单页导出（无界面）  ?sheet 全部页面总览图  ?audit 版式体检（写入 #wh-audit）
 */
(() => {
  'use strict';

  const W = 1920;
  const H = 1080;
  const NS = 'http://www.w3.org/2000/svg';
  const html = document.documentElement;
  const params = new URLSearchParams(location.search);
  const MODE = params.has('export') ? 'export'
    : params.has('sheet') ? 'sheet'
      : params.has('audit') ? 'audit' : 'present';
  const deck = document.querySelector('main.deck') || document.querySelector('.deck');
  if (!deck || deck.dataset.whInit) return;
  deck.dataset.whInit = '1';

  const slides = Array.from(deck.children).filter((el) => el.classList.contains('slide'));
  if (!slides.length) return;
  const STEPS = deck.dataset.mode === 'steps' && MODE === 'present';
  const REDUCED = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (MODE === 'export' || MODE === 'audit') html.classList.add('wh-export');
  if (MODE === 'sheet') html.classList.add('wh-sheet');
  html.dataset.whMode = STEPS ? 'steps' : 'static';

  /* ---------- 工具 ---------- */
  const f1 = (n) => (Math.round(n * 10) / 10).toString();
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const hash = (s) => {
    let h = 2166136261;
    for (let i = 0; i < s.length; i += 1) {
      h ^= s.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  };
  const rng = (seed) => {
    let a = seed >>> 0;
    return () => {
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };
  const jit = (r, amt) => (r() - 0.5) * 2 * amt;
  const svg = (tag, attrs = {}) => {
    const el = document.createElementNS(NS, tag);
    for (const k of Object.keys(attrs)) el.setAttribute(k, attrs[k]);
    return el;
  };
  const smoothPath = (pts) => {
    let d = `M${f1(pts[0][0])} ${f1(pts[0][1])}`;
    if (pts.length === 2) return `${d} L${f1(pts[1][0])} ${f1(pts[1][1])}`;
    for (let i = 1; i < pts.length - 1; i += 1) {
      const [x, y] = pts[i];
      const [nx, ny] = pts[i + 1];
      d += ` Q${f1(x)} ${f1(y)} ${f1((x + nx) / 2)} ${f1((y + ny) / 2)}`;
    }
    const last = pts[pts.length - 1];
    return `${d} L${f1(last[0])} ${f1(last[1])}`;
  };
  const scaleOf = () => {
    const r = deck.getBoundingClientRect();
    return r.width / W || 1;
  };
  // 元素相对某个容器的矩形（画布像素）
  const relRect = (el, box) => {
    const s = scaleOf();
    const a = el.getBoundingClientRect();
    const b = box.getBoundingClientRect();
    return {
      x: (a.left - b.left) / s,
      y: (a.top - b.top) / s,
      w: a.width / s,
      h: a.height / s,
    };
  };
  const slideOf = (el) => el.closest('.slide');
  const indexIn = (el) => slides.indexOf(slideOf(el));
  const textNodes = (root) => {
    const out = [];
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: (node) => {
        if (!node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        const p = node.parentElement;
        if (!p || p.closest('.notes, script, style, .wh-deco, .wh-ann')) return NodeFilter.FILTER_REJECT;
        if (p.closest('svg') && !p.closest('text')) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    while (walker.nextNode()) out.push(walker.currentNode);
    return out;
  };
  const visibleChars = (root) => textNodes(root).reduce((n, t) => n + t.nodeValue.replace(/\s+/g, '').length, 0);
  const titleOf = (slide) => {
    if (slide.dataset.title) return slide.dataset.title.trim();
    const t = slide.querySelector('.lead, .title, h1, h2');
    return t ? t.textContent.replace(/\s+/g, ' ').trim() : '';
  };

  /* ---------- 画布缩放 ---------- */
  const fit = () => {
    const s = MODE === 'present' ? Math.min(innerWidth / W, innerHeight / H) : 1;
    deck.style.setProperty('--wh-scale', `${s}`);
  };
  fit();
  addEventListener('resize', fit);

  /* ---------- 手写倾斜：每行轻微不正 ---------- */
  const TILT_SEL = '.lead, .line, .body > p, .col > p, .stack > p, .slide li, .takeaway, .formula, .node, .fig .cap, .cover .title';
  const applyTilt = () => {
    slides.forEach((slide, si) => {
      if (slide.classList.contains('no-tilt')) return;
      let k = 0;
      slide.querySelectorAll(TILT_SEL).forEach((el) => {
        if (el.closest('.no-tilt, svg, .hand-table, .tree, .code, .notes')) return;
        const r = rng(hash(`${si}:${k += 1}:${el.textContent.slice(0, 12)}`));
        const deg = -0.5 + r() * 0.62;
        el.style.rotate = `${deg.toFixed(2)}deg`;
        const centered = el.matches('.center-x, .node, .cover .title') || getComputedStyle(el).textAlign === 'center';
        if (!centered) el.style.transformOrigin = '0 60%';
        const free = el.parentElement && el.parentElement.matches('.body, .stack, .col');
        if (free && !centered && !el.matches('.lead')) el.style.translate = `${f1(r() * 9)}px 0`;
      });
    });
  };

  /* ---------- 手绘装饰 ---------- */
  const decoSvg = (el, w, h) => {
    const s = svg('svg', {
      class: 'wh-deco',
      width: f1(w),
      height: f1(h),
      viewBox: `0 0 ${f1(w)} ${f1(h)}`,
      'aria-hidden': 'true',
    });
    s.style.left = '0px';
    s.style.top = '0px';
    el.appendChild(s);
    return s;
  };
  const addPath = (parent, d, extra) => {
    const p = svg('path', { d });
    if (extra) for (const k of Object.keys(extra)) p.setAttribute(k, extra[k]);
    parent.appendChild(p);
    return p;
  };

  const drawUnderline = (el, r) => {
    const w = el.offsetWidth;
    const h = el.offsetHeight;
    const s = decoSvg(el, w, h);
    const y0 = h * 0.9;
    const x0 = -4 + jit(r, 3);
    const x1 = w + 5 + jit(r, 4);
    const pts = [];
    for (let i = 0; i <= 4; i += 1) {
      const t = i / 4;
      pts.push([x0 + (x1 - x0) * t, y0 + 1.5 - t * 4 + Math.sin(t * Math.PI) * 2 + jit(r, 1)]);
    }
    addPath(s, smoothPath(pts));
    if (el.classList.contains('double')) {
      const q = pts.map(([x, y], i) => [x + (i === 0 ? 14 : 0) + jit(r, 2), y + 8 + jit(r, 1)]);
      q[q.length - 1][0] -= 18;
      addPath(s, smoothPath(q));
    }
  };

  const drawStrike = (el, r) => {
    const w = el.offsetWidth;
    const h = el.offsetHeight;
    const s = decoSvg(el, w, h);
    const y = h * 0.56;
    addPath(s, smoothPath([[-5 + jit(r, 2), y + 3 + jit(r, 1.5)], [w * 0.5, y + jit(r, 2)], [w + 6 + jit(r, 2), y - 4 + jit(r, 1.5)]]));
  };

  const roughSide = (r, a, b, wobble) => {
    const mx = (a[0] + b[0]) / 2 + jit(r, wobble);
    const my = (a[1] + b[1]) / 2 + jit(r, wobble);
    return smoothPath([a, [mx, my], b]);
  };

  const drawBox = (el, r, over = 11, wobble = 2.4) => {
    const w = el.offsetWidth;
    const h = el.offsetHeight;
    const s = decoSvg(el, w, h);
    const c = [[jit(r, 3), jit(r, 3)], [w + jit(r, 3), jit(r, 3)], [w + jit(r, 3), h + jit(r, 3)], [jit(r, 3), h + jit(r, 3)]];
    const o = () => over * (0.6 + r() * 0.7);
    addPath(s, roughSide(r, [c[0][0] - o(), c[0][1] + jit(r, 1.5)], [c[1][0] + o(), c[1][1] + jit(r, 1.5)], wobble));
    addPath(s, roughSide(r, [c[1][0] + jit(r, 1.5), c[1][1] - o()], [c[2][0] + jit(r, 1.5), c[2][1] + o()], wobble));
    addPath(s, roughSide(r, [c[2][0] + o(), c[2][1] + jit(r, 1.5)], [c[3][0] - o(), c[3][1] + jit(r, 1.5)], wobble));
    addPath(s, roughSide(r, [c[3][0] + jit(r, 1.5), c[3][1] + o()], [c[0][0] + jit(r, 1.5), c[0][1] - o()], wobble));
  };

  const drawCircle = (el, r) => {
    const w = el.offsetWidth;
    const h = el.offsetHeight;
    const s = decoSvg(el, w, h);
    const cx = w / 2 + jit(r, 2);
    const cy = h / 2 + jit(r, 1.5);
    const rx = w / 2 + 6 + w * 0.03;
    const ry = h / 2 + 4 + h * 0.06;
    const start = -2.5 + jit(r, 0.3);
    const turns = 1.07 + r() * 0.05;
    const n = 64;
    const ph = r() * 6.28;
    const pts = [];
    for (let i = 0; i <= n; i += 1) {
      const t = i / n;
      const a = start + t * turns * Math.PI * 2;
      const k = 1 + 0.035 * Math.sin(a * 2 + ph) + t * 0.05;
      pts.push([cx + Math.cos(a) * rx * k, cy + Math.sin(a) * ry * k]);
    }
    addPath(s, smoothPath(pts));
  };

  const drawWarn = (el, r) => {
    const w = el.offsetWidth;
    const h = el.offsetHeight;
    const s = decoSvg(el, w, h);
    const top = [w / 2 + jit(r, 1.5), 1 + jit(r, 1)];
    const right = [w - 1 + jit(r, 1.5), h - 2 + jit(r, 1)];
    const left = [1 + jit(r, 1.5), h - 1 + jit(r, 1)];
    addPath(s, smoothPath([[top[0] - 3, top[1] + 5], top, [(top[0] + right[0]) / 2 + jit(r, 1), (top[1] + right[1]) / 2], right, [(right[0] + left[0]) / 2, right[1] + jit(r, 1.5)], left, [(left[0] + top[0]) / 2 + jit(r, 1), (left[1] + top[1]) / 2], [top[0] + 2, top[1] + 2]]));
    addPath(s, `M${f1(w / 2)} ${f1(h * 0.32)} L${f1(w / 2 + jit(r, 1))} ${f1(h * 0.64)}`);
    addPath(s, `M${f1(w / 2)} ${f1(h * 0.79)} L${f1(w / 2 + 0.6)} ${f1(h * 0.83)}`, { style: 'stroke-width:4.4px' });
  };

  const DECO = [
    ['.ul, .ul-blue, .ul-ink, .ul-green', drawUnderline],
    ['.box, .box-blue, .box-ink, .box-green', (el, r) => drawBox(el, r)],
    ['.shot', (el, r) => drawBox(el, r, 3, 1.2)],
    ['.circle, .circle-green, .circle-blue, .circle-ink', drawCircle],
    ['.warn', drawWarn],
    ['.strike', drawStrike],
  ];
  const buildDecos = () => {
    slides.forEach((slide, si) => {
      let k = 0;
      for (const [sel, fn] of DECO) {
        slide.querySelectorAll(sel).forEach((el) => {
          if (el.querySelector(':scope > .wh-deco')) return;
          k += 1;
          fn(el, rng(hash(`deco:${si}:${k}:${el.textContent.slice(0, 8)}`)));
        });
      }
    });
  };

  /* ---------- 思维导图连线 ---------- */
  const edgePoint = (b, from, to, gap) => {
    const cx = b.x + b.w / 2;
    const cy = b.y + b.h / 2;
    const dx = to[0] - from[0];
    const dy = to[1] - from[1];
    const hw = b.w / 2 + gap;
    const hh = b.h / 2 + gap;
    const tx = dx === 0 ? Infinity : hw / Math.abs(dx);
    const ty = dy === 0 ? Infinity : hh / Math.abs(dy);
    const t = Math.min(tx, ty);
    return [cx + dx * t, cy + dy * t];
  };
  const arrowHead = (tip, from, len = 15, spread = 0.46) => {
    const a = Math.atan2(tip[1] - from[1], tip[0] - from[0]);
    const p1 = [tip[0] - Math.cos(a - spread) * len, tip[1] - Math.sin(a - spread) * len];
    const p2 = [tip[0] - Math.cos(a + spread) * len, tip[1] - Math.sin(a + spread) * len];
    return `M${f1(p1[0])} ${f1(p1[1])} L${f1(tip[0])} ${f1(tip[1])} L${f1(p2[0])} ${f1(p2[1])}`;
  };
  const buildLinks = () => {
    slides.forEach((slide, si) => {
      slide.querySelectorAll('.link[data-from][data-to]').forEach((link, li) => {
        if (link.querySelector('svg')) return;
        const a = slide.querySelector(link.dataset.from);
        const b = slide.querySelector(link.dataset.to);
        if (!a || !b) {
          link.dataset.whError = `连线找不到节点 ${link.dataset.from} → ${link.dataset.to}`;
          return;
        }
        const r = rng(hash(`link:${si}:${li}`));
        const ra = relRect(a, link);
        const rb = relRect(b, link);
        const ca = [ra.x + ra.w / 2, ra.y + ra.h / 2];
        const cb = [rb.x + rb.w / 2, rb.y + rb.h / 2];
        const gap = Number(link.dataset.gap || 12);
        const p0 = edgePoint(ra, ca, cb, gap);
        const p1 = edgePoint(rb, cb, ca, gap);
        const dx = p1[0] - p0[0];
        const dy = p1[1] - p0[1];
        const len = Math.hypot(dx, dy) || 1;
        const bend = link.dataset.bend !== undefined ? Number(link.dataset.bend) : jit(r, 0.12) * len;
        const ctrl = [(p0[0] + p1[0]) / 2 - (dy / len) * bend, (p0[1] + p1[1]) / 2 + (dx / len) * bend];
        const s = svg('svg', { width: '1', height: '1', 'aria-hidden': 'true' });
        s.appendChild(svg('path', { d: `M${f1(p0[0])} ${f1(p0[1])} Q${f1(ctrl[0])} ${f1(ctrl[1])} ${f1(p1[0])} ${f1(p1[1])}` }));
        if (link.hasAttribute('data-arrow')) s.appendChild(svg('path', { d: arrowHead(p1, ctrl) }));
        link.appendChild(s);
      });
    });
  };

  /* ---------- 箭头标注 ---------- */
  const DIRS = {
    e: [1, 0], w: [-1, 0], n: [0, -1], s: [0, 1],
    ne: [0.8, -0.6], nw: [-0.8, -0.6], se: [0.8, 0.6], sw: [-0.8, 0.6],
  };
  const buildNotes = () => {
    slides.forEach((slide, si) => {
      slide.querySelectorAll('[data-note]').forEach((el, ni) => {
        if (el.whAnn) return;
        const r = rng(hash(`note:${si}:${ni}`));
        const ann = document.createElement('div');
        ann.className = `wh-ann c-${el.dataset.color || 'red'}`;
        ann.setAttribute('aria-hidden', 'true');
        const label = document.createElement('div');
        label.className = 'wh-ann-label';
        label.textContent = el.dataset.note.replace(/\\n/g, '\n');
        label.style.whiteSpace = 'pre';
        ann.appendChild(label);
        slide.appendChild(ann);
        el.whAnn = ann;
        ann.whTarget = el;

        const box = relRect(el, slide);
        const lw = label.offsetWidth;
        const lh = label.offsetHeight;
        const len = Number(el.dataset.len || 76);
        const gap = 8;
        const M = 28;
        let dir = (el.dataset.dir || 'e').toLowerCase();
        if (!DIRS[dir]) dir = 'e';

        const place = (d) => {
          const [dx, dy] = DIRS[d];
          const cx = box.x + box.w / 2;
          const cy = box.y + box.h / 2;
          const anchor = [
            cx + dx * (box.w / 2 + gap) - (dx !== 0 && dy !== 0 ? dx * box.w * 0.12 : 0),
            cy + dy * (box.h / 2 + gap),
          ];
          const tail = [anchor[0] + dx * len, anchor[1] + dy * len];
          let lx;
          let ly;
          if (dx > 0) lx = tail[0] + 8;
          else if (dx < 0) lx = tail[0] - 8 - lw;
          else lx = tail[0] - lw / 2;
          if (dy > 0) ly = dx === 0 ? tail[1] + 4 : tail[1] - lh * 0.3;
          else if (dy < 0) ly = dx === 0 ? tail[1] - lh - 4 : tail[1] - lh * 0.7;
          else ly = tail[1] - lh / 2;
          const fits = lx >= M && lx + lw <= W - M && ly >= M && ly + lh <= H - M;
          return { anchor, tail, lx, ly, fits };
        };
        const flipH = { e: 'w', w: 'e', ne: 'nw', nw: 'ne', se: 'sw', sw: 'se', n: 'n', s: 's' };
        const flipV = { n: 's', s: 'n', ne: 'se', se: 'ne', nw: 'sw', sw: 'nw', e: 'e', w: 'w' };
        let g = place(dir);
        if (!g.fits) {
          for (const d of [flipH[dir], flipV[dir], flipV[flipH[dir]]]) {
            const t = place(d);
            if (t.fits) {
              g = t;
              dir = d;
              break;
            }
          }
        }
        if (!g.fits) {
          ann.dataset.whClamped = '1';
          g.lx = clamp(g.lx, M, W - M - lw);
          g.ly = clamp(g.ly, M, H - M - lh);
        }
        label.style.left = `${f1(g.lx)}px`;
        label.style.top = `${f1(g.ly)}px`;
        ann.dataset.dir = dir;

        const [tx, ty] = g.tail;
        const [ax, ay] = g.anchor;
        const vx = ax - tx;
        const vy = ay - ty;
        const vl = Math.hypot(vx, vy) || 1;
        const bend = (r() > 0.5 ? 1 : -1) * (0.12 + r() * 0.1) * vl;
        const ctrl = [(tx + ax) / 2 - (vy / vl) * bend, (ty + ay) / 2 + (vx / vl) * bend];
        const s = svg('svg', { width: `${W}`, height: `${H}` });
        s.appendChild(svg('path', { d: `M${f1(tx)} ${f1(ty)} Q${f1(ctrl[0])} ${f1(ctrl[1])} ${f1(ax)} ${f1(ay)}` }));
        s.appendChild(svg('path', { d: arrowHead([ax, ay], ctrl) }));
        ann.insertBefore(s, label);
      });
    });
  };

  /* ---------- 逐步书写 ---------- */
  const CONTAINERS = '.body, .cols, .col, .stack, .row, .figs, .flow, .map, ul, ol, .cover-art, .cover-meta';
  const SKIP = '.notes, .wh-ann, script, style, template';

  const expandUnits = (el, out) => {
    if (el.matches(SKIP)) return;
    if (el.matches('table') && !el.hasAttribute('data-whole')) {
      for (const part of el.children) {
        if (part.matches('thead, caption')) out.push([part]);
        else if (part.matches('tbody, tfoot')) for (const tr of part.children) out.push([tr]);
        else if (part.matches('tr')) out.push([part]);
      }
      return;
    }
    if (el.matches(CONTAINERS) && !el.hasAttribute('data-whole')) {
      let arrow = null;
      for (const c of el.children) {
        if (c.matches('.arrow')) {
          arrow = c;
          continue;
        }
        const before = out.length;
        expandUnits(c, out);
        if (arrow && out.length > before) {
          out[before].unshift(arrow);
          arrow = null;
        }
      }
      if (arrow) out.push([arrow]);
      return;
    }
    out.push([el]);
  };

  const buildUnits = (slide) => {
    let groups = [];
    for (const c of slide.children) expandUnits(c, groups);
    // data-step：写了相同数字的元素（或其子元素）合成一步；这些步按数字从小到大占据它们原来的位置
    if (slide.querySelector('[data-step]')) {
      const keyOf = (g) => {
        for (const root of g) {
          const own = root.closest('[data-step]');
          if (own && slide.contains(own)) return Number(own.dataset.step) || 0;
          const inner = root.querySelector && root.querySelector('[data-step]');
          if (inner) return Number(inner.dataset.step) || 0;
        }
        return null;
      };
      const merged = [];
      const byKey = new Map();
      const slots = [];
      groups.forEach((g) => {
        const k = keyOf(g);
        if (k === null) {
          merged.push(g);
        } else if (byKey.has(k)) {
          byKey.get(k).push(...g);
        } else {
          const bucket = [...g];
          byKey.set(k, bucket);
          slots.push(merged.length);
          merged.push(null);
        }
      });
      const keys = [...byKey.keys()].sort((a, b) => a - b);
      slots.forEach((pos, i) => {
        merged[pos] = byKey.get(keys[i]);
      });
      groups = merged;
    }
    // 连线跟着它指向的节点一起出现：先画线，再写节点
    for (let gi = groups.length - 1; gi >= 0; gi -= 1) {
      const g = groups[gi];
      if (g.length !== 1 || !g[0].matches('.link[data-to]')) continue;
      const to = slide.querySelector(g[0].dataset.to);
      const host = to && groups.find((h) => h !== g && h.some((r) => r === to || r.contains(to)));
      if (host) {
        host.unshift(g[0]);
        groups.splice(gi, 1);
      }
    }
    const units = groups.filter((g) => g.length).map((roots) => ({ roots, anns: [] }));
    slide.querySelectorAll('[data-note]').forEach((el) => {
      if (!el.whAnn) return;
      const u = units.find((unit) => unit.roots.some((root) => root === el || root.contains(el))) || units[0];
      if (u) u.anns.push(el.whAnn);
    });
    return units;
  };

  const lineBoxes = (el) => {
    const prevRotate = el.style.rotate;
    el.style.rotate = '0deg';
    const s = scaleOf();
    const er = el.getBoundingClientRect();
    const rects = [];
    const range = document.createRange();
    for (const t of textNodes(el)) {
      range.selectNodeContents(t);
      for (const r of range.getClientRects()) {
        if (r.width < 1 || r.height < 1) continue;
        rects.push({ l: (r.left - er.left) / s, r: (r.right - er.left) / s, t: (r.top - er.top) / s, b: (r.bottom - er.top) / s });
      }
    }
    el.style.rotate = prevRotate;
    rects.sort((a, b) => a.t - b.t);
    const lines = [];
    for (const r of rects) {
      const ln = lines.find((l) => Math.min(l.b, r.b) - Math.max(l.t, r.t) > 0.45 * Math.min(l.b - l.t, r.b - r.t));
      if (ln) {
        ln.l = Math.min(ln.l, r.l);
        ln.r = Math.max(ln.r, r.r);
        ln.t = Math.min(ln.t, r.t);
        ln.b = Math.max(ln.b, r.b);
      } else lines.push({ ...r });
    }
    lines.sort((a, b) => a.t - b.t);
    return { lines, w: el.offsetWidth, h: el.offsetHeight };
  };

  // 逐行书写：polygon 裁剪，前面的行完整可见，当前行从左往右写出
  const writeFrames = (el) => {
    const { lines, w, h } = lineBoxes(el);
    if (!lines.length) return null;
    const m = 30;
    const right = Math.max(w, ...lines.map((l) => l.r)) + m;
    const bottom = Math.max(h, ...lines.map((l) => l.b)) + m;
    const bounds = lines.map((l, i) => ({
      top: i === 0 ? -m : (lines[i - 1].b + l.t) / 2,
      bot: i === lines.length - 1 ? bottom : (l.b + lines[i + 1].t) / 2,
      x0: l.l - 6,
      x1: l.r + 8,
      wgt: Math.max(1, l.r - l.l),
    }));
    const total = bounds.reduce((n, b) => n + b.wgt, 0);
    const poly = (top, bot, x) => `polygon(${[[-m, -m], [right, -m], [right, top], [x, top], [x, bot], [-m, bot]].map(([px, py]) => `${f1(px)}px ${f1(py)}px`).join(', ')})`;
    const frames = [];
    let acc = 0;
    bounds.forEach((b) => {
      frames.push({ offset: acc / total, clipPath: poly(b.top, b.bot, b.x0) });
      acc += b.wgt;
      frames.push({ offset: Math.min(1, acc / total), clipPath: poly(b.top, b.bot, b.x1) });
    });
    for (let i = 1; i < frames.length; i += 1) {
      if (frames[i].offset <= frames[i - 1].offset) frames[i].offset = Math.min(1, frames[i - 1].offset + 1e-4);
    }
    frames[frames.length - 1].offset = 1;
    return frames;
  };

  const strokeLen = (shape) => {
    try {
      return shape.getTotalLength();
    } catch {
      return 0;
    }
  };

  const playUnit = (unit, t0) => {
    const anims = [];
    let t = t0;
    const add = (el, frames, dur, { gap = 50, parallel = false, easing = 'cubic-bezier(.35,.1,.35,1)' } = {}) => {
      const a = el.animate(frames, { duration: dur, delay: t, fill: 'backwards', easing });
      anims.push(a);
      if (!parallel) t += dur + gap;
      return a;
    };
    const draw = (shape, speed = 1.15, min = 200, max = 760) => {
      const len = strokeLen(shape);
      if (!len) return;
      const dash = `${f1(len + 2)} ${f1(len + 2)}`;
      add(shape, [{ strokeDasharray: dash, strokeDashoffset: `${f1(len + 2)}` }, { strokeDasharray: dash, strokeDashoffset: '0' }], clamp(len * speed, min, max), { gap: 30, easing: 'cubic-bezier(.5,.05,.4,1)' });
    };
    const write = (el, perChar = 36) => {
      const frames = writeFrames(el);
      if (!frames) return false;
      const chars = Math.max(1, visibleChars(el));
      add(el, frames, clamp(chars * perChar, 280, 1700), { easing: 'linear', gap: 70 });
      return true;
    };
    const fade = (el, dur = 420) => add(el, [{ opacity: 0 }, { opacity: 1 }], dur, { gap: 40 });
    const drawDiagram = (s) => {
      const items = Array.from(s.querySelectorAll('path, line, polyline, polygon, rect, circle, ellipse, text, image'))
        .filter((n) => !n.closest('defs, marker, clipPath, mask, symbol'));
      const plan = items.map((n) => {
        if (n.matches('text, image')) return { n, kind: 'fade', dur: 260 };
        const cs = getComputedStyle(n);
        const stroked = cs.stroke !== 'none' && (cs.fill === 'none' || cs.fillOpacity === '0');
        const len = stroked ? strokeLen(n) : 0;
        if (len && !cs.strokeDasharray.match(/\d/)) return { n, kind: 'draw', len, dur: clamp(len * 1.1, 180, 800) };
        return { n, kind: 'fade', dur: 280 };
      });
      const sum = plan.reduce((x, p) => x + p.dur + 30, 0);
      const k = sum > 4200 ? 4200 / sum : 1;
      for (const p of plan) {
        if (p.kind === 'draw') {
          const dash = `${f1(p.len + 2)} ${f1(p.len + 2)}`;
          add(p.n, [{ strokeDasharray: dash, strokeDashoffset: `${f1(p.len + 2)}` }, { strokeDasharray: dash, strokeDashoffset: '0' }], p.dur * k, { gap: 30 * k });
        } else add(p.n, [{ opacity: 0 }, { opacity: 1 }], p.dur * k, { gap: 30 * k });
      }
    };

    for (const root of unit.roots) {
      root.removeAttribute('data-wh-p');
      if (REDUCED) continue;
      const before = anims.length;
      const imgs = root.matches('img') ? [root] : Array.from(root.querySelectorAll('img'));
      const diagrams = root.matches('svg') ? [root] : Array.from(root.querySelectorAll('svg')).filter((s) => !s.closest('.wh-deco, .link') && !s.matches('.wh-deco'));
      const linkPaths = root.matches('.link') ? Array.from(root.querySelectorAll('path')) : [];
      imgs.forEach((img) => fade(img, 480));
      diagrams.forEach(drawDiagram);
      linkPaths.forEach((p) => draw(p, 1.0, 220, 600));
      if (root.matches('tr, thead')) {
        root.querySelectorAll('th, td').forEach((cell) => write(cell, 22));
      } else if (imgs.length || diagrams.length) {
        root.querySelectorAll('.cap, figcaption, p, .line').forEach((cap) => {
          if (!cap.closest('svg')) write(cap, 30);
        });
      } else if (!linkPaths.length) {
        write(root);
      }
      const hls = Array.from(root.querySelectorAll('.hl, .hl-yellow, .hl-green, .hl-coral, .takeaway, .dot, .dot-yellow, .dot-green, .dot-coral'));
      if (root.matches('.takeaway, .hl, .hl-yellow, .hl-green, .hl-coral')) hls.unshift(root);
      hls.forEach((hl) => {
        const dot = hl.matches('[class*="dot"]');
        const end = getComputedStyle(hl).backgroundSize;
        const start = dot ? '0% 0%' : end.replace(/^\S+/, '0%');
        add(hl, [{ backgroundSize: start }, { backgroundSize: end }], dot ? 300 : 460, { gap: 40, easing: 'cubic-bezier(.4,.1,.3,1)' });
      });
      root.querySelectorAll('.wh-deco path').forEach((p) => {
        if (!p.closest('.link')) draw(p);
      });
      if (anims.length === before) fade(root, 360);
    }
    for (const ann of unit.anns) {
      ann.removeAttribute('data-wh-p');
      if (REDUCED) continue;
      ann.querySelectorAll('svg path').forEach((p, i) => draw(p, i === 0 ? 1.2 : 2.5, i === 0 ? 260 : 120, 520));
      const label = ann.querySelector('.wh-ann-label');
      if (label) write(label, 30);
    }
    return { anims, end: t };
  };

  /* ---------- 状态 ---------- */
  let cur = 0;
  let step = 0;
  let unitsBySlide = [];
  let running = [];
  let autoplay = null;

  const hideUnit = (u) => {
    u.roots.forEach((r) => r.setAttribute('data-wh-p', ''));
    u.anns.forEach((a) => a.setAttribute('data-wh-p', ''));
  };
  const stopAnims = () => {
    running.forEach((a) => a.cancel());
    running = [];
  };
  const finishAnims = () => {
    const live = running.filter((a) => a.playState === 'running' || a.playState === 'pending');
    live.forEach((a) => a.finish());
    running = [];
    return live.length > 0;
  };
  const isAnimating = () => running.some((a) => a.playState === 'running' || a.playState === 'pending');
  const autoSlide = (slide) => slide.matches('.cover, .end, [data-auto]');

  const setActive = (n) => {
    slides.forEach((s, i) => {
      s.classList.toggle('is-active', i === n);
      s.classList.toggle('is-prev', i < n);
      s.setAttribute('aria-hidden', i === n ? 'false' : 'true');
    });
  };

  const show = (n, how = 'start') => {
    n = clamp(n, 0, slides.length - 1);
    const changed = n !== cur;
    stopAnims();
    cur = n;
    setActive(n);
    const slide = slides[n];
    if (STEPS) {
      const units = unitsBySlide[n];
      units.forEach(hideUnit);
      if (how === 'end' || !units.length) {
        units.forEach((u) => {
          u.roots.forEach((el) => el.removeAttribute('data-wh-p'));
          u.anns.forEach((el) => el.removeAttribute('data-wh-p'));
        });
        step = units.length - 1;
      } else if (autoSlide(slide)) {
        let t = 120;
        units.forEach((u) => {
          const res = playUnit(u, t);
          running.push(...res.anims);
          t = res.end + 120;
        });
        step = units.length - 1;
      } else {
        const res = playUnit(units[0], 160);
        running.push(...res.anims);
        step = 0;
      }
    }
    if (MODE === 'present' && changed && !REDUCED) {
      slide.animate([{ opacity: 0 }, { opacity: 1 }], { duration: STEPS ? 140 : 200, easing: 'ease-out' });
    }
    if (MODE === 'present') {
      const h = `#/${n + 1}`;
      if (location.hash !== h) history.replaceState(null, '', h);
      updateUi();
    }
  };

  const next = () => {
    if (STEPS) {
      if (finishAnims()) return updateUi();
      const units = unitsBySlide[cur];
      if (step < units.length - 1) {
        step += 1;
        const res = playUnit(units[step], 0);
        running.push(...res.anims);
        return updateUi();
      }
    }
    if (cur < slides.length - 1) show(cur + 1, 'start');
  };

  const prev = () => {
    if (STEPS) {
      const units = unitsBySlide[cur];
      if (step > 0) {
        stopAnims();
        hideUnit(units[step]);
        step -= 1;
        return updateUi();
      }
    }
    if (cur > 0) show(cur - 1, 'end');
  };

  const hashIndex = () => {
    const m = location.hash.match(/^#\/?(\d+)/);
    return m ? clamp(Number(m[1]) - 1, 0, slides.length - 1) : 0;
  };

  /* ---------- 克隆（总览、演讲者视图、总览图） ---------- */
  const cleanClone = (slide, full) => {
    const c = slide.cloneNode(true);
    c.classList.add('is-active');
    c.removeAttribute('aria-hidden');
    c.querySelectorAll('[id]').forEach((el) => el.removeAttribute('id'));
    if (full) {
      c.removeAttribute('data-wh-p');
      c.querySelectorAll('[data-wh-p]').forEach((el) => el.removeAttribute('data-wh-p'));
    }
    c.querySelectorAll('.notes').forEach((el) => el.remove());
    return c;
  };
  const miniStage = (slide, full, doc = document) => {
    const stage = doc.createElement('div');
    stage.className = 'wh-mini';
    stage.appendChild(doc.importNode(cleanClone(slide, full), true));
    return stage;
  };
  const sizeMini = (frame) => {
    const stage = frame.querySelector('.wh-mini');
    if (stage) stage.style.setProperty('--mini', `${frame.clientWidth / W}`);
  };

  /* ---------- 界面 ---------- */
  const ICON = {
    prev: '<path d="M15 5l-7 7 7 7"/>',
    next: '<path d="M9 5l7 7-7 7"/>',
    grid: '<rect x="4" y="4" width="7" height="7" rx="1"/><rect x="13" y="4" width="7" height="7" rx="1"/><rect x="4" y="13" width="7" height="7" rx="1"/><rect x="13" y="13" width="7" height="7" rx="1"/>',
    notes: '<path d="M5 5h14M5 10h14M5 15h9"/>',
    presenter: '<rect x="3" y="4" width="18" height="12" rx="1.5"/><path d="M8 20h8M12 16v4"/>',
    full: '<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>',
    play: '<path d="M8 5l11 7-11 7z"/>',
    swap: '<path d="M4 8h13l-3-3M20 16H7l3 3"/>',
    help: '<circle cx="12" cy="12" r="9"/><path d="M9.6 9.4a2.5 2.5 0 1 1 3.4 2.3c-.7.3-1 .8-1 1.5v.5M12 17h.01"/>',
  };
  const ui = {};
  const updateUi = () => {
    if (MODE !== 'present' || !ui.count) return;
    const units = STEPS ? unitsBySlide[cur] : null;
    ui.count.textContent = STEPS && units.length > 1
      ? `${cur + 1} / ${slides.length} · ${step + 1}/${units.length}`
      : `${cur + 1} / ${slides.length}`;
    ui.progress.style.width = `${((cur + 1) / slides.length) * 100}%`;
    if (ui.notes.classList.contains('open')) fillNotes();
    if (ui.overview && ui.overview.classList.contains('open')) markOverview();
    updatePresenter();
  };
  const fillNotes = () => {
    const n = slides[cur].querySelector('.notes');
    ui.notes.innerHTML = '';
    const head = document.createElement('div');
    head.style.cssText = 'opacity:.6;font-size:13px;margin-bottom:6px';
    head.textContent = `第 ${cur + 1} 页 · ${titleOf(slides[cur])}`;
    ui.notes.appendChild(head);
    const body = document.createElement('div');
    body.innerHTML = n ? n.innerHTML : '（这一页没有讲稿）';
    ui.notes.appendChild(body);
  };
  const toast = (msg) => {
    const t = document.createElement('div');
    t.className = 'wh-ui';
    t.style.cssText = 'position:fixed;left:50%;top:22px;transform:translateX(-50%);z-index:80;padding:9px 16px;border-radius:8px;background:rgba(20,22,30,.9);color:#fff;font-size:14px';
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 2600);
  };

  const buildOverview = () => {
    const ov = document.createElement('div');
    ov.className = 'wh-overview wh-ui';
    slides.forEach((slide, i) => {
      const th = document.createElement('div');
      th.className = 'wh-thumb';
      th.title = `${i + 1}. ${titleOf(slide)}`;
      th.appendChild(miniStage(slide, true));
      const n = document.createElement('span');
      n.className = 'n';
      n.textContent = `${i + 1}`;
      th.appendChild(n);
      th.addEventListener('click', () => {
        ov.classList.remove('open');
        show(i, 'start');
      });
      ov.appendChild(th);
    });
    document.body.appendChild(ov);
    ui.overview = ov;
  };
  const markOverview = () => {
    ui.overview.querySelectorAll('.wh-thumb').forEach((th, i) => th.classList.toggle('cur', i === cur));
  };
  const toggleOverview = (force) => {
    if (!ui.overview) buildOverview();
    const open = force !== undefined ? force : !ui.overview.classList.contains('open');
    ui.overview.classList.toggle('open', open);
    if (open) {
      ui.overview.querySelectorAll('.wh-thumb').forEach(sizeMini);
      markOverview();
      const c = ui.overview.querySelectorAll('.wh-thumb')[cur];
      if (c) c.scrollIntoView({ block: 'center' });
    }
  };

  /* 演讲者视图：about:blank 弹窗，由本窗口直接写入 DOM */
  let pw = null;
  let pwStart = 0;
  let pwTimer = 0;
  const PRESENTER_CSS = `
    html, body { margin:0; height:100%; overflow:hidden; background:#14151a; color:#e9ebf3; font-family: var(--ui); }
    .pv { box-sizing:border-box; height:100%; padding:18px; display:grid; gap:16px;
      grid-template-columns: minmax(0, 62fr) minmax(0, 38fr); grid-template-rows: minmax(0, 1fr) auto; }
    .pv-cur { position:relative; align-self:start; }
    .pv-side { display:flex; flex-direction:column; gap:14px; min-height:0; }
    .pv-frame { position:relative; width:100%; aspect-ratio:16/9; overflow:hidden; border-radius:6px; background:#fdfdfb; }
    .pv-label { font-size:12px; letter-spacing:.08em; opacity:.55; margin:0 0 6px; }
    .pv-notes { flex:1; min-height:0; overflow:auto; font-size:21px; line-height:1.75; padding:14px 16px; border-radius:6px; background:#1d1f27; }
    .pv-notes:empty::before { content:'这一页没有讲稿'; opacity:.4; }
    .pv-foot { grid-column:1 / 3; display:flex; gap:28px; align-items:center; font-size:15px; opacity:.85; }
    .pv-foot b { font-size:26px; font-variant-numeric:tabular-nums; font-weight:600; }
    .pv-foot button { background:#2a2d38; color:#fff; border:0; border-radius:6px; padding:7px 14px; font-size:14px; cursor:pointer; }
  `;
  const openPresenter = () => {
    if (pw && !pw.closed) {
      pw.focus();
      return;
    }
    pw = window.open('', 'wh-presenter', 'width=1360,height=800');
    if (!pw) {
      toast('浏览器拦截了弹窗，请允许本页面打开新窗口');
      return;
    }
    const d = pw.document;
    d.open();
    d.write('<!doctype html><html><head><meta charset="utf-8"><title>演讲者视图</title></head><body></body></html>');
    d.close();
    document.querySelectorAll('head style').forEach((s) => d.head.appendChild(d.importNode(s, true)));
    const st = d.createElement('style');
    st.textContent = PRESENTER_CSS;
    d.head.appendChild(st);
    d.body.innerHTML = `
      <div class="pv">
        <div class="pv-cur"><p class="pv-label">当前</p><div class="pv-frame" id="pv-cur"></div></div>
        <div class="pv-side">
          <div><p class="pv-label">下一页</p><div class="pv-frame" id="pv-next"></div></div>
          <p class="pv-label" style="margin:4px 0 -8px">讲稿</p>
          <div class="pv-notes" id="pv-notes"></div>
        </div>
        <div class="pv-foot">
          <span>用时 <b id="pv-time">00:00</b></span>
          <span>页码 <b id="pv-page"></b></span>
          <span id="pv-step"></span>
          <button id="pv-reset">计时归零</button>
          <span style="opacity:.55">← → 翻页，与主窗口同步</span>
        </div>
      </div>`;
    d.addEventListener('keydown', onKey);
    d.getElementById('pv-reset').addEventListener('click', () => {
      pwStart = Date.now();
    });
    pw.addEventListener('resize', () => d.querySelectorAll('.pv-frame').forEach(sizeMini));
    pwStart = Date.now();
    clearInterval(pwTimer);
    pwTimer = setInterval(() => {
      if (!pw || pw.closed) {
        clearInterval(pwTimer);
        return;
      }
      const s = Math.floor((Date.now() - pwStart) / 1000);
      pw.document.getElementById('pv-time').textContent = `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
    }, 500);
    updatePresenter();
  };
  function updatePresenter() {
    if (!pw || pw.closed) return;
    const d = pw.document;
    const curF = d.getElementById('pv-cur');
    const nextF = d.getElementById('pv-next');
    if (!curF) return;
    curF.replaceChildren(miniStage(slides[cur], !STEPS, d));
    nextF.replaceChildren();
    if (cur + 1 < slides.length) nextF.appendChild(miniStage(slides[cur + 1], true, d));
    d.querySelectorAll('.pv-frame').forEach(sizeMini);
    const n = slides[cur].querySelector('.notes');
    d.getElementById('pv-notes').innerHTML = n ? n.innerHTML : '';
    d.getElementById('pv-page').textContent = `${cur + 1} / ${slides.length}`;
    const units = STEPS ? unitsBySlide[cur] : [];
    d.getElementById('pv-step').textContent = units.length > 1 ? `步骤 ${step + 1} / ${units.length}` : '';
  }

  const toggleFull = () => {
    if (document.fullscreenElement) document.exitFullscreen();
    else if (html.requestFullscreen) html.requestFullscreen().catch(() => {});
  };
  const toggleAuto = () => {
    if (autoplay) {
      clearTimeout(autoplay);
      autoplay = null;
      if (ui.play) ui.play.classList.remove('on');
      return;
    }
    if (ui.play) ui.play.classList.add('on');
    const tick = async () => {
      if (!autoplay) return;
      await Promise.all(running.map((a) => a.finished.catch(() => {})));
      if (!autoplay) return;
      const atEnd = !STEPS || step >= unitsBySlide[cur].length - 1;
      if (atEnd && cur === slides.length - 1) {
        toggleAuto();
        return;
      }
      autoplay = setTimeout(() => {
        next();
        tick();
      }, atEnd ? 2600 : 1100);
    };
    autoplay = setTimeout(tick, 10);
  };
  const black = (white) => {
    const on = !ui.black.classList.contains('on') || ui.black.classList.contains('white') !== white;
    ui.black.classList.toggle('white', white);
    ui.black.classList.toggle('on', on);
  };
  const altHref = () => (deck.dataset.alt ? deck.dataset.alt + location.hash : null);

  let typed = '';
  function onKey(e) {
    if (e.target && e.target.closest && e.target.closest('input, textarea, [contenteditable]')) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const k = e.key;
    let used = true;
    if (ui.help && ui.help.classList.contains('open') && k !== '?') {
      ui.help.classList.remove('open');
      if (k === 'Escape') return;
    }
    if (/^\d$/.test(k)) {
      typed += k;
      return;
    }
    if (k === 'Enter' && typed) {
      show(Number(typed) - 1, 'start');
      typed = '';
      e.preventDefault();
      return;
    }
    typed = '';
    if (['ArrowRight', 'ArrowDown', 'PageDown', 'Enter', 'l', 'j'].includes(k) || (k === ' ' && !e.shiftKey)) next();
    else if (['ArrowLeft', 'ArrowUp', 'PageUp', 'Backspace', 'h', 'k'].includes(k) || (k === ' ' && e.shiftKey)) prev();
    else if (k === 'Home') show(0, 'start');
    else if (k === 'End') show(slides.length - 1, 'start');
    else if (k === 'f' || k === 'F') toggleFull();
    else if (k === 'o' || k === 'O') toggleOverview();
    else if (k === 'Escape') {
      if (ui.overview) toggleOverview(false);
      ui.notes.classList.remove('open');
      ui.black.classList.remove('on');
    } else if (k === 'n' || k === 'N') {
      ui.notes.classList.toggle('open');
      if (ui.notes.classList.contains('open')) fillNotes();
    } else if (k === 's' || k === 'S') openPresenter();
    else if (k === 'b' || k === 'B' || k === '.') black(false);
    else if (k === 'w' || k === 'W') black(true);
    else if (k === 'r' || k === 'R') show(cur, 'start');
    else if (k === 'p' || k === 'P') toggleAuto();
    else if ((k === 't' || k === 'T') && altHref()) location.href = altHref();
    else if (k === '?') ui.help.classList.toggle('open');
    else used = false;
    if (used) {
      e.preventDefault();
      wake();
    }
  }

  let idle = 0;
  const wake = () => {
    if (!ui.bar) return;
    ui.bar.classList.add('show');
    ui.progress.classList.add('show');
    html.classList.remove('wh-idle');
    clearTimeout(idle);
    idle = setTimeout(() => {
      if (ui.bar.matches(':hover')) return wake();
      ui.bar.classList.remove('show');
      ui.progress.classList.remove('show');
      html.classList.add('wh-idle');
    }, 2200);
  };

  const buildUi = () => {
    const bar = document.createElement('div');
    bar.className = 'wh-bar wh-ui';
    const btn = (name, title, fn) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.title = title;
      b.setAttribute('aria-label', title);
      b.innerHTML = `<svg viewBox="0 0 24 24">${ICON[name]}</svg>`;
      b.addEventListener('click', (e) => {
        e.stopPropagation();
        fn();
      });
      bar.appendChild(b);
      return b;
    };
    const sep = () => {
      const s = document.createElement('span');
      s.className = 'wh-sep';
      bar.appendChild(s);
    };
    btn('prev', '上一步 ←', prev);
    ui.count = document.createElement('span');
    ui.count.className = 'wh-count';
    bar.appendChild(ui.count);
    btn('next', '下一步 → / 空格', next);
    sep();
    btn('grid', '总览 O', () => toggleOverview());
    btn('notes', '讲稿 N', () => {
      ui.notes.classList.toggle('open');
      if (ui.notes.classList.contains('open')) fillNotes();
    });
    btn('presenter', '演讲者视图 S', openPresenter);
    ui.play = btn('play', '自动播放 P', toggleAuto);
    if (deck.dataset.alt) btn('swap', STEPS ? '切到整页版 T' : '切到逐步书写版 T', () => { location.href = altHref(); });
    btn('full', '全屏 F', toggleFull);
    btn('help', '快捷键 ?', () => ui.help.classList.toggle('open'));
    document.body.appendChild(bar);
    ui.bar = bar;

    ui.progress = document.createElement('div');
    ui.progress.className = 'wh-progress wh-ui';
    document.body.appendChild(ui.progress);

    ui.notes = document.createElement('div');
    ui.notes.className = 'wh-notes wh-ui';
    document.body.appendChild(ui.notes);

    ui.black = document.createElement('div');
    ui.black.className = 'wh-black wh-ui';
    ui.black.addEventListener('click', () => ui.black.classList.remove('on'));
    document.body.appendChild(ui.black);

    ui.help = document.createElement('div');
    ui.help.className = 'wh-help wh-ui';
    const rows = [
      ['→ 空格 点击', STEPS ? '下一步（动画中再按一次＝立即写完）' : '下一页'],
      ['← Shift+空格', STEPS ? '上一步' : '上一页'],
      ['Home / End', '第一页 / 最后一页'],
      ['数字 + 回车', '跳到指定页'],
      ['O', '总览'], ['N', '讲稿'], ['S', '演讲者视图（双屏）'],
      ['P', '自动播放'], ['R', '重播本页'], ['B / W', '黑屏 / 白屏'], ['F', '全屏'],
    ];
    if (deck.dataset.alt) rows.push(['T', STEPS ? '切到整页版' : '切到逐步书写版']);
    ui.help.innerHTML = `<div>${rows.map(([a, b]) => `<div><kbd>${a}</kbd>${b}</div>`).join('')}</div>`;
    ui.help.addEventListener('click', () => ui.help.classList.remove('open'));
    document.body.appendChild(ui.help);

    document.addEventListener('keydown', onKey);
    addEventListener('mousemove', wake, { passive: true });
    addEventListener('hashchange', () => {
      const n = hashIndex();
      if (n !== cur) show(n, 'start');
    });
    addEventListener('resize', () => {
      if (ui.overview && ui.overview.classList.contains('open')) ui.overview.querySelectorAll('.wh-thumb').forEach(sizeMini);
    });
    deck.addEventListener('click', (e) => {
      if (e.target.closest('a, button, input, select, textarea, video, audio, [data-no-advance]')) return;
      const sel = getSelection && getSelection();
      if (sel && String(sel).length) return;
      if (e.shiftKey) prev();
      else next();
    });
    let tx = 0;
    let ty = 0;
    addEventListener('touchstart', (e) => {
      tx = e.touches[0].clientX;
      ty = e.touches[0].clientY;
    }, { passive: true });
    addEventListener('touchend', (e) => {
      const dx = e.changedTouches[0].clientX - tx;
      const dy = e.changedTouches[0].clientY - ty;
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.3) {
        if (dx < 0) next();
        else prev();
      }
    }, { passive: true });
    wake();
  };

  /* ---------- 总览图 ---------- */
  const buildSheet = () => {
    const grid = document.createElement('div');
    grid.className = 'wh-sheet-grid wh-ui';
    slides.forEach((slide) => {
      const th = document.createElement('div');
      th.className = 'wh-thumb';
      const stage = miniStage(slide, true);
      stage.style.setProperty('--mini', `${480 / W}`);
      th.appendChild(stage);
      grid.appendChild(th);
    });
    document.body.appendChild(grid);
    html.classList.add('wh-sheet-done');
  };

  /* ---------- 版式体检 ---------- */
  const runAudit = () => {
    const out = { version: 2, slides: [], font: {} };
    const famOk = document.fonts && document.fonts.check('40px "WH Hand"', '王虹手写');
    out.font.whHand = !!famOk;
    out.font.family = getComputedStyle(deck).fontFamily;
    const miss = document.querySelector('meta[name="wh-missing-glyphs"]');
    out.font.missing = miss ? miss.content : '';
    const SAFE = { l: 56, r: W - 56, t: 36, b: H - 36 };
    const inter = (a, b) => Math.max(0, Math.min(a.r, b.r) - Math.max(a.l, b.l)) * Math.max(0, Math.min(a.b, b.b) - Math.max(a.t, b.t));
    const area = (a) => Math.max(1, (a.r - a.l) * (a.b - a.t));
    const BLOCK = 'p, li, .line, .lead, .node, td, th, .cap, h1, h2, h3, figcaption, .takeaway, .formula, pre, text, .title, .wh-ann-label, .cover-meta > *, div';

    slides.forEach((slide, i) => {
      setActive(i);
      const res = { index: i + 1, title: titleOf(slide), errors: [], warnings: [] };
      const E = (m) => { if (!res.errors.includes(m)) res.errors.push(m); };
      const Wn = (m) => { if (!res.warnings.includes(m)) res.warnings.push(m); };
      const sr = slide.getBoundingClientRect();
      const loc = (r) => ({ l: r.left - sr.left, r: r.right - sr.left, t: r.top - sr.top, b: r.bottom - sr.top });
      const short = (el) => el.textContent.replace(/\s+/g, '').slice(0, 14);

      if (!slide.dataset.title && !slide.querySelector('.lead, .title')) Wn('缺少 data-title 或 .lead 标题句');
      const notes = slide.querySelector('.notes');
      if (!notes || !notes.textContent.trim()) Wn('缺少讲稿 .notes');
      const chars = visibleChars(slide);
      if (chars > 220) Wn(`单页文字 ${chars} 字，超过 220 字，考虑拆页`);
      if (slide.scrollHeight > H + 4) E(`内容总高 ${slide.scrollHeight}px，溢出画布`);
      slide.querySelectorAll('.body').forEach((b) => {
        if (b.scrollHeight > b.clientHeight + 4) E(`.body 内容高 ${b.scrollHeight}px，超出可用高度 ${b.clientHeight}px`);
      });
      slide.querySelectorAll('[data-wh-error]').forEach((el) => E(el.dataset.whError));
      slide.querySelectorAll('.wh-ann[data-wh-clamped]').forEach((a) => E(`标注「${a.textContent.slice(0, 12)}」四个方向都放不下，已被强行压进画布`));

      // 文字块
      const blocks = new Map();
      const range = document.createRange();
      for (const t of textNodes(slide)) {
        const p = t.parentElement;
        const block = p.closest(BLOCK) || p;
        range.selectNodeContents(t);
        const rects = Array.from(range.getClientRects()).filter((r) => r.width > 0.5 && r.height > 0.5).map(loc);
        if (!rects.length) continue;
        if (!blocks.has(block)) blocks.set(block, []);
        blocks.get(block).push(...rects);
        // 字号
        let size = parseFloat(getComputedStyle(p).fontSize);
        const inSvg = p.closest('svg');
        if (inSvg && inSvg.viewBox && inSvg.viewBox.baseVal && inSvg.viewBox.baseVal.width) {
          size *= inSvg.getBoundingClientRect().width / inSvg.viewBox.baseVal.width;
        }
        const isCap = !!p.closest('.cap, .cover-credit');
        if (size < (isCap ? 20 : 22)) E(`字号 ${size.toFixed(1)}px 过小：「${short(p)}」`);
        else if (!isCap && size < 26) Wn(`字号 ${size.toFixed(1)}px 偏小：「${short(p)}」`);
        for (const r of rects) {
          if (r.l < -1 || r.t < -1 || r.r > W + 1 || r.b > H + 1) E(`文字超出画布：「${short(p)}」`);
          else if (r.l < SAFE.l || r.r > SAFE.r || r.t < SAFE.t || r.b > SAFE.b) Wn(`文字贴边：「${short(p)}」`);
        }
      }
      // 末行孤字
      blocks.forEach((rects, block) => {
        if (block.closest('svg, .map, .hand-table, .tree, .code')) return;
        const lines = [];
        rects.slice().sort((a, b) => a.t - b.t).forEach((r) => {
          const ln = lines.find((l) => Math.min(l.b, r.b) - Math.max(l.t, r.t) > 0.45 * Math.min(l.b - l.t, r.b - r.t));
          if (ln) {
            ln.l = Math.min(ln.l, r.l);
            ln.r = Math.max(ln.r, r.r);
          } else lines.push({ ...r });
        });
        if (lines.length < 2) return;
        const last = lines[lines.length - 1];
        const fs = parseFloat(getComputedStyle(block).fontSize);
        if (last.r - last.l < fs * 1.7) Wn(`末行只剩一两个字（孤字）：「${short(block)}」`);
      });
      // 重叠
      const entries = [...blocks.entries()];
      for (let a = 0; a < entries.length; a += 1) {
        for (let b = a + 1; b < entries.length; b += 1) {
          const [ea, ra] = entries[a];
          const [eb, rb] = entries[b];
          if (ea.contains(eb) || eb.contains(ea)) continue;
          const isAnn = ea.matches('.wh-ann-label') || eb.matches('.wh-ann-label');
          let worst = 0;
          for (const x of ra) for (const y of rb) worst = Math.max(worst, inter(x, y) / Math.min(area(x), area(y)));
          if (worst > (isAnn ? 0.04 : 0.12)) E(`${isAnn ? '标注与文字' : '文字'}重叠：「${short(ea)}」×「${short(eb)}」`);
          else if (worst > 0.01) Wn(`文字轻微重叠：「${short(ea)}」×「${short(eb)}」`);
        }
      }
      // 标注压在图片上
      const imgs = Array.from(slide.querySelectorAll('img'));
      slide.querySelectorAll('.wh-ann-label').forEach((lab) => {
        const lr = loc(lab.getBoundingClientRect());
        imgs.forEach((img) => {
          const ir = loc(img.getBoundingClientRect());
          if (inter(lr, ir) / area(lr) > 0.1) E(`标注「${short(lab)}」压在图片上`);
        });
      });
      // 图片
      imgs.forEach((img) => {
        if (!img.complete || !img.naturalWidth) E(`图片加载失败：${(img.getAttribute('src') || '').slice(0, 60)}`);
        const r = loc(img.getBoundingClientRect());
        if (r.l < -1 || r.t < -1 || r.r > W + 1 || r.b > H + 1) E('图片超出画布');
        if (img.naturalWidth && r.r - r.l > img.naturalWidth * 1.6) Wn(`图片被放大 ${((r.r - r.l) / img.naturalWidth).toFixed(1)} 倍，可能发虚`);
      });
      // 中间留白断层
      if (!slide.matches('.cover, .end')) {
        const spans = [];
        blocks.forEach((rects) => rects.forEach((r) => spans.push([r.t, r.b])));
        slide.querySelectorAll('img, svg.diagram, .map, .hand-table').forEach((el) => {
          const r = loc(el.getBoundingClientRect());
          if (r.b - r.t > 2) spans.push([r.t, r.b]);
        });
        spans.sort((a, b) => a[0] - b[0]);
        let reach = null;
        let maxGap = 0;
        for (const [t, b] of spans) {
          if (reach !== null && t - reach > maxGap) maxGap = t - reach;
          reach = reach === null ? b : Math.max(reach, b);
        }
        if (maxGap > 300) Wn(`页面中间有 ${Math.round(maxGap)}px 的空洞`);
        if (spans.length) {
          const top = spans[0][0];
          const bottom = reach;
          if (bottom < H * 0.45) Wn('内容挤在上半屏，下半屏空着');
          if (top > H * 0.5) Wn('内容挤在下半屏');
        }
      }
      out.slides.push(res);
    });
    setActive(hashIndex());
    out.errors = out.slides.reduce((n, s) => n + s.errors.length, 0);
    out.warnings = out.slides.reduce((n, s) => n + s.warnings.length, 0);
    let node = document.getElementById('wh-audit');
    if (!node) {
      node = document.createElement('script');
      node.id = 'wh-audit';
      node.type = 'application/json';
      document.body.appendChild(node);
    }
    node.textContent = JSON.stringify(out).replace(/</g, '\\u003c');
    html.dataset.whAudit = 'done';
  };

  /* ---------- 启动 ---------- */
  const waitAssets = async () => {
    try {
      if (document.fonts) {
        const fonts = document.fonts.load('40px "WH Hand"', '王虹手写ABC123').then(() => document.fonts.ready);
        await Promise.race([fonts, new Promise((resolve) => setTimeout(resolve, 6000))]);
      }
    } catch {
      /* 字体缺失时继续使用回退字体 */
    }
    // 只需等图片尺寸确定（排版依赖它）；img.decode() 在无头虚拟时间下可能永不返回，不用它
    const imgs = Array.from(deck.querySelectorAll('img')).filter((img) => !img.complete);
    const loaded = Promise.all(imgs.map((img) => new Promise((resolve) => {
      img.addEventListener('load', resolve, { once: true });
      img.addEventListener('error', resolve, { once: true });
    })));
    await Promise.race([loaded, new Promise((resolve) => setTimeout(resolve, 8000))]);
  };

  const start = async () => {
    setActive(hashIndex());
    cur = hashIndex();
    applyTilt();
    await waitAssets();
    buildDecos();
    buildLinks();
    buildNotes();
    if (MODE === 'sheet') {
      buildSheet();
    } else if (MODE === 'audit') {
      runAudit();
    } else if (MODE === 'export') {
      show(hashIndex(), 'end');
    } else {
      if (STEPS) unitsBySlide = slides.map(buildUnits);
      buildUi();
      show(hashIndex(), 'start');
    }
    html.dataset.whReady = '1';
  };

  window.WH = {
    get index() { return cur; },
    get step() { return step; },
    get steps() { return STEPS ? unitsBySlide[cur].length : 1; },
    next, prev, show, finish: finishAnims, isAnimating, audit: runAudit,
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
  else start();
})();
