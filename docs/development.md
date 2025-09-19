# 开发指南

## 运行环境

- Python 3.11
- Node.js 18+
- PostgreSQL 15
- Redis (可选，用于队列与缓存)

## 本地启动

```bash
make install
make backend
make frontend
```

或使用 Docker：

```bash
cd infrastructure
docker compose up --build
```

## 数据库初始化

```bash
cd backend
python -m app.db.init_db
```

后续建议集成 Alembic 迁移：

```bash
alembic revision --autogenerate -m "create base tables"
alembic upgrade head
```

## 代码规范

- 后端：`ruff` + `mypy` 保持风格与类型检查
- 前端：ESLint + Prettier
- 提交前执行 `make lint`

## 测试

- 后端：`cd backend && pytest`
- ETL：`cd etl && pytest`
- 前端：可接入 Vitest/Playwright（未启用）

## 配置

- 核心环境变量写入 `backend/.env` / `etl/.env`
- ETL 数据源配置：`etl/config/sources.yaml`
