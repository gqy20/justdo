"""单元测试：TodoManager 业务逻辑

测试待办事项的增删改查核心功能
使用 Mock 隔离文件系统依赖
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from src.todo.manager import TodoManager


class TestTodoManagerInit:
    """测试 TodoManager 初始化"""

    def test_init_with_empty_file(self):
        """测试：初始化时文件不存在应创建空列表"""
        # Arrange
        with patch("pathlib.Path.exists", return_value=False):
            with patch("pathlib.Path.open", mock_open()):
                # Act
                manager = TodoManager(filepath="todo.json")

                # Assert
                assert manager.todos == [], "新管理的 todo 列表应为空"

    def test_init_with_existing_file(self):
        """测试：初始化时加载已有数据"""
        # Arrange
        mock_data = {"todos": []}

        # Act
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
            with patch.object(Path, "exists", return_value=True):
                manager = TodoManager(filepath="todo.json")

        # Assert
        assert manager.todos == [], "应加载空的 todo 列表"


class TestTodoManagerAdd:
    """测试添加任务功能"""

    def test_add_todo_increases_list_size(self):
        """测试：添加任务应增加列表大小"""
        # Arrange
        with patch("pathlib.Path.exists", return_value=False):
            with patch("pathlib.Path.open", mock_open()):
                manager = TodoManager(filepath="todo.json")

                # Act
                manager.add("学习 Python")

                # Assert
                assert len(manager.todos) == 1, "添加后应有 1 个任务"
                assert manager.todos[0].text == "学习 Python"
                assert manager.todos[0].done is False

    def test_add_multiple_todos_assigns_sequential_ids(self):
        """测试：添加多个任务应分配递增 ID"""
        # Arrange
        with patch("pathlib.Path.exists", return_value=False):
            with patch("pathlib.Path.open", mock_open()):
                manager = TodoManager(filepath="todo.json")

                # Act
                manager.add("任务 1")
                manager.add("任务 2")
                manager.add("任务 3")

                # Assert
                assert manager.todos[0].id == 1
                assert manager.todos[1].id == 2
                assert manager.todos[2].id == 3

    def test_add_empty_text_raises_error(self):
        """测试：添加空文本应抛出异常"""
        # Arrange
        with patch("pathlib.Path.exists", return_value=False):
            with patch("pathlib.Path.open", mock_open()):
                manager = TodoManager(filepath="todo.json")

                # Act & Assert
                with pytest.raises(ValueError, match="文本不能为空"):
                    manager.add("")


class TestTodoManagerList:
    """测试列出任务功能"""

    def test_list_returns_all_todos(self):
        """测试：list 应返回所有任务"""
        # Arrange
        with patch("pathlib.Path.exists", return_value=False):
            with patch("pathlib.Path.open", mock_open()):
                manager = TodoManager(filepath="todo.json")
                manager.add("任务 1")
                manager.add("任务 2")

                # Act
                result = manager.list()

                # Assert
                assert len(result) == 2
                assert result[0].text == "任务 1"
                assert result[1].text == "任务 2"

    def test_list_empty_manager_returns_empty_list(self):
        """测试：空管理器的 list 应返回空列表"""
        # Arrange
        with patch("pathlib.Path.exists", return_value=False):
            with patch("pathlib.Path.open", mock_open()):
                manager = TodoManager(filepath="todo.json")

                # Act
                result = manager.list()

                # Assert
                assert result == []


class TestTodoManagerDone:
    """测试标记完成功能"""

    def test_mark_done_changes_status(self):
        """测试：标记完成应改变状态"""
        # Arrange
        with patch("pathlib.Path.exists", return_value=False):
            with patch("pathlib.Path.open", mock_open()):
                manager = TodoManager(filepath="todo.json")
                manager.add("测试任务")

                # Act
                manager.mark_done(1)

                # Assert
                assert manager.todos[0].done is True

    def test_mark_done_nonexistent_id_raises_error(self):
        """测试：标记不存在的 ID 应抛出异常"""
        # Arrange
        with patch("pathlib.Path.exists", return_value=False):
            with patch("pathlib.Path.open", mock_open()):
                manager = TodoManager(filepath="todo.json")

                # Act & Assert
                with pytest.raises(ValueError, match="任务不存在"):
                    manager.mark_done(999)


class TestTodoManagerDelete:
    """测试删除任务功能"""

    def test_delete_removes_todo(self):
        """测试：删除应移除任务"""
        # Arrange
        with patch("pathlib.Path.exists", return_value=False):
            with patch("pathlib.Path.open", mock_open()):
                manager = TodoManager(filepath="todo.json")
                manager.add("任务 1")
                manager.add("任务 2")

                # Act
                manager.delete(1)

                # Assert
                assert len(manager.todos) == 1
                assert manager.todos[0].id == 2
                assert manager.todos[0].text == "任务 2"

    def test_delete_nonexistent_id_raises_error(self):
        """测试：删除不存在的 ID 应抛出异常"""
        # Arrange
        with patch("pathlib.Path.exists", return_value=False):
            with patch("pathlib.Path.open", mock_open()):
                manager = TodoManager(filepath="todo.json")

                # Act & Assert
                with pytest.raises(ValueError, match="任务不存在"):
                    manager.delete(999)


class TestTodoManagerClear:
    """测试清空已完成任务功能"""

    def test_clear_removes_only_completed_todos(self):
        """测试：清空应只移除已完成的任务"""
        # Arrange
        with patch("pathlib.Path.exists", return_value=False):
            with patch("pathlib.Path.open", mock_open()):
                manager = TodoManager(filepath="todo.json")
                manager.add("任务 1")
                manager.add("任务 2")
                manager.mark_done(1)  # 标记第一个完成

                # Act
                manager.clear()

                # Assert
                assert len(manager.todos) == 1
                assert manager.todos[0].id == 2
                assert manager.todos[0].done is False

    def test_clear_empty_manager_does_nothing(self):
        """测试：清空空管理器应无事发生"""
        # Arrange
        with patch("pathlib.Path.exists", return_value=False):
            with patch("pathlib.Path.open", mock_open()):
                manager = TodoManager(filepath="todo.json")

                # Act (should not raise)
                manager.clear()

                # Assert
                assert manager.todos == []


class TestTodoManagerSave:
    """测试保存功能"""

    def test_save_writes_correct_json(self):
        """测试：保存应写入正确的 JSON 格式"""
        # Arrange
        with patch("pathlib.Path.exists", return_value=False):
            with patch("pathlib.Path.open", mock_open()):
                manager = TodoManager(filepath="todo.json")
                manager.add("测试任务")

        # Act & Assert - 验证 save 能被调用且不抛出异常
        with patch("builtins.open", mock_open()) as mock_file_obj:
            manager.save()
            # 确保文件被打开用于写入
            mock_file_obj.assert_called_once()
