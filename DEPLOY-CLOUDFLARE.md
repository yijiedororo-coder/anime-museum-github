# GitHub与Cloudflare部署步骤（中文）

资料核对日期：2026年10月21日，日本时间。这个包没有登录或操作你的外部账号。

## 当前项目已经使用Workers，后续维护从这里开始

正式站点：https://anime-museum-github.yijiedororo.workers.dev/

正式仓库：https://github.com/yijiedororo-coder/anime-museum-github

站点所有者已说明Workers连接了本仓库，后续维护沿用同一个Worker。默认配置是`wrangler.jsonc`，名称必须与现有Worker一致：`anime-museum-github`。不需要重新创建Pages项目。

1. 在这个仓库的工作副本修改源码或数据。
2. 依赖缺失/锁文件改变时运行`npm ci`，之后运行`npm run build`。部署配置改变时再运行`npm run deploy:check`（不上传、不发布）。
3. 本地检查通过后提交并推送正式分支`main`。推送会触发公网更新。
4. Cloudflare → Workers & Pages → `anime-museum-github` → Builds，应设置构建命令`npm run build`、部署命令`npx wrangler deploy`、根目录为仓库根目录。
5. 等待该提交的构建和部署成功，然后打开网站检查。

**成功标志**：Cloudflare显示对应提交部署成功，网站`/build-info.json`里的`commit`与刚推送的完整Git SHA一致。仅仅首页能打开，不能证明刚才的修改已经部署。

本地手动部署仍可运行`npm run deploy:workers`，但需要Cloudflare登录授权。已经配置Git自动部署时，日常推送GitHub即可。

以下各节保留初次上传与其他部署方案，当前项目不必重新操作。

## 一、先选对文件

1. 日常开发、上传GitHub：解压 `anime-museum-github.zip`。
2. 已构建的网页：`anime-museum-cloudflare.zip`，里面根目录直接是 `index.html`、`assets/`、`data/`。这是预构建资产包，需要解压后使用Wrangler上传；不要把源码根目录当公开资产目录。
3. 完整历史资料：`anime-museum-full-backup.zip`。用于自己恢复，不作为Cloudflare公开目录；正常上传GitHub使用精简的源码包即可。

## 二、用GitHub Desktop上传源码（推荐）

目的：把每个源文件和图片存进仓库，让Cloudflare以后能自动更新。这个项目有一千多个文件，不适合用GitHub网页逐批拖拽；上传一个ZIP也不会让Cloudflare自动解压构建。

