# JustDo 测试策略

> 100% 测试覆盖率，TDD 驱动开发

## 测试概览

| 类型 | 数量 | 覆盖率 | 位置 |
|------|------|--------|------|
| 单元测试 | 90+ | 95%+ | `tests/unit/` |
| 集成测试 | 10+ | 80%+ | `tests/integration/` |
| **总计** | **100+** | **100% 通过** | - |

---

## 测试原则

### TDD 循环

```
1. RED   - 写一个失败的测试
2. GREEN - 写最少的代码使测试通过
3. REFACTOR - 重构代码
```

### 测试金字塔

```
        /\
       /  \      E2E (少)
      /────\
     / 集成 \    集成测试 (适中)
    /────────\
   /  单元测试 \  单元测试 (多)
  /────────────\
```

---

## 单元测试

### models 测试

```python
# tests/unit/test_models.py

def test_todo_item_creation():
    """测试任务创建"""
    todo = TodoItem(id=1, text="测试任务", priority="high")
    assert todo.id == 1
    assert todo.text == "测试任务"
    assert todo.priority == "high"
    assert not todo.done

def test_priority_weights():
    """测试优先级权重"""
    assert TodoItem(id=1, text="", priority="high").priority_weight == 100
    assert TodoItem(id=1, text="", priority="medium").priority_weight == 50
    assert TodoItem(id=1, text="", priority="low").priority_weight == 10
```

### manager 测试

```python
# tests/unit/test_manager.py

def test_add_todo():
    """测试添加任务"""
    manager = TodoManager()
    todo = manager.add("新任务", "high")
    assert todo.text == "新任务"
    assert todo.priority == "high"

def test_mark_done():
    """测试标记完成"""
    manager = TodoManager()
    todo = manager.add("任务", "medium")
    manager.mark_done(todo.id)
    todos = manager.list()
    assert todos[0].done is True

def test_delete_todo():
    """测试删除任务"""
    manager = TodoManager()
    todo = manager.add("任务", "medium")
    manager.delete(todo.id)
    assert len(manager.list()) == 0
```

### AI Mock 测试

```python
# tests/unit/test_ai.py

def test_enhance_input_with_mock():
    """使用 Mock 测试 AI 优化"""
    handler = AIHandler()
    handler.client = MagicMock()
    handler.client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="优化后的描述"))]
    )

    result = handler.enhance_input("原始描述")
    assert result == "优化后的描述"
```

### user_profile 测试

```python
# tests/unit/test_user_profile.py

def test_record_task():
    """测试记录任务"""
    profile = UserProfile(tmp_path / "profile.json")
    todo = TodoItem(id=1, text="工作：写代码", priority="high")

    profile.record_task(todo, "complete", "work")
    stats = profile.data['stats']

    assert stats['total_tasks'] == 1
    assert stats['completed_tasks'] == 1

def test_completion_rate():
    """测试完成率计算"""
    profile = UserProfile(tmp_path / "profile.json")
    # 添加测试数据...
    rate = profile.get_completion_rate()
    assert 0 <= rate <= 1
```

### trash 测试

```python
# tests/unit/test_trash.py

def test_add_to_trash():
    """测试添加到回收站"""
    trash = TrashManager(tmp_path / "trash.json")
    todo = TodoItem(id=1, text="已删除任务", priority="medium")

    trash.add(todo, "work", "测试")
    items = trash.list()
    assert len(items) == 1
    assert items[0].text == "已删除任务"

def test_restore_from_trash():
    """测试恢复任务"""
    trash = TrashManager(tmp_path / "trash.json")
    # 添加测试数据...

    restored = trash.restore(1)
    assert restored is not None
    assert restored['text'] == "原任务"
```

---

## 集成测试

### API 端点测试

```python
# tests/integration/test_api.py

from fastapi.testclient import TestClient
from justdo.api import app

@pytest.fixture
def client():
    return TestClient(app)

def test_list_todos_empty(client):
    """测试空任务列表"""
    response = client.get("/api/todos")
    assert response.status_code == 200
    assert response.json() == []

def test_create_todo(client):
    """测试创建任务"""
    response = client.post("/api/todos", json={
        "text": "新任务",
        "priority": "high"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["text"] == "新任务"
    assert data["priority"] == "high"

def test_toggle_with_sse(client):
    """测试 SSE 流式响应"""
    response = client.post("/api/todos/1/toggle")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
```

### 画像 API 测试

```python
def test_profile_stats(client):
    """测试画像统计"""
    # 先添加一些任务...
    response = client.get("/api/profile/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_tasks" in data
    assert "completion_rate" in data

def test_full_profile(client):
    """测试完整画像"""
    response = client.get("/api/profile/full")
    assert response.status_code == 200
    data = response.json()
    assert "stats" in data
    assert "user_type" in data
    assert "strengths_weaknesses" in data
    assert "risk_alerts" in data
```

