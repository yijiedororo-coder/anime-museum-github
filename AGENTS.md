# 动画博物馆维护约定

- 默认用中文说明目的、进度、结果及必要的风险。
- 当前维护源是本仓库 `yijiedororo-coder/anime-museum-github`。以GitHub最新提交为准；不要把旧的 `anime-merch-library` 或Sites发布目录直接覆盖到这里。
- 正式分支为 `main`。用户已说明现有Cloudflare站点连接了本仓库；推送正式分支会触发上线，提交前先完成相应检查。
- 现有正式站点：https://anime-museum-github.yijiedororo.workers.dev/
- 托管方式是 **Cloudflare Workers静态资产**，Worker名称 `anime-museum-github`。默认配置 `wrangler.jsonc`，资产目录 `dist`。`wrangler.pages.toml` 仅供可选Pages部署；不要默认另建站点。
- Cloudflare Builds实际部署命令为 `npx wrangler deploy --config wrangler.workers.jsonc --name anime-museum-github`。保留 `wrangler.workers.jsonc` 兼容入口，并与 `wrangler.jsonc` 保持一致；未先修改控制台部署命令并验证前，不要删除或改名。`npm run deploy:check`同时校验两个入口。
- 常规检查：`npm ci`（依赖缺失或锁文件更新时）、`npm run build`、部署配置变化时运行 `npm run deploy:check`。`dist` 是生成目录，应修改源码后重新构建。
- 对用户要求发布的修改，检查通过后提交并推送已授权的仓库，再核对公网结果。构建会生成 `/build-info.json`；Workers Builds会把源提交SHA写入该文件，可用它确认公网已经部署到对应提交。仅有HTTP 200或构建开始，不等于本次更新已上线。
- 缺少GitHub写入授权时，完成所有能独立完成的本地工作，保留可审阅的提交，说明真实授权缺口；不索要密码、令牌，不把凭证写入文件或日志。
- 保留原1,427部作品库、已有作品/商品/活动编号、路由顺序、来源和渠道。新增内容追加；合并时保留不同价格、月份、图片及渠道。
- 按年份调查的进度在 `data/chronology-progress.json`。首轮仅调查海贼王、学园默示录，后续作品和未核年份仍待处理。`data/early-works-research.json`为当次来源事实；采集脚本刷新公开页面，导入脚本校验日本日期。CSV与来源报告由构建生成，保留已入库商品位置；不要把首轮目录调查标成全市场收集完成。
- `tools`中的历史采集/导入脚本可能依赖未包含的缓存或固定日期。不要把旧缓存当作新来源，不直接运行一次性脚本覆盖已更新的数据。
- 定时采集仍在原本地环境运行，未自动迁移到本仓库或Cloudflare。修改采集和发布流程时，应先明确数据如何合并到当前维护源。
- 图片多数仍为来源外链。不要将来源报价写成实时库存，不丢失缺失信息或核查限制。
- GitHub、Cloudflare授权通过官方登录或已连接工具完成。不要提交`.env`、`.wrangler`、账号凭证或原Sites身份配置。
