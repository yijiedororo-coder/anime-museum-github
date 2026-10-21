import json, urllib.request
from html.parser import HTMLParser
from pathlib import Path

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.images=[]; self.links=[]; self.anchor=None; self.text=''
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='a': self.anchor=a.get('href'); self.links.append(self.anchor)
        if tag=='img': self.images.append({'src':a.get('data-src') or a.get('src'), 'alt':a.get('alt'), 'link':self.anchor, 'context':self.text[-100:]})
    def handle_endtag(self, tag):
        if tag=='a': self.anchor=None
    def handle_data(self, text):
        if text.strip(): self.text+=' '+text.strip()

root=Path(__file__).resolve().parent
for name,url in [('station','https://zutapoke.com/24910/'),('seven','https://zutapoke.com/27492/'),('plush','https://zutapoke.com/24880/'),('kotone','https://zutapoke.com/27755/'),('cd','https://zutapoke.com/27681/'),('official','https://gakuen.idolmaster-official.jp/')]:
    raw=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=40).read().decode('utf-8')
    (root/(name+'-source.html')).write_text(raw,encoding='utf-8')
    p=Page(); p.feed(raw)
    (root/(name+'-source.json')).write_text(json.dumps({'url':url,'images':p.images,'links':p.links},ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'name':name,'images':len(p.images)}))
