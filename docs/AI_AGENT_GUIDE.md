# 药物相互作用AI Agent使用指南

## 概述

本项目已成功集成了符合FDA CDS（临床决策支持）非医疗器械标准的AI Agent系统，用于提供药物信息和相互作用检查。

## 架构设计

### 三层验证架构

根据gole.md的要求，系统实现了多层验证：

```
用户请求
    ↓
【第1层：预AI验证】
├─ 输入清理和消毒
├─ 药物名称验证（RxNorm）
└─ 速率限制（未来实现）
    ↓
【第2层：AI生成】
├─ 从RxNorm获取标准化信息
├─ 从OpenFDA获取官方标签
├─ 使用安全约束的提示词
└─ 低温度设置（0.3）获得事实性回答
    ↓
【第3层：后AI验证】
├─ 通过FDA API检查药物相互作用
├─ 严重程度分类
└─ 自动升级到医疗专业人员
    ↓
响应 + 强制免责声明
```

## 核心组件

### 1. RxNorm API适配器 (`app/services/rxnorm_service.py`)

- **功能**: 药物标准化命名和验证
- **数据源**: NIH国家医学图书馆RxNorm
- **主要方法**:
  - `get_rxcui()`: 获取药物的唯一标识符
  - `validate_drug_name()`: 验证药物是否存在
  - `get_drug_properties()`: 获取药物属性
  - `get_drug_context()`: 获取完整上下文信息

### 2. OpenFDA API适配器 (`app/services/openfda_service.py`)

- **功能**: FDA批准的药品标签和不良事件信息
- **数据源**: FDA OpenFDA API
- **主要方法**:
  - `get_drug_label()`: 获取FDA药品标签
  - `get_warnings_and_precautions()`: 获取警告和注意事项
  - `get_adverse_events()`: 获取不良事件报告（FAERS）
  - `check_drug_interactions_fda()`: 从FDA标签提取相互作用

### 3. AI Agent服务 (`app/services/ai_agent_service.py`)

- **功能**: 核心AI引擎，整合所有数据源
- **支持的AI模型**:
  - OpenAI GPT-4o / GPT-4o-mini（推荐用于生产）
  - Anthropic Claude 3.5 Sonnet（最佳安全性）
- **主要方法**:
  - `validate_drug_input()`: 预AI验证
  - `ask_medication()`: 完整的用药咨询流程
  - `check_drug_interactions()`: 药物相互作用检查

## API端点

### 1. 用药咨询

**端点**: `POST /api/v1/medication/ask-medication`

**请求体**:
```json
{
  "drug_name": "aspirin",
  "question": "这种药物有什么副作用？"
}
```

**响应**:
```json
{
  "success": true,
  "drug_name": "aspirin",
  "question": "这种药物有什么副作用？",
  "answer": "根据FDA批准的药品标签...",
  "disclaimer": "此信息仅供教育用途...",
  "severity": "info",
  "sources": ["FDA Drug Label", "RxNorm"]
}
```

### 2. 药物相互作用检查

**端点**: `POST /api/v1/medication/check-interaction`

**请求体**:
```json
{
  "drug1": "warfarin",
  "drug2": "aspirin"
}
```

**响应**:
```json
{
  "success": true,
  "drug1": "warfarin",
  "drug2": "aspirin",
  "found_interactions": true,
  "interactions": [
    {
      "drug": "warfarin",
      "interacts_with": "aspirin",
      "description": "增加出血风险...",
      "severity": "中度",
      "source": "FDA Label"
    }
  ],
  "recommendation": "请与您的医疗保健提供者讨论这些药物的联合使用。",
  "disclaimer": "此信息仅供教育用途..."
}
```

### 3. 获取免责声明

**端点**: `GET /api/v1/medication/disclaimer`

### 4. 验证药物名称

**端点**: `POST /api/v1/medication/validate-drug?drug_name=aspirin`

### 5. 获取药物信息（无AI）

**端点**: `GET /api/v1/medication/drug-info/aspirin`

## 配置说明

### 环境变量 (`.env`)

```bash
# 数据库
DATABASE_URL=postgresql+psycopg://drugnet:drugnet@localhost:5432/drugnet

# AI API密钥（必须配置）
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key

# AI模型配置
AI_MODEL=gpt-4o-mini  # 或 gpt-4o, claude-3-5-sonnet-20241022
AI_TEMPERATURE=0.3
```

### 配置文件 (`app/core/config.py`)

