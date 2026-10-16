# Phase 2A-0D Git基线、备份恢复和新机回归

## Git身份补齐与首次提交（最新补充）

用户已明确提供并授权作者姓名 `linnan123!`、邮箱 `linlovenan@hotmail.com`；仅设置本仓库user.name/user.email，未改全局Git。经复核47项白名单及暂存秘密扫描后，以 `chore: establish verified Phase 1.5 and Phase 2A-0D baseline` 创建首次本地提交；无远端、无push。提交完整SHA与核验结果另存忽略目录data/baseline-2a0d-cd332047d6/git-baseline-result.json，并可通过git log -1核对，避免文档自引用提交哈希。下文“作者信息待补/未提交”为此前检查时的历史状态，已由本节更新；Git身份阻塞解除，资源与原数据来源问题仍未解除，仍未进入2A-1。


日期：2026-10-16（UTC+8）。本轮只做资源优化、本地Git准备、数据库逻辑备份/隔离恢复和现有业务回归；未进入2A-1，未安装WhisperX/PyTorch或下载模型。

## 执行结论

- 历史验收栈与本轮新回归栈均已使用对应Compose项目stop，全部卷/媒体/容器保留，业务vietdubai五服务持续运行。
- 验收库逻辑备份及新数据库恢复演练PASS，全部四张表逐行一致；这是当前4个成功Job快照，不补造历史缺失失败Job。
- 独立新库/Redis/网络/媒体目录的真实端到端回归PASS，含失败恢复、重复投递、确认接口和重启持久化。
- .gitignore已补齐，候选文件扫描未见高风险模式；仅本地git init已完成。作者身份缺失，已向用户请求姓名/邮箱；**尚未首次commit，没有commit SHA，不设置虚假身份**。后续只按用户提供信息设置仓库级user.name/user.email。
- 宿主内存最终复测约2.80GiB可用，仍不足，原业务库状态和历史缺失记录仍未核实，暂不建议进入2A-1。

## 1. 停止范围和资源

业务项目vietdubai来自根docker-compose.yml，使用vietdubai_postgres_data / vietdubai_media_data及vietdubai_default网络。历史项目vietdub-acceptance15-155d3886e3来自docs/testing/acceptance/compose.yml，使用独立PG卷、Redis匿名卷、D盘acceptance-media/155d3886e3绑定目录及独立default/ingress网络。网络/挂载inspect未见与业务共享；停止前历史任务无queued/running。

停止前Docker stats：历史Web179.3MiB、API98.07MiB、Worker164.2MiB、PG45.98MiB、Redis15.94MiB，合计约503.5MiB。先完成备份/恢复，再执行：

```powershell
docker compose --project-name vietdub-acceptance15-155d3886e3 --env-file "D:/VietDub AI/data/acceptance-final/155d3886e3/acceptance.env" -f "D:/VietDub AI/docs/testing/acceptance/compose.yml" stop
```

本轮新项目vietdub-acceptance15-2a0d-cd332047d6使用独立配置参数与新媒体目录acceptance-media/2a0d-cd332047d6，测试完成后也只stop。15个容器最终5个业务running、10个验收/回归Exited(0)；7个卷全部保留。恢复项目可按对应regression-context或历史参数执行start，需先确认13000/18000端口不被另一验收栈占用；不要同时启动这两个共用端口的验收栈。

停止后业务容器合计约400MiB；Docker配额8161988608字节≈7.601GiB。Windows总可见16457144KiB≈15.69GiB，可用810248KiB≈0.773GiB（即时采样，非稳定上限）。WSL /proc/meminfo：MemAvailable6492964KiB≈6.19GiB、Cached2381036KiB≈2.27GiB，swap使用0；vmmemWSL工作集约4411.9MiB。说明部分内存仍驻留WSL/缓存，停止容器不保证立刻归还Windows。没有kill其他应用、drop_caches、重启WSL或修改.wslconfig。

