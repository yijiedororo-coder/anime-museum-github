# 增加一个 IP 专题

公开一个新专题，只做两件事：新增一个数据文件，再在 `data/ip-registry.js` 的 `sections` 末尾登记一条。不要改 `index.html`、`museum.js`、`tools/verify.mjs`、`tools/build.mjs`。

`npm run build` 会按登记表加载数据、校验，并把数据文件和 `copy` 里列出的附表复制进 `dist`。页面通过 `data/ip-loader.js` 按同一份登记表插入脚本。

## 登记

```javascript
{
  id: 'example-ip',
  file: 'data/ip/example-ip.js',
  global: 'MUSEUM_IP_EXAMPLE',
  slot: '给维护者看的名字，页面不显示',
  copy: ['data/ip/example-ip-products.csv']
}
```

- `id` 用小写英文和连字符，并且要和数据里的作品 `id` 相同。它就是路由 `#/ip/<id>`。
- `file` 只能是 `data/` 下的 `.js`。`global` 用大写字母、数字和下划线，全表不能重复。
- `copy` 可选，用来带上 CSV、JSON 或报告。路径限于 `data/` 或 `reports/`。
- 不要写 `beforeCatalog`。青ブタ和学マス已经占着目录前面的位置；新专题排在原有 1,427 部之后。
- `slot` 不会被页面读取。

## 空位

还没有核实资料时，数据文件保持这样，页面上不会出现该专题，也不会显示日期、商品或价格：

```javascript
// 空位：尚未填入已核实资料，页面不展示。
window.MUSEUM_IP_EXAMPLE = { placeholder: true, items: [] };
```

偶像大师按品牌分开占位，另外还有绝区零和 hololive。这些文件已经登记，填资料之前不要删掉 `placeholder: true`，也不要写入作品条目。

可以公开时：删掉 `placeholder`，把 `items` 换成下面的作品对象。只填写已经核对过的内容。没有来源的日期、商品、价格、角色和衣装说明留空，不要补写。

## 最小的一份作品

样板是学园偶像大师（`gakuen-idolmaster`，`data/gakumas-data.js`）。新文件不要往那个大文件里追加。

```javascript
window.MUSEUM_IP_EXAMPLE = {
  items: [{
    id: 'example-ip',
    name: '中文名',
    aliases: '日文名 略称 英文名',
    region: '日本',
    year: 'YYYY',
    mediaType: '游戏',
    status: '一句已核对的状态',
    cast: '',
    score: '',
    summary: '自己写的一句话，不复制官方原文',
    poster: 'https://官方站点/ogp.png',
    localPoster: 'assets/example-ip/poster.png',
    sourceUrl: 'https://官方站点/',
    retrievedAt: 'YYYY-MM-DD',
    originalTitle: '原文名称',
    eventAsOf: 'YYYY-MM-DD（日本时间）',
    eventSources: { official: ['官方站', 'https://官方站点/'] },
    eventJournal: {
      eyebrow: 'EXAMPLE / SCHEDULE',
      title: '未来三十天',
      summary: '只统计下面这些已核对的日程。',
      credit: '官方公告 ·',
      placeholder: '搜索活动',
      links: [{ name: '官方站', url: 'https://官方站点/' }]
    },
    events: [{
      id: 'example-ip-yyyymmdd-stream',
      kind: 'event',
      name: '活动名',
      category: '直播',
      start: 'YYYY-MM-DD HH:mm',
      end: 'YYYY-MM-DD',
      summary: '一句事实',
      reward: '',
      cost: '',
      regions: ['线上'],
      sourceUrl: 'https://官方公告/',
      sources: ['official'],
      checkedAt: 'YYYY-MM-DD',
      activeDates: [],
      steps: [],
      places: [],
      notes: [],
      pending: [],
      media: { images: [], verifiedFacts: [], resources: [], sources: [] }
    }]
  }]
};
```

上线前至少要有：

- 作品档案：上表这些身份字段。`localPoster` 必须是仓库里的文件，放在 `assets/<id>/`。构建只会复制登记作品用到的本地图。
- 日程：`events` 至少一条，并带上 `eventSources`、`eventAsOf`、`eventJournal`。`sourceUrl` 和渠道链接都要用 `https://`。`events[].media`、`regions`、`sources` 不能省。
- 衣装考察：单独做一条活动，`category` 写 `衣装考察`，`sourceUrl` 指向已发布的考察原文。没有原文就不要加这一条。

没有日程就不要写 `events: []`。没有系列作品就不要写 `seriesWorks`。空数组仍会被当成“有这个字段”，但长度为 0 时，活动和系列文件夹不会打开。

`eventJournal` 建议写上。不写时，封面用中性句子；青ブタ自己的手帖文案不会套到新专题上。

## 周边、角色、系列

周边不是必填。一旦有 `merch`，每条都要有本作品内不重复的 `id`、`name`、以 `https://` 开头的 `sourceUrl`，以及 `channels` 数组（每条 `url` 也是 `https://`）。同时写上：

- `channelSummary`：`{name, description, examples, sourceUrl}`。页面会直接读取它。
- `goodsSourceUrl`、`goodsSourceName`：来源链接和链接文字。不写的话，新专题不会回落到学マス的商品库。
- `goodsExport`：CSV 的站内路径，并把该文件放进登记项的 `copy`。
- 如果写 `articleIndex`，要同时提供 `collectionReport`，并且 `collectionReport.products` 等于周边条数，`archivePages` 要有值。页面会直接读取它们。

图片用官方商品图的 `https` 地址。不要放第三方图。本地图必须真实存在。`imagePlaceholder: true` 表示来源没有单独的商品图。

角色用 `characterProfiles`，系列用 `seriesWorks`。系列海报的 `localPoster` 同样必须存在。系列封面可以写 `seriesIntro: {eyebrow, title, summary}`，`title` 里的换行会变成换行。现有筛选按钮只区分「全部」「TV 动画」「剧场版」；其他形式的作品仍会列在「全部」里。角色若有对应篇章，写在该角色的 `arc`，不要沿用其他作品的篇章名。

可选的展示字段：`recordNote`（资料说明）、`tourSummary`（展览分支那一句）、`posterWide: true`（宽海报）、`goodsScopeNote`（周边资料范围）。不填时，学マス和青ブタ仍用原来的句子，其他专题用中性句子。

## 检查

```bash
npm run build
```

通过时会看到 `check passed` 和 `build complete`。校验仍要求原目录正好 1,427 部，编号不重复，本地海报在仓库内，周边和活动来源为 HTTPS。标记为 `placeholder: true` 的空位必须是 `items: []`，并且不会进入馆藏。

不要改已有作品编号和原目录顺序，不要改学マス、青ブタ、olevod 的资料内容，也不要改 `wrangler.jsonc` 与 `wrangler.workers.jsonc` 的文件名。正式分支 `main` 一推送就会部署；专题合并前在各自的 PR 里核对。
