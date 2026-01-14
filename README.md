# justdo - Just do it! 🚀

一个用 TDD 方式开发的简单命令行待办事项工具，支持任务优先级、AI 智能建议、用户画像分析。

> **Just do it!** - 简单、高效的待办事项管理工具

## ✨ 特性

- 📋 **任务管理** - 添加、完成、删除任务，支持优先级（高🔴/中🟡/低🟢）
- 🤖 **AI 增强** - 智能任务描述优化、个性化反馈、流式响应
- 👤 **用户画像** - 自动分析任务习惯，识别优势短板
- 🗑️ **回收站** - 删除任务暂存，支持恢复和自动清理
- 🌐 **Web 界面** - 日式和风设计的单页应用
- ⚡ **高性能** - AI 响应优化（54秒 → 2.85秒）

## 安装

```bash
# 使用 pip 安装
pip install justdo

# 使用 uv 安装
uv pip install justdo

# 安装 AI 功能支持
pip install justdo[ai]

# 安装 Web 界面支持
pip install justdo[web]
```

## 使用方法

### CLI 基础命令

```bash
# 添加任务（默认中等优先级）
jd add "购买牛奶"

# 添加高优先级任务 (1=高, 2=中, 3=低)
jd add "紧急任务" -l 1

# 列出所有任务
jd list

# 按优先级排序显示
jd list -s p

# 标记任务为完成（支持范围语法）
jd done 1
jd done 1 2-5 7

# 删除任务
jd delete 1

# 清空所有已完成的任务
jd clear
```

### AI 功能

```bash
# 设置 API Key（智谱 GLM）
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://open.bigmodel.cn/api/paas/v4"

# AI 优化任务描述
jd add "写代码" --ai
# → AI 优化: 写代码 → 完成核心功能模块编码工作

# AI 智能建议（流式输出）
jd suggest --ai

# AI 对话模式
jd --chat "帮我分析今天的工作安排"
```

### Web 界面

```bash
# 启动 Web 服务器（默认端口 8848）
jd-web

# 访问浏览器
open http://localhost:8848
```

Web 功能包括：
- 🎨 日式和风极简设计
- 📊 用户画像可视化
- 🔄 实时流式反馈
- 📱 响应式布局

### 用户画像

```bash
# 查看 API 请求示例
curl http://localhost:8848/api/profile/full
```

画像分析内容：
- 📈 **基础统计** - 总任务数、完成率、连续天数
- 🎯 **用户类型** - 执行模式、时间偏好、活动模式
- 💪 **优势短板** - AI 分析强项和改进建议
- ⚠️ **风险预警** - 任务堆积、拖延提醒

### 回收站

```bash
# 查看 API 请求示例
curl http://localhost:8848/api/trash
```

回收站功能：
- 🗂️ 删除任务自动暂存
- 🔄 支持恢复已删除任务
- ⏰ 30 天自动清理
- 📊 按类别/优先级统计

## 优先级说明

| 优先级 | Emoji | 数字 | 说明 |
|--------|-------|------|------|
| high | 🔴 | 1 | 高优先级（紧急重要） |
| medium | 🟡 | 2 | 中优先级（默认） |
| low | 🟢 | 3 | 低优先级（可延后） |

## 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.8+ |
| CLI | argparse |
| Web | FastAPI + uvicorn |
| AI | OpenAI API (GLM-4) |
| 数据存储 | JSON |
| 测试 | pytest |
| 包管理 | uv / setuptools |

## 开发

```bash
# 克隆仓库
git clone https://github.com/gqy20/justdo.git
cd justdo

# 使用 uv 安装开发依赖
uv pip install -e ".[dev,ai,web]"

# 运行测试
uv run python -m pytest

# 查看测试覆盖率
uv run python -m pytest --cov=justdo

# 安装包到本地
uv build
pip install dist/justdo-0.1.3-py3-none-any.whl
```

## 项目结构