GPU采样：RTX3060，总12288MiB，已用915MiB、空闲11201MiB；沿用0C官方CUDA容器枚举PASS，本轮未重复模型测试。C盘约30.79GiB剩余、D盘约307.95GiB剩余（均动态）。Docker虚拟盘C:/Users/Administrator/AppData/Local/Docker/wsl/disk/docker_data.vhdx为6784286720字节≈6.32GiB；system df中镜像2.861GB、构建缓存1.993GB、7卷152.5MB。虚拟盘大小不等于应用有效数据，未移动/压缩/清理任何盘或卷。

## 2. 数据库备份与恢复证据

源：历史验收PostgreSQL容器vietdub-acceptance15-155d3886e3-postgres-1，库vietdub_acceptance_15，角色acceptance15。备份在本轮唯一新目录独占创建，未覆盖既有备份。

- 文件：data/baseline-2a0d-cd332047d6/acceptance15.dump
- PostgreSQL pg_dump -Fc，退出0；7259字节。
- SHA-256：`9a712386ee39a6a921d493944ae8e59da923086c4cf1a2f5b4d27acaf536c040`
- pg_restore --list成功，退出0；备份字节已读回并参与实际恢复。
- 全新目标库：`restore_2a0d_cd332047d6`，位于同一PG16服务器，createdb只创建此新库，pg_restore --exit-on-error -d该目标退出0；没有向原库restore，也没有drop数据库。
- 对源和目标分别在READ ONLY事务中按主键排序读取alembic_version/projects/episodes/jobs全字段，JSON逐行完全一致：revision0001，项目2、剧集4、Job4、approved=true共4集。

恢复数据库随历史PG卷保留；历史栈停止后暂不可访问，但没有删除。备份在D盘，PG卷在C盘，两者位置不同；尚无另一设备/离线副本，逻辑dump本身也不包含媒体或角色全局对象。当前备份是无在途任务时的数据库快照及既有媒体哈希核对，不宣称已完成整套跨系统灾备演练。建议后续把dump、媒体副本、哈希和受控配置复制到独立设备再恢复一次，不将.env或dump提交Git。

缺失历史Job991d40ed-1462-4dc8-837e-4125126a368e与episode dbdb8da7-e2f2-4780-9f09-c46501e3cb0f：历史最终报告/JSON仍记载预期损坏媒体失败，当前库没有该行，对应MP4仍在磁盘。没有依据判定删除时间或原因；本次恢复忠实保留当前4个Job，不从证据伪造第五行。

业务vietdub库上轮只读检查项目/剧集/Job均0；没有原电脑快照证明其原本为空，标记**原业务数据状态未核实**，不因新回归成功视为已恢复。原电脑PG备份/只读对照或用户明确接受当前快照作为新基线仍待后续决定。

## 3. 新电脑真实链路回归

复用data/acceptance-final的isolation.py和run_chain.py，复制到本轮忽略目录，只替换context路径及FFprobe调用位置；不修改backend业务逻辑或历史脚本。新Compose项目名、数据库卷、Redis、网络、媒体目录均与旧栈不同。虽然使用相同内部DB名称、Redis /15与队列acceptance15，实际不同实例/网络，隔离检查在空库下确认通过。只使用已有镜像，--no-build --pull never；新空库正常运行既有0001初始化，不触碰旧数据库。

主机Python首次调用缺httpx，改用项目已有.test-deps经PYTHONPATH加载后运行，没有安装新依赖。完整脚本退出0并写REAL_CHAIN_PASS。停止归档脚本曾遇GBK读取中文JSON失败，明确指定UTF-8后成功；这两项是辅助脚本运行修正，未改变业务。

