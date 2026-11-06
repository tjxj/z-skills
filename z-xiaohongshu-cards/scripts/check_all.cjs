#!/usr/bin/env node
/*
 * 逐个渲染 styles/ 下的模板，确认风格库可以复现。
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
  .filter((d) => fs.statSync(path.join(root, 'styles', d)).isDirectory())
  .filter((d) => !only.length || only.includes(d));

let bad = 0;
for (const id of ids) {
  const dir = path.join(root, 'styles', id);
  const need = ['template.html', 'STYLE.md'];
  const missing = need.filter((f) => !fs.existsSync(path.join(dir, f)));
  const samples = fs.existsSync(path.join(dir, 'samples')) ? fs.readdirSync(path.join(dir, 'samples')).length : 0;
  if (!samples) missing.push('samples/');
  const html = missing.includes('template.html') ? '' : fs.readFileSync(path.join(dir, 'template.html'), 'utf8');
  const local = /\/Users\/|\/home\/|[A-Z]:\\/.test(html);
  const sheet = write ? path.join(dir, 'preview.jpg') : path.join(tmp, `${id}.jpg`);
  const run = spawnSync(process.execPath, [path.join(__dirname, 'render.cjs'), path.join(dir, 'template.html'), '--out', path.join(tmp, id), '--sheet', sheet], { encoding: 'utf8' });
  const ok = run.status === 0 && !missing.length && !local;
  if (!ok) bad++;
  console.log(`${ok ? '通过' : '失败'} ${id}${missing.length ? ' 缺少 ' + missing.join(' ') : ''}${local ? ' 含本机路径' : ''}`);
  if (run.status !== 0) console.log((run.stdout + run.stderr).trim());
}
fs.rmSync(tmp, { recursive: true, force: true });
console.log(bad ? `${bad} 个风格未通过` : `${ids.length} 个风格全部通过`);
process.exit(bad ? 1 : 0);
