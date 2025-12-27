# Todo CLI - 命令行待办事项工具

## 技术栈
- Python 3.x
- pytest (测试框架)
- argparse (命令行解析)
- JSON (数据存储)

## 项目结构
```
todo-cli/
├── src/
│   └── todo/
│       ├── __init__.py
│       ├── models.py      # 数据模型
│       ├── manager.py     # 核心业务逻辑
│       └── cli.py         # 命令行接口
├── tests/
│   └── unit/
│       ├── test_models.py
│       ├── test_manager.py
│       └── test_cli.py
├── todo.json              # 数据存储（自动生成）
├── requirements.txt
└── README.md
```

## 功能
- `add` - 添加任务
- `list` - 列出所有任务
- `done` - 标记任务完成
- `delete` - 删除任务
- `clear` - 清空已完成任务
