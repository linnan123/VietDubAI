# Phase 2A-0C 环境恢复和GPU验证

## Git基线补齐（最新补充）

用户已提供作者linnan123! / linlovenan@hotmail.com，仓库级配置后创建首个本地基线提交（47个已审查文件）；未配置远端、未push、未改全局配置。完整SHA以git log -1及data/baseline-2a0d-cd332047d6/git-baseline-result.json为准。下方待作者信息/未commit为历史检查状态；该阻塞已解除，资源与原数据核实结论不变。


## Phase 2A-0D 最新结果（2026-10-16 UTC+8，优先于下方0C历史状态）

历史隔离验收栈已安全stop；本轮新建的独立回归栈完成后也stop，全部卷/媒体保留，最终仅vietdubai五个业务服务运行。当前验收库已完成PG16 custom dump及全新restore_2a0d_cd332047d6数据库恢复，四表逐行一致（2项目/4集/4Job/4已确认），备份7259字节，SHA-256为9a712386ee39a6a921d493944ae8e59da923086c4cf1a2f5b4d27acaf536c040。

新机真实HTTP→API→PG/Redis/Celery→FFprobe/FFmpeg链路PASS：并发上传202/409、重复投递幂等、存储故障恢复同Job attempts2成功、损坏输入失败及拒绝确认、成功确认与重启持久化、源MP4/WAV哈希保持。测试复用既有脚本和本地镜像，无业务源码修改。不是浏览器真人点击验收。

.gitignore已补齐敏感/数据库/媒体/模型缓存规则，46个初始候选文件扫描未见高风险模式；仅本地Git初始化完成，作者信息缺失已请求，未首次commit/推送。旧Phase1.5源码21项哈希一致。Windows停止验收栈后可用810248KiB≈0.773GiB，Docker配额7.601GiB，WSL内部可用约6.19GiB，GPU空闲11201MiB；Windows资源门槛仍未通过，不能仅根据容器停止宣布优化完成。报告末轮即时复测可用内存回升至2941164KiB≈2.80GiB，仍低于规划目标，之前采样保留。

历史缺失失败Job和原业务库空状态仍未核实，没有补造记录。备份恢复和真实链路阻塞已解除；Git作者/commit、宿主资源及原数据来源仍待处理，暂不建议进入2A-1。详见[基线与备份报告](phase-2a-baseline-and-backup.md)。下方0C原记录保留作历史，不覆盖Phase1.5验收报告。


日期：2026-10-16，UTC+8；检查约21:24–21:29。项目：D:\VietDub AI。仅环境检查、现有测试与方案；没有进入2A-1，没有安装WhisperX/PyTorch、下载ASR权重或调用付费API。

## 结论

**Docker Engine可用；RTX3060的Linux容器GPU枚举透传PASS；两套基础服务正常响应，现有测试9 passed。完整数据库基线、可恢复备份、Git及资源门槛仍未完成，暂不放行Phase2A-1。**

本轮开始Docker已由外部启动，10个容器已运行；没有由代理执行启动/重启/重建业务服务。初次沙箱访问Docker返回permission denied，经获准在沙箱外复查成功，不能把这次沙箱权限限制当作Engine故障。

## 1. Docker、WSL与存储

| 项目 | 实测 |
|---|---|
| Docker Client/Server | 29.8.2，server可达；desktop-linux context |
| Compose | v5.6.0 |
| WSL | docker-desktop Running/Version2；Ubuntu Stopped/Version2；Ubuntu未启动不妨碍Docker自己的WSL发行版 |
| Engine | Linux x86_64；内核6.18.54.1-microsoft-standard-WSL2；20CPU；7.601GiB内存配额；nvidia runtime可见 |
| 逻辑存储 | /var/lib/docker，overlayfs/containerd snapshotter |
| Windows数据盘 | C:/Users/Administrator/AppData/Local/Docker/wsl/disk/docker_data.vhdx，检查时6616514560字节；main/ext4.vhdx为100663296字节 |
| 设置 | WslEngineEnabled=true；dataFolder/diskImageLocation字段为空，但实际VHDX已定位；未改Docker设置 |
| Compose项目 | vietdubai：running(5)；vietdub-acceptance15-155d3886e3：running(5) |
| 卷 | vietdubai_postgres_data、vietdubai_media_data、vietdub-acceptance15-155d3886e3_postgres_data及两个Redis匿名卷，共5个；未删除/重建 |
| 验收媒体 | D:/VietDub AI/acceptance-media/155d3886e3绑定至/acceptance-media；验收entry.py只读挂载 |