支持的配置项：
- `ai_model`: AI模型选择
- `ai_temperature`: 生成温度（0.3推荐，更事实性）
- `rxnorm_api_base`: RxNorm API基础URL
- `openfda_api_base`: OpenFDA API基础URL

## 安装和运行

### 1. 安装依赖

```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装requirements
pip install -r requirements/base.txt
```

### 2. 配置环境变量

编辑 `.env` 文件，填入你的OpenAI或Anthropic API密钥。

### 3. 启动服务

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用Make命令（如果配置了Makefile）
make run
```

### 4. 访问API文档

打开浏览器访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 合规性和安全性

### FDA CDS非医疗器械标准

本系统设计符合FDA 2022年9月终版指南的四项标准：

1. ✅ **不获取医疗影像或诊断设备信号**
2. ✅ **显示和分析医疗信息**
3. ✅ **提供建议支持但不提供具体指令**:
   - 提供选项列表而非单一建议
   - 不支持时间紧迫决策
   - 不替代医疗专业人员判断
4. ✅ **允许医疗专业人员审查依据**:
   - 显示信息来源（FDA标签、RxNorm）
   - 透明的算法逻辑
   - 提供引用和参考

### 安全措施

- **多层验证**: 预AI → AI生成 → 后AI验证
- **强制免责声明**: 每个响应都包含医疗免责声明
- **输入验证**: 通过RxNorm验证所有药物名称
- **错误处理**: 完善的异常处理和用户友好的错误消息
- **低温度设置**: AI温度0.3，减少幻觉，提高事实性

### 免责声明示例

系统在每个响应中都包含：

```
此信息仅供教育用途，不能替代专业医疗建议。
对于任何关于医疗状况或药物的问题，请始终咨询您的医生或其他合格的医疗保健提供者。

本应用不：
✗ 诊断医疗状况
✗ 开处方药
✗ 替代您的医生建议
✗ 提供紧急医疗服务

如遇紧急情况，请立即拨打911。
```

## 成本估算

### 小规模（1,000用户，每天10次查询）
- OpenAI GPT-4o-mini: ~$5-10/月
- 托管: $25/月
- **总计**: ~$30-35/月

### 中规模（10,000用户，每天50次查询）
- OpenAI GPT-4o: ~$200-300/月
- 托管: $50/月
- **总计**: ~$250-350/月

## 下一步开发建议

### 短期（1-2周）
1. ✅ 添加速率限制中间件
2. ✅ 实现缓存机制（Redis）
3. ✅ 添加日志记录和监控
4. ✅ 编写单元测试

### 中期（1-2月）
1. 集成DrugBank API（商业许可）获得更准确的相互作用数据
2. 添加多药物相互作用检查（3+药物）
3. 实现用户药物列表管理
4. 添加用药提醒功能

### 长期（3-6月）
1. 移动应用（React Native或Flutter）
2. 个性化用户档案
3. 药房集成
4. 多语言支持（西班牙语优先）

## 测试

### 手动测试示例

使用curl或Postman测试：

```bash
# 测试用药咨询
curl -X POST "http://localhost:8000/api/v1/medication/ask-medication" \
  -H "Content-Type: application/json" \
  -d '{
    "drug_name": "aspirin",
    "question": "What are the side effects?"
  }'

# 测试药物相互作用
curl -X POST "http://localhost:8000/api/v1/medication/check-interaction" \
  -H "Content-Type: application/json" \
  -d '{
    "drug1": "warfarin",
    "drug2": "aspirin"
  }'
```

## 故障排除

### 常见问题

1. **AI API密钥错误**
   - 确保在`.env`中正确配置了`OPENAI_API_KEY`或`ANTHROPIC_API_KEY`
   - 检查API密钥是否有效且有余额

2. **RxNorm或OpenFDA API超时**
   - 这些是免费的公共API，可能会有延迟
   - 检查网络连接
   - 考虑实现本地缓存

3. **药物未找到**
   - 尝试使用通用名而不是品牌名
   - 检查拼写
   - 某些药物可能不在RxNorm数据库中

## 参考资源

- [RxNorm API文档](https://lhncbc.nlm.nih.gov/RxNav/APIs/)
- [OpenFDA API文档](https://open.fda.gov/apis/)
- [FDA CDS指南](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software)
- [OpenAI API文档](https://platform.openai.com/docs)
- [Anthropic Claude文档](https://docs.anthropic.com)

## 许可证和免责声明

本软件仅供教育和研究用途。不得用于实际临床决策，除非获得适当的医疗监督和法律批准。

使用本软件的风险由用户自行承担。开发者不对任何医疗建议、诊断或治疗负责。
