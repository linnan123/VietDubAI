# Phase 1 验证记录

执行日期：2026-10-15。主机为 Windows，Python 3.13.14、Node 24.19.0；容器目标为 Python 3.12、Node 22。

## 已执行

- `python -m compileall -q backend`：通过。
- 在 backend 目录执行 `python -m pytest -q --basetemp "D:\VietDub AI\.test-tmp"`：**8 passed, 1 skipped, 1 warning**，0.94 秒。
- 已覆盖项目与剧集 CRUD、非法名称 / 文件、文件体积与请求总体积限制、不可覆盖原片、重复任务幂等、人工确认、失败重试、过期租约重新投递、mock 适配器。
- Alembic 在 SQLite 验证库执行 `upgrade head` → `check` → `downgrade base` → `upgrade head`：均成功，check 输出 `No new upgrade operations detected.`。
- FastAPI OpenAPI 生成成功，共 10 个路径。
- 前端 `tsc --noEmit`：通过。
- 前端 `next build`：通过，页面静态生成成功，首页 First Load JS 105 kB。
- 前端 `pnpm install --offline --frozen-lockfile`：最终通过，sharp 安装检查成功。

## 失败与修正

- Python 首次下载依赖遇到 Windows 沙箱网络限制，经提升权限重试后安装成功；依赖位于忽略的 `.test-deps`，未修改全局环境。
- 首次从仓库根运行测试，未正确包含 backend 导入路径；改为 README 中的 backend 工作目录，并增加 pytest.ini。
- 测试默认临时目录被 Windows 沙箱限制，改用工作区内独立临时目录并提升权限重跑，最终测试通过。
- Starlette TestClient 对 anyio 的 BlockingPortal 别名产生 1 项弃用警告，不影响本次断言。
- 前端首次 pnpm 安装遇到沙箱链接权限，提升权限后 Next.js 大包下载超时；降低并发并延长超时重试后包下载成功。安装不完整时 TypeScript 检查因 React / Next 模块缺失而失败；依赖完整后重新检查通过。
- pnpm 11 最初因 sharp 安装脚本未批准而返回非零；为项目显式配置 sharp 构建许可。该问题未影响上述 Next.js 构建。
- pnpm 自动插入的许可占位符曾与手动配置形成重复 YAML 键；清除占位符后，冻结锁文件安装成功。

## 未完成的环境验证

- 主机未安装 Docker，无法验证 Compose 启动、PostgreSQL 迁移或 Redis / Celery 跨进程执行。
- 主机未安装 FFmpeg / FFprobe，真实 MP4 → WAV 集成测试自动跳过。该测试已加入测试套件，Docker 镜像包含 FFmpeg，在容器内运行 pytest 将实际执行。
- 当前验证不能证明 PostgreSQL 并发上传、worker 强制终止恢复或浏览器完整交互已通过。

Phase 1 之外的识别、翻译、说话人编辑、配音及成片渲染未实现，未调用付费 API。
