#!/usr/bin/env node
/*
 * 逐个渲染 styles/ 下的风格，确认风格库可以复现。JSON 风格还要通过 tests/stress.json 的极限内容压测。
 *   node check_all.cjs [--write-preview] [风格 id ...]
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const root = path.resolve(__dirname, '..');
const argv = process.argv.slice(2);
const write = argv.includes('--write-preview');
const only = argv.filter((a) => !a.startsWith('--'));
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-check-'));
const ids = fs.readdirSync(path.join(root, 'styles'))
  .filter((d) => !d.startsWith('_') && fs.statSync(path.join(root, 'styles', d)).isDirectory())
  .filter((d) => !only.length || only.includes(d));
const node = (script, args) => spawnSync(process.execPath, [path.join(__dirname, script), ...args], { encoding: 'utf8' });

/* JSON 风格先用样例内容生成页面，再用同一份极限内容压测 */
function buildAndRender(json, id, html, sheet) {
  const built = node('build.cjs', [json, '--style', id, '--out', html]);
  if (built.status !== 0) return built;
  const run = node('render.cjs', [html, '--out', path.join(tmp, id), '--sheet', sheet]);
  fs.rmSync(html, { force: true });
  return run;
}

let bad = 0;
for (const id of ids) {
  const dir = path.join(root, 'styles', id);
  const isJson = fs.existsSync(path.join(dir, 'style.css'));
  const need = isJson ? ['style.css', 'sample.json', 'STYLE.md'] : ['template.html', 'STYLE.md'];
  const missing = need.filter((f) => !fs.existsSync(path.join(dir, f)));
  const samples = fs.existsSync(path.join(dir, 'samples')) ? fs.readdirSync(path.join(dir, 'samples')).length : 0;
  if (!samples) missing.push('samples/');
  const sources = isJson ? ['style.css', 'pages.html', 'sample.json'] : ['template.html'];
  const text = sources.map((f) => path.join(dir, f)).filter((f) => fs.existsSync(f)).map((f) => fs.readFileSync(f, 'utf8')).join('\n');
  const local = /\/Users\/|\/home\/|[A-Z]:\\\\/.test(text);
  const sheet = write ? path.join(dir, 'preview.jpg') : path.join(tmp, `${id}.jpg`);
  const runs = [];
  if (isJson) {
    if (!missing.includes('sample.json')) runs.push(buildAndRender(path.join(dir, 'sample.json'), id, path.join(dir, '.check.html'), sheet));
    runs.push(buildAndRender(path.join(root, 'tests/stress.json'), id, path.join(root, 'tests/.check.html'), path.join(tmp, `${id}-stress.jpg`)));
  } else {
    runs.push(node('render.cjs', [path.join(dir, 'template.html'), '--out', path.join(tmp, id), '--sheet', sheet]));
  }
  const failed = runs.filter((r) => r.status !== 0);
  const ok = !failed.length && !missing.length && !local;
  if (!ok) bad++;
  console.log(`${ok ? '通过' : '失败'} ${id}${missing.length ? ' 缺少 ' + missing.join(' ') : ''}${local ? ' 含本机路径' : ''}`);
  failed.forEach((r) => console.log((r.stdout + r.stderr).trim()));
}
fs.rmSync(tmp, { recursive: true, force: true });
console.log(bad ? `${bad} 个风格未通过` : `${ids.length} 个风格全部通过`);
process.exit(bad ? 1 : 0);
