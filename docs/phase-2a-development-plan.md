# Phase 2A 开发计划（2A-0 设计交付）

日期：2026-10-16，UTC+8。仅技术调查与设计，不授权进入 2A-1。本轮不安装依赖/模型、不下载权重、不调用收费 API、不执行数据库迁移、不修改已验收业务。配套：[验收指标](testing/phase-2a-acceptance-criteria.md)、[环境与哈希基线](testing/phase-2a-environment-readiness.md)。

## 1. 架构检查与复用边界

实际链路：Next.js 15.5.14 / React 19 → /api rewrite → FastAPI → SQLAlchemy → PostgreSQL 16；Redis 7 + Celery 5.5.2；API/Worker 使用 python:3.12-slim + FFmpeg。API 启动自动执行 alembic upgrade head，故后续不能用含新迁移的 API 镜像连接旧库做“只读检查”。前端已有 513 MiB 请求代理缓冲配置，512 MiB 上传的内存风险保留。

| 现有文件/能力 | 可复用内容 | 缺口与处理 |
|---|---|---|
| app/services.py、media.py | 上传流、不可替换源文件、SHA-256、FFprobe、单声道16k PCM WAV、原子输出 | ASR只读WAV；不重新生成或覆盖原WAV/MP4；需记录WAV哈希与时间轴来源 |
| app/models.py、0001_initial.py | Project/Episode、媒体approved、持久化事务 | 仅projects/episodes/jobs三表；无Segment/Speaker/字幕版本/ASRJob。Episode.approved仅表示媒体确认，不表示字幕确认 |
| app/tasks.py | DB发件箱式扫描、条件UPDATE认领、lease、晚确认、丢Worker重投 | 现有Job.episode_id唯一且任务固定处理媒体，不可拿来承载多次ASR；无心跳fencing、退避和次数上限，1950秒时限不能直接套CPU ASR |
| app/providers.py | SpeechRecognizer Protocol 与 MockRecognizer 契约思路 | 只返回固定0–1000ms“你好”且虚构speaker_1；不读音频，不在生产任务调用；需要带元信息的类型化结果及能力标记 |
| main.py、repositories.py | FastAPI/Pydantic/Repository风格、任务查询与人工重试交互 | 无ASR启动、字幕读取/编辑/确认/导出接口；后续新增路由，保留旧契约 |
| tests/test_phase1.py | 9个测试覆盖CRUD、上传、幂等、重试、真实媒体、mock契约 | SQLite及直接task.run不足以验证PostgreSQL并发、Redis投递、模型质量；Phase1.5真实链路证据另存报告 |

后端依赖已精确列版本（FastAPI 0.115.12、SQLAlchemy 2.0.40、Alembic 1.15.2、psycopg 3.2.9等），但不是完整传递依赖哈希锁。基础镜像/服务标签未固定digest。本轮不修改这些文件。当前无身份认证，按本机受信单用户范围设计，不扩大公开部署边界。

## 2. 技术路线与官方调查

建议 **faster-whisper + CTranslate2，CPU/int8，多语言 small，language=zh、task=transcribe、batch=1、单并发**。先 base 多语言冒烟可降低成本；不能用 .en 或默认英语蒸馏模型代替中文模型。small 不达质量门槛才对比 medium 或可选对齐，不默认 large。此为候选选择，尚无本机中文推理结果。

| 方案 | 时间戳/中文 | CPU与依赖 | 决策 |
|---|---|---|---|
| faster-whisper | 多语言Whisper、片段时间戳，可开word_timestamps与Silero VAD；中文word未必对应单个汉字 | CTranslate2推理，预转换模型可不安装PyTorch；PyAV/ONNX Runtime等仍须完整锁定 | 首选，适合句级中文字幕 |
| WhisperX | ASR后加语言相关强制对齐，可提供更细粒度边界；不保证修正识别错误，重叠对白和无字典字符仍有缺失 | 可CPU int8，但多出torch/torchaudio、对齐模型与更多依赖 | 不必须；只有时间误差实测不达标才单独评测，暂不启用说话人分离 |
| 原生PyTorch Whisper | 多语言支持，CPU可运行 | FP32通常较慢；模型与torch驻留、安装体积更大 | 不作为16GB机器默认后端 |

