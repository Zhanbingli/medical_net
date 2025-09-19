# 架构概览

## 总体设计

平台由三层组成：

1. **数据层**：PostgreSQL 存储药品、疾病、相互作用以及证据信息；ETL 模块通过 Prefect 流程定期同步外部数据并写入数据库。
2. **服务层**：FastAPI 提供 REST 与 GraphQL 接口，同时内置规则与版本管理扩展点。
3. **可视化层**：React + D3 展示药物网络图谱，支持按药品查询并高亮适应症、相互作用。

## 服务拓扑

- `backend` 暴露 `http://localhost:8000` REST/GraphQL 接口。
- `frontend` 静态站点通过 Vite 开发服务器提供，反向代理到后端接口。
- `etl` 以 Prefect Flow 形式执行数据拉取、转换和入库。
- Docker Compose 将 PostgreSQL、Redis（可选）与应用容器统一编排。

## 数据模型

主要表

- `drugs`：药品基本信息、ATC 编码
- `conditions`：疾病与适应症
- `drug_conditions`：药品与适应症关联，包含证据等级与临床备注
- `drug_interactions`：药品-药品相互作用，记录严重程度、机制、处理建议
- `evidence_sources` / `interaction_evidence`：引用文献或指南及其可信度

模型定义位于 `backend/app/models/`，可通过 Alembic 迁移维护。

## 扩展点

- 引入 Redis + RQ/Celery 以处理批量交互评分、缓存热点查询。
- 在 `etl/pipelines/sources/` 下扩展新的数据适配器，统一输出标准化 DataFrame。
- 在 `frontend/src/components/` 中补充筛选器、风险提示、患者用药方案比较等模块。
