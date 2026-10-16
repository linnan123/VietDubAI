# VietDub AI Phase 1.5：运行环境与端到端验收

## 最终复核与归档：PASS（2026-10-16 20:32，UTC+8）

**Phase 1.5 最终判定：PASS。** 用户已亲自完成独立工作台真实浏览器上传和人工确认；本轮只读复核独立 PostgreSQL、API / Worker 日志及磁盘媒体，与用户报告一致。此前阻塞的强制浏览器步骤已获得实际成功证据。本节为最终结论，下方 BLOCKED / 失败诊断均保留为历史记录，不代表仍有未解决强制验收项。本次 PASS 仅针对 Phase 1.5 本机隔离环境验收，不代表公开生产部署就绪，不自动授权 Phase 2。

### 浏览器操作与服务端记录交叉核验

操作来源明确区分：**文件选择、上传、点击确认由用户在浏览器完成；本轮代理执行的是只读数据库、文件、日志与服务状态复核**，没有用 HTTP 脚本代替这次浏览器操作。

| 字段 | 实际记录 |
|---|---|
| Compose 项目 | vietdub-acceptance15-155d3886e3 |
| 数据库 / 用户 | vietdub_acceptance_15 / acceptance15 |
| 项目 | Phase 1.5 浏览器端到端验收；8ebe396b-154e-4a39-bae4-b439c977c5c6 |
| 剧集 | 浏览器真实上传与确认；2e1af50e-9f2c-4614-af11-0cb0773b6076 |
| 真实 Job | 870546d4-2a6e-47c8-883d-bfa1cf7d359f |
| 任务状态 | succeeded，attempts=1，error=null |
| 人工确认 | episodes.approved=true；Phase 1 使用该字段记录确认，没有独立审批审计表或确认时间字段 |
| 元数据 | duration_ms=20033，width=1080，height=1920，video_codec=h264 |
| 原片 | /acceptance-media/2e1af50e-9f2c-4614-af11-0cb0773b6076/e8822022-94aa-40fb-b9b4-3a58544fb355.mp4 |
| WAV | 同一目录 audio.wav；PCM s16le、16000 Hz、单声道、16-bit、320250 帧、20.015625 秒 |

WAV 参数再次通过 Python wave 与最终 API 容器内 FFprobe 独立读取；20.03 秒界面显示对应整数 20033 ms，WAV 与源音轨的微小尾部时长差符合此前实测。未覆盖或修改任何原始视频。

API 日志真实上传响应为 `POST /episodes/2e1af50e-9f2c-4614-af11-0cb0773b6076/upload` **202**（20:29:04），确认接口 **200**（20:29:52）。请求来源为独立 Web 所在网络。该窗口内 Worker 实际收到 process 任务 `1b29f947-8cef-4905-a710-842199120f25`，于 20:29:19 成功返回，耗时约 0.311 秒。注意 Celery 消息 ID 不等于数据库 Job ID，现有 INFO 日志不输出参数；对应关系由本轮该时间窗口新任务、数据库成功记录与真实输出共同核验，不把 Celery 的 succeeded 单独当作业务成功证据。

### 完整性与异常复核

实际读取磁盘 SHA-256，与上传前及数据库记录比对：

```text
sample-20s.mp4 = 本次浏览器上传原片 = 数据库 source_sha256：
9623ec9c1fd5aaf77b5f7c6f9c59cc34e8c5d1222806fd80915991df90590df1
用户原始 test/temp.mp4（保持上传前值）：
d165f26cdbf7e60d6c7c72d95456e8e157e08e17e257eaa6b32901dca6c4a9ea
本次浏览器任务 WAV：
a08f51209ca77e824bc16d7c293d84618d79cd272b542ca0eeebf407c16684d8
```

本轮收集的 API / Worker / 当前修复 Web 日志中，未检出 Traceback、ERROR、500 Internal、ECONNRESET 或请求体截断标记。日志存在“成功返回”并不能排除应用捕获的失败，因此同时只读检查全部独立任务：**5 个 Job 中 4 个 succeeded、1 个预期负向测试 failed；没有 queued / running 遗留。** 唯一 failed 仍为已知损坏文件剧集 dbdb8da7-e2f2-4780-9f09-c46501e3cb0f，attempts=4、approved=false，不是未处理异常或待修产品故障。旧 Web 被替换前的 500 日志已在 upload-500-before.log 单独归档，不宣称历史从未出错。

隔离再次通过：数据库、媒体挂载、容器网络、新 Redis /15 和 acceptance15 队列均维持独立；现有业务数据库、媒体目录、Redis 队列未被访问或修改。五个独立服务仍运行，PostgreSQL / Redis healthy，真实 Celery ping 为 pong。验收数据和卷原样保留，不执行清理或 down -v。

### 强制验收证据矩阵

| 必需项 | 判定与证据 |
|---|---|
| 既有自动化测试 | PASS；最近真实执行 9 passed、1 warning、0 skipped，退出 0；checks.json / upload-checks.log；本轮复核历史输出，未重复运行或宣称新测 |
| 前端类型与生产构建 | PASS；修复 Web 镜像实际 typecheck、Next.js build 均退出 0；upload-typecheck.log / upload-web-build.log |
| PostgreSQL Alembic | PASS；真实验收 PostgreSQL upgrade / check 退出 0，本轮 current 仍为 0001 (head) |
| Redis / Celery 实际入队执行 | PASS；独立 Redis PONG、Worker pong，真实上传 Job 与 WAV 输出，非 mock |
| 持久化与幂等性 | PASS；此前 API / Worker 重启、并发上传 202/409、真实重复投递保持一个 Job / 不重复处理；chain-events.json / upload-fix-results.json |
| 失败及重试恢复 | PASS；真实存储故障 failed 后恢复并重试 succeeded，同一 Job attempts=2；损坏媒体失败/错误展示符合预期 |
| 授权 10–30 秒 MP4、FFprobe、FFmpeg | PASS；实际 20 秒样本，真实元数据与 16 kHz 单声道 PCM WAV，哈希保持一致 |
| 浏览器完整上传与任务展示 | PASS；用户亲自操作的成功结果 + 本轮 PostgreSQL / API 日志 / Worker / 磁盘输出交叉核验 |
| 人工确认、刷新持久化、不覆盖数据 | PASS；用户确认界面、独立数据库 approved=true；此前重复确认及失败确认 409、刷新与哈希对比均有真实证据 |

Chrome 扩展的自动化 filechooser 权限限制归为**测试工具局限**：它仍可能阻止代理自动选文件，但不阻止用户手动选择，且不再阻塞已完成人工验收的产品上传功能。与已修复的 Next.js 10 MiB 代理截断缺陷分开记录。现有非阻塞限制包括实验性大请求缓冲的内存风险、单 beat、本机无认证和缺少独立审批审计日志；512 MiB 极限压力、故障灾备等未纳入本轮 Phase 1.5 必需验收，不能由 PASS 推断已测。

### 本轮命令与归档

工作目录 `D:\VietDub AI`，脚本通过 context.json 中带项目名、验收 env 文件和独立 compose.yml 的完整参数列表执行，所有数据库查询显式使用只读事务：

| 命令 / 检查 | 实际退出码 |
|---|---|
| `$env:PYTHONIOENCODING='utf-8'; python data/acceptance-final/isolation.py --allow-records` | 0 |
| `python data/acceptance-final/archive_review.py` | 0 |
| 脚本内 scoped exec API：SET TRANSACTION READ ONLY 后查询项目/剧集/Job | 0 |
| 脚本内 scoped exec API：ffprobe -v error -show_streams -of json <验收 WAV> | 0 |
| 脚本内 scoped logs --no-color --timestamps api worker web | 0 |
| 脚本内 scoped ps、alembic current、Redis -n 15 ping、Celery inspect ping | 各 0 |

最终原始证据：`data/acceptance-final/155d3886e3/archive-review.json`、`archive-commands.json`、`archive-services.log`、`final-archive-isolation.log`。历史自动化和真实链路日志保留在同一目录；`archive-manifest.json` 对主要证据文件记录 SHA-256 以便本机核对，不包含密码 env 文件。此次仅更新报告并生成忽略目录内的只读验收辅助脚本/证据，不修改业务逻辑或配置。

### Phase 2A 前置条件（仅列出，未执行）

1. 用户明确授权 Phase 2A，并先确定其范围、验收指标及阶段边界；Phase 1.5 PASS 不是自动开工许可。
2. 保留本次环境配置、证据与基线；后续开发/测试继续使用独立数据库、媒体目录和队列，先制定备份/恢复及新增 Alembic 迁移方案。
3. 明确授权素材、数据隐私与供应商数据流；真实模型/第三方服务的硬件、许可证、成本与密钥注入方式需另行确认，不沿用本轮权限自动安装或调用。
4. 对拟增加的功能先定义整数毫秒时间轴、版本/幂等键、人工审批与可回滚测试；公开部署前另补认证、资源/并发配额及上传内存压力验证。

**Phase 1.5 到此结束，未执行 Phase 2A。**

---

## 浏览器上传 HTTP 500 根因与修复（2026-10-16，最新记录）

**最终判定：BLOCKED（Phase 1.5 整体）。已定位并修复 Web 代理上传缺陷，同一 13000 路径的真实 HTTP 上传、异步处理与人工确认通过；自动化浏览器仍被扩展本地文件权限阻止，完整浏览器选文件流程尚需人工复验。** 本节优先于下方历史结论，不将 HTTP 客户端上传表述为浏览器上传成功。

### 第一阶段：只读诊断及根因证据

先读取本报告、独立验收 Compose、Next.js 配置与上传页面、FastAPI 上传路由、upload_media 服务、上传大小中间件及媒体处理代码。未发现适用 AGENTS.md。重新执行 isolation.py --allow-records 退出 0，确认操作目标仍为完全独立验收栈。

13000 对应 Compose 项目 `vietdub-acceptance15-155d3886e3` 的 web 服务；其余服务与容器名分别为：

```text
web       vietdub-acceptance15-155d3886e3-web-1       127.0.0.1:13000 -> 3000
api       vietdub-acceptance15-155d3886e3-api-1       127.0.0.1:18000 -> 8000
worker    vietdub-acceptance15-155d3886e3-worker-1
postgres  vietdub-acceptance15-155d3886e3-postgres-1  无主机端口
redis     vietdub-acceptance15-155d3886e3-redis-1     无主机端口
```

API / Worker 实际连接的数据库仍为 `vietdub_acceptance_15`、用户 acceptance15、数据库 IP 172.19.0.2；Redis 为新容器 172.19.0.3 的 /15，实际消费队列 acceptance15，媒体路径均为 `/acceptance-media`，绑定 `D:\VietDub AI\acceptance-media\155d3886e3`。没有使用业务数据库、媒体卷或 Redis。最终再次验证隔离通过。

前端文件 input 的 onChange 在选择文件后立即构造 FormData，发起 **POST `/api/episodes/2e1af50e-9f2c-4614-af11-0cb0773b6076/upload`**，由 Next.js rewrites 转发到 `http://api:8000/episodes/.../upload`；不是文件选择后仅刷新剧集。上传成功后刷新项目/任务/剧集，后台已有 beat/Worker 再处理媒体。错误信息 `请求失败 (500)` 来自响应不是可识别 detail JSON 时的前端兜底文案。

旧 Web 容器实际日志（保存为 `data/acceptance-final/155d3886e3/upload-500-before.log`）：

```text
Request body exceeded 10MB for /api/episodes/2e1af50e-9f2c-4614-af11-0cb0773b6076/upload.
Only the first 10MB will be available unless configured.
Failed to proxy http://api:8000/episodes/2e1af50e-9f2c-4614-af11-0cb0773b6076/upload
[Error: socket hang up] { code: 'ECONNRESET' }
```

