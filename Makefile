.PHONY: help install dev web test clean lint

# 默认目标
help:
	@echo "JustDo - 可用命令："
	@echo ""
	@echo "  make install   - 安装依赖"
	@echo "  make dev       - 启动开发服务器（后台运行）"
	@echo "  make web       - 启动 Web 服务器"
	@echo "  make stop       - 停止开发服务器"
	@echo "  make test       - 运行测试"
	@echo "  make clean     - 清理临时文件"
	@echo "  make lint      - 代码检查"

# 安装依赖
install:
	pip install -e ".[cli,web,test]"

# 启动开发服务器（后台运行）
dev:
	@echo "启动开发服务器..."
	@.venv/bin/uvicorn justdo.api:app --host 0.0.0.0 --port 8848 --reload --log-level debug 2>&1 &

# 启动 Web 服务器（前台运行）
web:
	@echo "启动 Web 服务器 (http://0.0.0.0:8848)..."
	@.venv/bin/uvicorn justdo.api:app --host 0.0.0.0 --port 8848 --log-level info

# 停止开发服务器
stop:
	@echo "停止开发服务器..."
	@pkill -f "uvicorn justdo.api:app" || echo "服务器未运行"

# 运行测试
test:
	pytest

# 清理临时文件
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage

# 代码检查
lint:
	ruff check src/
	ruff format --check src/