| 项目 | 实测证据 |
|---|---|
| 真MP4上传/并发 | 同集并发上传返回202/409，仅一个Job |
| FFprobe/FFmpeg | 20033ms视频；WAV pcm_s16le/16000Hz/单声道/16bit，320250帧、20.015625秒 |
| 真实Celery | 新Redis/队列实际处理，首个Job succeeded/attempts1 |
| 幂等 | 成功Job重复投递两次，Worker消费完成；attempts仍1，WAV哈希不变 |
| 故障重试 | 仅临时改名新测试媒体副本目录触发失败；恢复目录后同Job重试succeeded/attempts2 |
| 负向样本 | 本轮新建损坏MP4失败，重试仍failed/attempts2；失败集确认返回409 |
| 确认保护 | 成功集approve返回200，重复确认一致；批准前无成功媒体时409 |
| 持久化 | 新API/Worker重启后，成功/失败状态、attempts、approved及WAV哈希保持 |
| 源MP4 | 测试源和所有有效上传副本SHA-256均9623ec9c1fd5aaf77b5f7c6f9c59cc34e8c5d1222806fd80915991df90590df1 |
| 原始test/temp.mp4 | d165f26cdbf7e60d6c7c72d95456e8e157e08e17e257eaa6b32901dca6c4a9ea保持 |
| WAV | a08f51209ca77e824bc16d7c293d84618d79cd272b542ca0eeebf407c16684d8 |

项目68b5b6a3-b4da-4751-ac06-d5728d75d19f；成功Job dcc03290-84f5-45b6-87f6-e0d22798467f；故障恢复Job6487f901-32f7-4bdb-b1c0-7bfdf18916f7；负向Job d2726cac-fc5c-41bb-a372-b4c1ab3b81e4。本轮确认由HTTP调用审批接口验证，不宣称真人浏览器点击；浏览器交互验收仍为历史证据。本轮不重跑已在0C通过的9项测试，因为未修改业务源码；本轮补充的是原来缺少的真实PG/Redis/Celery和重启链路。

## 4. Git与可核对源码基线

起始项目/父目录无Git，未找到项目远端。21个Phase1.5基线源码/配置（包括backend、前端关键文件、根Compose和README）全部与此前哈希快照一致；现有代码可核对，但没有原电脑Git历史，不能称恢复了原commit。补充.gitignore后，本轮只初始化本地仓库，不配置远端、不push、不改全局Git。

补充排除.env.*（保留.env.example）、私钥/凭据、数据库与dump/备份、视频音频、models/model-cache/.cache及权重、虚拟环境和构建产物。git check-ignore验证实际.env、新测试env、MP4/WAV、模型和dump路径均被忽略；.env.example为change-this-local-password占位，无真实凭据。

46个初始候选文本文件按私钥、常见供应商token和字面秘密模式扫描无高风险命中，历史0C扫描的Compose命中仅变量模板；秘密实际env及备份只留忽略目录。新增本文后候选47项，提交前仍复扫暂存内容。启发式扫描不证明绝对无秘密；不纳入媒体、数据库、模型、data证据或二进制。

Windows目录所有者为Administrators导致Git safe.directory检查；所有后续命令使用进程级 `git -c safe.directory="D:/VietDub AI" ...`，没有写全局例外。作者user.name/user.email未配置，已请求用户提供；在回复前不擅设身份、不commit。

拟纳入首次版本管理的完整文件清单：

- `.env.example`
- `.gitignore`
- `README.md`
- `backend/.dockerignore`
- `backend/Dockerfile`
- `backend/alembic.ini`
- `backend/app/__init__.py`
- `backend/app/db.py`
- `backend/app/main.py`
- `backend/app/media.py`
- `backend/app/middleware.py`
- `backend/app/models.py`
- `backend/app/providers.py`
- `backend/app/repositories.py`
- `backend/app/services.py`
- `backend/app/tasks.py`
- `backend/migrations/env.py`
- `backend/migrations/versions/0001_initial.py`
- `backend/pytest.ini`
- `backend/requirements.txt`
- `backend/tests/test_phase1.py`
- `docker-compose.yml`
- `docs/architecture.md`
- `docs/phase-2a-development-plan.md`
- `docs/phase-2a-gpu-development-plan.md`
- `docs/testing/acceptance/compose.yml`
- `docs/testing/acceptance/entry.py`
- `docs/testing/phase-1-5-environment-acceptance.md`
- `docs/testing/phase-2a-acceptance-criteria.md`
- `docs/testing/phase-2a-baseline-and-backup.md`
- `docs/testing/phase-2a-environment-readiness.md`
- `docs/testing/phase-2a-environment-recovery.md`
- `docs/testing/phase-2a-gpu-readiness.md`
- `docs/validation.md`
- `frontend/.dockerignore`
- `frontend/Dockerfile`
- `frontend/app/globals.css`
- `frontend/app/layout.tsx`
- `frontend/app/page.tsx`
- `frontend/next-env.d.ts`
- `frontend/next.config.ts`
- `frontend/package.json`
- `frontend/pnpm-lock.yaml`
- `frontend/pnpm-workspace.yaml`
- `frontend/postcss.config.js`
- `frontend/tailwind.config.ts`
- `frontend/tsconfig.json`