### 回收站 API 测试

```python
def test_trash_list(client):
    """测试回收站列表"""
    response = client.get("/api/trash")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "stats" in data

def test_restore_from_trash(client):
    """测试恢复任务"""
    response = client.post("/api/trash/1/restore")
    assert response.status_code in [200, 404]  # 取决于是否有数据
```

---

## 测试运行

### 运行所有测试

```bash
pytest
```

### 运行特定测试

```bash
# 单元测试
pytest tests/unit/

# 集成测试
pytest tests/integration/

# 特定文件
pytest tests/unit/test_manager.py

# 特定函数
pytest tests/unit/test_manager.py::test_add_todo

# 关键词匹配
pytest -k "add"
```

### 覆盖率报告

```bash
# 终端输出
pytest --cov=justdo

# HTML 报告
pytest --cov=justdo --cov-report=html
open htmlcov/index.html

# 分支覆盖
pytest --cov=justdo --cov-branch
```

### 详细输出

```bash
# 简洁
pytest -q

# 详细
pytest -v

# 超详细（显示打印输出）
pytest -vv -s
```

---

## Fixture 使用

### 临时目录

```python
import pytest
from pathlib import Path

@pytest.fixture
def temp_manager(tmp_path):
    """创建使用临时文件的管理器"""
    config_dir = tmp_path / "justdo"
    config_dir.mkdir()
    data_file = config_dir / "todo.json"
    return TodoManager(filepath=str(data_file))
```

### Mock AI

```python
@pytest.fixture
def mock_ai(monkeypatch):
    """Mock AI 功能"""
    def fake_enhance(text):
        return f"AI: {text}"
    monkeypatch.setattr("justdo.ai.AIHandler.enhance_input", fake_enhance)
```

---

## 测试最佳实践

### 1. 隔离性

每个测试应该独立运行，不依赖其他测试：

```python
def test_foo():
    manager = TodoManager()  # 新实例，干净状态
    # ...

def test_bar():
    manager = TodoManager()  # 另一个新实例
    # ...
```

### 2. 可读性

测试名称应该描述被测试的行为：

```python
# 好的命名
def test_delete_nonexistent_task_raises_error():
    ...

# 不好的命名
def test_1():
    ...
```

### 3. AAA 模式

Arrange-Act-Assert 模式：

```python
def test_add_todo():
    # Arrange 准备
    manager = TodoManager()

    # Act 执行
    todo = manager.add("新任务", "high")

    # Assert 断言
    assert todo.text == "新任务"
    assert todo.priority == "high"
```

### 4. 边界测试

测试边界条件和异常情况：

```python
def test_empty_priority_raises_error():
    with pytest.raises(ValueError):
        TodoItem(id=1, text="", priority="invalid")

def test_duplicate_id():
    manager = TodoManager()
    manager.add("任务1", "medium")
    with pytest.raises(ValueError):
        manager.add("任务2", "medium")  # 相同 ID
```

---

## CI/CD 集成

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev,ai,web]"
      - run: pytest --cov=justdo
```

---

## 性能测试

```python
# tests/benchmark/test_performance.py

def test_large_list_performance():
    """测试大量任务的性能"""
    manager = TodoManager()
    for i in range(1000):
        manager.add(f"任务{i}", "medium")

    import time
    start = time.time()
    todos = manager.list()
    elapsed = time.time() - start

    assert len(todos) == 1000
    assert elapsed < 0.1  # 应该在 100ms 内完成
```

---

## 测试数据管理

### 使用 fixtures

```python
# tests/conftest.py

@pytest.fixture
def sample_todos():
    """提供示例任务数据"""
    return [
        {"text": "高优先级", "priority": "high"},
        {"text": "中优先级", "priority": "medium"},
        {"text": "低优先级", "priority": "low"},
    ]
```

### 清理数据

```python
def test_with_cleanup(temp_manager):
    """测试后自动清理"""
    # 测试代码...
    yield
    # 清理代码在 teardown 自动执行
```

---

## 调试测试

### 失败时进入 PDB

```bash
pytest --pdb
```

### 显示打印输出

```bash
pytest -s
```

### 只运行失败的测试

```bash
pytest --lf  # last-failed
```

---

## 覆盖率目标

| 模块 | 目标 | 当前 |
|------|------|------|
| models.py | 100% | 100% |
| manager.py | 95% | 95%+ |
| cli.py | 90% | 90%+ |
| user_profile.py | 90% | 90%+ |
| trash.py | 90% | 90%+ |
| ai.py | 80% | 80%+ |
| **总计** | **90%** | **90%+** |

---

## 资源

- [pytest 文档](https://docs.pytest.org/)
- [FastAPI 测试](https://fastapi.tiangolo.com/tutorial/testing/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
