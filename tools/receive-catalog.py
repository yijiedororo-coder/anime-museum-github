"""Receive public catalog extracted through the browser into this local project."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import json, hashlib
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        html = '<!doctype html><meta charset="utf-8"><title>本地作品资料导入</title><h1>本地作品资料导入</h1><form action="/import" method="post"><label for="catalog">作品 JSON</label><textarea id="catalog" name="catalog" rows="10" cols="80"></textarea><button type="submit">保存到本地图书馆</button></form>'
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())

    def do_POST(self):
        if self.path != '/import':
            self.send_error(404)
            return
        try:
            size = int(self.headers.get('Content-Length', 0))
            if not 0 < size < 5_000_000:
                raise ValueError('资料大小不正确')
            payload = json.loads(parse_qs(self.rfile.read(size).decode())['catalog'][0])
            records = payload['items']
            if len(records) != 1431 or len(set(r['sourcePage'] for r in records)) != 30:
                raise ValueError('分页资料不完整')
            items, seen = [], {}
            for r in records:
                title = r['name'].strip()
                key = title
                if key in seen:
                    items[seen[key]].setdefault('alternateRecords', []).append(r)
                    continue
                seen[key] = len(items)
                poster = r.get('poster', '')
                if poster and urlparse(poster).hostname != 'static.olelive.com':
                    raise ValueError('封面地址不正确')
                items.append({**r, 'id': 'ole-' + hashlib.sha1(key.encode()).hexdigest()[:12]})
            result = {'sourceUrl': payload['sourceUrl'], 'retrievedAt': datetime.now(timezone.utc).isoformat(), 'pageCount': 30, 'sourceCount': len(records), 'count': len(items), 'duplicatesMerged': len(records)-len(items), 'items': items, 'sourceRecords': records}
            data_dir = ROOT / 'data'
            data_dir.mkdir(exist_ok=True)
            (data_dir / 'olevod-catalog.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
            safe = json.dumps(result, ensure_ascii=False).replace('<', '\\u003c')
            (data_dir / 'catalog-data.js').write_text('window.ANIME_CATALOG = ' + safe + ';\n', encoding='utf-8')
            msg = f'导入完成：{len(items)} 部作品，30 页，移除 {len(records)-len(items)} 条重复记录，{sum(bool(r["poster"]) for r in items)} 张封面。'
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(('<meta charset="utf-8"><h1>' + msg + '</h1>').encode())
            print(msg, flush=True)
        except (ValueError, KeyError, TypeError) as error:
            self.send_error(400, str(error))

HTTPServer(('127.0.0.1', 4191), Handler).serve_forever()
