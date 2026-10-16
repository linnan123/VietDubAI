# Phase 2A-0 GPU 环境准备报告

检查日期：2026-10-16，UTC+8（约21:08–21:11）。此报告针对用户声明的新电脑。结论：**宿主GPU与WSL2安装已确认；Docker GPU链路未验证，Phase1.5运行基线迁移未确认；暂不具备进入2A-1的完整条件。**

仅检查和设计；没有启动/停止Docker或WSL、拉取镜像、安装模型依赖、下载权重、调用收费API、修改数据库、迁移或覆盖Phase1.5验收记录。旧CPU方案保留作历史参考，新GPU方案优先。

## 实际环境检测

| 检查 | 实测结果 | 判定 |
|---|---|---|
| nvidia-smi | NVIDIA GeForce RTX3060；驱动595.95；WDDM；12288MiB；首次856MiB已用，约11432MiB剩余 | 宿主GPU枚举PASS |
| GPU复核 | 查询返回868MiB已用、11248MiB空闲（显存动态变化，驱动保留等可能使总量不等于两者简单相加） | 只是采样，非推理峰值 |
| CUDA支持 | nvidia-smi显示CUDA Version 13.2 | 驱动能力上限，不证明已安装CUDA Toolkit13.2/容器CUDA/cuDNN/torch |
| CPU | i7-12700，12物理核、20逻辑处理器 | 与用户配置一致 |
| 内存 | TotalVisibleMemorySize=16457144KiB，FreePhysicalMemory=6323736KiB；约15.69GiB可见、6.03GiB可用 | 当前可用量有限，Docker未启动；尚不能证明全栈资源足够 |
| 磁盘 | C剩余15527661568字节≈14.46GiB；D剩余330728550400字节≈308.02GiB | D充足，C需控制镜像/WSL盘/临时缓存增长 |
| Windows/WSL | Windows10.0.26200.9711；WSL3.0.3.0；内核6.18.54.1-1 | WSL已安装 |
| WSL发行版 | Ubuntu与docker-desktop均Version2、Stopped | WSL2发行版确认，运行及GPU访问未测试 |
| Docker Desktop | 安装文件ProductVersion4.95.0.242831，查询未发现Docker进程 | 安装存在，不等于运行正常 |
| Docker CLI | 29.8.2，API1.56，context=desktop-linux | 客户端可执行 |
| Docker Engine | docker version无法连接dockerDesktopLinuxEngine命名管道，沙箱外复查相同 | BLOCKED：服务端不可达，不判定其已卸载或损坏 |
| Linux容器GPU | 镜像及容器列表均因Engine不可达失败，未运行GPU容器 | NOT RUN，不将Windows nvidia-smi冒充容器验证 |
| Git | status及rev-parse均not a git repository，无可记录commit | 基线缺少Git历史，不能判clean；未init/commit/reset/clean |

初次沙箱内CIM/WSL访问受限；随后经获准的沙箱外只读检查取得上述真实CPU、内存与WSL结果。Docker不可达在两种上下文均出现，未把沙箱权限错误当作WSL未安装。

主要命令：`nvidia-smi`、GPU csv查询、`wsl --status`、`wsl --version`、`wsl --list --verbose`、`docker version`、`docker context show`、`docker image ls`、`docker ps -a`、CIM CPU/OS查询、`Get-PSDrive`。WSL输出编码通过WSL_UTF8=1复核；每项结论依据对应输出，未以整段命令最终退出码替代单项判定。

## 项目与Phase1.5迁移核查

源文件、Phase1.5最终PASS报告、验收Compose/入口、历史证据及浏览器媒体存在。旧环境报告列出的26个基线文件和3个媒体文件共29项SHA-256均匹配；历史archive-manifest.json列出的12份证据文件全部匹配。历史原片与WAV分别保持9623ec9c1fd5aaf77b5f7c6f9c59cc34e8c5d1222806fd80915991df90590df1、a08f51209ca77e824bc16d7c293d84618d79cd272b542ca0eeebf407c16684d8。

**已确认文件层迁入，不等于运行基线迁入。** 当前不能列出本机容器、镜像或命名卷，不能确认PostgreSQL数据/0001 revision、原5个Job、approved记录、Redis、Celery与Web运行状态。data目录递归搜索未发现.dump/.backup/.sql/.tar/.gz备份文件；这不排除Docker卷或目录外备份存在。没有读.env内容，不把包含连接地址的日志或SQLite文件当PostgreSQL备份。

