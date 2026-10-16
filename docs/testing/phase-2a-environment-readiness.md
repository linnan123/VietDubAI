# Phase 2A-0 环境准备与 Phase 1.5 基线

检查日期：2026-10-16（UTC+8）。范围：只读检查、官方资料调查、三份文档；未开始 Phase 2A-1。

## 判定

设计准备完成；尚不具备直接开始安装和真实推理的完整条件。Git 基线缺失、Docker 当前不可达、资源与备份恢复尚待验证。Phase 1.5 历史 PASS 保留，不将本轮访问失败推断为已验收业务故障。

## 本轮证据与边界

- `git status --short`、`git rev-parse HEAD` 均退出 128，提示 not a git repository；根目录无 .git。当前 commit：不可获取；工作区 clean/dirty：不可判定。没有执行 init、commit、reset、clean、checkout 或全局配置变更。文件哈希只是内容快照，不能替代 Git 历史和可恢复备份。
- 未发现适用 AGENTS.md。检查 README、架构、Phase 1.5 报告、backend/app 全部源文件、依赖、Dockerfile、0001 迁移、测试、Compose 及验收入口。
- Phase 1.5 报告顶部最终 PASS（2026-10-16 20:32 UTC+8）优先于保留的历史 BLOCKED 段落。9 passed、真实 PostgreSQL/Redis/Celery、浏览器验收均为历史证据，本轮未重跑或重新授予 PASS。
- `docker version --format '{{.Server.Version}}'` 无法连接 dockerDesktopLinuxEngine 管道；不能确认服务、卷、镜像 digest 或当前数据库 revision。没有启动、停止、重建容器。
- `wsl --status` 返回 Wsl/E_ACCESSDENIED；CIM CPU/内存查询被拒绝。16GB、无独立 NVIDIA GPU 为用户给定约束；CPU 型号、实际可用内存、指令集、磁盘余量及 WSL 配额未验证。
- Dockerfile 目标为 Python 3.12；目录存在 CPython 3.13 缓存，但缓存不证明当前主机解释器版本或模型兼容性。
- 未读出 .env 内容，未访问业务数据库，未迁移、安装、下载权重、调用付费 API 或改业务文件。仅新增本交付三份 Markdown。

## 备份与恢复方案（仅设计，未执行）

1. 先只读确定每个栈的 Compose project、数据库名称/用户、容器和真实卷/绑定目录；分别登记业务、开发、Phase 1.5 验收，禁止凭默认项目名推断。验收历史项目为 vietdub-acceptance15-155d3886e3，数据库 vietdub_acceptance_15，媒体绑定 acceptance-media/155d3886e3，Redis /15、队列 acceptance15；仍需现场复核。
2. 每次新建独立备份目录：`<备份根>/phase15/<UTC时间>-<随机UUID>/`，目录及文件使用独占创建，存在即失败，禁止覆盖或复用。备份应另存一份到不同磁盘/受控存储；容量先核算。不要把 data 目录视为天然已有备份。
3. 每库执行 PostgreSQL 16 对应版本的 `pg_dump -Fc` 输出到新文件，检查退出码、文件大小及 `pg_restore --list`；角色/授权单独登记，凭据用受控 secret 注入，禁止进入文档、日志或仓库。不要直接复制运行中的 PGDATA。dump 对数据库提供一致性快照，但不保证跨媒体原子一致。
4. 取得维护窗口授权后阻止新上传/队列写入、等待在途任务结束；再配对数据库快照与媒体副本。若暂不允许维护窗口，在线 dump 只能算单库快照：记录前后任务与媒体哈希，检测变化并标记非一致备份，不能宣称完成灾备。此轮未进行任何停写操作。
5. 对业务 media_data、开发媒体以及验收绑定目录分别完整复制到新目标，保留 MP4/WAV 与关联路径，逐文件 SHA-256、大小、相对路径建清单；禁止移动、镜像删除、去重删除或清理原目录。保存代码快照、依赖锁、Compose、镜像 ID/digest、迁移版本、验收证据；配置中密码单独加密保管。
6. Redis 只作投递媒介，数据库任务为事实来源。保存路由和必要配置；恢复时用全新 Redis/队列，扫描数据库可恢复任务，禁止重放旧 broker 快照造成跨环境投递。
7. 在全新隔离 PG/媒体/Redis/网络恢复 dump 与媒体，验证记录数、FK、revision、源哈希及读取工作流；禁止指向旧栈启动 API（入口自动迁移）。备份成功的定义包含一次隔离恢复验证；仅有文件不算通过。
8. 恢复仅写新目标并以人工明确切换为最后步骤，不覆盖当前数据库和媒体。RPO 建议为开工前冻结点，RTO 初始目标 60 分钟，均需实测后确认。

## 开工前门槛

- 用户另行授权 Phase 2A-1 及独立环境安装/模型下载范围。
- 定位原 Git 仓库或经确认建立本地版本基线并记录 commit；不擅自提交。保存下列哈希及隔离可恢复备份。
- 恢复 Docker/WSL 可读可运行状态，核验 CPU、内存、磁盘及旧栈隔离；不要因排障重建 Phase 1.5。
- 确认授权中文素材及人工真值；锁定依赖、模型 revision 与许可证；准备独立模型缓存。
- 选定 small 多语言 CPU int8 冒烟配置；资源不足先 base 多语言，只允许在新栈实测，不修改老栈。

## 源文件 SHA-256 快照

以下为本轮生成文档前读取的字节哈希；交付后再次核对。未包含 .env、数据库内容或秘密配置。未执行完整媒体备份。

