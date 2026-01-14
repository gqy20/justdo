"""集成测试：FastAPI Web API

测试 FastAPI 端点的行为
"""

import pytest
from pathlib import Path

from justdo.api import app
from justdo.manager import TodoManager


@pytest.fixture
def test_db_path(tmp_path):
    """创建临时数据库路径"""
    return tmp_path / "test_todos.json"


@pytest.fixture
def client(test_db_path):
    """创建测试客户端"""
    from fastapi.testclient import TestClient

    # 覆盖 TodoManager 的文件路径
    # 通过依赖注入或 monkey patch
    import justdo.api
    original_get_manager = justdo.api.get_manager

    def mock_get_manager():
        return TodoManager(str(test_db_path))

    justdo.api.get_manager = mock_get_manager

    from fastapi.testclient import TestClient
    _client = TestClient(app)

    yield _client

    # 恢复原始函数
    justdo.api.get_manager = original_get_manager


class TestAPITodos:
    """测试 /api/todos 端点"""

    def test_list_todos_empty(self, client):
        """测试：空列表应返回空数组"""
        response = client.get("/api/todos")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_todos_with_items(self, client):
        """测试：应返回所有任务"""
        # 先添加任务
        client.post("/api/todos", json={"text": "任务1", "priority": "medium"})
        client.post("/api/todos", json={"text": "任务2", "priority": "high"})

        # 获取列表
        response = client.get("/api/todos")
        assert response.status_code == 200
        todos = response.json()
        assert len(todos) == 2
        assert todos[0]["text"] == "任务1"
        assert todos[1]["text"] == "任务2"

    def test_list_todos_filter_done(self, client):
        """测试：应支持过滤已完成任务"""
        # 添加并完成一个任务
        r1 = client.post("/api/todos", json={"text": "任务1", "priority": "medium"})
        todo_id = r1.json()["id"]
        client.post(f"/api/todos/{todo_id}/done")

        # 添加另一个任务
        client.post("/api/todos", json={"text": "任务2", "priority": "medium"})

        # 只获取未完成
        response = client.get("/api/todos?done=false")
        assert response.status_code == 200
        todos = response.json()
        assert len(todos) == 1
        assert todos[0]["text"] == "任务2"


class TestAPICreateTodo:
    """测试创建任务"""

    def test_create_todo_success(self, client):
        """测试：应成功创建任务"""
        response = client.post("/api/todos", json={"text": "新任务", "priority": "high"})
        assert response.status_code == 201
        data = response.json()
        assert data["text"] == "新任务"
        assert data["priority"] == "high"
        assert "id" in data
        assert data["done"] is False

    def test_create_todo_default_priority(self, client):
        """测试：默认优先级应为 medium"""
        response = client.post("/api/todos", json={"text": "任务"})
        assert response.status_code == 201
        assert response.json()["priority"] == "medium"

    def test_create_todo_empty_text_raises_error(self, client):
        """测试：空文本应返回 400"""
        response = client.post("/api/todos", json={"text": "", "priority": "medium"})
        assert response.status_code == 422  # Pydantic 验证错误


class TestAPIMarkDone:
    """测试标记完成"""

    def test_mark_done_success(self, client):
        """测试：应成功标记任务为完成"""
        # 先创建任务
        r = client.post("/api/todos", json={"text": "任务", "priority": "medium"})
        todo_id = r.json()["id"]

        # 标记完成
        response = client.post(f"/api/todos/{todo_id}/done")
        assert response.status_code == 200
        assert response.json()["done"] is True

    def test_mark_done_nonexistent_raises_error(self, client):
        """测试：不存在的任务应返回 404"""
        response = client.post("/api/todos/99999/done")
        assert response.status_code == 404


class TestAPIDeleteTodo:
    """测试删除任务"""

    def test_delete_todo_success(self, client):
        """测试：应成功删除任务"""
        # 先创建任务
        r = client.post("/api/todos", json={"text": "任务", "priority": "medium"})
        todo_id = r.json()["id"]

        # 删除
        response = client.delete(f"/api/todos/{todo_id}")
        assert response.status_code == 204

        # 验证已删除
        response = client.get("/api/todos")
        assert len(response.json()) == 0

    def test_delete_nonexistent_raises_error(self, client):
        """测试：删除不存在的任务应返回 404"""
        response = client.delete("/api/todos/99999")
        assert response.status_code == 404


class TestAPIClear:
    """测试清空已完成任务"""

    def test_clear_removes_done_todos(self, client):
        """测试：应删除所有已完成任务"""
        # 添加任务
        r1 = client.post("/api/todos", json={"text": "任务1", "priority": "medium"})
        r2 = client.post("/api/todos", json={"text": "任务2", "priority": "medium"})

        # 完成一个
        todo_id = r1.json()["id"]
        client.post(f"/api/todos/{todo_id}/done")

        # 清空
        response = client.post("/api/clear")
        assert response.status_code == 200
        assert response.json()["cleared"] == 1

        # 验证只剩未完成的
        response = client.get("/api/todos")
        todos = response.json()
        assert len(todos) == 1
        assert todos[0]["text"] == "任务2"


class TestAPISuggest:
    """测试智能建议"""

    def test_suggest_returns_tasks(self, client):
        """测试：应返回按优先级排序的任务"""
        client.post("/api/todos", json={"text": "低优先级", "priority": "low"})
        client.post("/api/todos", json={"text": "高优先级", "priority": "high"})

        response = client.get("/api/suggest")
        assert response.status_code == 200
        data = response.json()
        assert "todos" in data
        assert len(data["todos"]) == 2
        assert data["todos"][0]["text"] == "高优先级"


class TestAPIChat:
    """测试 AI 对话"""

    @pytest.mark.skipif(not pytest.importorskip("os").getenv("OPENAI_API_KEY"), reason="需要 OPENAI_API_KEY")
    def test_chat_returns_response(self, client):
        """测试：应返回 AI 响应"""
        client.post("/api/todos", json={"text": "任务", "priority": "medium"})

        response = client.post("/api/chat", json={"message": "我接下来应该做什么"})
        assert response.status_code == 200
        assert "response" in response.json()
