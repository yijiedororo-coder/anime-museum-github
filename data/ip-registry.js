// IP 专题登记。
// 新增一个会公开的专题：添加数据文件，再在 sections 末尾追加一条。
// 不要给新专题写 beforeCatalog，这样它会排在原有 1,427 部目录之后。
// placeholder 数据（items 为空）不会出现在页面上。slot 只给维护者看，页面不读取。
window.MUSEUM_IP_REGISTRY = {
  sections: [
    {
      id: 'aobuta-autumn-2026',
      file: 'data/aobuta-data.js',
      global: 'MUSEUM_EVENTS',
      beforeCatalog: true,
      copy: ['data/aobuta-products.csv']
    },
    {
      id: 'gakuen-idolmaster',
      file: 'data/gakumas-data.js',
      global: 'MUSEUM_ADDITIONS',
      beforeCatalog: true,
      copy: [
        'data/gakumas-products.csv',
        'data/gakumas-collection-report.json',
        'data/gakumas-oct20-research.json',
        'reports/gakumas-2026-10-20.md'
      ]
    },
    { id: 'idolmaster-shinycolors', file: 'data/ip/idolmaster-shinycolors.js', global: 'MUSEUM_IP_SHINYCOLORS', slot: '偶像大师 闪耀色彩', copy: ['data/ip/idolmaster-shinycolors-products.csv'] },
    { id: 'idolmaster-millionlive', file: 'data/ip/idolmaster-millionlive.js', global: 'MUSEUM_IP_MILLIONLIVE', slot: '偶像大师 百万现场', copy: ['data/ip/idolmaster-millionlive-products.csv'] },
    { id: 'idolmaster-cinderella', file: 'data/ip/idolmaster-cinderella.js', global: 'MUSEUM_IP_CINDERELLA', slot: '偶像大师 灰姑娘女孩', copy: ['data/ip/idolmaster-cinderella-products.csv'] },
    { id: 'idolmaster-sidem', file: 'data/ip/idolmaster-sidem.js', global: 'MUSEUM_IP_SIDEM', slot: '偶像大师 SideM', copy: ['data/ip/idolmaster-sidem-products.csv'] },
    { id: 'idolmaster-765', file: 'data/ip/idolmaster-765.js', global: 'MUSEUM_IP_765', slot: '偶像大师 765', copy: ['data/ip/idolmaster-765-products.csv'] },
    { id: 'zenless-zone-zero', file: 'data/ip/zenless-zone-zero.js', global: 'MUSEUM_IP_ZZZ', slot: '绝区零', copy: ['data/ip/zenless-zone-zero-products.csv'] },
    { id: 'hololive', file: 'data/ip/hololive.js', global: 'MUSEUM_IP_HOLOLIVE', slot: 'hololive', copy: ['data/ip/hololive-products.csv'] },
    { id: 'idolmaster', file: 'data/ip/idolmaster.js', global: 'MUSEUM_IP_IDOLMASTER', slot: '偶像大师 全系列', copy: ['data/ip/idolmaster-products.csv'] }
  ]
};
