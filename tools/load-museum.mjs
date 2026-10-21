import { readFileSync, existsSync } from 'node:fs';
import { resolve, dirname, relative, isAbsolute } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';
import assert from 'node:assert/strict';

export const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const DATA_JS = /^data\/[a-z0-9][a-z0-9./_-]*\.js$/;
const COPY_FILE = /^(data|reports)\/[a-z0-9][a-z0-9./_-]*\.(js|json|csv|md)$/;
const GLOBAL_NAME = /^[A-Z][A-Z0-9_]*$/;
const SECTION_ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

function inside(file) {
  if (typeof file !== 'string' || isAbsolute(file) || file.split('/').includes('..')) throw new Error('非法路径 ' + file);
  const full = resolve(root, file);
  const rel = relative(root, full);
  if (!rel || rel.startsWith('..') || isAbsolute(rel)) throw new Error('路径越界 ' + file);
  return full;
}

function run(context, file, timeout) {
  vm.runInNewContext(readFileSync(inside(file), 'utf8'), context, { timeout });
}

export function loadMuseum() {
  const context = { window: {} };
  run(context, 'data/catalog-data.js', 20000);
  run(context, 'data/ip-registry.js', 5000);
  const registry = context.window.MUSEUM_IP_REGISTRY;
  assert(registry && Array.isArray(registry.sections) && registry.sections.length, '缺少 IP 登记');
  const seen = new Set();
  const globals = new Set();
  for (const section of registry.sections) {
    assert(SECTION_ID.test(section.id), '登记 id 不合法 ' + section.id);
    assert(!seen.has(section.id), '登记 id 重复 ' + section.id);
    seen.add(section.id);
    assert(GLOBAL_NAME.test(section.global), '全局变量名不合法 ' + section.global);
    assert(!globals.has(section.global), '全局变量重复 ' + section.global);
    globals.add(section.global);
    assert(DATA_JS.test(section.file), '数据文件路径不合法 ' + section.file);
    assert(existsSync(inside(section.file)), '缺少数据文件 ' + section.file);
    for (const extra of section.copy || []) {
      assert(COPY_FILE.test(extra), '附加文件路径不合法 ' + extra);
      assert(existsSync(inside(extra)), '缺少附加文件 ' + extra);
    }
    run(context, section.file, 20000);
    const bag = context.window[section.global];
    assert(bag && typeof bag === 'object', section.id + ' 没有写到 ' + section.global);
  }
  assert(context.window.ANIME_CATALOG?.items?.length, '缺少作品目录');
  return { context, registry, catalog: context.window.ANIME_CATALOG };
}

export function visibleItems(bag) {
  if (!bag || bag.placeholder === true) return [];
  return (bag.items || []).filter(item => item && item.placeholder !== true);
}

export function orderedWorks(context, registry) {
  const front = [];
  const back = [];
  for (const section of registry.sections) {
    const items = visibleItems(context.window[section.global]);
    (section.beforeCatalog ? front : back).push(...items);
  }
  return [...front, ...context.window.ANIME_CATALOG.items, ...back];
}

export function sectionFiles(registry) {
  return registry.sections.flatMap(section => [section.file, ...(section.copy || [])]);
}
