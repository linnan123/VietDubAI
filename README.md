# VietDub AI V0.1

授权短剧的中译越配音制作系统。当前仅实现 Phase 1：项目 / 剧集 CRUD、安全上传、持久化异步媒体分析、WAV 提取、人工确认与最小中文工作台。没有真实 ASR、翻译、TTS 或付费 API 调用。

## Docker 启动

安装 Docker Compose v2，在仓库根目录：

```powershell
Copy-Item .env.example .env
# 编辑 .env 的 POSTGRES_PASSWORD，使用 URL 安全的随机字符串
docker compose up --build
```

打开 http://localhost:3000，API 文档 http://localhost:8000/docs。首次 API 启动执行 Alembic 迁移。创建项目 → 添加剧集 → 上传含音轨的 MP4 → 等待任务 → 人工确认。队列扫描间隔 15 秒，页面 4 秒刷新。失败任务可重试；已上传原片不可替换。删除记录不会删除原片。

```powershell
docker compose exec api pytest -q
docker compose exec api alembic current
docker compose logs worker
docker compose down
```

`down` 保留数据库与媒体卷。不要使用 `down -v`，除非确认永久删除数据。

## 本地开发与测试

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r backend\requirements.txt
Set-Location backend
..\.venv\Scripts\python -m pytest -q
..\.venv\Scripts\python -m alembic upgrade head
```

本地默认 SQLite 只用于开发验证。完整运行需 PostgreSQL、Redis、FFmpeg / FFprobe（在 PATH 中）与 MEDIA_ROOT 配置；设置 DATABASE_URL、REDIS_URL 后启动 uvicorn / celery，与 Compose 命令相同。前端推荐通过 Compose 启动，/api 代理目标为 Docker 服务 api。

前端独立验证使用 Node 22 与 pnpm 11.25.0：在 frontend 目录运行 `pnpm install --frozen-lockfile`、`pnpm typecheck`、`pnpm build`。项目包含依赖锁文件。

架构、恢复策略、安全边界与后续阶段见 [docs/architecture.md](docs/architecture.md)。实际执行测试与环境限制见 [docs/validation.md](docs/validation.md)。
