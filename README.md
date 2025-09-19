# 医疗用药知识图谱平台

该项目构建一个药物-疾病-药物相互作用的知识图谱与可视化平台，帮助临床医师准确掌握用药范围及联用风险。

## 模块组成

- **backend**: 基于 FastAPI 的核心服务，提供 REST/GraphQL API、规则引擎及知识版本管理。
- **etl**: 数据抽取、清洗、加载脚本，同步外部公开数据源及院内知识库。
- **frontend**: React + TypeScript 的交互式药物可视化界面，支持图谱检索、风险高亮。
- **infrastructure**: 包含 Docker、CI/CD、监控等运维配置。
- **docs**: 项目文档、数据字典、API 说明与运维指南。

## OpenFDA ETL Pipeline (Updated)

- Configure target substances in `etl/config/sources.yaml` under the `openfda.substances` list; these values are used both for constructing the API query and for filtering the payload to a single row per substance.
- Run the adapter locally via `cd etl && python -m pipelines.scheduler`; the scheduler now skips disabled sources, tolerates empty OpenFDA responses, and loads unique rows into the database without violating `drugs.atc_code` constraints.
- Unit tests covering the adapter can be executed with `cd etl && pytest tests/test_openfda_adapter.py` to validate deduplication and search-term handling.

## 快速开始

1. 安装依赖：`make install`
2. 启动开发环境：`docker compose up --build`
3. 打开前端：`http://localhost:5173`
4. 查看 API 文档：`http://localhost:8000/docs`

更多细节请见 `docs/`。
