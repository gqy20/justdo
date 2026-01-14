# JustDo API 文档

> JustDo RESTful API 接口完整参考

## 概述

JustDo API 是基于 FastAPI 构建的 RESTful API，提供任务管理、用户画像分析、回收站和 AI 对话功能。

- **Base URL**: `http://localhost:8848`
- **API 前缀**: `/api`
- **内容类型**: `application/json`
- **交互文档**: [`/docs`](http://localhost:8848/docs) (Swagger UI)
- **备用文档**: [`/redoc`](http://localhost:8848/redoc) (ReDoc)

---

## 认证

当前版本无需认证。如需使用 AI 功能，请设置环境变量：

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://open.bigmodel.cn/api/paas/v4"  # 可选
```

---

## 数据模型

### TodoCreate

创建任务请求

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| text | string | ✅ | 任务文本（最小长度 1） |
| priority | string | ❌ | 优先级：`high`/`medium`/`low`（默认 `medium`） |

### TodoResponse

任务响应

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 任务 ID |
| text | string | 任务文本 |
| priority | string | 优先级 |
| done | boolean | 完成状态 |
| feedback | string \| null | AI 反馈（添加/完成时的鼓励） |
| original_text | string \| null | AI 优化前的原始文本 |

### ChatRequest

AI 对话请求

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| message | string | ✅ | 用户消息（最小长度 1） |

---

## 端点

### 任务管理

#### 1. 获取任务列表

```http
GET /api/todos?done=false
```

**查询参数**：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| done | boolean | ❌ | 过滤已完成/未完成任务 |

**响应**：`TodoResponse[]`

**示例**：

```bash
curl http://localhost:8848/api/todos
curl http://localhost:8848/api/todos?done=false
```

---

#### 2. 创建任务

```http
POST /api/todos?ai=false
```

**查询参数**：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| ai | boolean | ❌ | 是否使用 AI 优化任务描述 |

**请求体**：`TodoCreate`

**响应**：`201 Created` + `TodoResponse`

**示例**：

```bash
# 普通创建
curl -X POST http://localhost:8848/api/todos \
  -H "Content-Type: application/json" \
  -d '{"text": "购买牛奶", "priority": "medium"}'

# AI 优化创建
curl -X POST "http://localhost:8848/api/todos?ai=true" \
  -H "Content-Type: application/json" \
  -d '{"text": "写代码", "priority": "high"}'
```

---

#### 3. 标记完成

```http
POST /api/todos/{todo_id}/done
```

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| todo_id | integer | 任务 ID |

**响应**：`200 OK` + `TodoResponse`

**示例**：

```bash
curl -X POST http://localhost:8848/api/todos/1/done
```

---

#### 4. 切换状态（流式）

```http
POST /api/todos/{todo_id}/toggle
```

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| todo_id | integer | 任务 ID |

**响应**：`text/event-stream` (Server-Sent Events)

**事件类型**：

| 类型 | 说明 |
|------|------|
| status | 任务状态更新 |
| feedback_chunk | AI 反馈流式片段 |

**示例**：

```bash
curl -N http://localhost:8848/api/todos/1/toggle
```

---

#### 5. 删除任务

```http
DELETE /api/todos/{todo_id}?reason=
```

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| todo_id | integer | 任务 ID |

**查询参数**：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| reason | string | ❌ | 删除原因 |

**响应**：`204 No Content`

**示例**：

```bash
curl -X DELETE "http://localhost:8848/api/todos/1?reason=已完成"
```

---

#### 6. 清空已完成

```http
POST /api/clear
```

**响应**：`200 OK` + `{"cleared": integer}`

**示例**：

```bash
curl -X POST http://localhost:8848/api/clear
```

---

#### 7. 智能建议

```http
GET /api/suggest
```

**响应**：`200 OK` + `{"todos": TodoResponse[]}`

按优先级排序返回未完成任务。

---

### AI 对话

#### 8. AI 聊天

```http
POST /api/chat
```

**请求体**：`ChatRequest`

**响应**：`200 OK` + `{"response": string}`

**错误**：`503 Service Unavailable`（未配置 API Key）

**示例**：

```bash
curl -X POST http://localhost:8848/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我分析今天的工作安排"}'
```

---

### 用户画像

#### 9. 基础统计

```http
GET /api/profile/stats
```

**响应**：`ProfileStatsResponse`

| 字段 | 类型 | 说明 |
|------|------|------|
| total_tasks | integer | 总任务数 |
| completed_tasks | integer | 已完成任务数 |
| completion_rate | float | 完成率 |
| current_streak | integer | 当前连续天数 |
| longest_streak | integer | 最长连续天数 |

---

#### 10. 用户类型

```http
GET /api/profile/user-type
```

**响应**：`ProfileUserTypeResponse`

| 字段 | 类型 | 说明 |
|------|------|------|
| execution_pattern | string | 执行模式 |
| time_preference | string | 时间偏好 |
| activity_pattern | string | 活动模式 |

---

#### 11. 优势短板

```http
GET /api/profile/strengths-weaknesses
```

**响应**：`ProfileSWResponse`

| 字段 | 类型 | 说明 |
|------|------|------|
| strengths | string[] | 优势列表 |
| weaknesses | string[] | 短板列表 |
| suggestions | string[] | 改进建议 |

---

#### 12. 风险预警

```http
GET /api/profile/risk-alerts
```

**响应**：`ProfileRiskAlert[]`

| 字段 | 类型 | 说明 |
|------|------|------|
| level | string | 预警级别 |
| type | string | 预警类型 |
| message | string | 预警消息 |

---

#### 13. 完整画像

```http
GET /api/profile/full
```

**响应**：`ProfileFullResponse`

包含所有画像数据的完整响应。

---

#### 14. 画像总结

```http
GET /api/profile/summary
```

**响应**：`{"summary": string}`

纯文本格式的用户画像总结。

---

### 回收站

#### 15. 回收站列表

```http
GET /api/trash?limit=10&category=work
```

**查询参数**：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| limit | integer | ❌ | 限制返回数量 |
| category | string | ❌ | 按类别过滤 |

**响应**：`TrashListResponse`

| 字段 | 类型 | 说明 |
|------|------|------|
| items | TrashItemResponse[] | 回收站项目列表 |
| stats | TrashStatsResponse | 统计数据 |

---

#### 16. 回收站统计

```http
GET /api/trash/stats
```

**响应**：`TrashStatsResponse`

| 字段 | 类型 | 说明 |
|------|------|------|
| total_items | integer | 总项目数 |
| by_category | object | 按类别统计 |
| by_priority | object | 按优先级统计 |
| avg_days_in_trash | float | 平均滞留天数 |
| will_auto_delete | integer | 即将自动删除数量 |

---

#### 17. 恢复任务

```http
POST /api/trash/{todo_id}/restore
```

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| todo_id | integer | 任务 ID |

**响应**：`200 OK` + 恢复的任务信息

**错误**：`404 Not Found`（任务不在回收站）

---

#### 18. 永久删除

```http
DELETE /api/trash/{todo_id}
```

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| todo_id | integer | 任务 ID |

**响应**：`204 No Content`

---

#### 19. 清空回收站

```http
POST /api/trash/clear
```

**响应**：`200 OK` + `{"cleared": integer}`

---

#### 20. 清理旧项目

```http
POST /api/trash/cleanup?days=7
```

**查询参数**：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| days | integer | ❌ | 清理 N 天前的项目（默认使用自动删除天数） |

**响应**：`200 OK` + `{"cleaned": integer}`

---

## 错误响应

| 状态码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用（AI 功能未配置） |

**错误格式**：

```json
{
  "detail": "错误消息"
}
```

---

## SSE 流式响应

`/api/todos/{id}/toggle` 端点使用 Server-Sent Events (SSE) 返回流式数据：

```
data: {"type": "status", "data": {...}}

data: {"type": "feedback_chunk", "data": "这是"}

data: {"type": "feedback_chunk", "data": "AI反馈"}
```

---

## 优先级权重

| 优先级 | 权重值 |
|--------|--------|
| high | 100 |
| medium | 50 |
| low | 10 |