最初9个本地镜像（含1个无tag镜像）；已有API/Worker/Web、Postgres16、Redis7、Python3.12及媒体检查镜像。随后仅新增NVIDIA CUDA测试镜像。现存API镜像ID为sha256:058c2599ac9bb262d1d0c852496852013bb8d3ab14129945437c1d752296ce2d，两套运行中API和本次pytest测试均使用它。没有执行compose up/down、volume rm、数据库初始化/迁移或prune。

## 2. GPU透传实测

Windows `nvidia-smi`：RTX3060，驱动595.95，WDDM，12288MiB，采样时992MiB使用；显示CUDA13.2是驱动能力，不证明安装Toolkit13.2。

按[NVIDIA官方样例](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/sample-workload.html)使用--gpus all验证。选择CUDA12.8.1 base镜像对应前期CUDA12.8候选路线，新驱动可承载该测试；本次实际运行成功。未修改Windows或Clash代理，Docker现有代理仅只读查看。

```powershell
docker pull nvidia/cuda:12.8.1-base-ubuntu22.04
docker run --rm --pull=never --network none --gpus all nvidia/cuda:12.8.1-base-ubuntu22.04 nvidia-smi
```

pull退出0；run退出0。固定镜像digest：`sha256:001469ea0f3dec85a1ca929aeea3b58ae369d4c11228b10aec1f642bb6ca7a6f`。容器输出RTX3060、Driver595.95、总显存12288MiB；首次官方镜像采样929MiB使用，后续归档采样见gpu.json。容器工具NVIDIA-SMI595.61与驱动595.95是不同字段，不将二者混同。容器时间13:27 UTC对应本地21:27 UTC+8。

独立诊断也用已有python:3.12-slim执行相同GPU注入，退出0、943MiB使用。所有测试容器--rm、无业务挂载、无网络；官方镜像下载留在Docker缓存，未删除既有镜像。此处PASS仅指GPU可枚举/驱动接口透传，**没有执行CUDA计算、cuDNN、torch或ASR测试**，不能因此宣布模型兼容性PASS。

## 3. 基础服务和自动化测试

| 服务/检查 | vietdubai业务栈 | Phase1.5验收栈 |
|---|---|---|
| PostgreSQL | healthy；pg_isready退出0；revision0001 | healthy；pg_isready退出0；revision0001 |
| Redis | /0 PONG，退出0 | /15 PONG，退出0 |
| Worker | celery@380bc5503a7a返回pong | acceptance15@b28e54d9d89b返回pong |
| API /health | 8000端口HTTP200 | 18000端口HTTP200 |
| Web首页 | 3000端口HTTP200 | 13000端口HTTP200 |
| Web /api/projects代理 | HTTP200，0项目 | HTTP200，2项目 |
| FFmpeg/FFprobe | 两者版本命令退出0，7.1.5-0+deb13u1 | 相同 |

只读数据库检查使用API现有连接，在每个连接首条SQL执行SET TRANSACTION READ ONLY，再查询revision/项目/剧集/Job，并只读哈希对应文件。没有通过业务写接口创建、编辑、确认或重试记录。Worker ping是控制通道应答，不声称新任务已真实执行。

现有自动化测试在临时容器中运行：

```powershell
docker run --rm --pull=never --network none --entrypoint python vietdubai-api:latest -m pytest -q -p no:cacheprovider --basetemp=/tmp/phase2a0c-tests
```

退出0：**9 passed、1 warning、0 skipped，1.04秒**。warning为Starlette/AnyIO弃用提示。无数据库/媒体卷挂载，测试仅在容器临时文件系统和测试SQLite内执行，包括真实FFmpeg测试；临时容器已自动移除。镜像app代码与运行中验收API的哈希一致，tasks.py和test_phase1.py也与本地字节哈希一致。此测试验证现有代码在新电脑能运行，不能替代真实PostgreSQL并发、Celery实际任务、浏览器上传回归。

