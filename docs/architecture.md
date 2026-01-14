# JustDo 架构设计

> 代码即真相，文档跟随代码

## 系统概述

JustDo 是一个采用 TDD 方式开发的命令行待办事项工具，支持任务优先级、AI 智能建议、用户画像分析和 Web 界面。

```
┌─────────────────────────────────────────────────────────────┐
│                        用户层                               │
├─────────────────────────────────────────────────────────────┤
│  CLI (jd)          │  Web UI          │  API 直接调用        │
│  argparse          │  SPA + FastAPI   │  REST/HTTP          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                        业务层                               │
├─────────────────────────────────────────────────────────────┤
│  TodoManager      │  UserProfile      │  TrashManager       │
│  - CRUD           │  - 行为分析        │  - 软删除           │
│  - 排序过滤        │  - 画像统计        │  - 恢复清理         │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                        数据层                               │
├─────────────────────────────────────────────────────────────┤
│  justdo.json       │  justdo.profile.json │  justdo.trash.json │
│  任务数据           │  用户画像数据          │  回收站数据        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                        外部服务                             │
├─────────────────────────────────────────────────────────────┤
│  OpenAI API (GLM-4) - AI 优化、对话、情感反馈               │
└─────────────────────────────────────────────────────────────┘
```

---

## 模块依赖关系

```
                    ┌─────────────┐
                    │   cli.py    │  CLI 入口
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   api.py    │  FastAPI Web 入口
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼──────┐   ┌───────▼──────┐   ┌──────▼─────┐
│  manager.py  │   │ ai.py        │   │ emotion.py │
│  核心业务     │   │ AI 集成      │   │ 情感反馈    │
└───────┬──────┘   └──────┬──────┘   └────────────┘
        │                 │
        │         ┌───────▼──────┐
        │         │ prompts.py   │
        │         │ Prompt 模板  │
        │         └──────────────┘
        │
┌───────▼──────┐   ┌──────────────┐
│  models.py   │   │ user_profile │
│  数据模型     │   │ trash.py     │
└──────────────┘   │ 回收站管理    │
                   └──────────────┘
```

---

## 核心模块

### models.py - 数据模型

```python
TodoItem
├── id: int              # 唯一标识
├── text: str            # 任务文本
├── priority: str        # 优先级 (high/medium/low)
├── done: bool           # 完成状态
└── priority_weight: int # 优先级权重（计算属性）
```

**职责**：
- 定义数据结构
- 提供类型校验
- 优先级权重计算逻辑

---

### manager.py - 任务管理器

```python
TodoManager
├── add()           # 添加任务
├── list()          # 列出任务
├── mark_done()     # 标记完成
├── toggle()        # 切换状态
├── delete()        # 删除任务
├── clear()         # 清空已完成
└── sort()          # 排序逻辑
```

**职责**：
- 核心 CRUD 操作
- 数据持久化（JSON）
- 排序和过滤逻辑

---

### cli.py - 命令行接口

```python
# 入口点: jd 命令
jd add "任务"        # 添加任务
jd list             # 列出任务
jd done 1           # 标记完成
jd delete 1         # 删除任务
jd clear            # 清空已完成
jd suggest --ai     # AI 建议
jd --chat "消息"    # AI 对话
```

**职责**：
- 参数解析（argparse）
- 用户交互输出
- 命令分发

---

### api.py - Web API

```python
FastAPI App
├── GET  /               # 首页（SPA）
├── GET  /api/todos      # 列表
├── POST /api/todos      # 创建
├── POST /api/todos/{id}/toggle  # 流式切换
├── GET  /api/profile/*  # 画像分析
├── GET  /api/trash      # 回收站
└── POST /api/chat       # AI 对话
```

**职责**：
- RESTful API 定义
- 请求/响应模型（Pydantic）
- SSE 流式响应

---

### ai.py - AI 集成

```python
AIHandler
├── enhance_input()  # 优化任务描述
├── chat()           # 对话交互
└── suggest()        # 智能建议
```

**职责**：
- OpenAI API 封装
- 流式响应处理
- 错误重试机制

---