1. 安装官方 [GitHub Desktop](https://desktop.github.com/)，用自己的GitHub账号登录。
2. 解压源码包，找到里面有 `package.json` 的 `anime-museum-github` 文件夹。
3. GitHub Desktop → File → Add local repository，选择这个文件夹。
4. 若提示它还不是Git仓库，点击提示中的 `create a repository here`。确认Local path是上一步的目录，避免又创建一个嵌套的空文件夹。不要替换包里已有的 `.gitignore`。
5. 确认Changes里能看见源码和海报。在Summary填 `Initial import`，如果仍有未提交文件，点击Commit。
6. 点击Publish repository。仓库名称建议 `anime-museum`，建议保留 `Keep this code private`，然后确认发布。

成功标志：打开GitHub仓库，根目录直接能看到 `package.json`、`README.md`、`index.html`、`assets`、`data`、`tools`，而不是只有一个ZIP或又套一层文件夹。

说明：发布公共仓库会让任何人看到源码和数据。包内未加入账号凭证；图片和资料仍归各权利人。

## 三、可选：连接Cloudflare Pages（下述为另一种部署方案）

1. 登录 [Cloudflare控制台](https://dash.cloudflare.com/)，进入Workers & Pages。
2. 选择Create application → Pages → Connect to Git。请确认进入Pages，不是新建普通Worker。
3. 选择GitHub，只授权刚才的仓库，然后选择该仓库。Cloudflare支持Private仓库。
4. 填写以下内容：

| 设置 | 填写 |
|---|---|
| Project name | anime-museum（若更名，同步修改仓库wrangler.pages.toml里的name） |
| Production branch | main，或你仓库实际的默认分支 |
| Framework preset | None |
| Build command | npm run build |
| Build output directory | dist |
| Root directory | 留空 |

5. 不需要设置API Token、数据库密码、Sites ID或其他环境密钥。包里的 `.nvmrc` 已指定Node 22。
6. 点击Save and Deploy，等待构建完成。

成功标志：部署显示Success，打开Cloudflare提供的 `pages.dev` 地址能看到博物馆；点进学园偶像大师→活动档案，可以打开27条活动和完整报告。

以后修改源码或数据：在同一个解压出的仓库修改 → GitHub Desktop Commit → Push origin → 等待Cloudflare自动部署。只修改最早的原项目文件夹、没有把改动复制进这个仓库并Push，不会触发更新。

## 四、不连接GitHub时，上传预构建包

目的：直接发布已经生成的网页。请先解压 `anime-museum-cloudflare.zip`，找到含 `index.html` 的目录。

1. 安装官方 [Node.js](https://nodejs.org/) 的受支持版本（22或更新）。在解压后的网页目录打开PowerShell。
2. 执行下列命令。它们会在你授权后访问Cloudflare并创建/发布项目；请自己核对账号及项目名。首次npx提示下载Wrangler时，确认软件来自Cloudflare官方包。

```powershell
npx wrangler login
npx wrangler pages project create anime-museum --production-branch main
npx wrangler pages deploy . --project-name anime-museum --branch main
```

项目已存在时，跳过create命令。不要在“完整备份目录”运行 `pages deploy .`。

成功标志：命令显示部署成功并给出Pages地址，打开后能浏览作品与商品。此方式不会自动监控你的本地修改；以后需重新构建/上传。

为什么不直接拖ZIP：Cloudflare Pages网页拖拽最多1,000个文件，本项目超出限制；Wrangler支持20,000个文件，单个文件上限25MiB。部署包已检查文件大小和数量。Direct Upload项目以后不能直接切换成Git integration，想自动更新优先选择第三节。

## 五、可选：部署为Cloudflare Workers静态网站

若你选择Workers而不是Pages，在源码目录先构建，再执行：

```powershell
npm run build
npx wrangler login
npx wrangler deploy
```

使用不同配置文件避免Pages与Workers混淆。Workers的名字在 `wrangler.jsonc` 中修改。这里仅托管静态资产，没有额外爬虫或数据库后端。

## 六、容易遇到的情况

- 首页404：检查输出目录是否为 `dist`，仓库根目录是否直接有package.json；预构建包解压后index.html应在你上传目录的根层。
- 更新后还是旧画面：先确认GitHub已Push、Cloudflare最新部署已成功，再刷新浏览器。构建会替换这个导出仓库自己的dist目录，请不要手工编辑dist，修改源码后重新构建。
- 个别商品图不显示：商品图多是外链，可能受来源网站/地区网络影响，打包并未把它们全部镜像到本地。
- 报告链接：本次迁移已改为站内地址，不会把访客带回旧的Sites域名。外部资料来源链接仍正常保留。
- 定时采集：原Codex自动化不会随ZIP迁移。先核查新资料、合并到本仓库的data，再Commit/Push；不要直接运行写有固定日期的旧导入脚本。

## 官方依据

- [Pages连接GitHub及自动部署](https://developers.cloudflare.com/pages/get-started/git-integration/)
- [Pages Direct Upload及上传限制](https://developers.cloudflare.com/pages/get-started/direct-upload/)
- [Pages Node版本配置](https://developers.cloudflare.com/pages/configuration/build-image/)
- [Workers静态资产配置](https://developers.cloudflare.com/workers/static-assets/binding/)
- [GitHub Desktop添加本地仓库](https://docs.github.com/en/desktop/adding-and-cloning-repositories/adding-a-repository-from-your-local-computer-to-github-desktop)