## 4. 数据库迁移与媒体一致性

业务库vietdub：projects=0、episodes=0、jobs=0。该事实不能证明数据丢失，也不能证明原业务库本来为空；没有原库快照可比较，故“业务数据完整迁入”仍未确认。

验收库vietdub_acceptance_15：projects=2、episodes=4、jobs=4，四个Job均succeeded，四集approved=true，没有queued/running。所有四个source_path与wav_path文件存在，源MP4实际SHA-256均与DB source_sha256一致；WAV也全部可读并哈希留档。浏览器验收记录episode=2e1af50e-9f2c-4614-af11-0cb0773b6076、job=870546d4-2a6e-47c8-883d-bfa1cf7d359f仍在，attempts=1；故不是全部原数据库未迁入。

但与历史archive-review及最终报告对照：历史5个Job，当前少了预期失败Job `991d40ed-1462-4dc8-837e-4125126a368e` 及episode `dbdb8da7-e2f2-4780-9f09-c46501e3cb0f`。该集损坏MP4 `2034434d-1a63-4b0b-9117-2bbd7612d591.mp4` 仍在验收媒体目录，是当前DB未引用文件。不能判断何时/为何消失，不能宣布完整迁移成功。代理未删除或补写任何记录、未清理该媒体。

旧基线26个代码/报告文件与3个媒体哈希共29项重新核对一致；Phase1.5历史报告未覆盖。当前业务卷/验收绑定已分离，未将验收数据复制进业务库。

### 备份恢复方案（本轮未执行dump/restore）

当前目录data内未找到.dump/.backup/.sql/.tar/.gz类型备份；目录外、原电脑及卷备份未知，不能断言全机无备份。已有日志/截图/JSON不等价于PostgreSQL逻辑备份。

1. 原电脑仍可用时，先只读核查原业务/验收库的revision、记录数与缺失ID，明确是否存在有意删除。分别用PG16的pg_dump -Fc导出到新建UTC时间+UUID目录，独占创建禁止覆盖；配置秘密单独受控保存。新电脑现有库也先独立备份，禁止用原库直接覆盖。
2. 若需要数据库与媒体一致恢复，取得维护窗口后阻止新写入并等待在途任务完成，配对dump与逐文件SHA-256媒体副本；本轮没有停服务/停写。不能直接复制运行中的PGDATA。
3. 检查dump退出码、pg_restore --list、哈希，再在全新隔离PG16/Redis/媒体目标恢复。核验旧5个Job与approved、FK、revision、源文件哈希；恢复测试前避免启动会自动迁移的API。验证完毕后另行确认切换/合并，不覆盖当前数据。
4. 若只找回媒体，可重新计算SHA-256、FFprobe元数据并提取新的WAV副本；这些是派生技术事实。项目归属/原ID、人工approved决策、Job创建时间/attempts/error及历史事务关系不能从MP4推导，必须来自可信数据库备份。现有证据可辅助人工核对或在**新隔离库**显式重建部分演示样本，但不能冒充原始数据库恢复，更不能伪造原审批审计。
5. 没有原备份时，需用户明确确认丢失范围及是否接受隔离重建基线；在此之前缺失失败记录和业务空库保持BLOCKED，不补写。当前四个成功记录的存在证明部分状态保留，但无法证明完整迁移过程或时间点。

## 5. Git与秘密信息检查

项目D:/VietDub AI与父目录D:/均无.git，未发现项目子目录可用.git/config；此前git status/rev-parse也提示非仓库。源码/文档中的GitHub链接均为上游依赖引用，没有识别到VietDub项目远端地址，不能由此假定GitHub账户没有远端仓库；需要原仓库URL或原电脑.git备份。未访问未知远端、未更改全局Git配置、未init/commit/push。