另一现有测试剧集 dd1c22bd-3641-4abf-8942-e9a91643c240 同样有 10MB 截断与 ECONNRESET 日志。**真正失败点是 Next.js 请求体克隆/转发，不是 FFmpeg、SQL 外键或数据库权限。** 32,984,229 字节样本超过默认 10 MiB。当前安装的 Next.js 15.5.14 源码 `dist/server/body-streams.js` 默认 10×1024×1024，resolve-routes.js 读取 experimental.middlewareClientMaxBodySize；[官方 v15 配置说明](https://nextjs.org/docs/15/app/api-reference/config/next-config-js/middlewareClientMaxBodySize)与本机代码相符。

没有找到该失败请求对应的 API 500 traceback，因此不编造 Python 堆栈。API 日志 GET 项目/任务持续 200，上传前只读快照确认上述两集 source_sha256 / metadata_json 均为空，且没有其 Job；旧 Web 错误不代表 API 已提交上传记录。素材尚未进入媒体处理。只读检查与后续实际成功写入也没有发现数据库、外键、目录映射或权限故障。

### 第二阶段：最小修复及影响边界

本轮项目文件修改：

1. `frontend/next.config.ts`：增加 `experimental: { middlewareClientMaxBodySize: 513 * 1024 * 1024 }`。与既有后端 512 MiB 文件限制 + 1 MiB multipart 请求开销对齐，不修改后端限额，不吞异常或伪造成功。
2. `docs/testing/acceptance/compose.yml`：仅将验收 web 镜像指定为 `vietdub-acceptance15-web:upload-fix`，避免覆盖业务镜像标签。独立 API / Worker / PostgreSQL / Redis、业务 Compose、数据库与媒体处理逻辑均未修改。
3. 本验收报告。

没有升级依赖、安装软件、改证书/代理、修改全局配置或删除任何数据卷。验证脚本及日志在已忽略的 data/ 目录。仅重建独立验收 Web 容器，保留所有既有测试记录和文件。该 Next.js 选项属于实验选项，最大请求可能占用较多内存；当前限本机受信单用户环境，未做 512 MiB 极限或并发内存压力验收，公开部署仍需入口配额与资源限制。这不是绕过上传安全检查。

### 第三阶段：实际命令及退出码

下面 `$AC` 是本报告后续章节定义的独立 Compose 前缀（包含项目名、acceptance.env 和验收 compose.yml），绝不能替换为业务默认配置。

| 命令 / 操作 | 实际结果 |
|---|---|
| scoped compose logs --no-color --tail 160 web api | 0；保存 upload-500-before.log，定位 10MB 与 ECONNRESET |
| `python data/acceptance-final/isolation.py --allow-records`（修复前、修复后） | 各 0；实际运行环境隔离通过 |
| 独立 API 只读 projects / episodes / jobs 快照 | 0；upload-baseline.json，确认待上传记录未被部分写入 |
| `docker build --progress plain -t vietdub-acceptance15-web:upload-fix frontend` | 0；Next.js 15.5.14 编译、类型检查、生产构建完成；upload-web-build.log |
| `docker @AC up -d --no-deps --no-build web` | 0；仅独立验收 Web 重建 |
| `python data/acceptance-final/checks.py` | 0；所有内部检查命令退出 0，详见 upload-checks.log 和 checks.json |
| `docker @AC exec -T api pytest -v -rs` | 0；**9 passed, 1 warning in 0.90s**，没有 skipped |
| scoped API Alembic upgrade head / current / check | 均 0；真实独立 PostgreSQL，0001 (head)，No new upgrade operations detected. |
| scoped API、Worker 的 pip check；pg_isready；Redis -n 15 ping；实际 Celery inspect ping | 均 0；No broken requirements、accepting connections、PONG、Worker pong |
| `$env:PYTHONPATH='D:\VietDub AI\.test-deps'; python data/acceptance-final/verify_upload_fix.py` | 0；经 13000/api 的真实上传与媒体/确认/重复上传回归通过 |
| `docker @AC exec -T web pnpm run typecheck` | 0；tsc --noEmit；upload-typecheck.log |
| scoped logs --timestamps web api worker | 0；upload-fix-services.log，实际上传 202、重复上传 409 |
| `python data/acceptance-final/upload_final_status.py` | 0；五服务 Up，PG / Redis healthy；运行镜像配置实际为 537919488 字节 |

真实自动化测试名称与上轮相同，9 项全部通过，唯一 warning 仍是 Starlette TestClient 的 anyio BlockingPortal 弃用提示。SQLite / mock 单元测试没有当作真实分布式链路；真实链路证据单独见下。

诊断中的失败也保留：首次非提权主机 HTTP 只读探测因沙箱 WinError 10013 退出 1，按授权提权后同一只读探测退出 0；不是数据库连接缺陷。修复前另发起一次旧 Web HTTP 复现，但 Web 重建与该尚未结束的请求重叠，客户端 RemoteProtocolError、退出 1，该次不能当作稳定复现到 HTTP 500；根因依据是用户实际 500 及旧 Web 明确截断/重置日志。一次内联 Node 配置诊断因 PowerShell 引号解析退出 1，改为 upload_final_status.py 后退出 0。一次浏览器脚本路径转义错误在执行前被拒绝，改用正斜杠路径后进入真实 chooser；没有因此上传重复文件。

### 真实代理上传、媒体处理与数据完整性

为保留用户待操作的“浏览器真实上传与确认”剧集，本轮 HTTP 回归复用**已存在且确认无源文件/任务**的验收剧集 `dd1c22bd-3641-4abf-8942-e9a91643c240`，未创建重复项目/剧集。通过 `http://127.0.0.1:13000/api` POST 实际 sample-20s.mp4，返回 **202**，真实 Job `7d1fec7f-993f-4e9d-ada7-c53d9c740e60`；API 日志 202 时间为 2026-10-16 20:20:46（UTC+8）。没有直连 18000 绕过代理。

- 真实隔离 Redis / Celery 执行完成，任务 succeeded、attempts=1；本轮轮询实际采样为 queued、queued、succeeded，未捕获短暂 running，不将其声称为已观察。详见 upload-fix-results.json。
- FFprobe 元数据 20033 ms、1080×1920、H.264；Worker 实际 WAV 为 PCM signed 16-bit little-endian、16000 Hz、单声道、20.015625 秒，Python wave 与 FFprobe 双重确认。
- 经同一 Web 代理人工确认接口两次均 200；只 approved 变为 true，元数据、源 SHA 未变。再次上传返回真实 409，仍只有一个对应 Job，所有既有其他 Job 未新增。
- 原 temp.mp4 SHA-256 前后均为 `d165f26cdbf7e60d6c7c72d95456e8e157e08e17e257eaa6b32901dca6c4a9ea`。
- sample-20s.mp4 及新上传原片前后 SHA-256 均为 `9623ec9c1fd5aaf77b5f7c6f9c59cc34e8c5d1222806fd80915991df90590df1`。
- 新 WAV SHA-256 为 `a08f51209ca77e824bc16d7c293d84618d79cd272b542ca0eeebf407c16684d8`。
- 浏览器实际打开独立链路项目，看到该集“人工确认完成 / 分析完成”、20.03 秒及 WAV 参数；完整刷新再选择项目后仍相同，截图 upload-fix-browser-refreshed.jpg。这验证展示/刷新持久化，**不等同浏览器完成文件选择上传**。

### 剩余阻塞及人工步骤

在修复后 Chrome 工作台选中“Phase 1.5 浏览器端到端验收”，真实点击 input、取得文件 chooser、设置绝对路径，仍收到扩展要求启用 Allow access to file URLs 的错误，未发起上传 HTTP。没有改扩展/Windows 权限，也没有将 HTTP 客户端结果替换成浏览器验收。

下一项仅需用户手动在 `http://localhost:13000` 的 **“Phase 1.5 浏览器端到端验收”→“浏览器真实上传与确认”** 选择原 sample-20s.mp4，等待“分析完成”，点击“确认媒体分析”，刷新后检查仍显示确认完成。不要在业务端口 3000 操作，不要新建重复剧集。自动化待上传剧集仍未写入源文件，供该人工操作继续验证。只有这项真实浏览器流程通过并核对记录后，才能将整体从 BLOCKED 改为 PASS；当前停止在 Phase 1.5。

---

## 独立环境真实验收（2026-10-16，最新结论）

**最终判定：BLOCKED。** 独立 PostgreSQL / Redis / Celery / API 真实媒体链路及现有自动化测试通过；浏览器创建项目、剧集、显示任务、失败重试、人工确认通过。浏览器选择本地文件仍被扩展权限拦截，因此“浏览器完整上传 → 处理 → 确认”未完成，不判定 PASS。没有证据表明这是业务代码缺陷。本节优先于以下历史报告；历史 BLOCKED 原因中的数据写入授权已经解决。

### 授权与隔离证明

用户明确授权仅在全新独立验收数据库、媒体目录创建、修改和清理测试数据。首先复核原有 Compose 服务状态，并读取 README、架构和本报告。未查询或修改原有业务记录；原有服务仅做 Docker 元数据和状态检查。

- 独立 Compose 项目：`vietdub-acceptance15-155d3886e3`，使用 `docs/testing/acceptance/compose.yml`，不继承业务 Compose。
- 独立 PostgreSQL 容器、数据库 `vietdub_acceptance_15`、用户 `acceptance15`，新卷 `vietdub-acceptance15-155d3886e3_postgres_data`。
- 独立 Redis 容器及新卷；不是业务 Redis 的另一个队列。broker 为该新容器的 `redis://redis:6379/15`，实际消费队列、exchange、routing key 均为 `acceptance15`。
- 独立媒体目录 `D:\VietDub AI\acceptance-media\155d3886e3`，API 和 Worker 均挂载为 `/acceptance-media`，未挂载业务媒体卷。
- API 和 Worker 实际 SQL 查询返回数据库名 `vietdub_acceptance_15`、用户 `acceptance15`；数据库解析 IP 为 `172.19.0.2`，Redis 为 `172.19.0.3`，与新容器实际网络地址一致。
- 新建项目专用 default（internal）及 ingress 网络；与原有业务容器没有共同网络或存储卷。PostgreSQL / Redis 不发布主机端口，API 为 `127.0.0.1:18000`，Web 为 `127.0.0.1:13000`。
- 正式写入前验证 API / Worker 所见项目、剧集、任务数均为 0，并验证 active_queues 仅为 acceptance15。最终复核仍隔离，记录为 2 个项目、4 个剧集、3 个任务；浏览器剧集仍待上传，没有伪造其任务。

原始证据目录：`data/acceptance-final/155d3886e3/`。`isolation.json` 是写入前证明，`isolation-final.json` 是最终只读复核。新密码仅在忽略目录中的 acceptance.env，报告不披露。未删除任何卷、未执行 down -v、未改变全局配置。

### 实际修改范围

本轮只新增验收夹具 `docs/testing/acceptance/compose.yml`、`docs/testing/acceptance/entry.py`，在 `.gitignore` 忽略 `acceptance-media/`，并更新本报告。entry.py 仅用于独立验收 API / Worker 的队列配置和启动；没有修改生产业务逻辑、原有 Compose 或数据库迁移。辅助脚本及日志位于已忽略的 `data/acceptance-final/`。

首次夹具把所有服务放在 internal 网络，出现主机无法访问已发布端口的问题。在写入任何项目记录前，为 API / Web 增加全新的独立 ingress 网络并重新核验隔离后解决；PostgreSQL / Redis / Worker 保持 internal 网络。该修正不是更改全局 Docker 网络或绕过业务测试。

### 命令、退出码与日志

以下 PowerShell 前缀仅指向独立验收项目，不能省略后改用业务 Compose。密码由本机已生成的 env 文件读取：

```powershell
Set-Location 'D:\VietDub AI'
$AC = @('compose', '--project-name', 'vietdub-acceptance15-155d3886e3', '--env-file', 'D:\VietDub AI\data\acceptance-final\155d3886e3\acceptance.env', '-f', 'D:\VietDub AI\docs\testing\acceptance\compose.yml')
```

| 实际执行命令（辅助脚本内部使用相同前缀） | 退出码 / 结果 |
|---|---|
| `python data/acceptance-final/setup.py`；内部 config --quiet、up -d --no-build | 0；创建全新隔离栈 |
| `python data/acceptance-final/isolation.py` | 0；写入前数据库为空、地址/挂载/队列/网络验证通过 |
| 首次 `python data/acceptance-final/run_chain.py` | 1；internal 网络导致 ready 阶段不可达，主动中断，尚未创建测试记录 |
| 修正夹具后 scoped up -d --no-build 与 isolation.py | 0；端口可达且仍隔离，数据库仍为空 |
| `$env:PYTHONPATH='D:\VietDub AI\.test-deps'; python data/acceptance-final/run_chain.py` | 0；真实链路完整执行，记录 REAL_CHAIN_PASS |
| `python data/acceptance-final/checks.py` | 0；下列全部子命令退出 0 |
| `docker @AC exec -T api alembic upgrade head` | 0；真实独立 PostgreSQL |
| `docker @AC exec -T api alembic current` | 0；0001 (head) |
| `docker @AC exec -T api alembic check` | 0；No new upgrade operations detected. |
| `docker @AC exec -T api python -m pip check`；worker 同命令 | 各 0；依赖一致性通过 |
| `docker @AC exec -T api pytest -v -rs` | 0；9 passed, 1 warning in 1.01s |
| `docker @AC exec -T postgres pg_isready -U acceptance15 -d vietdub_acceptance_15` | 0；accepting connections |
| `docker @AC exec -T redis redis-cli -n 15 ping` | 0；PONG |
| scoped API Python：entry.configure 后 celery.control.inspect(timeout=8).ping() | 0；acceptance15 Worker pong |
| `python data/acceptance-final/audit_ui.py before` 与 `after`（同上述 PYTHONPATH） | 各 0；浏览器确认与失败重试的实际数据库状态符合预期 |
| `python data/acceptance-final/isolation.py --allow-records` | 0；最终隔离验证通过 |
| `docker compose ps`（仅只读查看原有服务状态） | 0；五个原有服务仍 Up，PostgreSQL / Redis healthy |

`chain-events.json` 保留真实 HTTP 状态码、任务状态、Docker 子命令及退出码、Worker 日志和媒体参数；`checks.json` 保留完整测试及迁移输出；`ui-before.json`、`ui-after.json` 保留浏览器操作前后数据。一次诊断输出遇到 Windows GBK 无法打印日志中的字符，退出 1；改为 UTF-8 输出后完成日志读取，不是产品测试失败。补充读取时误将辅助脚本路径写在运行目录下，Get-Content 报路径不存在；随后从 data/acceptance-final 正确读取，未修改或丢失文件。当前目录 git status 返回 128（不是 Git 仓库），因此未声称有 Git diff 校验，也未修改 Git 配置。

### 自动化测试实际结果

Linux 最终 API 镜像，Python 3.12.15、pytest 8.3.5，以下 9 项全部 PASSED，无 skipped：test_crud、test_validation、test_size_limit、test_request_body_limit、test_upload_immutable_and_idempotent_job、test_failed_job_retry_and_recovery、test_probe_rejects_non_mp4_and_missing_audio、test_real_media_pipeline、test_mock_providers。

唯一 warning 为 Starlette TestClient 引用 anyio.abc.BlockingPortal 的 DeprecationWarning，未修改依赖以消除无关警告。现有 ORM / mock 单元测试不当作 PostgreSQL / Redis / Celery 验收证据；真实服务链路由独立测试另行验证。前端 TypeScript / build 的既有通过结果见历史章节，本轮未重新构建，不将历史结果表述为本轮执行。

### 真实媒体与异步链路

素材使用用户提供的 `test/temp.mp4` 的既有 20 秒派生副本 `data/acceptance-20261016/6db4894c-3b25-443a-8dd9-cb89e6a5265c/sample-20s.mp4`，未覆盖用户原文件。FFprobe 实测 MP4 时长 20.033333 秒，H.264、1080×1920、AAC 44100 Hz 双声道；音轨时长 20.016009 秒。不是 mock 媒体处理。

- 真实上传：暂停独立 Worker 后，同一新剧集的并发上传返回 202 / 409，只产生一个 Job 和一个原片。任务 `8fda02f8-9392-4337-919a-cfbc4c8e1620` 在 API 重启后仍 queued、attempts=0；启动 Worker 后观察 queued → running → succeeded、attempts=1。
- FFmpeg 真实输出：pcm_s16le、16000 Hz、1 声道、每采样 2 字节、320250 帧、20.015625 秒。Python wave 与独立 FFprobe 均确认；与源音轨差约 0.384 ms。
- 重复执行：实际向隔离 Redis 投递同一成功 Job 两次，Worker 日志确认两次收到并成功返回；业务 attempts 仍为 1，WAV / 原片 SHA 不变，没有新增业务 Job。
- 失败恢复：仅将验收上传副本目录暂时改名，真实 FFprobe 失败，任务 `f7855dcb-e804-4785-8ba5-10708bc56c56` failed、attempts=1；finally 恢复副本目录后，retry API 返回 200，同一 Job 再次处理 succeeded、attempts=2，输出真实 WAV。未移动业务媒体或用户素材。
- 损坏文件：测试专用 invalid.mp4 通过文件头初筛但真实 FFprobe 失败。任务 `991d40ed-1462-4dc8-837e-4125126a368e` 的 API 重试及浏览器重试均产生真实再执行，最终 failed、attempts=3；这是预期负向测试，不是未修复产品故障。界面显示 Media processing failed (CalledProcessError); verify MP4 streams and FFmpeg installation.
- 人工确认：未成功任务确认返回 409，不改已有记录。成功任务两次确认 200，仅 approved 变更，第二次响应不变；元数据、原片和 WAV 未被覆盖。另一成功任务通过浏览器确认，API 比较同样仅 approved=false → true。
- 持久化：重启独立 API / Worker，成功/失败状态、次数、确认标记仍在独立 PostgreSQL；原片和 WAV 哈希保持一致。

哈希证据：

```text
用户 temp.mp4（前后相同）:
d165f26cdbf7e60d6c7c72d95456e8e157e08e17e257eaa6b32901dca6c4a9ea
20 秒样本及上传原片（前后相同）:
9623ec9c1fd5aaf77b5f7c6f9c59cc34e8c5d1222806fd80915991df90590df1
成功处理 WAV:
a08f51209ca77e824bc16d7c293d84618d79cd272b542ca0eeebf407c16684d8
```

### 浏览器验收与唯一剩余阻塞

在 Chrome 的 `http://localhost:13000` 独立工作台真实创建项目“Phase 1.5 浏览器端到端验收”和剧集“浏览器真实上传与确认”。另在独立真实链路项目中确认了 20.03 秒、1080×1920、16 kHz 单声道展示、成功状态、人工确认，以及损坏任务的“重试处理”→“排队中”→“失败”及错误提示；API 前后快照确认上述操作确实生效。

首次 filechooser.setFiles 被扩展的 Allow access to file URLs 权限拦截。用户回复“已开启，继续验收”后，实际再次点击 file input、取得 chooser，再次调用 setFiles（60 秒超时），仍立即返回相同权限错误；没有上传 HTTP 请求，页面依旧“待上传”。不推断用户未开启，也不能证明当前自动化连接的 Chrome 配置文件已生效；未擅自修改扩展权限或切换浏览器规避限制。

浏览器工具没有进程退出码：该步骤结果为工具错误而非成功，最新 DOM 和 `browser-upload-still-blocked.jpg` 证明该剧集没有任务。已完成的浏览器确认/错误展示截图为 `browser-approval-retry.jpg`、`browser-failed-task-final.jpg`，不得用它们冒充完整浏览器上传通过。

**仅建议下一项操作：手动在已打开的独立工作台 http://localhost:13000，选择“Phase 1.5 浏览器端到端验收”→“浏览器真实上传与确认”，点击上传并选择上述 sample-20s.mp4，然后告知已选择。** 这是最小且最可能绕开自动化扩展权限阻塞的操作；不要在业务工作台 3000 上传。随后才能继续核对该浏览器剧集的真实任务、WAV、确认及哈希，全部通过才可改判 PASS。当前保留独立服务和测试数据，便于继续验收；不进入 Phase 2。

---

## PyPI TLS 分层复验与构建恢复（2026-10-16，UTC+8）

**最新最终判定：BLOCKED（完整 Phase 1.5）；Docker 构建与基础服务已恢复通过。** 当前剩余阻塞不是 PyPI：真实媒体上传、重试、幂等、持久化及人工确认会写入项目/任务记录，而用户本轮明确限制“不修改业务功能或数据库数据”。已异步请求允许新建独立验收数据库及媒体目录；截至本节记录未获得该授权，未执行这些写入类验收。只有所有必需项通过才能宣布 Phase 1.5 PASS。

本节优先于下方先前的 TLS BLOCKED 记录。没有擅自修改 Clash、Windows 代理、系统 PATH、全局 Git 配置、包索引或业务代码，没有删除数据卷，没有引入 Phase 2 模型或付费 API。

### 已读取与实际修复

先读取了 backend/Dockerfile、backend/requirements.txt、docker-compose.yml 和本报告。没有发现适用的 AGENTS.md；读取组合命令最终退出 1 是 rg 无匹配，不是文档读取失败。

唯一新增的生产配置修改在 `backend/Dockerfile` 的 pip 行：

```dockerfile
RUN pip install --no-cache-dir --disable-pip-version-check --retries 6 --timeout 30 -r requirements.txt
```

理由：原有完整错误为间歇性 `SSLEOFError / UNEXPECTED_EOF_WHILE_READING`，本轮正式构建前已在原始 BuildKit 路径验证正常 TLS 与真实 wheel 下载，因此只增强有限网络容错，不需要换源、升级 Python/pip 或导入未经证实必要的 CA。`--timeout 30` 是 socket 等待超时，不是完整构建时限；`--retries 6` 为有界重试。未使用 trusted-host、PYTHONHTTPSVERIFY=0 或关闭证书校验。requirements.txt、Compose、APT 修复和基础镜像均保留。

**不能将本次网络恢复归功于 pip 参数：BuildKit 的正常握手/下载证据早于这一改动。参数增强容错，不能保证外部网络不会再次中断。**

### 分层诊断原始记录

脚本：`data/tls-check/probe.py`、`run_diagnostics.py`、`check_proxy_ports.py`，均为忽略目录中的验收辅助文件。主机、临时容器、BuildKit 完整输出（包含 TLS traceback）分别保存在：

```text
data/tls-check/ee333383-4c31-420e-8e6f-1a04d5edc252/windows.json
data/tls-check/ee333383-4c31-420e-8e6f-1a04d5edc252/container.json
data/tls-check/ee333383-4c31-420e-8e6f-1a04d5edc252/buildkit.json
```

`python data/tls-check/run_diagnostics.py` 本轮执行一次，Windows / container / buildkit 三个子进程均退出 0。**脚本退出 0 只表示完成记录，不把捕获到的 TLS 异常视为通过。** Windows 最初 pip 子命令使用了缓存，详见下文补验，未用它证明实时网络正常。

| 层 | Windows 主机首次探测 | 临时 Python 容器 | BuildKit RUN |
|---|---|---|---|
| DNS：pypi.org | 成功，198.18.0.115 | 同一地址，解析成功 | 同一地址，解析成功 |
| DNS：files.pythonhosted.org | 成功，198.18.0.116 | 同一地址，解析成功 | 同一地址，解析成功 |
| TCP：两个域名 443 | 建连成功 | 建连成功 | 建连成功 |
| TLS：默认 CA + 主机名验证 | 两个域名均在握手阶段 EOF | 两个域名均 TLSv1.3 成功 | 两个域名均 TLSv1.3 成功 |
| HTTP：https://pypi.org/simple/ | 未到 HTTP，TLS EOF，无状态码 | 200，实际读取 64 bytes | 200，实际读取 64 bytes |
| HTTP：https://files.pythonhosted.org/ | 未到 HTTP，TLS EOF，无状态码 | 404，已到 HTTP | 404，已到 HTTP |
| pip 下载 fastapi==0.115.12 | 首次缓存命中退出 0，不作实时下载证据 | 实际下载 metadata + 95 kB wheel，退出 0 | 实际下载 metadata + wheel，退出 0 |

files.pythonhosted.org 的根路径 404 只证明 TLS 和 HTTP 已达，不能证明特定包可下载；特定包可用性由其后的真实 pip wheel 下载另行证明。DNS 有结果也不证明解析到的是公网源站；这里只记录实际地址和后续连接结果，不把 DNS/TCP 成功等同 TLS 成功。

### Python、pip、OpenSSL 与证书信任

| 环境 | Python | pip | OpenSSL |
|---|---|---|---|
| Windows | 3.13.14 | 26.1.2 | 3.0.21，2026-06-09 |
| 临时容器 / BuildKit / 最终 API | 3.12.15 | 25.0.1 | 3.5.7，2026-06-09 |

所有 ssl.create_default_context 探测均为 verify_mode=2（CERT_REQUIRED）、check_hostname=true。Windows 上默认 OpenSSL cafile/capath 为 null，但已加载 57 张证书（54 张 CA），不能仅因没有 PEM 默认路径认定 Windows 不信任 CA。Linux 默认 `/usr/lib/ssl/cert.pem` 和 `/usr/lib/ssl/certs`，加载 150 张 CA。

未配置 SSL_CERT_FILE、SSL_CERT_DIR、REQUESTS_CA_BUNDLE、CURL_CA_BUNDLE 或 PIP_CERT。最终 API 的 pip 配置键列表为空，pip 自带 certifi bundle 存在：`/usr/local/lib/python3.12/site-packages/pip/_vendor/certifi/cacert.pem`。容器与 BuildKit 成功验证到的证书颁发者包括 `GlobalSign Atlas R3 DV TLS CA 2025 Q4`。

历史失败栈在 `ssl.do_handshake()` / `SSLContext.wrap_socket()` 阶段中断，未完成该连接的 TLS 握手、未进入 HTTP，不是已证实的 SSLCertVerificationError。没有证据支持关闭验证或盲目安装 CA；本轮同一默认信任路径已真实成功。

### 失败包、wheel 与根因边界

历史确切失败项为 `fastapi==0.115.12`：

```text
索引：https://pypi.org/simple/fastapi/
metadata：https://files.pythonhosted.org/packages/50/b3/b51f09c2ba432a576fe63758bddc81f78f0c6309d9e5c10d194313bf021e/fastapi-0.115.12-py3-none-any.whl.metadata
错误：SSLError(SSLEOFError(8, '[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol'))
构建退出：pip 1，Compose build 1
```

本轮相同 `py3-none-any` wheel 已在 Python 3.12 临时容器和 BuildKit 中下载，并在最终镜像安装成功。SQLAlchemy、psycopg-binary、pydantic-core 等也实际选择了 cp312/manylinux wheel；最终 pip check 通过。没有证据显示 fastapi 版本不存在或 Python 3.12 不兼容，所以没有修改依赖版本。

可确定的故障位置是历史 DNS/TCP 成功之后、HTTP 之前的 TLS 握手中断；本轮容器/BuildKit 已恢复。不能确定是外部链路恢复、转发路径变化还是间歇故障消失，不将其擅自归因于某个特定代理组件。

### 代理配置、端口与补验

- 当前 Docker info：HTTPProxy/HTTPSProxy=`http.docker.internal:3128`，NoProxy=`hubproxy.docker.internal`。
- 主机进程没有 HTTP_PROXY/HTTPS_PROXY/ALL_PROXY；Windows urllib 检出的用户代理为 127.0.0.1:7890。代理信息只输出协议、主机、端口及是否含凭据，不输出用户名/密码/令牌。
- 容器和 BuildKit 没有显式代理环境变量。其 Docker 内部地址解析分别为 http.docker.internal=192.168.65.1、host.docker.internal=192.168.65.254；Windows 对这些名称的解析不同。这是观测到的环境差异，不单独认定为配置故障。
- 本轮 TCP 补验：主机 127.0.0.1:7890、容器 http.docker.internal:3128 和 host.docker.internal:7890 均可建连。端口可达不等于代理可完成 HTTPS，也不证明各环境实际使用了相同出口。
- `python data/tls-check/check_proxy_ports.py` 退出 0，并额外执行一次 Windows `pip download fastapi==0.115.12 --no-deps --only-binary=:all: --no-cache-dir --retries 0 --timeout 15 --disable-pip-version-check`；该子命令退出 0，实际下载 metadata 与 wheel。此后续结果才是 Windows 非缓存下载成功证据，与较早 TLS 失败分开记录。

未调整 Docker Desktop、Windows 或 Clash 代理配置，未换第三方包索引；没有证据支持改端口或更改全局出口。

### 实际重建、启动、迁移和测试

| 命令 | 退出码与结果 |
|---|---|
| `docker compose --progress plain build api worker` | **0**；本轮仅正式构建一次，APT CACHED，Python 依赖全部实际下载/安装，API 与 Worker 均 Built |
| 启动前 `SELECT tablename FROM pg_tables WHERE schemaname='public'` | 0；原库无表 |
| `docker compose up -d --no-build` | **0**；沿用 Compose，API 启动命令执行用户要求的 Alembic upgrade head；未创建项目、剧集或媒体任务 |
| 首次 `python data/docker-build-check/verify_runtime.py` | 1；Compose ps 已返回，诊断脚本因 Windows GBK 无法打印替换字符而中断，不是容器失败 |
| 修正辅助脚本 UTF-8 输出及独立日志文件后再运行同一脚本 | **0**；所有下列检查均完成，未修改业务代码 |
| `docker compose exec -T api python -m pip check` | 0；No broken requirements found |
| `docker compose exec -T worker python -m pip check` | 0；No broken requirements found |
| 最终 API Python/SSL/9 项依赖版本查询 | 0；版本与 requirements.txt 匹配 |
| pip 配置键 / certifi 路径只读检查 | 0；配置键为空，CA 文件存在 |
| 结束前只读查询 projects/episodes/jobs 数量 | 0；均为 **0** |

最终镜像：

```text
vietdubai-api manifest list:
sha256:058c2599ac9bb262d1d0c852496852013bb8d3ab14129945437c1d752296ce2d
vietdubai-worker manifest list:
sha256:739f4deb506663d4d256a899dab2ea76f39cba821743b90c72c9dcfadcddb07d
```

运行检查完整命令、stdout/stderr、退出码保存在：
`data/docker-build-check/runtime-results-9252b98a-ae31-4bc6-ab11-672358995f4b.json`。

该日志中的逐项真实结果：

| 检查 | 实际结果 |
|---|---|
| 最终 API ffmpeg / ffprobe -version | 两项退出 0，7.1.5-0+deb13u1 |
| 最终 Worker ffmpeg / ffprobe -version | 两项退出 0，7.1.5-0+deb13u1 |
| PostgreSQL pg_isready | 0，accepting connections |
| Redis redis-cli ping | 0，PONG |
| 最终 API alembic current | 0，0001 (head)，真实 PostgreSQL |
| 最终 API alembic check | 0，No new upgrade operations detected |
| 最终 API 本机 health | 0，HTTP 200，status=ok |
| Celery inspect ping --timeout=10 | 0，1 node online，pong |
| Web 容器通过 Next.js /api/projects 代理 | 0，真实 API HTTP 200 |
| 容器 pytest -v -rs | 0，**9 passed, 1 warning in 0.89s** |

九项测试逐项均 PASSED：test_crud、test_validation、test_size_limit、test_request_body_limit、test_upload_immutable_and_idempotent_job、test_failed_job_retry_and_recovery、test_probe_rejects_non_mp4_and_missing_audio、test_real_media_pipeline、test_mock_providers。Starlette/anyio BlockingPortal 弃用警告仍存在。测试 fixture 使用新建内存 SQLite 和临时文件，不修改真实 PostgreSQL 业务记录；其中 mock 测试不作为完整媒体异步链路证据。

### 真实异步和浏览器已验证范围

Worker 日志已实际出现：

```text
Connected to redis://redis:6379/0
celery@380bc5503a7a ready.
Scheduler: Sending due task recover-jobs (app.tasks.dispatch)
Task app.tasks.dispatch[...] received
Task app.tasks.dispatch[...] succeeded ... None
```

这证明 Redis broker → Celery worker 的真实定时调度可执行，但不是媒体 Job 成功处理证据。数据库没有媒体任务，未伪造状态或注入数据。

本轮使用已连接 Chrome 只读打开 `http://localhost:3000`，中文工作台真实显示“创建第一个项目以开始制作”“请先选择项目”。与上次 ENOTFOUND api 不同，本轮 Web 代理只读请求已实测 200。没有点击创建项目或选择上传文件，因此不宣称浏览器上传/失败重试流程通过。日志里仍可能包含 Web 旧的 ENOTFOUND 历史行，当前连通性以本轮 HTTP 200 和 API access log 为准。

### 完整 Phase 1.5 判定与唯一下一项操作

| 必需项 | 最新状态 |
|---|---|
| TLS 分层定位、正常证书验证、实际 wheel 下载 | PASS（本轮快照；不保证外部网络永远稳定） |
| 最终 API/Worker 构建、版本与依赖检查 | PASS |
| 五服务运行、真实 PostgreSQL Alembic、Redis/Celery 调度 | PASS |
| 本轮现有自动化测试 | PASS，9/9 |
| 已有授权素材与本机 WAV | 沿用此前真实处理记录，不冒充本轮 Worker 产物 |
| 真实 MP4 网络上传 → Celery 提取成功 | BLOCKED，等待独立验收数据写入授权 |
| 真实 PostgreSQL Job 持久化、重复/并发幂等、失败重试 | BLOCKED，同上 |
| 成功人工确认不覆盖、浏览器完整上传与任务状态 | BLOCKED，同上 |

**唯一下一项操作：确认是否允许仅在全新独立验收数据库和媒体目录创建测试项目/任务记录，现有数据库保持只读。** 这是因为用户本轮明确要求“不修改数据库数据”，而上传/重试/审批必然写库；不是仍需修改代理或再次盲目重建。本轮暂不创建独立库或其测试记录，也不自动进入 Phase 2。

---

## Docker 构建专项修复（2026-10-16，UTC+8）

本轮仅修复 Docker 构建及基础运行环境，不修改业务逻辑、不进入 Phase 2。本节结果优先于下方先前的 BLOCKED 历史记录；完整业务验收与构建专项分别判断。

**本轮最终结论：BLOCKED。FFmpeg APT 安装已修复并完成容器内验证；完整 API/Worker 镜像随后被新的 PyPI TLS EOF 网络故障阻塞。没有宣称完整构建或应用运行验收通过。**

### 修改与配置检查

检查了 backend/Dockerfile、frontend/Dockerfile、docker-compose.yml 以及两份 .dockerignore。Compose 的 API/Worker 共用 backend 构建上下文，无需重构或修改 Compose；两份 .dockerignore 已排除缓存/数据库/媒体或 node_modules 等内容，无需修改。

生产文件修改仅 `backend/Dockerfile`：

- 保留 `python:3.12-slim`、Debian trixie 和官方 deb.debian.org/security 源。构建实际基底 digest 仍为 `sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1`。
- 为 APT 设置 Acquire::Retries=3，HTTP/HTTPS 单次连接/数据等待超时 30 秒；这不是整个构建的 30 秒总时限。
- `APT::Update::Error-Mode=any` 防止部分索引失败被当作完整成功。
- update 与 install 分别最多执行三轮，轮间等待 5 / 10 秒；失败时打印轮次和退出码，最后返回实际失败码。安装重试时不重新执行 update，避免基础镜像的更新后钩子清理已下载包；成功后清理索引。
- 保留 --no-install-recommends，不执行 apt-get upgrade，不降低证书或仓库签名验证。

本轮还更新本报告。辅助检查脚本及运行日志仅写入忽略的 `data/docker-build-check/`。没有修改基础镜像版本、Clash 配置、Windows 代理、PATH、全局 Git 配置或业务代码；未删除现有卷与项目数据。

### 代理与网络诊断：证据及边界

Docker 客户端和引擎均为 29.8.2。`docker info` 显示 HTTPProxy / HTTPSProxy 为 `http.docker.internal:3128`，NoProxy 为 `hubproxy.docker.internal`。这是当前引擎报告的地址，不能仅凭该地址认定转发异常。

只读检查 Docker Desktop settings-store.json 和用户 Docker CLI config.json，未发现显式 proxy 覆盖字段；当前进程没有 HTTP_PROXY/HTTPS_PROXY/ALL_PROXY/NO_PROXY 环境变量。Windows 用户代理为 ProxyEnable=1、ProxyServer=127.0.0.1:7890，netstat 确认 7890 在监听。上述配置均未改变；没有读取或输出代理凭据。

在临时 `python:3.12-slim` 容器实际访问：

| 官方地址 | HTTP | HTTPS |
|---|---|---|
| deb.debian.org/debian/dists/trixie/InRelease | 200 | 200 |
| deb.debian.org/debian/pool/main/libx/libx11/libx11-xcb1_1.8.12-1_amd64.deb | 200 | 200 |
| deb.debian.org/debian/pool/main/f/fontconfig/fontconfig_2.15.0-2.3_amd64.deb（本次构建报 502 后复测） | 200 | 200 |

每次读取前 32 字节验证响应可读，不代表下载完全部软件包。当前容器网络通，但构建过程中仍观察到个别 HTTP 502，错误地址仍显示 198.18.0.98:80。证据支持“间歇性上游/转发路径故障”，**不足以确定是 Clash、Docker 内部代理或远端 CDN 中哪一层造成，也不足以证明某个协议始终异常**。因此不擅自改全局代理、切换国内源或关闭验证；以有界重试处理瞬时故障。

只读诊断命令：

```powershell
docker version --format '{{.Client.Version}} {{.Server.Version}}'
docker info --format 'HTTPProxy={{.HTTPProxy}} HTTPSProxy={{.HTTPSProxy}} NoProxy={{.NoProxy}}'
docker compose ps
python data/docker-build-check/inspect_network.py
```

上述命令均退出 0。另用 Python winreg 只读查询 Windows Internet Settings 的 ProxyEnable / ProxyServer，subprocess 执行 netstat，退出 0；只读列举 Docker settings-store.json 顶层键退出 0。未读取全部设置内容或修改配置。网络检查脚本运行了自动清理自身的临时诊断容器，没有删除业务容器或数据卷。

### 构建与基础运行结果

最终 Dockerfile 的 APT 步骤实际下载 133 MB，完成全部 205 个依赖包安装。日志中 libavutil59 曾显示 Ign，随后成功补下载；最终未触发外层整轮重试。外层重试为有界容错代码，本次没有用人工故障注入验证三轮耗尽分支。原来的 APT 退出码 100 已不再阻止构建；下一次重建直接命中成功的 APT 缓存层。

过程记录：首次带重试的构建观察到 fontconfig、libzix 等包返回 502。之后检查 `docker run --rm python:3.12-slim cat /etc/apt/apt.conf.d/docker-clean`（退出码 0），确认基础镜像的 APT::Update::Post-Invoke 会清理下载缓存。为避免每轮重新 update 清掉缓存，主动中止该构建（工具退出码 1，非自然构建失败），将 update/install 改为独立重试后重新构建。未更改基础镜像缓存清理文件本身。

#### 新阻塞：PyPI TLS 连接被提前关闭

完整构建到达 Dockerfile 的原有 `pip install --no-cache-dir -r requirements.txt` 时失败，pip 退出 1，Compose build 退出 1。第一次失败在 `https://pypi.org/simple/fastapi/`；复用成功的 APT 层再次重建时，PyPI 索引经重试一度可读，但 fastapi wheel metadata 的 `files.pythonhosted.org` 请求仍连续失败。

关键日志：

```text
Fetched 133 MB in 6min 54s
Setting up ffmpeg (7:7.1.5-0+deb13u1) ...
[后续重建] APT RUN ... CACHED
SSLError(SSLEOFError(8, '[SSL: UNEXPECTED_EOF_WHILE_READING]
EOF occurred in violation of protocol (_ssl.c:1010)'))
HTTPSConnectionPool(host='files.pythonhosted.org', port=443):
Max retries exceeded with url:
/packages/50/b3/b51f09c2ba432a576fe63758bddc81f78f0c6309d9e5c10d194313bf021e/fastapi-0.115.12-py3-none-any.whl.metadata
target worker: failed to solve ... pip install ... exit code: 1
```

第一次 pip 还输出 `No matching distribution found for fastapi==0.115.12`，但其上游证据是 HTTPS 获取失败，**不能据此认定依赖版本不存在，也未修改 requirements.txt**。这是 TLS EOF，不是已证实的 CA 缺失；没有使用 trusted-host、HTTP PyPI、禁用证书验证或盲换镜像源。

进一步只读探测：

| 测试 | 结果 |
|---|---|
| 容器默认路径访问 `https://pypi.org/simple/fastapi/` | TLS UNEXPECTED_EOF_WHILE_READING |
| 容器显式使用已报告的 `http://http.docker.internal:3128` | 同一 TLS EOF |
| 容器临时 ProxyHandler 指向现有 `http://host.docker.internal:7890` | 同一 TLS EOF；仅本次请求，不改变代理配置 |
| Windows Python urllib 默认路径访问同一 PyPI URL | 退出 1，同一 TLS EOF |

探测脚本 `python data/docker-build-check/probe_pypi.py` 两次执行均退出 0，但该退出码只表示脚本记录完了异常，**不表示网络探测成功**。主机和容器都受影响，不能把根因仅归于 Dockerfile 或 Docker Desktop；需要恢复到 pypi.org 与 files.pythonhosted.org 的正常 TLS 链路。未擅自修改 Clash/Windows 代理。

#### 容器内媒体工具验证

因为最终 API/Worker 镜像未完成，另以当前 Dockerfile 从 FROM 到 APT RUN 的原样内容，通过标准输入构建诊断镜像 `vietdubai-media-check`；APT 层确实命中上面已安装成功的缓存。没有新增生产多阶段构建或改写 Compose。

```powershell
python data/docker-build-check/verify_apt_layer.py
# 内部执行：
# docker build --progress plain --file - --tag vietdubai-media-check backend
docker run --rm vietdubai-media-check ffmpeg -version
docker run --rm vietdubai-media-check ffprobe -version
```

三项退出码均 **0**：FFmpeg 与 FFprobe 均为 **7.1.5-0+deb13u1**，Debian GCC 14 构建。完整版本输出和诊断层构建日志保存在 `data/docker-build-check/apt-layer-results.json`。这是容器中真实执行，**仅证明已成功的基础媒体层，不冒充最终 API/Worker 镜像可用**。诊断镜像保留；自动清理的只是本次工具版本检查容器，未挂载业务数据卷。

#### 本轮命令及最终状态

| 命令 | 退出码 / 实际结果 |
|---|---|
| `docker compose config --quiet` | 0 |
| 第一次 `docker compose --progress plain build api worker`（初版循环） | 主动中止后工具码 1；原因是发现更新钩子会使安装重试重复下载，未伪称自然失败 |
| 最终版 `docker compose --progress plain build api worker` | 1；APT 成功，原 pip 步骤 TLS EOF 失败 |
| 同一最终版再次 `docker compose --progress plain build api worker` | 1；APT CACHED，pip 在 files.pythonhosted.org metadata 重试耗尽 |
| `python data/docker-build-check/verify_apt_layer.py` | 0；诊断镜像构建及两个版本命令通过 |
| `docker compose ps`（结束前） | 0；postgres healthy、redis healthy、web Up；无 api/worker |
| `docker compose exec -T postgres pg_isready -U vietdub -d vietdub` | 0；accepting connections |
| `docker compose exec -T redis redis-cli ping` | 0；PONG |

现有 Web 继续使用先前已构建的镜像，在 127.0.0.1:3000 运行；本次没有重建前端或替换容器。API/Worker 没有成功启动；因此未执行最终镜像内 ffmpeg/ffprobe、API health、Worker inspect ping、PostgreSQL Alembic 和容器 pytest 检查。`verify_runtime.py` 仅已准备，未执行，不能计作通过。本轮没有重新执行应用自动化测试，历史 9 passed 不作本轮完整镜像的测试结果。

#### 剩余最少操作

本次构建修复范围内只剩 **PyPI/files.pythonhosted.org 的 TLS 网络阻塞**。需要由用户检查现有网络/代理转发，恢复这两个官方域名的 HTTPS；没有足够证据给出可靠的全局代理修改命令，本次也没有权限范围内可确定有效的配置改动。不需要重新安装 Python/FFmpeg，也不需要更换基础镜像或清空卷。

可先用下面的准确命令复核；应输出 200，而不是 TLS EOF：

```powershell
Set-Location 'D:\VietDub AI'
docker run --rm python:3.12-slim python -c "import urllib.request; print(urllib.request.urlopen('https://pypi.org/simple/fastapi/',timeout=20).status)"
```

网络恢复后继续原构建；成功的 APT 层可复用：

```powershell
docker compose --progress plain build api worker
docker compose up -d --no-build
python data/docker-build-check/verify_runtime.py
```

只有构建成功后才执行后两行。运行检查脚本会逐项保存真实命令、返回码和完整输出到 `data/docker-build-check/runtime-results.json`，包括最终 API/Worker 的 ffmpeg/ffprobe、基础服务、迁移检查和现有 pytest。不要使用 down -v、删除卷或修改业务逻辑绕过阻塞。报告到此停止，不进入 Phase 2。

---

## 最新复验：2026-10-16（UTC+8）

**当前最终判定：BLOCKED。** 以下为本次实测；下方 2026-10-15 的记录保留为历史，不代表当前工具仍未安装。

### 用户补充 temp.mp4 后的继续检查

用户随后指定 `D:\VietDub AI\test\temp.mp4`。重新检查实际素材并生成独立验收片段，未覆盖原片；本节更新下文先前的素材缺口。

| 项目 | 本轮实测 |
|---|---|
| temp.mp4 | 97,377,367 bytes；60.046803 秒；H.264 1080×1920；AAC 44100 Hz 双声道 |
| 原片 SHA-256 | `d165f26cdbf7e60d6c7c72d95456e8e157e08e17e257eaa6b32901dca6c4a9ea`，操作前后相同 |
| 新验收样本 | 从原片前 20 秒无重编码另存；实际容器 20.033333 秒，符合 10–30 秒时长范围 |
| 样本音轨 | AAC，44100 Hz，双声道，20.016009 秒 |
| 实际 WAV | pcm_s16le，16000 Hz，单声道，20.015625 秒，640,578 bytes |
| Python wave 核对 | 320,250 frames，16000 Hz，1 channel，2 bytes/sample |
| WAV 与样本音轨差 | -0.000384 秒；与容器时长差 -0.017708 秒 |
| 样本 SHA-256 | `9623ec9c1fd5aaf77b5f7c6f9c59cc34e8c5d1222806fd80915991df90590df1` |

产物目录：`D:\VietDub AI\data\acceptance-20261016\6db4894c-3b25-443a-8dd9-cb89e6a5265c\`，包含 `sample-20s.mp4` 与 `audio.wav`。素材由用户在中文素材请求中指定，未独立人工试听判断语言；没有使用 ASR 或任何 Phase 2 服务。

本轮命令和结果：

- `ffprobe -v error -show_entries 'format=duration,size:stream=codec_type,codec_name,width,height,sample_rate,channels,duration' -of json 'D:\VietDub AI\test\temp.mp4'`：成功；随后同一组合命令的 `docker compose ps` 在沙箱内因引擎管道权限拒绝，外层码 1，不代表 FFprobe 失败。
- 沙箱外 `docker compose ps; docker image inspect vietdubai-api --format '{{.Id}}'`：ps 成功，postgres/redis healthy、web 运行；inspect 退出码 1，API 镜像仍不存在。
- Python stat/hashlib 检查原片：退出码 0。
- `python data/acceptance-20261016/new_source_check.py`：退出码 **0**。内部剪辑、样本 probe、WAV 提取、WAV probe 四个子进程均退出 **0**，Python wave 与原片未改变断言通过。

剪辑使用 `ffmpeg -nostdin -v error -i <temp.mp4> -t 20 -map 0:v:0 -map 0:a:0 -c copy -map_metadata -1 -n <新目录/sample-20s.mp4>`；提取使用 `ffmpeg -nostdin -v error -protocol_whitelist file -i <sample-20s.mp4> -vn -map 0:a:0 -ac 1 -ar 16000 -c:a pcm_s16le -n <新目录/audio.wav>`。路径为上列实际绝对路径。所有输出均为新 UUID 目录，`-n` 禁止覆盖。

**更新结论：验收样本时长与本机真实 WAV 提取已完成；不再需要用户另找 10–30 秒文件。完整验收仍 BLOCKED，因为 API/worker 镜像未就绪，尚未通过真实网络上传、PostgreSQL 业务迁移、Redis/Celery 处理及浏览器业务流程。** 此次没有再次执行已知网络失败的完整构建，也没有将本机 FFmpeg 输出当作 worker 产物。现有 9 项测试结果沿用同日先前实际执行记录，未宣称本轮又重跑一次。

最少剩余操作：恢复 Docker 构建访问 Debian/npm 的网络后执行 `Set-Location 'D:\VietDub AI'`、`docker compose up --build -d`，再运行下文列出的服务检查。后续真实上传应使用本节生成的 `sample-20s.mp4`，不修改原片。

### 本次环境变化

已先读取 README.md、docs/architecture.md 和本报告。没有改动业务逻辑、Dockerfile、Compose、系统 PATH 或全局 Git 配置，没有安装系统软件或删除已有数据。已安装的 Docker Desktop 经 `docker desktop start` 启动。原本没有 `.env`，本次仅新建本地随机数据库密码配置，未输出密码。

| 工具 | 实际路径与版本 | 本次结果 |
|---|---|---|
| Docker | `C:\Program Files\Docker\Docker\resources\bin\docker.exe`，29.8.2 | 客户端可执行；Desktop 启动后 Linux 引擎 29.8.2 可用 |
| Docker Compose | `C:\Program Files\Docker\cli-plugins\docker-compose.exe`，v5.6.0 | 可执行 |
| FFmpeg | `C:\ffmpeg\bin\ffmpeg.exe` | 2026-05-25-git-34dfa8bf2b，gyan.dev full build，可执行 |
| FFprobe | `C:\ffmpeg\bin\ffprobe.exe` | 同一构建，可执行 |
| PostgreSQL | Compose `postgres:16-alpine` | 实际 16.15，容器 healthy，pg_isready accepting connections，SQL select version() 成功 |
| Redis | Compose `redis:7-alpine` | 容器 healthy，redis-cli ping 返回 PONG |
| FastAPI / Celery | 沿用现有 backend Dockerfile 构建 | 构建受到 Debian 下载 502 阻塞；未完成完整异步链路 |

主机 Python 仍为 3.13.14；没有为了验收升级依赖。PATH 中可直接找到 Docker、FFmpeg 和 FFprobe，本次没有修改 PATH。目录检索仍有 Program Files 受保护目录访问拒绝，不影响已找到二进制的实际执行证据。

### 实际媒体处理

源文件：`D:\VietDub AI\test\MiniMax_H3_00001_.mp4`。

| 参数 | FFprobe 实测 |
|---|---|
| 文件大小 / 哈希 | 1,203,085 bytes；SHA-256 `3e8b72ade65b992e4351cc4880e0a3d64bcec8355ee21fe8f44bb85198153554` |
| 容器时长 | 5.167000 秒 |
| 视频 | H.264，480 × 864，5.166667 秒 |
| 原音轨 | AAC，32000 Hz，双声道，5.167000 秒 |
| 输出 WAV | pcm_s16le，16000 Hz，单声道，5.184000 秒 |
| Python wave 交叉核对 | 16000 Hz，1 channel，2 bytes/sample，82944 frames |
| 音轨时长差 | 输出比源音轨长 0.017 秒（AAC 解码/填充差值；记录实测，不声明完全等长） |

实际输出保留于：`D:\VietDub AI\data\acceptance-20261016\3eef6f8f-dad2-4d7f-bb9a-a6fc3d98c4a7\audio.wav`。使用新 UUID 目录和 `-n`，未覆盖已有文件。FFprobe、FFmpeg、Python wave 三项检查成功；原片处理前后 SHA-256 相同。

**素材限制：现有文件只有 5.167 秒，未达到原验收要求的 10–30 秒。音轨语言未人工试听确认，不能从媒体标签或文件名认定中文。已向用户请求合格素材路径，未擅自循环拼接或修改原片凑时长。** 本机 WAV 提取成功不代表 Celery worker 产物验收成功。

实际媒体命令（由 `data/acceptance-20261016/media_check.py` 执行，各子进程退出码均 0）：

```powershell
ffprobe -v error -show_entries 'format=duration,size:stream=index,codec_type,codec_name,width,height,sample_rate,channels,duration' -of json 'D:\VietDub AI\test\MiniMax_H3_00001_.mp4'
ffmpeg -nostdin -v error -protocol_whitelist file -i 'D:\VietDub AI\test\MiniMax_H3_00001_.mp4' -vn -map 0:a:0 -ac 1 -ar 16000 -c:a pcm_s16le -n 'D:\VietDub AI\data\acceptance-20261016\3eef6f8f-dad2-4d7f-bb9a-a6fc3d98c4a7\audio.wav'
ffprobe -v error -show_entries 'format=duration,size:stream=index,codec_type,codec_name,width,height,sample_rate,channels,duration' -of json 'D:\VietDub AI\data\acceptance-20261016\3eef6f8f-dad2-4d7f-bb9a-a6fc3d98c4a7\audio.wav'
```

### 现有自动化测试逐项结果

```powershell
Set-Location 'D:\VietDub AI'
$env:PYTHONPATH='D:\VietDub AI\.test-deps'
python -m pytest backend/tests -v -rs --basetemp 'D:\VietDub AI\data\acceptance-20261016-tests'
```

退出码 **0**，**9 passed, 1 warning in 2.11s**，本次没有跳过项。

| 测试 | 实际结果 | 证据范围 |
|---|---|---|
| test_crud | PASSED | SQLite 隔离 API |
| test_validation | PASSED | 输入与审批前置条件 |
| test_size_limit | PASSED | 文件大小限制 |
| test_request_body_limit | PASSED | 请求体大小限制 |
| test_upload_immutable_and_idempotent_job | PASSED | 使用 mock 媒体函数的单元级幂等/审批 |
| test_failed_job_retry_and_recovery | PASSED | 使用 monkeypatch 的重试/恢复逻辑 |
| test_probe_rejects_non_mp4_and_missing_audio | PASSED | mock FFprobe 数据校验 |
| test_real_media_pipeline | PASSED | 真实 FFmpeg/FFprobe，但为 1 秒合成测试素材、SQLite、进程内执行 |
| test_mock_providers | PASSED | mock 适配器契约 |

仍有 Starlette/anyio BlockingPortal 弃用警告。上述测试**不是 PostgreSQL/Redis/Celery 集成验收**。本次 frontend `node node_modules/typescript/bin/tsc --noEmit` 退出码 0。

### Compose 尝试、关键日志与命令退出码

| 命令/操作 | 本次结果 |
|---|---|
| 读取三份指定文档 | 退出码 0 |
| 读取 browser-use 技能、Compose 并 rg 搜索 AGENTS.md | 组合码 1；技能/配置读取成功，rg 无匹配 |
| 首次内联 Python 目录检查 | 退出码 1；PowerShell 引号转义导致 SyntaxError，随后使用既有环境脚本重查 |
| `python data/acceptance-20261015/check_environment.py` | 成功打印本次实际路径；随后组合命令查询不存在的 tools 目录使外层码 1 |
| `where.exe docker` / `where.exe ffmpeg` / `where.exe ffprobe` | 均找到上表路径 |
| `docker --version` / `docker compose version` | 客户端成功；版本见环境表 |
| 初次 `docker info` | 退出码 1；dockerDesktopLinuxEngine 管道不存在 |
| `docker desktop start` | 退出码 0，`Starting Docker Desktop` |
| `docker info --format '{{json .ServerVersion}}'` | 退出码 0，`29.8.2` |
| `ffmpeg -version` / `ffprobe -version` / 源媒体完整 probe | 组合退出码 0；输出媒体自带大段 tags，之后改用 show_entries 精简字段 |
| 准备缺失时才创建的 .env；`docker compose config --quiet`; `docker compose ps` | 组合退出码 0；启动前无既有项目容器；密码未输出 |
| 第一次 `docker compose up --build -d` | 外层退出码 1；Debian apt 子步骤退出码 100 |
| 第二次 `docker compose up --build -d` | 按原配置重试；再次出现大量 Debian HTTP 502。持续约 222 秒仍有依赖下载失败，发送 Ctrl-C 中止，工具返回 1；不是自然完成的构建结果。npm 下载重试后完成，web 镜像已导出 |
| `docker compose up -d postgres redis` | 启动成功；首次紧接的 pg_isready 尚未就绪，后续复核已成功 |
| `docker compose exec -T postgres pg_isready -U vietdub -d vietdub`（复核） | 0，accepting connections |
| `docker compose exec -T postgres psql -U vietdub -d vietdub -c 'select version();'` | 0，PostgreSQL 16.15 |
| `docker compose exec -T redis redis-cli ping` | 0，PONG |
| `docker compose ps`（复核） | 0，postgres/redis healthy |
| `python data/acceptance-20261016/media_check.py` | 0，FFprobe / FFmpeg / wave 均通过 |
| `python -m pytest ...` | 0，9 passed |
| frontend `node node_modules/typescript/bin/tsc --noEmit` | 0 |
| 构建期间 `docker image inspect vietdubai-web --format '{{.Id}}'` | 1，当时镜像尚未导出；不作为业务失败 |
| Chrome 打开 `http://localhost:3000` | 浏览器返回 ERR_CONNECTION_REFUSED；没有伪造 UI 流程成功 |
| `docker compose up -d --no-deps web` | 0；在 web 镜像实际导出后，仅启动真实前端检查页面，不模拟 API |
| Chrome 再次打开本机页面、填写验收项目名并点击创建 | 页面真实呈现；提交后 alert 显示 `Error: 请求失败 (500)`，没有创建成功 |
| `docker compose logs --tail 12 web` / 最后 `--tail 8 web` | 0；`Failed to proxy http://api:8000/projects`，`getaddrinfo ENOTFOUND api` |
| 最后 `docker compose ps` | 0；postgres/redis healthy，web 运行且仅绑定 127.0.0.1:3000；无 api/worker |

首次构建关键日志：

```text
Err:1 http://deb.debian.org/debian trixie InRelease
502 Bad Gateway [IP: 198.18.0.98 80]
E: Failed to fetch .../trixie/InRelease 502 Bad Gateway
target api: failed to solve ... exit code: 100
```

第二次重试已取得 InRelease，但多个 deb 下载仍返回 502。未关闭仓库签名检查、未改软件源、未改代理或业务代码。npm 的 swc 下载曾 timeout，随后依赖安装完成，web 镜像实际导出并单独启动成功。未因 API 阻塞而改写前端代理或使用模拟 API。

浏览器部分验收使用 browser-use 技能与已连接的 Chrome：实际打开中文工作台，填写 `Phase 1.5 浏览器连通性检查` 并点击创建项目。页面显示 `Error: 请求失败 (500)`，DOM 与截图均已观察；web 日志对应 ENOTFOUND api。**这只证明页面与请求错误提示可见，不能证明上传、业务任务失败信息或成功处理流程通过。** 未进行文件上传，因为创建项目所需的 API 不存在。没有上传外部站点，没有修改页面状态或伪造请求响应。

### 最新必需项判定

| 验收项 | 当前判定 |
|---|---|
| Windows 工具可执行与路径 | PASS |
| 真实现有 MP4 → WAV 及参数 | PASS（5.167 秒现有素材的本机处理） |
| 原要求 10–30 秒中文授权素材 | BLOCKED，需合格素材并确认中文 |
| PostgreSQL/Redis 基础可用性 | PASS（仅连接与健康检查） |
| PostgreSQL Alembic / 真实业务迁移 | BLOCKED，API 镜像未成功就绪 |
| Redis/Celery 入队、成功、失败、重试、持久化 | BLOCKED，worker/API 构建受阻 |
| PostgreSQL 并发幂等、成功审批不覆盖 | BLOCKED；不得以 SQLite 单元测试替代 |
| Next.js 浏览器完整上传/任务/错误流程 | BLOCKED；真实页面和请求失败提示已验证，但 API/worker 缺席，未完成上传与任务流程 |
| 既有自动化测试 | PASS，9/9 |

为完整链路准备了 `data/acceptance-20261016/chain_check.py`，尚未执行，不计作任何验收证据。该脚本仅在真实 API/worker 就绪后才可运行；不会将任务状态人工改为成功。

### 最少手动操作与准确命令

现在**不需要重新安装 Docker 或 FFmpeg，也不需要修改 PATH**。需恢复 Docker 构建访问 Debian/npm 源的网络；502 来源需检查本机网络或 Docker Desktop 的网络/代理设置，本次没有足够证据确定具体配置原因，不能给出可靠的自动修改命令。恢复后重跑原配置：

```powershell
Set-Location 'D:\VietDub AI'
docker info
docker compose up --build -d
docker compose ps
docker compose exec -T api alembic current
docker compose exec -T api alembic check
docker compose exec -T redis redis-cli ping
docker compose exec -T api celery -A app.tasks.celery inspect ping
```

再提供符合 10–30 秒要求的中文 MP4 绝对路径，可用以下命令核对时长（将路径替换为实际文件）：

```powershell
& 'C:\ffmpeg\bin\ffprobe.exe' -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 'D:\实际路径\中文短剧.mp4'
```

不要删除数据卷，不执行 down -v，不覆盖现有 .env。PostgreSQL/Redis/web 保持运行，现有数据卷保留，等待后续继续验收；API/worker 未启动。恢复网络后可按上面的原命令重新构建应用镜像，无须清理数据库。业务代码修复清单为空；本轮只新增验收产物、本地缺失的 .env，并更新报告。完成报告后停止，不进入 Phase 2。

---

## 历史记录：2026-10-15

验收日期：2026-10-15（UTC+8）  
项目：`D:\VietDub AI`  
最终判定：**BLOCKED**

原因：现有自动化测试、前端构建和 SQLite 迁移通过；但未找到可用 Docker、FFmpeg/FFprobe、PostgreSQL 和 Redis 服务，不能执行必需的完整异步链路与媒体提取验收。不能将本地直接调用或 mock 单元测试视为端到端通过。

## 1. 范围与数据保护

首先阅读了 README.md、docs/architecture.md 和 docs/validation.md，并检查现有测试及前端代理配置。未发现适用的 AGENTS.md。

没有安装或下载第三方软件，没有升级依赖、修改 PATH、修改全局 Git 配置或删除已有数据。没有进入 Phase 2，没有调用 AI 或付费 API。未修改业务代码、Compose、依赖锁文件或迁移文件。构建命令会更新忽略的 `.next` / TypeScript 缓存。

数据库迁移与本地文件验收均使用本次新建的独立 SQLite 数据库。保留所有验收产物；未对此前的 `backend/migration-check.db` 或其他数据库执行降级。测试内的删除操作仅发生在隔离内存数据库。

## 2. 实际环境检查

| 项目 | 实测结果 | 判断 |
|---|---|---|
| OS | Python platform：Windows-11-10.0.26200-SP0；.NET：Windows NT 10.0.26200.0 | 可用 |
| PowerShell | 7.6.5 | 可用 |
| Python | 3.13.14，`C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe` | 可用；未验证容器目标 Python 3.12 |
| Node | v24.19.0，Codex bundled runtime | 可用；未验证容器目标 Node 22 |
| Docker / Compose | PATH 中无 docker；常见安装目录无二进制；com.docker.service 查询返回 1060；无匹配进程 | 未找到可用安装，BLOCKED |
| FFmpeg / FFprobe | PATH 和扫描目录均未发现可执行文件；无匹配进程 | BLOCKED |
| PostgreSQL | PATH 无 psql/postgres；常见安装目录无二进制；常见服务名称查询返回 1060；5432 无 TCP 端点 | BLOCKED |
| Redis | PATH 无 redis-server/redis-cli；Redis / Memurai 服务查询返回 1060；6379 无 TCP 端点 | BLOCKED |
| Celery | Python 包 5.5.2 已存在；无匹配 worker 进程，无可用 broker | 包可导入，完整运行 BLOCKED |
| 本机 Web / API | 3000 / 8000 无 TCP 端点；未启动完整应用 | 前端交互验收 BLOCKED |

Python 使用既有 `.test-deps`：FastAPI 0.115.12、SQLAlchemy 2.0.40、Alembic 1.15.2、psycopg 3.2.9、Celery 5.5.2、redis-py 5.3.1、pytest 8.3.5。**redis-py 和 psycopg 可导入，不代表 Redis/PostgreSQL 服务端已安装或运行。**

### 检索范围与权限边界

检查 PATH、常见卸载注册表项及服务注册表项，并检索以下位置：

- `C:\Program Files`、`C:\Program Files (x86)`
- `C:\Users\Administrator\AppData\Local\Programs`
- `C:\Users\Administrator\.cache\codex-runtimes`
- `D:\VietDub AI`
- `C:\ffmpeg`、`D:\ffmpeg`、`C:\tools`、`D:\tools`
- `C:\ProgramData\chocolatey`、Administrator 的 Scoop 与 WinGet Packages 目录

前两个目录存在，其余部分候选目录不存在；未检出目标二进制。Program Files 中两个受保护子目录返回 WinError 5，未强行绕过。未宣称扫描了所有磁盘、WSL 发行版、非标准远程服务或其他用户目录。

沙箱内 Get-Service 无法打开 SCM。使用沙箱外只读 `sc.exe query` 复核 `com.docker.service`、`postgresql-x64-16/17/18`、`Redis`、`Memurai`，每个子进程退出码均为 **1060（服务不存在）**。`tasklist` 无目标进程；`netstat -ano -p tcp` 无上述四个端口端点。socket 探测沙箱内返回 10013、沙箱外返回 10035，未将这些值误当作服务正常或端口明确关闭的证据。

## 3. 执行命令与退出码

以下 Python 验证命令均使用现有依赖：

```powershell
$env:PYTHONPATH = 'D:\VietDub AI\.test-deps'
```

所有提升执行权限的操作仅用于只读环境检查或隔离测试；未运行系统安装命令。组合命令的外层退出码不能代替内部工具退出码，差异已标出。

| 编号 | 实际执行的命令 / 操作 | 退出码与结果 |
|---|---|---|
| 01 | `Get-Content README.md; Get-Content docs/architecture.md; Get-Content docs/validation.md; rg --files -g AGENTS.md ...` | 1；文档读取成功，rg 未匹配 AGENTS.md |
| 02 | `$PSVersionTable.PSVersion.ToString()`、`[Environment]::OSVersion.VersionString`、`Get-Command ...`、`python --version`、`node --version`、Get-Service/Get-Process、读取现有测试与 next.config.ts | 组合命令 0；Get-Service 有非终止权限错误，未据组合码认定服务枚举成功 |
| 03 | 常见安装路径递归查找；卸载注册表过滤；`rg --files -g '*.mp4' -g '*.wav' ...` | 外层显式 0；当时未匹配媒体；不据此认定用户随后提供的文件不存在 |
| 04 | `python -m pytest backend/tests -q -rs --basetemp 'D:\VietDub AI\data\acceptance-20261015\pytest'` | 1；父目录未创建导致 7 个 setup errors，1 passed / 1 skipped |
| 05 | frontend：`node node_modules/typescript/bin/tsc --noEmit` | **0，通过** |
| 06 | 创建验收目录后，以 `pytest-run2` 为 basetemp 重跑 | 沙箱挂起；发送 Ctrl-C 后工具返回 1，未作为测试结果 |
| 07 | 追加检索 Program Files、Local Programs、bundled runtime、工作区及服务注册表 | 0；未匹配目标二进制；部分 PowerShell 格式化输出为空，不单独作为安装判据 |
| 08 | frontend：`$env:NEXT_TELEMETRY_DISABLED='1'; node node_modules/next/dist/bin/next build` | **0，通过** |
| 09 | 内联 Python socket 检查的首次命令 | 1；PowerShell 引号转义导致 SyntaxError，随后改成文件脚本 |
| 10 | 沙箱外只读 Get-Service/Get-Process/根目录及 OS 注册表查询组合命令 | 0，但无可用格式化输出；随后由 Python / sc.exe / netstat 复核 |
| 11 | `python data/acceptance-20261015/check_environment.py`，沙箱内及沙箱外各执行一次 | 均 0；打印 OS、工具路径、包版本、端口探测、目录扫描结果 |
| 12 | 沙箱外 `python -m pytest backend/tests -q -rs --basetemp 'D:\VietDub AI\data\acceptance-20261015\pytest-run3'` | **0；8 passed, 1 skipped, 1 warning，0.87 秒** |
| 13 | Python Path/stat/hashlib 检查用户素材 | 0；文件存在、1,203,085 bytes、SHA-256 如下 |
| 14 | Python subprocess 调用六个 `sc.exe query <服务名称>` | Python 外层 0；六个 sc.exe 子进程均 1060 |
| 15 | `python data/acceptance-20261015/run_local_acceptance.py`（沙箱内） | 完成 6 个迁移命令后 TestClient 挂起；Ctrl-C 后工具返回 1 |
| 16 | Python subprocess 调用 `netstat -ano -p tcp` 并复核 sc.exe 子进程返回码 | 外层 0；netstat 0、无目标端点；sc.exe 均 1060 |
| 17 | 沙箱外 `python data/acceptance-20261015/run_local_acceptance.py` | **0；隔离迁移、本地实际文件上传、重复请求及负向确认检查通过** |
| 18 | Python subprocess 调用 `tasklist /FO CSV /NH` | 外层与 tasklist 均 0，无匹配运行进程 |
| 19 | 最后再次计算用户素材大小和 SHA-256 | 0；与开始时一致 |

编号 17 内部迁移命令工作目录为 backend，`DATABASE_URL` 指向新建的 `data/acceptance-20261015/4e1307a2-133d-499b-9ef6-686618c43fad/acceptance.db`：

| 命令 | 退出码 | 输出 |
|---|---|---|
| `python -m alembic upgrade head` | 0 | 成功 |
| `python -m alembic current` | 0 | `0001 (head)` |
| `python -m alembic check` | 0 | `No new upgrade operations detected.` |
| `python -m alembic downgrade base` | 0 | 成功，仅针对本次新库 |
| `python -m alembic upgrade head` | 0 | 成功 |
| `python -m alembic check` | 0 | `No new upgrade operations detected.` |

两个 Python 辅助脚本位于忽略的 `data/acceptance-20261015/` 下，只用于本次验收。`check_environment.py` 使用 shutil.which、socket、importlib.metadata 与目录遍历；`run_local_acceptance.py` 每次生成 UUID 新目录，使用真实文件、TestClient 和直接 `process.run()`，不 monkeypatch 处理函数。它们不是完整异步链路测试程序。

## 4. 自动化测试结果

最终复测：**8 passed, 1 skipped, 1 warning**。

- 跳过项：`test_real_media_pipeline`，原因 FFmpeg / FFprobe not installed。
- 警告：Starlette TestClient 使用 anyio BlockingPortal 弃用别名。
- TypeScript 检查通过。
- Next.js 15.5.14 生产构建通过，首页 First Load JS 为 105 kB。

重要边界：现有成功处理测试用 monkeypatch 替换 probe/extract_wav，并通过 `process.run()` 执行；恢复投递测试替换了 `delay`。这些是单元级逻辑证据，不是 Redis、worker 或真实媒体成功的证据。现有真实媒体测试即便在有 FFmpeg 的环境通过，也仅使用 1 秒色块/正弦波，不能替代本次要求的 10–30 秒中文素材验收。

## 5. 真实素材与本地 API 结果

用户指定素材：`D:\VietDub AI\test\MiniMax_H3_00001_.mp4`，仅作本机验收，未上传外部服务。

```text
bytes: 1203085
sha256: 3e8b72ade65b992e4351cc4880e0a3d64bcec8355ee21fe8f44bb85198153554
```

开始与结束的源文件哈希相同，上传副本哈希也相同。素材存在已确认；**时长是否 10–30 秒、音轨是否中文、分辨率、编码、采样率等均未验明**，不能从文件名推断。

隔离验收运行目录：`data/acceptance-20261015/4e1307a2-133d-499b-9ef6-686618c43fad/`。

```text
episode_id: e4d67cd0-b44d-4478-a8ff-d598eddc6cd5
job_id: fe697106-46cd-460e-bd73-d010eef9c123
第一次真实文件上传：HTTP 202，job.status=queued
第二次相同剧集上传：HTTP 409，Source media is immutable
Job 行数：始终 1
第一次直接调用处理函数：failed，attempts=1
错误：Media processing failed (FileNotFoundError); verify MP4 streams and FFmpeg installation.
失败后人工确认：HTTP 409，Successful media analysis is required
重试请求：HTTP 200，同一 job_id，status=queued
第二次直接调用处理函数：failed，attempts=2，仍为 FileNotFoundError
再次人工确认：HTTP 409；操作前后剧集 API 对象完全相等
原片与上传副本 SHA-256：始终相同
```

这是**真实字节上传 + SQLite + 进程内 API + 同步处理函数**的部分验收，不经过浏览器、HTTP 网络代理、Redis 或 Celery worker。FileNotFoundError 是缺少可执行文件的实际失败，不是人工伪造处理结果。

FFprobe 未执行成功；没有获得真实元数据。FFmpeg WAV 提取未执行成功；没有生成可供验收的 WAV，也没有实测 16 kHz、单声道或音视频时长差。以上项目全部 **BLOCKED**。

## 6. A–J 验收矩阵

| 项目 | 判定 | 证据 / 缺口 |
|---|---|---|
| A 既有测试 | 部分通过 / BLOCKED | 8 passed；真实媒体测试跳过，不能认定全部通过 |
| B Alembic | SQLite PASS；PostgreSQL BLOCKED | 独立新库升级、检查、回滚、再升级均通过；缺 PostgreSQL |
| C Redis + Celery 入队、执行、完成、失败、重试 | BLOCKED | 无 broker/worker；仅本地同步失败与 API 重试通过，无异步完成证据 |
| D 重复请求不产生重复任务 | 本地串行 PASS；完整链路 BLOCKED | 实际文件第二次上传 409、Job=1；未验证 PostgreSQL 并发与重复 broker 投递 |
| E 10–30 秒中文 MP4 真实上传 | 部分通过 / BLOCKED | 用户文件已实际上传，但时长、音轨语言未确认；未经过完整部署入口 |
| F FFprobe 参数检查 | BLOCKED | 未找到可执行文件 |
| G WAV 提取与采样率/声道/时长确认 | BLOCKED | 未找到 FFmpeg/FFprobe，无验收 WAV |
| H 前端显示上传、任务和错误 | BLOCKED | 编译构建通过，不代表浏览器交互通过；无完整 API/worker；代理固定指向 Docker 服务名 api |
| I 人工确认不覆盖数据 | 负向 PASS；成功路径 BLOCKED | 两次未就绪确认均 409，剧集对象与源文件哈希不变；无真实成功任务可验收成功确认及重复确认 |
| J 如实记录阻塞 | PASS | 未将 mock、同步函数或构建成功冒充端到端通过 |

## 7. Windows 安装与后续验证步骤（建议，未执行）

以下步骤涉及第三方下载、系统安装或进程 PATH 修改，**本次均未执行，执行前需要用户批准具体动作**。无需升级现有 Python 或 Node。

### Docker Desktop

先参照 [Docker 官方 Windows 安装说明](https://docs.docker.com/desktop/setup/install/windows-install/) 和 [权限说明](https://docs.docker.com/desktop/setup/install/windows-permission-requirements/)，确认 Windows、虚拟化和 WSL 2 条件。不要在未核验 WSL 状态时自动执行更新或安装。

建议先执行以下只读检查：

```powershell
wsl --status
wsl --version
```

经批准后从官方页面下载 Windows 安装器，验证数字签名，再按选择的安装模式操作。例如，传统系统级安装命令：

```powershell
Get-AuthenticodeSignature "$env:USERPROFILE\Downloads\Docker Desktop Installer.exe"
Start-Process -FilePath "$env:USERPROFILE\Downloads\Docker Desktop Installer.exe" -ArgumentList 'install','--backend=wsl-2' -Verb RunAs -Wait -WindowStyle Hidden
```

风险：第三方软件执行、管理员权限、虚拟化/服务/网络组件变化、磁盘占用，可能需要重启；WSL 安装/更新另行批准。安装后手动启动 Docker Desktop，检查：

```powershell
docker --version
docker compose version
docker info
```

### FFmpeg / FFprobe

从 [FFmpeg 官方下载页](https://ffmpeg.org/download.html) 指向的 Windows 构建提供方取得包含 ffmpeg.exe 与 ffprobe.exe 的 ZIP。核验提供方公布的校验和；建议解压到新建的项目 tools 子目录，不做系统级安装或永久 PATH 修改。

以下为批准后的示例；实际 ZIP 路径须与下载文件一致：

```powershell
$archive = "$env:USERPROFILE\Downloads\ffmpeg-release-essentials.zip"
Get-FileHash -LiteralPath $archive -Algorithm SHA256
$destination = 'D:\VietDub AI\tools\ffmpeg-acceptance'
if (Test-Path -LiteralPath $destination) { throw '目标目录已存在，请选择新的目录' }
Expand-Archive -LiteralPath $archive -DestinationPath $destination
Get-ChildItem -LiteralPath $destination -Recurse -Filter ffprobe.exe
Get-ChildItem -LiteralPath $destination -Recurse -Filter ffmpeg.exe
```

风险：第三方二进制、额外磁盘占用；处理不可信媒体可能消耗较多 CPU/内存。先用绝对路径执行 `ffprobe.exe -version` 和 `ffmpeg.exe -version`。只有另外批准进程级 PATH 调整后，才在当前 PowerShell 会话设置 `$env:Path = '<实际 bin 目录>;' + $env:Path`，使现有后端能找到命令；不使用 setx，不修改系统 PATH。

### 启动现有完整架构

优先通过 Docker 提供 PostgreSQL/Redis，不额外安装 Windows 原生数据库服务。以下命令会下载镜像、构建依赖并创建容器/卷，也需先批准。若已有 `.env`，不得覆盖：

```powershell
Set-Location 'D:\VietDub AI'
if (-not (Test-Path -LiteralPath '.env')) { Copy-Item '.env.example' '.env' }
# 手动配置本地随机 POSTGRES_PASSWORD；不要将内容贴入日志
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose exec api alembic current
docker compose exec api alembic check
docker compose exec postgres pg_isready -U vietdub -d vietdub
docker compose exec redis redis-cli ping
docker compose exec api celery -A app.tasks.celery inspect ping
docker compose exec api pytest -q -rs
docker compose logs --tail 100 api worker
```

注意：现有 pytest fixture 仍使用 SQLite。即使容器内 pytest 全绿，也不能称 PostgreSQL 业务集成已通过；还必须通过真实部署 API 创建独立验收项目、上传、轮询并核对持久化记录。对已有 PostgreSQL 库只做 upgrade/current/check，回滚测试应另建专用验收库。不得执行 `docker compose down -v` 或清空 Redis。

### 真实媒体及完整链路补验

先用 FFprobe 检查源素材，并人工试听确认中文；时长若不在 10–30 秒，另选授权素材或经许可另存剪辑副本，不覆盖原片：

```powershell
ffprobe -v error -show_format -show_streams -of json 'D:\VietDub AI\test\MiniMax_H3_00001_.mp4'
```

通过浏览器 `http://localhost:3000` 新建独立项目/剧集并上传；记录源文件哈希、episode_id、job_id。等待 beat 投递，在 worker 日志及 API 同时确认 queued → running → succeeded；短任务若界面未捕获 running，保留 worker 日志和数据库证据。

- 重复上传应 409，Job 行数仍为 1；验证并发请求时同样只有一个业务任务。
- 向 worker 重复投递同一成功 job_id，检查 attempts 与产物哈希不变；不以 Redis 队列消息数代替业务幂等断言。
- 用专用无效 MP4 验收 failed 与错误显示；retry 保留原 job_id，attempts 增加。不可替换原片，失败重试不应伪造成功；需要真实成功重试时应使用可恢复的环境故障和独立测试实例。
- 对 worker 生成的实际 audio.wav 执行 `ffprobe -v error -show_format -show_streams -of json '<实际 WAV 路径>'`，确认 pcm_s16le、sample_rate=16000、channels=1，并记录时长及与源音轨的差值；同时可用 Python wave 核对 `getnframes()/getframerate()`。不对不存在的文件编造参数。
- 如需单独执行 FFmpeg 对照提取，使用新目标文件与 `-n`：`ffmpeg -nostdin -v error -i '<授权源文件>' -vn -map 0:a:0 -ac 1 -ar 16000 -c:a pcm_s16le -n '<全新验收文件.wav>'`。该对照不能替代 worker 产物验收。
- 在成功任务人工确认前后保存剧集与任务快照及媒体哈希；首次仅 approved 变为 true，第二次确认不得改变其他数据或新增任务。
- 浏览器实际核对上传反馈、刷新后任务持久化、成功状态及失败错误信息，记录截图/结果；构建成功不替代此步骤。

## 8. 必要修复与最终判定

业务代码修复：**无**。本轮未取得业务缺陷的充分证据，保持架构与项目文件不变。初次测试父目录错误、命令引号错误和沙箱挂起属于验收执行问题，已通过修正命令/隔离目录和沙箱外重试解决，不掩盖初始失败。

仍需解决：

1. 经批准配置可运行的 Docker 环境，验证 PostgreSQL、Redis、Celery 与 Compose。
2. 经批准提供 FFmpeg/FFprobe，确认用户素材满足时长与中文音轨要求。
3. 完成真实 WAV、浏览器显示、成功确认与重复/并发异步任务补验。

**最终：BLOCKED。** 已通过的部分检查不能覆盖必需项的缺口。没有宣称完整端到端 PASS，也没有因环境缺失直接判定业务代码 FAIL。Phase 1.5 报告到此结束，不自动进入 Phase 2。
