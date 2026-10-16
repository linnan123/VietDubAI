# Phase 2A-0 GPU 开发计划

2026-10-16，UTC+8。硬件目标：RTX3060 12GB、i7-12700、16GB RAM、Windows + Docker Desktop + WSL2。新GPU方案替代旧文档的CPU-only默认假设；旧CPU路线仅保留诊断/可选备选价值。仅检查与设计，不进入2A-1，不安装大型依赖或下载模型。

## 路线决定与WhisperX可行性

优先 **WhisperX中文识别+中文强制对齐**，关闭diarization；**faster-whisper GPU**作依赖或对齐不满足要求时的备选。同一字幕数据契约保留mock，不让现有9项测试依赖GPU。WhisperX底层ASR通常已使用faster-whisper/CTranslate2，二者不是完全独立的识别模型；新增价值主要是VAD与对齐流程。

初测small多语言、cuda、float16、batch_size=4、language=zh、task=transcribe、diarization=false；参数只是起点，必须记录beam/VAD/上下文等完整配置。small不是small.en；中文角色/数字/口音与音乐、重叠对白需真实语料判断。对齐不是纠错，错误文字也可能被强行映射到音频；必须报告缺失边界，不能伪造逐字时间戳。

[WhisperX v3.7.4对齐源码](https://github.com/m-bain/whisperX/blob/v3.7.4/whisperx/alignment.py)明确处理无空格中文，zh默认映射到 `jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn`。必须另行授权取得对齐权重并固定revision；模型许可见[模型卡](https://huggingface.co/jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn)。首轮ASR fp16不代表对齐模型也必须fp16；对齐先采用所选实现默认精度，单独记录与验证，避免为了统一精度损害稳定性。

12GB显存对small/batch4是合理试验起点，但没有本机推理证据，不承诺峰值。ASR与对齐顺序运行，优先阶段性卸载不使用的模型、回收CT2对象/torch缓存并测实际显存，不在同一GPU同时执行多个任务。medium/large不是默认扩展项。若WhisperX依赖或对齐失败，明确记录失败并评测faster-whisper GPU片段/word时间戳；不能静默降级后声称WhisperX对齐通过。

## 推荐兼容组合（候选，尚未安装验证）

| 层 | 首轮固定候选 | 选择依据/验证 |
|---|---|---|
| 宿主驱动 | 当前595.95，保持现状 | nvidia-smi可见3060；CUDA13.2是驱动能力，不要求安装13.2 Toolkit |
| 系统 | WSL2 Linux x86-64容器，Python3.12 | 避开Windows原生Celery/动态库差异；独立镜像，不改旧backend Dockerfile |
| WhisperX | 3.7.4稳定tag | 其版本元数据要求torch/torchaudio~=2.8.0、CT2>=4.5；不选动态main的3.8.7rc1 |
| PyTorch | torch2.8.0 + torchaudio2.8.0，cu128 wheel | 官方有此CUDA12.8组合；torchvision若解析器确需则0.23.0，不默认加无关包 |
| CUDA用户态 | CUDA12.8、cuBLAS12、cuDNN9 | 由受控容器/依赖锁提供并记录实际库路径、补丁版本；不用宿主Toolkit充当容器库 |
| CTranslate2 | 4.6.0候选 | 满足WhisperX范围；4.5起cuDNN9，不能装cuDNN8；检查实际支持float16与小模型GPU运算 |
| faster-whisper | 1.2.0候选 | 满足WhisperX>=1.1.1；其CT2范围>=4,<5与4.6一致 |
| 传递依赖 | 完整hash lock后冻结 | v3.7.4限制Python3.12下numpy>=2.0.2,<2.1、av<16、pandas<2.3、pyannote-audio<4；不能不加约束装最新依赖 |

这是一组由官方元数据交集推导的**可验证候选**，不是官方整套认证，也不是本机已验证组合。torch和CT2使用不同运行时，torch.cuda.is_available()成功不保证CT2能找到cuDNN/cuBLAS。构建阶段需pip check、全部导入、动态库加载与无权重CUDA张量测试，记录torch.version.cuda及cuDNN版本；随后授权模型实测。运行阶段禁止自动升级解析器结果。若需更新较旧依赖的安全补丁，重新评审兼容矩阵并锁定后验证，不直接追latest。

依据：[WhisperX v3.7.4 pyproject](https://github.com/m-bain/whisperX/blob/v3.7.4/pyproject.toml)、[PyTorch2.8官方cu128组合](https://pytorch.org/get-started/previous-versions/#v2-8-0)、[CT2 v4.6变更及4.5 cuDNN9要求](https://github.com/OpenNMT/CTranslate2/blob/v4.6.0/CHANGELOG.md)、[faster-whisper1.2依赖](https://github.com/SYSTRAN/faster-whisper/blob/v1.2.0/requirements.txt)。[NVIDIA兼容文档](https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html)说明较新驱动与较旧CUDA运行时的兼容原则；本机实际容器仍需验证。[Docker官方GPU支持](https://docs.docker.com/desktop/features/gpu/)要求Windows的WSL2后端；本机Engine目前不可达。

## 显存、内存与磁盘预算

工程估计，非实测：small/batch4 ASR及分阶段中文对齐预留GPU峰值4–8GiB，控制全卡已用峰值<=10GiB，至少留下约2GiB桌面/波动空间。初测前空闲显存目标>=8GiB；显存变化需全过程采样。torch memory_allocated/reserved只含torch分配，漏掉CT2和其他进程，不能作为唯一峰值。

宿主16GB是更紧约束：当前约6GiB可用且Docker未启动；推理前需关闭高占用应用并测全栈。规划ASR容器上限6GiB、CPU线程4、单进程推理；WSL总量以约8–10GiB为候选，须依据Windows余量和旧栈共同调整，不本轮写.wslconfig。GPU显存不会替代解码/模型加载所需主内存。缓存/镜像/构建临时文件建议D盘预留>=40GiB；当前C只剩约14.46GiB，应先核实Docker虚拟盘和系统临时路径，不擅自搬盘。

OOM不盲目重试相同配置：记录错误与峰值，释放进程，再按预先审查配置batch4→2→1；每种配置形成新指纹/新任务，保留失败审计，最多一次资源恢复尝试。仍失败则终止并报告；不得静默改CPU/int8或模型。诊断torch.cuda.empty_cache不能释放CT2对象或所有外部显存。

## 独立GPU Worker架构

现有Next.js→FastAPI→SQLAlchemy/PostgreSQL，Redis/Celery媒体Worker及0001迁移保持原状。后续新建asr-worker GPU镜像、独立依赖锁与Compose项目；开发/验收新建PG、Redis、网络、媒体副本。旧Phase1.5环境不挂入新API；当前API启动自动upgrade head，不能为查看数据直接连接原库启动新镜像。

新API在事务写asr_jobs → 独立ASR dispatcher → `asr.gpu`队列 → GPU Worker只读16kHz WAV → 校验 → 一次事务提交候选字幕版本和任务成功。mock使用`asr.mock`且无GPU device reservation；未来cloud队列单独接入，默认未启用，秘密只由项目外secret注入。队列名隔离还需broker实例/网络隔离，不能误消费旧media或acceptance15队列。新dispatcher不导入/调用现有媒体process。

GPU服务限定一个副本、单个GPU、Celery `concurrency=1`、prefetch=1。选择Linux prefork时不得父进程预先初始化CUDA；在唯一子进程内惰性加载ASR/对齐，避免fork后CUDA错误。pool=solo虽简便但不能依赖prefork式硬超时；若选择solo需额外子进程看门狗及杀进程恢复测试，首选前者。媒体Worker不申请GPU。指定GPU UUID/设备并用每GPU租约防误扩容竞争，任务租约本身不能阻止两个误启动副本各占一个任务。

Provider契约：mock / whisperx_gpu / faster_whisper_gpu，返回schema_version、输入哈希、语言、原始segments、可选word/char边界、timing_method、warnings、模型/对齐revision、config_hash和运行指标。没有说话人分离时speaker_id=null，现有mock的speaker_1只为占位不视为识别能力。部署mock不导入torch；GPU模块懒加载，CI无需GPU或权重。

缓存目录按模型ID/revision/精度划分，包含ASR、中文对齐、VAD、tokenizer及额外运行资产的完整manifest。授权准备时锁+临时目录+SHA-256校验后原子发布；运行只读、本地路径、离线模式，缺任何资产即MODEL_CACHE_MISSING，禁止任务隐式联网。WhisperX即使关闭diarization也可能导入pyannote依赖并加载VAD，必须显式选择和预置VAD；禁用diarization不等于无需VAD/对齐权重或完全不安装pyannote。

## 持久化、人工保护、接口与回滚

保留现有每集唯一的媒体Job；新增asr_jobs、asr_attempts、subtitle_versions、subtitle_segments、subtitle_heads。复用[原2A详细数据/API设计](phase-2a-development-plan.md)的字段/约束，GPU方案覆盖其中默认CPU provider及资源参数：

- ASRJob幂等键含episode/WAV哈希/provider/ASR与对齐模型revision/精度/batch/VAD/beam/分段参数/pipeline_version；重复消息最多一个结果，显式重跑带nonce。queued→running→succeeded，瞬态失败retry_wait→queued，最多3次执行、30/120秒退避；缺缓存、非法输入、CUDA版本冲突、OOM不做普通自动重试。
- 30秒心跳、120秒租约、15秒扫描、递增generation和attempt_token fencing；续租和所有提交匹配活跃token，旧Worker迟到不能写结果。硬超时由独立子进程退出保障，visibility timeout需大于最长任务；初始只接<=10分钟音频，总时限30分钟，后续以测量冻结。
- Segment整数start_ms/end_ms、start>=0、end>start，ordinal版本内唯一连续；校验WAV时长与视频尾差，统一秒转毫秒和切块offset。非重叠字幕轨，重叠对白进入人工review；缺失逐字对齐可保留片段边界但必须标timing_method/缺失，不假造。
- 字幕不可变版本，ASR重跑只新增候选；人工编辑派生manual版本，head.revision CAS，冲突409，批准指针独立，media approved语义不变。任务完成不能移动已有head/approved，更不能覆盖人工文字/时间。
- 新增ASR启动/查询/failed重试、字幕版本读取/人工修订/显式选择/批准、固定版本SRT/JSON导出接口。SRT UTF-8/连续编号/HH:MM:SS,mmm；JSON整数毫秒含schema与来源哈希；换行不伪造时间、导出旧批准快照内容保持一致。

迁移仅设计0002新增表/索引/FK/CHECK，不修改0001和jobs唯一约束；仅后续隔离PG16测试upgrade/check、并发约束和副本降级再升级。应用回滚优先停ASR入口/消费者、切旧应用并保留新增表。数据downgrade会丢字幕，必须备份/恢复验证并明确批准后只在指定副本演练；不自动DROP人工数据，不以旧dump覆盖现库。本轮未生成迁移脚本。

## 许可与实施门槛

WhisperX3.7.4声明BSD-2-Clause；faster-whisper/CTranslate2 MIT；Whisper原始代码/权重MIT；中文对齐候选模型卡Apache2.0。逐revision保存许可证/NOTICE，检查VAD、pyannote、PyTorch和FFmpeg/PyAV等完整SBOM与捆绑条款，不能由一个库的许可推断所有模型商用已放行。关闭diarization，不调用需token的说话人服务；无API密钥写项目。真实素材版权与模型许可分别核对。

顺序：人工启动并核验Docker→只读清点Phase1.5迁移与可恢复备份/Git→无模型容器GPU枚举→确认内存/磁盘预算→用户另行授权2A-1→新镜像依赖锁及无权重CUDA计算验证→授权缓存权重→真实ASR/对齐与faster-whisper对照。数据库/API/UI业务实施仍需对应阶段范围，不由环境通过自动展开。当前只能完成设计，尚不能判定可以直接进入2A-1；见[GPU准备报告](testing/phase-2a-gpu-readiness.md)。