.gitignore已排除.env、.venv、node_modules、.next、__pycache__、.pytest_cache、data、acceptance-media、*.db和测试临时目录。**不足**：未通用排除.env.*、密钥/证书文件、其他路径媒体、*.sqlite/备份、模型缓存/权重（如models、.cache、*.pt/*.pth/*.safetensors/*.onnx）；本轮按只检查范围不修改规则。

对41个候选文本文件进行启发式秘密扫描，不输出匹配值。结果：.env有密码配置且已忽略；.env.example为显式示例占位；两个Compose的命中为环境变量模板。未命中所设模式的私钥或供应商token。扫描不是完整审计：排除了data、媒体、依赖、构建和缓存，并跳过大文件/非候选扩展；被忽略的data中存在验收env，必须持续受控，不能强制add。无凭据被输出到报告或提交。

安全初始化方案：先确认原远端/备份是否可恢复；无基线再经确认初始化。先扩充.gitignore保留安全.env.example例外，审查全部候选路径及二进制、使用更完整秘密扫描工具，随后只按明确源码白名单暂存，检查cached diff/文件清单与秘密扫描结果，最后获得明确确认才首次commit；push另行确认目标。不要git add .，不要把原始视频/模型/数据库/验收env/证据日志自动提交。

## 6. 资源风险

开始C盘剩16272076800字节≈15.15GiB，结束采样33142005760字节≈30.87GiB；D盘结束剩330728476672字节≈308.02GiB。C盘期间出现明显外部变化，本轮没有清理/删除文件，不推断空间增长原因。Docker VHDX仍在C，不能用D的余量保证Docker拉取/构建空间；建议后续正式GPU镜像准备前核实增长并保证所选存储>=40GiB余量，搬迁Docker磁盘需单独备份与确认，不本轮执行。

运行两套栈时宿主可用1499736KiB≈1.43GiB（总可见15.69GiB），Docker配额7.601GiB；这是目前更紧的资源阻塞。12GB显存不替代主内存。后续可由用户关闭高占用应用或确认停用不需要的栈后再测，GPU开发前目标宿主可用>=8GiB、推理中保留余量；不能擅自停止现有服务来达标，也不本轮修改WSL配额。

## 7. 可继承证据与需重测项

可继承：Phase1.5原PASS的历史结论、原测试日志/浏览器人工记录、未变更代码和媒体哈希、既有接口与阶段设计。不能继承为新机PASS：数据库完整恢复、灾备可用性、浏览器重新上传/人工确认、PG并发/真实Celery投递恢复、服务重启持久性、新GPU计算或ASR兼容性。

本轮新测：Docker/WSL运行、GPU容器枚举、PG只读状态/媒体核对、Redis/Worker应答、API/Web/代理HTTP200、FFmpeg工具、隔离9测试。未进行写入式端到端测试，遵守现有数据保护要求；后续使用明确隔离新库/媒体做真实队列与浏览器回归，不覆盖旧验收记录。

## 8. 命令、证据和放行条件

命令与退出码原始记录在data/recovery-2a0c-7a554fd883：checks.json（PG/Redis/Worker/工具/pytest/HTTP）、extra.json（GPU补充/容器卷项目/代理）、gpu.json（官方CUDA验证及digest）、secret-scan.json（仅路径/行号/分类）、protected-hashes.json，以及对应辅助脚本。均位于已忽略data目录，不含秘密匹配值；辅助脚本不修改业务数据库。主报告为本轮唯一新增docs文件。

docker info、compose version、wsl列表与库存检查在获准沙箱外成功；GPU pull/run退出0；两个pg_isready、只读数据库查询、Redis ping、Worker ping、FFmpeg/FFprobe及pytest均退出0；HTTP与代理200。首次沙箱内Docker权限失败是已解决的工具访问限制，不列产品故障。

剩余BLOCKED：

- 原验收库缺失一条负向记录、业务库空状态缺少原库对照；完整迁移和备份恢复演练未确认。
- Git来源/可恢复远端未定位，未建立已批准的版本基线；ignore与秘密审查需在首次提交前补齐。
- 当前主内存余量不足，Docker C盘存储需规划；未达到GPU开发资源门槛。
- 新电脑真实队列/浏览器写入式回归尚未在独立环境重测。

**暂不放行2A-1。** GPU透传这一阻塞已解除；下一步仅在上述基线/资源问题处理并获用户明确授权后进行独立GPU依赖和模型准备。本轮无down -v、volume删除、数据库重置/迁移、源媒体覆盖、代理修改、Git提交或AI模型安装。完成后停止。