待核实/补齐：原Git仓库与commit；业务/验收PG逻辑备份及恢复证明；Docker命名卷/原媒体卷；对应镜像digest或可重建来源；受控配置及路径映射；新电脑真实PG/Redis/Celery、MP4→WAV、浏览器确认回归证据。原PASS保持有效历史记录，不能直接授予新电脑运行PASS。

## 人工处理与后续验证顺序

1. 启动Docker Desktop并确认使用WSL2 Linux Engine，等待server可达；本轮不启动是为避免自动唤起旧容器及写业务数据。若启动仍失败，检查Docker诊断与WSL状态，先不重装、清理或重置卷。
2. 只读清点镜像、容器、卷和Compose project。确认原PG数据是否迁入；缺失时从原电脑受控导出PG16 custom dump、媒体及配置，恢复到**新隔离目标**，不覆盖现有数据。不要直接运行根Compose导致初始化空库并误认为恢复成功；API入口会自动迁移。
3. 找回原Git仓库或经明确确认建立基线；备份新建UTC时间+UUID目录，禁止覆盖，跨盘保存并在新PG/媒体目录恢复验证。沿用旧环境文档的备份一致性方案，历史报告不动。
4. 确认Docker磁盘映像/模型缓存/构建临时目录实际位置，优先D盘并预留至少40GiB；不要擅自搬迁现有VHDX或修改全局设置。释放宿主内存，GPU Worker试运行前目标宿主可用>=8GiB，按实际监测调整。
5. Engine可达后先用**已存在且确认含nvidia-smi的Linux镜像**执行：`docker run --rm --pull=never --network none --gpus all --entrypoint nvidia-smi <本地已核验镜像ID>`。无宿主目录/数据库挂载，不启动业务；无镜像时先报告，镜像准备另行授权。退出0并看到同一RTX3060才算容器枚举通过；仍不等于CUDA计算通过。
6. 明确批准2A-1后，按GPU计划构建隔离镜像及下载已审查模型缓存；分别验证torch CUDA张量、CTranslate2 float16和真实中文对齐，不能以torch成功替代CT2成功。

## 本轮写入前SHA-256

下表记录本轮保护对象及旧验收指标文件；后者因用户要求更新GPU标准，是唯一计划改写项。无Git diff时用哈希复核，哈希不替代备份。

| 文件 | SHA-256 |
|---|---|
| `README.md` | `ee4ae551f09dd789df6ad625ab35fb5286a0c163abf78cc8aa66e6fd25ff11ee` |
| `docker-compose.yml` | `a9ca320e83fd3f937858c7ee837c9b5d871894bca47433076eaf2c67d31eade9` |
| `docs/architecture.md` | `2ed2be4845600758da8590d4fac2266b2f1bd2a6892f879cea8d8ac618580471` |
| `docs/testing/phase-1-5-environment-acceptance.md` | `01c8c8dcf3216eec98902bf75d55a8e996afbb7e55bd0b83b7e24d9c5410acab` |
| `docs/testing/acceptance/compose.yml` | `05f58e3b36155de592306178fdc9178f2068e09b7b31a5893b41db71415a42a0` |
| `docs/testing/acceptance/entry.py` | `251a80ad9029e7c620f1b4bddd050fe81bd86c90ab3ca12784cb6a3359c5954f` |
| `frontend/package.json` | `c2e798006effcd8c024feafe1e30c31fd15b0f8911615ded0f4354f68bce2995` |
| `frontend/pnpm-lock.yaml` | `12b7aa609d8d2ea287b81f4279242cbe70f98379994a5b03b5d4d0f7c644cf1d` |
| `frontend/next.config.ts` | `a614867fd5880f0e8648ba14390314bdbe6f65a0f540530c3011b4a6b02b3a5a` |
| `backend/Dockerfile` | `90921cd841df057696d25821fc8000e648024f9a15d3a92cae6188ed970cd3d7` |
| `backend/requirements.txt` | `51e439a19a0c35de142aa44443656edb32669b94bee5655101fdd0f79ef31cd3` |
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
| `docs/testing/phase-2a-acceptance-criteria.md` | `d6a521f67371f192bd6c1167c4d19a100cf84eef3e515164f1fb0441192904c5` |

## 交付后复核

24个本轮写入前哈希对象中，仅用户要求更新的phase-2a-acceptance-criteria.md发生变化，其余23项不变。旧基线所列29项及历史archive-manifest所列12项再次全部匹配；Phase1.5验收记录与原MP4/WAV未修改。三份交付文档UTF-8可读。仅新增GPU计划、GPU准备报告及更新验收标准，未执行任何业务或模型测试。
