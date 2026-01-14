# JustDo 组件清单

> 模块职责边界一览

## 源码结构

```
src/justdo/
├── __init__.py       # 包导出
├── models.py         # TodoItem 数据模型
├── manager.py        # TodoManager 核心逻辑
├── cli.py            # 命令行接口
├── ai.py             # AI 集成（GLM-4）
├── emotion.py        # 情感反馈引擎
├── prompts.py        # AI Prompt 模板
├── user_profile.py   # 用户画像分析
├── trash.py          # 回收站管理
├── api.py            # FastAPI Web 接口
└── static/
    └── index.html    # 单页 Web 应用
```

---

## 模块清单

### models.py

**职责**：数据模型定义

| 类/函数 | 职责 | 导出 |
|---------|------|------|
| `TodoItem` | 任务数据模型 | ✅ |
| `priority_weights` | 优先级权重映射 | ✅ |

**依赖**：`dataclasses`, `typing`

**被依赖**：所有业务模块

---

### manager.py

**职责**：核心业务逻辑

| 函数 | 职责 | 导出 |
|------|------|------|
| `TodoManager.__init__()` | 初始化管理器 | - |
| `TodoManager.add()` | 添加任务 | ✅ |
| `TodoManager.list()` | 列出任务 | ✅ |
| `TodoManager.mark_done()` | 标记完成 | ✅ |
| `TodoManager.toggle()` | 切换状态 | ✅ |
| `TodoManager.delete()` | 删除任务 | ✅ |
| `TodoManager.clear()` | 清空已完成 | ✅ |

**依赖**：`models`, `json`, `pathlib`

**被依赖**：`cli`, `api`

---

### cli.py

**职责**：命令行接口

| 函数 | 职责 | 导出 |
|------|------|------|
| `main()` | CLI 入口 | ✅ |
| `_build_parser()` | 构建参数解析器 | - |
| `_print_todo()` | 打印任务 | - |
| `_print_profile()` | 打印画像 | - |

**依赖**：`manager`, `user_profile`, `trash`, `ai`

**入口点**：`jd` 命令

---

### ai.py

**职责**：AI 功能集成

| 类/函数 | 职责 | 导出 |
|---------|------|------|
| `AIHandler` | AI 处理器 | ✅ |
| `get_ai_handler()` | 获取单例 | ✅ |
| `AIHandler.enhance_input()` | 优化输入 | ✅ |
| `AIHandler.chat()` | 对话 | ✅ |
| `AIHandler.suggest()` | 智能建议 | ✅ |

**依赖**：`openai`, `models`

**可选依赖**：`openai` 包

---

### emotion.py

**职责**：情感反馈引擎

| 函数 | 职责 | 导出 |
|------|------|------|
| `trigger_unified_analysis()` | 统一分析（优化） | ✅ |
| `trigger_feedback_stream()` | 流式反馈 | ✅ |
| `_get_time_context()` | 时间上下文 | ✅ |
| `_build_unified_prompt()` | 构建统一 Prompt | - |

**依赖**：`openai`, `prompts`

**被依赖**：`api`

---

### prompts.py

**职责**：AI Prompt 模板

| 函数 | 职责 | 导出 |
|------|------|------|
| `TASK_ANALYSIS_PROMPT` | 任务分析模板 | ✅ |
| `CHAT_PROMPT` | 对话模板 | ✅ |
| `SUGGEST_PROMPT` | 建议模板 | ✅ |
| `FEEDBACK_STREAM_PROMPT` | 流式反馈模板 | ✅ |
| `UNIFIED_ANALYSIS_PROMPT` | 统一分析模板 | ✅ |

**依赖**：无

**被依赖**：`ai`, `emotion`

---

### user_profile.py

**职责**：用户画像分析

| 类/函数 | 职责 | 导出 |
|---------|------|------|
| `UserProfile` | 画像管理器 | ✅ |
| `get_profile_path()` | 获取画像路径 | ✅ |
| `guess_category()` | 猜测任务类别 | ✅ |

**依赖**：`models`, `json`, `pathlib`

