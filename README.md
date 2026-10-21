# 动画博物馆 · Anime Museum

可部署到 Cloudflare 的独立静态网站，整理自 2026年10月21日的项目快照。

- 原作品库1,427部，另有学园偶像大师、青春猪头少年两个专题，共1,429个作品入口。
- 学园偶像大师周边5,516条、活动与提醒27条。
- 青春猪头少年周边409条、活动43条、系列作品6部、角色资料12份。
- 保留自由探索、作品目录、立体书架、作品横向展览、活动及商品详情、筛选与CSV下载。

## 开始使用

安装 Node.js 22 或更新的受支持版本，打开本目录的终端：

```powershell
npm run build
npm run preview
```

成功标志：出现 `check passed`、`build complete`，随后浏览器打开 http://127.0.0.1:4173 能看见博物馆。构建和预览只使用Node内置模块，无需安装前端依赖。

上传GitHub前先解压源码包，上传里面的文件；不要只把ZIP放进仓库。完整步骤见 [部署操作说明](DEPLOY-CLOUDFLARE.md)。

## Cloudflare Pages推荐设置

| 设置 | 内容 |
|---|---|
| 创建方式 | Pages → Connect to Git → GitHub |
| Framework preset | None |
| Production branch | main（以实际分支为准） |
| Build command | npm run build |
| Build output directory | dist |
| Root directory | 留空，仓库根目录 |
| Node.js | .nvmrc 已指定22；无需配置密钥 |

后续修改这个GitHub仓库并Push后，Cloudflare会自动构建更新。原Sites网址不会自动跟着更新；两边现在是独立部署。

## 文件分工

- `index.html`、`museum.js`、`museum.css`、`events.js`、`series.js`：网页及交互。
- `data/`：全部馆藏资料、原始作品资料、文章索引和CSV。
- `assets/`：本地海报与已有本地图片。
- `reports/`：完整调查报告。
- `tools/build.mjs`：构建独立的 `dist/`，不会调用Sites或访问外部账号。
- `tools/verify.mjs`：校验作品、图片、商品、活动及交互节点。
- `tools/preview.mjs`：仅本机可访问的预览服务。
- `tools/`其他Python/历史导入工具：保留维护源码，**不是日常构建步骤**。许多工具读取旧缓存或使用一次性整理日期，不要直接运行覆盖新资料。完整缓存、研究输入、旧版页面和截图在“完整备份ZIP”中。
- `wrangler.toml`：Pages配置。`wrangler.workers.jsonc`：可选Workers静态资产配置。

## 范围说明

这是已有网站的源码和数据交付，不包含Git历史、账号凭证、Sites工作区身份配置或浏览器登录信息。作品编号、顺序、原来源及旧商品渠道保持不变；本站报告链接已改为本站相对地址。

绝大多数商品图片继续引用原来源公开图片，并非全部下载到本地；来源删除、防盗链或网络环境会影响它们。`SOURCE-LINKS.json`列出了外部图片域名和数量。

本项目为静态档案馆，没有新增登录、后台数据库或云端爬虫。原Codex定时任务仍属于原本地环境；上传Cloudflare不会自动搬迁该任务。采集后需更新本仓库数据并Push，才会触发Cloudflare同步。

图片、角色、商标及第三方资料的权利归原权利人；这里未擅自替第三方素材授予开源许可。可将GitHub仓库设为Private，再授权Cloudflare读取该仓库。