[faster-whisper 官方说明](https://github.com/SYSTRAN/faster-whisper)支持CPU int8、片段/词时间戳、VAD，并声明Python>=3.9；转写返回生成器，性能计时必须耗尽它，否则测到的不是推理耗时。其依赖见[官方requirements](https://github.com/SYSTRAN/faster-whisper/blob/master/requirements.txt)。

[WhisperX 官方仓库](https://github.com/m-bain/whisperX)描述了强制对齐与CPU模式。[当前开发分支元数据](https://github.com/m-bain/whisperX/blob/main/pyproject.toml)为3.8.7rc1，Python>=3.10,<3.14，torch/torchaudio约2.8、torchvision约0.23；这是调查时的动态分支信息，不是已验证安装锁。选择稳定release后必须重新核对其依赖，不能拼接不同版本教程。中文对齐模型也必须固定revision并测试数字、语气词、专名与重叠语音。

[CTranslate2 wheel文档](https://opennmt.net/CTranslate2/installation.html)列出Linux/Windows x86-64和Python>=3.9；Python3.12在范围内，但实际wheel、CPU指令集、glibc与依赖组合仍须构建验证。Windows原生需VC++运行库，Celery以Linux容器为目标。[PyTorch官方](https://pytorch.org/get-started/locally/)提供CPU构建并支持包含3.12的Python范围；没有NVIDIA GPU不妨碍CPU推理。仅WhisperX/转换等需要时才在独立镜像加入匹配的CPU torch/torchaudio，不将GPU wheel和CUDA作为默认依赖。

部署首选Windows Docker Desktop的Linux容器，经[WSL2后端](https://docs.docker.com/desktop/features/wsl/)运行；Windows负责开发与管理，容器负责模型运行。CPU推理不需要GPU直通；WSL资源限额须与API/DB和Windows共同预算。本轮无法验证本机Docker/WSL状态，见环境报告。

中文短剧中的背景音乐、哭喊、混响、口音、重叠对白、角色名和无声幻觉都需要真实素材评价。固定中文识别而非翻译；保留原始输出与归一化文本，避免自动繁简/标点处理隐藏错误；不把Whisper时间戳称为强制对齐精度或说话人识别结果。

## 3. 商业许可清单与风险

代码许可、模型许可、训练素材与实际视频授权分开登记。以下是候选上游声明，最终以选定版本/模型revision附带LICENSE/NOTICE为准；未完成整套发行物审计，不宣称所有传递依赖已获商业许可放行。

| 项目 | 上游声明/依据 | 商用落地要求 |
|---|---|---|
| faster-whisper / CTranslate2 | [MIT](https://github.com/SYSTRAN/faster-whisper)、[MIT](https://github.com/OpenNMT/CTranslate2/blob/master/LICENSE) | 保留版权与许可；核查二进制捆绑依赖 |
| OpenAI Whisper代码与原始权重 | [MIT](https://github.com/openai/whisper#license) | 记录权重来源；不将其他微调权重自动视为同许可证 |
| Systran转换small模型 | [模型卡](https://huggingface.co/Systran/faster-whisper-small) | 固定revision、文件哈希、转换来源与许可证副本，核对原始权重关系 |
| WhisperX | [BSD-2-Clause及元数据](https://github.com/m-bain/whisperX/blob/main/pyproject.toml) | 保留版权/免责声明；历史版本可能不同，逐版核对 |
| PyTorch | [BSD风格及第三方条款](https://github.com/pytorch/pytorch/blob/main/LICENSE) | 核对选定wheel内第三方声明，不能只写“torch免费” |
| Silero VAD | [MIT](https://github.com/snakers4/silero-vad/blob/master/LICENSE) | 确认实际打包VAD版本及权重许可 |
| 候选中文wav2vec2对齐 | [模型卡apache-2.0](https://huggingface.co/jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn) | 仅作为候选，核对选定WhisperX语言映射、revision、NOTICE与来源 |
| PyAV/FFmpeg、ONNX Runtime、tokenizers等 | 随最终锁文件生成SBOM逐项检查 | FFmpeg取决于构建开关和捆绑组件的LGPL/GPL条件；现有镜像也不能因ASR库MIT而豁免 |

Phase2A不需要pyannote说话人分离，不启用可能需账户同意/令牌的受限模型。未来云Provider另做数据流、费用、地域、保留政策和授权评审；密钥只由外部secret运行时注入，不保存在项目、DB、队列参数或日志。

## 4. 独立运行环境与任务协议（设计）

后续新增独立 `asr-worker/`、依赖锁文件、CPU Dockerfile、独立Compose覆盖/项目；不向已验收backend/requirements.txt、旧API/Worker镜像安装torch。2A开发使用新的数据库、Redis实例、队列、网络及媒体副本；旧Phase1.5栈保持原样。新API镜像可在隔离栈增加ASR路由和迁移，不能接旧数据库。最终集成基础业务时另行评审。

新API创建ASRJob事务记录 → 独立dispatcher投递 `asr.cpu` → ASR Worker → 结果校验及新字幕版本事务提交。mock走 `asr.mock` 同一结果契约；未来cloud以provider注册和独立队列接入，默认禁止网络。消息只传job_id，不传秘密、完整字幕或任意用户路径。任务由DB记录决定合法WAV位置和配置。

Provider请求含schema_version、input_sha256、language、model_revision、参数摘要；响应含原始segments、可选words、warnings、model/config指纹、duration与timing_method。生产speaker_id默认为null；mock输出明确标mock，不能计作真实推理。旧list[dict]可通过适配层兼容测试，但不把占位speaker_1当真实声纹。

Worker只读挂载媒体输入，独立可写结果/临时目录；不挂Docker socket，不发布外部端口；非root，限制线程/CPU/内存、prefetch=1、concurrency=1。模型缓存采用模型ID/revision/量化类型目录，授权下载时独占锁、临时目录、校验SHA-256后原子发布manifest；运行时只读cache，local_files_only和离线开关启用，缺缓存明确failed，禁止在任务中静默下载。模型常驻一次，启动readiness确认缓存与加载成功。

ASRJob独立状态：queued → running → succeeded，瞬态故障进入retry_wait → queued，超过预算failed。建议最多3次执行，30/120秒退避加抖动；损坏输入、缺模型、schema错误、OOM不盲目重试，修复配置后人工重试。人工重试只允许failed且无活动租约，保留attempt审计，显式增加预算。

DB唯一幂等指纹=episode+WAV哈希+provider+model_revision+全部解码/分段参数+pipeline_version；相同请求返回已有job，显式重新识别加run_nonce并创建新结果。dispatcher扫描queued/到期retry_wait/过期租约。每次认领生成递增lease_generation与attempt_token，每30秒心跳，建议租约120秒；所有续租/成功/失败提交均须匹配token且未过期，旧Worker无法覆盖新认领结果。全任务时限初始30分钟、仅接收<=10分钟素材；按实测RTF调整。不得沿用媒体任务1950秒硬套6小时音频。DB断连停止提交，租约恢复；结果文件按attempt唯一命名，事务只引用已完整校验的文件。只有完整字幕版本与Job状态同事务提交后才业务成功。

## 5. 数据模型（仅设计）

保留0001及现有Job。建议新迁移0002增加下列表，使用项目现有UUID字符串风格，时间审计使用TIMESTAMPTZ UTC。

| 表 | 关键字段和约束 |
|---|---|
| asr_jobs | id、episode_id FK、input_sha256、provider、model_id/revision、config_json/hash、pipeline_version、idempotency_key UNIQUE、status CHECK、attempts/max_attempts、next_retry_at、lease_until、lease_generation、attempt_token、error_code/脱敏error、created/started/finished_at；索引(status,next_retry_at)、episode |
| asr_attempts | id、job_id FK、attempt_no、token、开始/结束、错误分类、运行指标；UNIQUE(job_id,attempt_no)；保留失败历史 |
| subtitle_versions | id、episode_id FK、version_no、parent_version_id、kind(asr/manual)、source_job_id、status(draft/approved)、content_hash、revision、created_by/at、approved_by/at、input_sha256；UNIQUE(episode_id,version_no)，source_job_id非空时UNIQUE保证一次任务一次结果 |
| subtitle_segments | id、version_id FK、ordinal、lineage_id、start_ms、end_ms、text_zh、raw_text、speaker_id nullable、timing_method、confidence nullable、edited_fields；UNIQUE(version_id,ordinal)，CHECK(start_ms>=0 AND end_ms>start_ms)，整数毫秒 |
| subtitle_heads | episode_id PK/FK、current_version_id、approved_version_id nullable、revision；指针和目标版本必须同集，事务中校验并用复合FK或等效约束保证 |

end_ms<=音频有效时长在事务校验；以WAV采样帧换算音频时长，同时检查不超视频时长（只允许已登记尾差），不能用跨表CHECK冒充数据库保证。ordinal连续从1，start_ms非递减；初版单字幕轨禁止交叠，真实重叠对白标记review_required，人工决定合并，不静默截掉文本。秒→毫秒使用统一十进制四舍五入，块偏移在转换后加原始音频offset；切块重叠区域按时间+文本去重，不重置时间轴。

ASR原始版本与人工版本不可变。人工每次保存创建子版本，记录actor/时间/来源和修改字段，head.revision乐观锁；旧请求返回409。首次ASR结果仅在无head时条件创建head；已有head时重跑只新增候选，不更新head或approved指针，无论已有版本是否标记edited。人工显式选择候选需要当前revision，确认创建批准快照；编辑已批准版本派生新draft，原批准快照与导出仍可复现。并发编辑和ASR完成均锁head或CAS；ASR不得UPDATE人工segments。speaker留空，Phase2A不设计声纹识别业务。

## 6. API与字幕导出（仅设计）

| 接口 | 行为 |
|---|---|
| POST /episodes/{id}/asr-jobs | provider=mock/local_cpu，language固定zh，受控model/config_id，Idempotency-Key；媒体Job成功且approved且WAV有效才202；相同key不同请求409，未满足前置409 |
| GET /asr-jobs/{id} | 状态、attempt、错误码、版本ID、配置指纹、指标；不泄露主机路径 |
| POST /asr-jobs/{id}/retry | failed人工重试，版本化预算审计；活动任务409 |
| GET /episodes/{id}/subtitle-versions | 分页版本列表、来源、当前/批准标记 |
| GET /subtitle-versions/{id} | JSON segments、schema_version、revision、语言和时间轴元信息 |
| POST /subtitle-versions/{id}/revisions | base head revision / If-Match及完整修改，派生不可变manual版本；校验失败422、并发409 |
| POST /episodes/{id}/subtitle-selection | 显式选候选为current，必须expected_revision；不自动批准 |
| POST /subtitle-versions/{id}/approve | 校验完整性及expected_revision，更新approved指针、审计；不复用媒体approve |
| GET /subtitle-versions/{id}/export?format=srt或json | 显式版本快照导出；草稿可导但标明draft，不暗中取最新候选 |

JSON UTF-8，整数start_ms/end_ms，schema_version、episode/version/source哈希、语言、timing_method和segments。SRT UTF-8，连续编号，HH:MM:SS,mmm，保留全局时间轴；屏幕换行在同一cue内部完成，不因字数凭空切时间。初始分段优先原ASR时间边界+静音/标点，超长段只有可信word边界才细分，否则人工检查。建议1–6秒、每行<=20中文可见字符、最多2行；对模型无法精确分割的情形发出质量提示。导出必须防控制字符/非法时间且不丢中文，文件名由服务端安全生成。

## 7. 迁移、回滚与实施顺序

0002仅新增表/索引/约束，不改0001、不复用jobs唯一约束，不改旧媒体approved语义，无历史数据回填。先在全新PG16从0001升级、alembic check、检查DDL与既有记录哈希，验证并发唯一约束；再执行隔离副本的0002→0001→0002演练。新API启动自动迁移的风险需通过独立栈控制，部署时迁移由显式步骤管理。

优先应用回滚：关闭ASR入口/消费者、等待或冻结新任务、切回旧应用，保留新增字幕表。数据回滚有损：先备份新增表及结果并验证恢复，取得明确授权才downgrade，按head→segments→versions→attempts→jobs顺序解除依赖；不得自动DROP有人工字幕的数据，也不恢复旧dump覆盖新业务数据。本轮不创建或执行任何迁移脚本。

Phase2A-1需另行授权后按顺序：补齐Git/可恢复备份 → 恢复并验证Docker/WSL资源 → 建立独立Compose与空DB/媒体副本 → 锁定Python3.12 CPU镜像/依赖/模型许可 → 授权下载small缓存并校验 → 离线真实CPU冒烟及基准 → 复核路线。数据库/API/UI功能可在之后明确批准的子阶段实施，不能把2A-1环境验证默认扩展成全部业务开发。Phase2B翻译、TTS、Phase3渲染均不在本次范围。

## 资源估算的外部参照

[faster-whisper上游CPU基准](https://github.com/SYSTRAN/faster-whisper#small-model-on-cpu)在i7-12700K、8线程、small、beam=5条件下报告int8耗时1分42秒、内存1477MB；其测试材料与本机中文短剧不同，不能直接作为本项目性能保证。采用batch=1和4GiB初始限额是保守设计，实际峰值必须同时计入Celery、解码及结果处理；具体本机测试方法与暂定阈值见验收文档。