| 文件 | SHA-256 |
|---|---|
| `README.md` | `ee4ae551f09dd789df6ad625ab35fb5286a0c163abf78cc8aa66e6fd25ff11ee` |
| `.gitignore` | `c015d3364e628ae9f268d4c91e0f56102d62a6fd2b647f6c2cc9ba277eb75858` |
| `docker-compose.yml` | `a9ca320e83fd3f937858c7ee837c9b5d871894bca47433076eaf2c67d31eade9` |
| `docs/architecture.md` | `2ed2be4845600758da8590d4fac2266b2f1bd2a6892f879cea8d8ac618580471` |
| `docs/testing/phase-1-5-environment-acceptance.md` | `01c8c8dcf3216eec98902bf75d55a8e996afbb7e55bd0b83b7e24d9c5410acab` |
| `docs/testing/acceptance/compose.yml` | `05f58e3b36155de592306178fdc9178f2068e09b7b31a5893b41db71415a42a0` |
| `docs/testing/acceptance/entry.py` | `251a80ad9029e7c620f1b4bddd050fe81bd86c90ab3ca12784cb6a3359c5954f` |
| `frontend/package.json` | `c2e798006effcd8c024feafe1e30c31fd15b0f8911615ded0f4354f68bce2995` |
| `frontend/pnpm-lock.yaml` | `12b7aa609d8d2ea287b81f4279242cbe70f98379994a5b03b5d4d0f7c644cf1d` |
| `frontend/next.config.ts` | `a614867fd5880f0e8648ba14390314bdbe6f65a0f540530c3011b4a6b02b3a5a` |
| `backend/app/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `backend/app/db.py` | `403dc57bb734cf492629d77a6cf5577a298d17564b46595423b004243212ca6a` |
| `backend/app/main.py` | `e08bfa986ba254a6c09f28c6485183beecdd6831a546dd2954f3761294586492` |
| `backend/app/media.py` | `1c462deef1d9a7bcbfc9cf0d59601c8c50f19197822bc752c986ab30dd9aff84` |
| `backend/app/middleware.py` | `817f15cd3c26360af22a4f7e22c46d0bc4869e157b0961fce8312c8da6f22b12` |
| `backend/app/models.py` | `04f93a95193da8a3b7ee43e58dabc54bcc47b078d63d66b99bf532e1d61e86e0` |
| `backend/app/providers.py` | `4e15a421e6ba57daf698e0e2b117cda058e82b8b279d2bf9df3285468549ac47` |
| `backend/app/repositories.py` | `fcaa64fa0dfd18bc7447864088473d3d4aa0d1d6cb66b85babcab08b6f3d8ac0` |
| `backend/app/services.py` | `515248d3eb2f3de236c07c3c9084bdc9b32761ec0c28f2d265bbc1e6bb8e88dc` |
| `backend/app/tasks.py` | `c8a6aa24c92e6b0c21934e0a93b830f16814529fc9c29ebe39e418c9cd0c6200` |
| `backend/migrations/env.py` | `0267b391b8d8cce4173befcf607d9dfd818dfac15179058d60408024213d6aa5` |
| `backend/migrations/versions/0001_initial.py` | `e4255908c795bc560f73d96485342d1721e7c74ea953e97e0042ce8aa1b06834` |
| `backend/requirements.txt` | `51e439a19a0c35de142aa44443656edb32669b94bee5655101fdd0f79ef31cd3` |
| `backend/Dockerfile` | `90921cd841df057696d25821fc8000e648024f9a15d3a92cae6188ed970cd3d7` |
| `backend/alembic.ini` | `ebfad8a9c8f352d2381e48df599dd04dad764ca95b03f0dc9949d0691c6d2517` |
| `backend/tests/test_phase1.py` | `e564eb0089a239e268dc035897a6cc40a2c96f9ce8ed170611d0dd30c8ae8ad4` |

## 本轮媒体只读核对

| 文件 | SHA-256 |
|---|---|
| `test/temp.mp4` | `d165f26cdbf7e60d6c7c72d95456e8e157e08e17e257eaa6b32901dca6c4a9ea` |
| `acceptance-media/155d3886e3/2e1af50e-9f2c-4614-af11-0cb0773b6076/audio.wav` | `a08f51209ca77e824bc16d7c293d84618d79cd272b542ca0eeebf407c16684d8` |
| `acceptance-media/155d3886e3/2e1af50e-9f2c-4614-af11-0cb0773b6076/e8822022-94aa-40fb-b9b4-3a58544fb355.mp4` | `9623ec9c1fd5aaf77b5f7c6f9c59cc34e8c5d1222806fd80915991df90590df1` |

历史报告预期 temp.mp4=d165f26cdbf7e60d6c7c72d95456e8e157e08e17e257eaa6b32901dca6c4a9ea；浏览器上传 MP4=9623ec9c1fd5aaf77b5f7c6f9c59cc34e8c5d1222806fd80915991df90590df1；WAV=a08f51209ca77e824bc16d7c293d84618d79cd272b542ca0eeebf407c16684d8。这里只核对所列样本，不代表全部媒体完整性验证。

## 交付后复核

本轮重新读取上述26个代码/配置/报告基线文件与3个媒体文件，29项SHA-256全部一致；三个媒体值均与Phase1.5最终报告一致。三份新文档UTF-8可读且无替换字符。仅文档交付，未运行业务回归测试或模型推理；未执行备份或恢复演练。Git缺失使得无法提供git diff，不能据此宣称Git工作区clean。