```
justdo/
├── src/
│   └── justdo/
│       ├── __init__.py       # 包导出，版本 0.1.3
│       ├── models.py         # TodoItem 数据模型
│       ├── manager.py        # TodoManager 核心逻辑
│       ├── cli.py            # 命令行接口
│       ├── ai.py             # AI 集成（GLM-4）
│       ├── emotion.py        # 情感反馈引擎
│       ├── prompts.py        # AI Prompt 模板
│       ├── user_profile.py   # 用户画像分析
│       ├── trash.py          # 回收站管理
│       ├── api.py            # FastAPI Web 接口
│       └── static/
│           └── index.html    # 单页 Web 应用
├── tests/
│   ├── unit/                 # 单元测试
│   └── integration/          # 集成测试
├── docs/                     # 项目文档
│   ├── api.md                # API 文档
│   ├── architecture.md       # 架构设计
│   ├── components.md         # 组件清单
│   ├── development.md        # 开发指南
│   └── testing.md            # 测试策略
├── pyproject.toml            # 包配置
├── justdo.json               # 数据存储（自动生成）
├── justdo.profile.json       # 用户画像（自动生成）
└── justdo.trash.json         # 回收站（自动生成）
```

## 📚 文档

- [API 文档](docs/api.md) - RESTful API 完整参考
- [架构设计](docs/architecture.md) - 系统架构与模块关系
- [组件清单](docs/components.md) - 模块职责边界
- [开发指南](docs/development.md) - 开发环境与工作流
- [测试策略](docs/testing.md) - TDD 与测试覆盖

### 在线 API 文档

启动 Web 服务后访问：
- **Swagger UI**: http://localhost:8848/docs
- **ReDoc**: http://localhost:8848/redoc

### 主要端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/todos` | GET/POST | 列表/创建任务 |
| `/api/todos/{id}/toggle` | POST | 切换状态（SSE 流式） |
| `/api/todos/{id}` | DELETE | 删除任务 |
| `/api/profile/full` | GET | 完整用户画像 |
| `/api/trash` | GET | 回收站列表 |
| `/api/chat` | POST | AI 对话 |

## 测试

项目采用 TDD 开发模式，**100 个测试全部通过**：

- 数据模型测试 - 优先级、权重计算
- 业务逻辑测试 - CRUD、排序、过滤
- CLI 命令测试 - 参数解析、输出格式
- AI 功能测试 - 模拟 AI 响应、流式输出
- 用户画像测试 - 统计分析、风险预警
- 回收站测试 - 添加、恢复、清理
- API 集成测试 - REST 接口、SSE 流式

## 性能优化

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| AI 响应时间 | 54 秒 | 2.85 秒 | **19x** |
| AI 调用次数 | 4 次 | 1 次 | **75%** |

优化手段：
- 统一分析：4 个场景 → 1 个 prompt
- 流式响应：Token 级实时输出
- 并发删除：批量操作优化

## 为什么叫 justdo？

- ✅ **简洁有力** - 两个音节，朗朗上口
- ✅ **寓意完美** - "Just do it!" 正是待办事项的核心精神
- ✅ **命令简短** - `jd` 两个字母，快速输入
- ✅ **易记易搜** - 用户搜索 "just do" 很容易找到
- ✅ **国际化** - 英语通用，全球用户都能理解

## 配置

### 环境变量

| 变量 | 说明 | 必需 |
|------|------|------|
| `OPENAI_API_KEY` | 智谱 API Key | AI 功能 |
| `OPENAI_BASE_URL` | API 基础 URL | 可选 |

### 数据文件

| 文件 | 位置 | 说明 |
|------|------|------|
| `justdo.json` | `~/.local/share/justdo/` | 任务数据 |
| `justdo.profile.json` | `~/.local/share/justdo/` | 用户画像 |
| `justdo.trash.json` | `~/.local/share/justdo/` | 回收站 |

## 链接

- **GitHub**: https://github.com/gqy20/justdo
- **PyPI**: https://pypi.org/project/justdo/
- **文档**: http://home.gqy20.top/justdo/

## License

MIT
