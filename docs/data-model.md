# 数据字典（初稿）

## 表：drugs
| 字段 | 类型 | 说明 |
| ---- | ---- | ---- |
| id | varchar | 药品唯一 ID（可使用外部编码） |
| name | varchar | 药品名称 |
| description | text | 简要说明 |
| atc_code | varchar | ATC 编码 |
| created_at | timestamptz | 创建时间 |
| updated_at | timestamptz | 更新时间 |

## 表：conditions
| 字段 | 类型 | 说明 |
| id | varchar | 适应症/疾病 ID |
| name | varchar | 名称 |
| description | text | 描述 |
| created_at | timestamptz | 创建时间 |
| updated_at | timestamptz | 更新时间 |

## 表：drug_conditions
| 字段 | 类型 | 说明 |
| id | varchar | 复合主键（drug_id:condition_id） |
| drug_id | varchar | 药品 ID |
| condition_id | varchar | 疾病 ID |
| usage_note | text | 使用说明 |
| evidence_level | varchar | 证据等级 |
| created_at | timestamptz | 创建时间 |

## 表：drug_interactions
| 字段 | 类型 | 说明 |
| id | varchar | 药物交互 ID（建议组合） |
| drug_id | varchar | 主药品 ID |
| interacting_drug_id | varchar | 交互药品 ID |
| severity | varchar | 严重程度（minimal/moderate/major） |
| mechanism | text | 交互机制 |
| management | text | 临床处理建议 |
| created_at | timestamptz | 创建时间 |
| updated_at | timestamptz | 更新时间 |

## 表：evidence_sources
| 字段 | 类型 | 说明 |
| id | varchar | 证据 ID |
| title | varchar | 文献或指南标题 |
| url | varchar | 链接 |
| source_type | varchar | 来源类型（指南/文献/数据库） |
| abstract | text | 摘要 |
| created_at | timestamptz | 创建时间 |

## 表：interaction_evidence
| 字段 | 类型 | 说明 |
| id | varchar | 证据关联 ID |
| interaction_id | varchar | 交互 ID |
| evidence_id | varchar | 证据 ID |
| summary | text | 摘要 |
| confidence | varchar | 信心等级 |
| created_at | timestamptz | 创建时间 |
