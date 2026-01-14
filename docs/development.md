# JustDo 开发指南

> 开发环境设置与工作流程

## 环境要求

- Python 3.8+
- pip / uv（推荐）
- git

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/gqy20/justdo.git
cd justdo
```

### 2. 创建虚拟环境

```bash
# 使用 venv
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# 或使用 uv（推荐）
uv venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
# 完整安装（包含 AI 和 Web 功能）
pip install -e ".[dev,ai,web]"

# 或使用 uv
uv pip install -e ".[dev,ai,web]"
```

### 4. 验证安装

```bash
jd --version
jd-web --help
pytest
```

---

## 项目结构

```
justdo/
├── src/justdo/           # 源代码
│   ├── __init__.py
│   ├── models.py         # 数据模型
│   ├── manager.py        # 业务逻辑
│   ├── cli.py            # CLI 入口
│   ├── ai.py             # AI 集成
│   ├── emotion.py        # 情感反馈
│   ├── prompts.py        # Prompt 模板
│   ├── user_profile.py   # 用户画像
│   ├── trash.py          # 回收站
│   ├── api.py            # Web API
│   └── static/
│       └── index.html    # Web UI
├── tests/                # 测试
│   ├── unit/             # 单元测试
│   └── integration/      # 集成测试
├── docs/                 # 文档
│   ├── api.md
│   ├── architecture.md
│   └── components.md
├── pyproject.toml        # 包配置
├── Makefile              # 快捷命令
├── CLAUDE.md             # 项目指令
└── README.md             # 项目说明
```

---

## 开发工作流

### TDD 开发流程

```bash
# 1. 写测试
# tests/unit/test_manager.py

# 2. 运行测试（失败）
pytest tests/unit/test_manager.py -k test_new_feature

# 3. 实现功能
# src/justdo/manager.py

# 4. 运行测试（通过）
pytest tests/unit/test_manager.py

# 5. 查看覆盖率
pytest --cov=justdo --cov-report=html
```

### 本地开发

```bash
# 启动开发服务器（热重载）
make dev
# 或
uvicorn justdo.api:app --reload --host 0.0.0.0 --port 8848

# 访问
open http://localhost:8848
```

### 运行测试

```bash
# 所有测试
pytest

# 单元测试
pytest tests/unit/

# 集成测试
pytest tests/integration/

# 覆盖率报告
pytest --cov=justdo --cov-report=html

# 详细输出
pytest -v
```

---

## 代码风格

### 格式化

```bash
# 使用 ruff 格式化
ruff format src/

# 检查格式
ruff format --check src/
```

### Linting

```bash
# 使用 ruff 检查
ruff check src/

# 自动修复
ruff check --fix src/
```

---

## 调试

### CLI 调试

```bash
# 启用详细输出
jd --verbose list

# 查看数据文件
cat ~/.local/share/justdo/justdo.json
```

### Web API 调试

```bash
# 启动开发服务器（调试模式）
jd-web

# 访问交互式文档
open http://localhost:8848/docs

# 查看日志
tail -f /tmp/justdo.log
```

---

## AI 功能配置

### 环境变量

```bash
# 智谱 GLM-4
export OPENAI_API_KEY="your-zhipu-api-key"
export OPENAI_BASE_URL="https://open.bigmodel.cn/api/paas/v4"

# 或 OpenAI
export OPENAI_API_KEY="your-openai-api-key"
# OPENAI_BASE_URL 可选，默认官方地址
```

### 测试 AI 功能

```bash
# AI 优化任务描述
jd add "写代码" --ai

# AI 智能建议
jd suggest --ai

# AI 对话
jd --chat "帮我分析今天的工作"
```

---

## 构建和发布

### 本地构建

```bash
# 构建 wheel
python -m build

# 安装本地构建
pip install dist/justdo-0.1.2-py3-none-any.whl
```

### 发布到 PyPI

```bash
# 1. 更新版本号
# pyproject.toml: version = "0.1.3"

# 2. 创建 Git 标签
git tag v0.1.3
git push origin v0.1.3

# 3. GitHub Actions 自动发布到 PyPI
```

---

## Makefile 快捷命令

```bash
make help     # 显示帮助
make install  # 安装依赖
make dev      # 启动开发服务器
make web      # 启动 Web 服务器
make stop     # 停止开发服务器
make test     # 运行测试
make clean    # 清理临时文件
make lint     # 代码检查
```

---

## 常见问题

### Q: AI 功能不工作？

检查环境变量：
```bash
echo $OPENAI_API_KEY
echo $OPENAI_BASE_URL
```

### Q: 数据文件在哪里？

```bash
# Linux/macOS
~/.local/share/justdo/

# Windows
%LOCALAPPDATA%\justdo\
```

### Q: 如何重置所有数据？

```bash
# 删除数据文件
rm ~/.local/share/justdo/*.json

# 或使用 CLI
jd clear
```

### Q: 如何启用详细日志？

```bash
# API 调试
jd-web --log-level debug

# 测试调试
pytest -vv --log-cli-level=DEBUG
```

---

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### Commit 规范

| 类型 | 说明 | 示例 |
|------|------|------|
| feat | 新功能 | `feat: 添加回收站功能` |
| fix | 修复 Bug | `fix: 修复优先级排序` |
| docs | 文档 | `docs: 更新 API 文档` |
| test | 测试 | `test: 添加画像测试` |
| refactor | 重构 | `refactor: 优化 AI 调用` |
| chore | 构建/工具 | `chore: 更新依赖` |

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE)