**被依赖**：`cli`, `api`

---

### trash.py

**职责**：回收站管理

| 类/函数 | 职责 | 导出 |
|---------|------|------|
| `TrashManager` | 回收站管理器 | ✅ |
| `TrashItem` | 回收站项目 | ✅ |
| `get_trash_path()` | 获取回收站路径 | ✅ |

**依赖**：`models`, `json`, `pathlib`, `datetime`

**被依赖**：`cli`, `api`

---

### api.py

**职责**：FastAPI Web 接口

| 函数 | 职责 | 导出 |
|------|------|------|
| `app` | FastAPI 应用实例 | ✅ |
| `main()` | Web 服务器入口 | ✅ |

**路由分组**：

| 前缀 | 端点数 | 说明 |
|------|--------|------|
| `/` | 1 | 首页 |
| `/api/todos` | 6 | 任务管理 |
| `/api/profile` | 6 | 用户画像 |
| `/api/trash` | 6 | 回收站 |
| `/api/chat` | 1 | AI 对话 |
| `/api/suggest` | 1 | 智能建议 |
| `/api/clear` | 1 | 清空已完成 |
| `/static` | - | 静态文件 |

**依赖**：`fastapi`, `uvicorn`, `manager`, `user_profile`, `trash`, `emotion`

**入口点**：`jd-web` 命令

---

### static/index.html

**职责**：单页 Web 应用

| 特性 | 说明 |
|------|------|
| 日式和风设计 | 极简 UI 风格 |
| 响应式布局 | 支持移动端 |
| SSE 支持 | 实时流式反馈 |
| 无框架依赖 | 原生 JavaScript |

**技术栈**：HTML5 + CSS3 + Vanilla JS

---

## 数据文件

| 文件 | 位置 | 说明 |
|------|------|------|
| `justdo.json` | `~/.local/share/justdo/` | 任务数据 |
| `justdo.profile.json` | `~/.local/share/justdo/` | 用户画像 |
| `justdo.trash.json` | `~/.local/share/justdo/` | 回收站 |

---

## 入口点

| 命令 | 入口点 | 说明 |
|------|--------|------|
| `jd` | `justdo.cli:main` | CLI 命令 |
| `jd-web` | `justdo.api:main` | Web 服务器 |

---

## 依赖关系图

```
cli.py ──┬──> manager.py ──> models.py
         │
         ├──> user_profile.py ──┬──> models.py
         │                      └──> json/pathlib
         │
         ├──> trash.py ─────────┬──> models.py
         │                      └──> json/pathlib
         │
         └──> ai.py ────────────└──> openai (可选)

api.py ──┬──> manager.py ──> models.py
         │
         ├──> user_profile.py
         │
         ├──> trash.py
         │
         └──> emotion.py ───> prompts.py
                              └──> openai (可选)
```

---

## 职责边界

### 单一职责原则 (SRP)

| 模块 | 唯一职责 |
|------|----------|
| `models.py` | 数据结构定义 |
| `manager.py` | 业务逻辑 |
| `cli.py` | 用户交互（命令行） |
| `api.py` | 用户交互（Web） |
| `ai.py` | AI 集成 |
| `emotion.py` | 情感反馈 |
| `user_profile.py` | 用户分析 |
| `trash.py` | 软删除管理 |

### 依赖方向

```
用户层 (cli/api)
      │
      ▼
业务层 (manager/ai/emotion/user_profile/trash)
      │
      ▼
数据层 (models + JSON)
```

**原则**：
- 高层模块不依赖低层模块细节
- 低层模块不依赖高层模块
- 依赖倒置：通过抽象接口隔离

---

## 测试覆盖

| 模块 | 单元测试 | 集成测试 |
|------|----------|----------|
| models.py | ✅ | - |
| manager.py | ✅ | - |
| cli.py | ✅ | - |
| ai.py | ✅ (Mock) | - |
| user_profile.py | ✅ | - |
| trash.py | ✅ | - |
| api.py | - | ✅ |

**总计**：100 个测试全部通过
