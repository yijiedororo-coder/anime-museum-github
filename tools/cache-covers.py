"""Cache the public poster files requested by the user; retain source URLs."""
from pathlib import Path
from urllib.request import Request, urlopen
from concurrent.futures import ThreadPoolExecutor, as_completed
import json, hashlib

ROOT=Path(__file__).resolve().parent.parent
path=ROOT/'data/olevod-catalog.json'
data=json.loads(path.read_text(encoding='utf-8'))
cover_dir=ROOT/'assets/olevod'
cover_dir.mkdir(exist_ok=True)
urls=list(dict.fromkeys(r['poster'] for r in data['sourceRecords'] if r.get('poster')))

def fetch(url):
    key=hashlib.sha256(url.encode()).hexdigest()[:20]
    existing=list(cover_dir.glob(key+'.*'))
    if existing:
        return url,existing[0].relative_to(ROOT).as_posix(),''
    for attempt in range(2):
        try:
            with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=15) as response:
                content=response.read(4_000_001)
            if len(content)>4_000_000:
                raise ValueError('Image exceeds 4 MB')
            ext='jpg' if content.startswith(b'\xff\xd8\xff') else 'png' if content.startswith(b'\x89PNG\r\n\x1a\n') else 'webp' if content.startswith(b'RIFF') and content[8:12]==b'WEBP' else 'gif' if content.startswith(b'GIF8') else None
            if not ext:
                raise ValueError('Response is not a supported image')
            target=cover_dir/(key+'.'+ext)
            target.write_bytes(content)
            return url,target.relative_to(ROOT).as_posix(),''
        except Exception as error:
            if attempt==1:
                return url,None,str(error)

results={}
with ThreadPoolExecutor(max_workers=4) as pool:
    tasks=[pool.submit(fetch,url) for url in urls]
    for n,task in enumerate(as_completed(tasks),1):
        url,local,error=task.result()
        results[url]={'local':local,'error':error}
        if n%100==0 or n==len(urls):
            print(f'Cached {n}/{len(urls)} posters',flush=True)
for item in data['items']:
    for record in [item,*item.get('alternateRecords',[])]:
        result=results.get(record.get('poster'),{})
        if result.get('local'):
            record['localPoster']=result['local']
data['coverCache']={'requested':len(urls),'saved':sum(bool(r['local']) for r in results.values()),'failed':[{'url':u,'error':r['error']} for u,r in results.items() if not r['local']],'bytes':sum(p.stat().st_size for p in cover_dir.iterdir())}
path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
frontend={k:v for k,v in data.items() if k!='sourceRecords'}
(ROOT/'data/catalog-data.js').write_text('window.ANIME_CATALOG = '+json.dumps(frontend,ensure_ascii=False).replace('<','\\u003c')+';\n',encoding='utf-8')
print(json.dumps(data['coverCache'],ensure_ascii=False),flush=True)