### emotion.py - 情感反馈

```python
trigger_unified_analysis()   # 统一分析（性能优化）
trigger_feedback_stream()    # 流式反馈
_get_time_context()          # 时间上下文
```

**职责**：
- 个性化反馈生成
- 时间场景感知
- 流式输出优化

---

### user_profile.py - 用户画像

```python
UserProfile
├── record_task()           # 记录任务行为
├── analyze_user_type()     # 分析用户类型
├── analyze_strengths_and_weaknesses()  # 优势短板
├── get_risk_alerts()       # 风险预警
└── get_user_summary()      # 画像总结
```

**职责**：
- 用户行为追踪
- 统计分析
- 风险预警

---

### trash.py - 回收站

```python
TrashManager
├── add()              # 添加到回收站
├── list()             # 列出回收站
├── restore()          # 恢复任务
├── delete_permanently() # 永久删除
├── clear()            # 清空回收站
└── cleanup_old()      # 清理旧项目
```

**职责**：
- 软删除实现
- 30天自动清理
- 恢复机制

---

## 数据流

### 添加任务流程

```
用户输入
    │
    ├─ CLI: jd add "任务"
    │       │
    │       ▼
    │   TodoManager.add()
    │       │
    │       ├─ 生成 ID
    │       ├─ 创建 TodoItem
    │       ├─ 写入 JSON
    │       └─ 返回结果
    │
    └─ Web: POST /api/todos
            │
            ├─ AI 优化（可选）
            ├─ TodoManager.add()
            ├─ UserProfile.record_task()
            └─ 返回 TodoResponse
```

### AI 反馈流程（性能优化后）

```
任务操作（添加/完成）
    │
    ▼
检查 OPENAI_API_KEY
    │
    ▼
trigger_unified_analysis()
    │
    ├─ 收集数据：stats, category, hourly, deletion
    ├─ 构建统一 Prompt（4 场景 → 1 次）
    ├─ 流式获取响应
    └─ 提取 task_feedback
    │
    ▼
返回给用户
```

---

## 设计决策

### 1. JSON 存储方案

**选择原因**：
- 简单易读，便于调试
- 无需额外依赖
- 适合小型应用

**权衡**：
- ❌ 不适合高并发
- ❌ 无事务支持
- ✅ 够用即可

### 2. 优先级权重系统

| 优先级 | 权重 | 理由 |
|--------|------|------|
| high | 100 | 紧急且重要 |
| medium | 50 | 默认优先级 |
| low | 10 | 可延后 |

**排序规则**：`-weight, id` （权重降序，ID 升序）

### 3. AI 性能优化

| 优化前 | 优化后 | 提升 |
|--------|--------|------|
| 4 次 API 调用 | 1 次 API 调用 | **75%** |
| 54 秒响应 | 2.85 秒响应 | **19x** |

**手段**：
- 统一分析 Prompt
- 流式响应输出
- 减少无效调用

---

## 扩展点

### 1. 数据存储

当前使用 JSON，可扩展为：

```python
# 接口设计
class StorageBackend(ABC):
    @abstractmethod
    def load(self) -> List[TodoItem]: ...

    @abstractmethod
    def save(self, items: List[TodoItem]): ...

# 实现
class JSONStorage(StorageBackend): ...  # 当前
class SQLiteStorage(StorageBackend): ...  # 未来
class PostgreSQLStorage(StorageBackend): ...  # 未来
```

### 2. AI 提供商

当前支持 OpenAI 兼容 API，可扩展：

```python
class AIProvider(ABC):
    @abstractmethod
    def chat(self, prompt: str) -> str: ...

class OpenAIProvider(AIProvider): ...     # 当前
class AnthropicProvider(AIProvider): ...  # 未来
class LocalLLMProvider(AIProvider): ...   # 未来
```

---

## 安全考虑

| 风险 | 当前措施 | 改进建议 |
|------|----------|----------|
| API Key 泄露 | 环境变量 | 密钥管理服务 |
| 文件注入 | JSON 解析 | 输入验证 |
| 路径遍历 | 固定数据目录 | 权限检查 |