## 5. 下一阶段资源建议与放行

D盘独立模型缓存建议D:/VietDub AI/model-cache（已忽略），后续挂载到独立GPU Worker只读/cache；授权下载阶段写临时目录、校验manifest后发布。ASR/中文对齐/VAD分别固定revision；不把cache打进API镜像。不移动现有Docker VHDX；GPU镜像层仍会占C盘，正式构建前需要预留至少40GiB或另行规划Docker存储。

单套业务容器当前约400MiB只是Docker stats工作集，不含Windows、Docker虚拟机、镜像缓存及上传缓冲峰值。GPU Worker候选主内存上限4GiB起步、确有需要才升6GiB；CPU线程4、Celery concurrency1/prefetch1、每GPU一个推理任务；small FP16 batch4初测，OOM按独立配置降batch2/1，不静默CPU回退。显存全卡峰值目标<=10GiB，给桌面留余量。16GB机器不能默认业务峰值+6GiB Worker+Windows能同时满足，需实测；WSL当前7.601GiB配额也应与宿主余量共同核算。

目前Windows可用约0.77GiB，**资源门槛仍未通过**。建议用户关闭无需的浏览器/其他应用后重测；若要释放WSL驻留缓存或重启Docker，需要另行安排业务停机窗口，不擅自停业务栈或更改全局配置。GPU准备前目标宿主可用>=8GiB、运行中持续留余量，实际阈值可在有测量依据时评审，但不能以WSL内部可用量替代Windows余量。

已解除：Docker/GPU容器透传、当前验收库备份可恢复、新机真实端到端链路。待解决：作者信息与首个commit、宿主内存/C盘构建余量、原业务库空状态/缺失负向历史行的来源核实、异机备份副本。**暂不建议进入Phase2A-1**；本轮完成后停止。

## 证据路径

所有原始证据位于data/baseline-2a0d-cd332047d6（忽略、不提交）：backup-result.json、backup-commands.json、database-snapshots.json、acceptance15.dump、regression-context.json、isolation.json、chain-events.json、chain-result.json、stop-regression.log、final-containers.log、final-volumes.log、final-resources-after-stop.json、git-scan.json、git-candidate-files.json、before-hashes.json、integrity-result.json及辅助脚本。regression.env为秘密文件，不读取进报告、不提交。数据库恢复演练仅写新库；故障注入只改本轮媒体副本的临时目录名并已恢复。

## 暂存复核

47项白名单文件已暂存，逐项读取Git索引内容复扫，未命中所设高风险模式；没有媒体、dump、秘密env或data证据进入索引。作者姓名/邮箱仍未收到，尚未commit。默认git diff --cached --check报告历史Phase1.5 Markdown两处行末双空格（755/756行，为已有Markdown换行）；按保护历史记录要求未修改，不能宣称默认空白检查全通过。Git工作区LF/CRLF提示未触发源码覆盖；进程级忽略Markdown行末空格的空白检查另行运行，不更改全局配置。原有57个源码/文档/媒体对象仅获准更新的环境恢复报告改变，其余保持字节哈希一致。

## 最终即时复测

报告整理后再次只读检查：Windows FreePhysicalMemory=2941164KiB≈2.80GiB（较停止后0.77GiB回升，说明内存会动态回收）；仍低于先前>=8GiB准备目标。当前业务库READ ONLY计数仍0/0/0，仅vietdubai五服务运行。保留先前采样，不将2.80GiB写成稳定保证；进入2A-1结论仍为暂缓。作者信息未收到，47文件已暂存且无commit SHA；排除历史Markdown双空格后的进程级空白检查通过。
