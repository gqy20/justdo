"""单元测试：数据模型类

测试 TodoItem 数据模型的创建和序列化
"""

import pytest
from todo.models import TodoItem


class TestTodoItemCreation:
    """测试 TodoItem 创建功能"""

    def test_create_todo_item_with_valid_text(self):
        """测试：使用有效文本创建 TodoItem 应成功"""
        # Arrange（准备）
        text = "购买牛奶"

        # Act（执行）
        todo = TodoItem(id=1, text=text, done=False)

        # Assert（断言）
        assert todo.id == 1, "TodoItem id 应该等于 1"
        assert todo.text == "购买牛奶", "TodoItem text 应该等于 '购买牛奶'"
        assert todo.done is False, "TodoItem done 应该为 False"

    def test_create_todo_item_empty_text_raises_error(self):
        """测试：使用空文本创建 TodoItem 应抛出异常"""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="文本不能为空"):
            TodoItem(id=1, text="", done=False)

    def test_create_todo_item_none_text_raises_error(self):
        """测试：使用 None 文本创建 TodoItem 应抛出异常"""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="文本不能为空"):
            TodoItem(id=1, text=None, done=False)

    def test_create_todo_item_negative_id_raises_error(self):
        """测试：使用负数 ID 创建 TodoItem 应抛出异常"""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="ID 必须为正整数"):
            TodoItem(id=-1, text="测试", done=False)


class TestTodoItemSerialization:
    """测试 TodoItem 序列化功能"""

    def test_to_dict_returns_correct_format(self):
        """测试：to_dict 应返回正确格式的字典"""
        # Arrange
        todo = TodoItem(id=1, text="写代码", done=False)

        # Act
        result = todo.to_dict()

        # Assert
        expected = {"id": 1, "text": "写代码", "done": False}
        assert result == expected, f"to_dict 应返回 {expected}"

    def test_from_dict_creates_valid_todo_item(self):
        """测试：from_dict 应从字典创建有效的 TodoItem"""
        # Arrange
        data = {"id": 5, "text": "学习 TDD", "done": True}

        # Act
        todo = TodoItem.from_dict(data)

        # Assert
        assert todo.id == 5, "TodoItem id 应该等于 5"
        assert todo.text == "学习 TDD", "TodoItem text 应该等于 '学习 TDD'"
        assert todo.done is True, "TodoItem done 应该为 True"

    def test_from_dict_with_missing_fields_raises_error(self):
        """测试：from_dict 缺少必要字段应抛出异常"""
        # Arrange
        incomplete_data = {"id": 1}  # 缺少 text 和 done

        # Act & Assert
        with pytest.raises(KeyError):
            TodoItem.from_dict(incomplete_data)


class TestTodoItemEquality:
    """测试 TodoItem 相等性比较"""

    def test_two_todos_with_same_values_are_equal(self):
        """测试：相同值的两个 TodoItem 应相等"""
        # Arrange
        todo1 = TodoItem(id=1, text="测试", done=False)
        todo2 = TodoItem(id=1, text="测试", done=False)

        # Act & Assert
        assert todo1 == todo2, "相同值的 TodoItem 应该相等"

    def test_two_todos_with_different_ids_are_not_equal(self):
        """测试：不同 ID 的 TodoItem 不应相等"""
        # Arrange
        todo1 = TodoItem(id=1, text="测试", done=False)
        todo2 = TodoItem(id=2, text="测试", done=False)

        # Act & Assert
        assert todo1 != todo2, "不同 ID 的 TodoItem 不应该相等"


class TestTodoItemPriority:
    """测试 TodoItem 优先级功能"""

    def test_create_todo_item_with_valid_priority(self):
        """测试：使用有效优先级创建 TodoItem 应成功"""
        # Arrange & Act
        todo = TodoItem(id=1, text="测试", done=False, priority="high")

        # Assert
        assert todo.priority == "high", "TodoItem priority 应该等于 'high'"

    def test_create_todo_item_default_priority_is_medium(self):
        """测试：不指定优先级时应默认为 medium"""
        # Arrange & Act
        todo = TodoItem(id=1, text="测试", done=False)

        # Assert
        assert todo.priority == "medium", "默认优先级应该是 'medium'"

    def test_create_todo_item_with_invalid_priority_raises_error(self):
        """测试：使用无效优先级应抛出异常"""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="优先级必须是.*之一"):
            TodoItem(id=1, text="测试", done=False, priority="urgent")

    def test_to_dict_includes_priority(self):
        """测试：to_dict 应包含 priority 字段"""
        # Arrange
        todo = TodoItem(id=1, text="测试", done=False, priority="low")

        # Act
        result = todo.to_dict()

        # Assert
        assert "priority" in result, "to_dict 应包含 priority 字段"
        assert result["priority"] == "low", "priority 应该等于 'low'"

    def test_from_dict_with_priority(self):
        """测试：from_dict 应正确解析 priority"""
        # Arrange
        data = {"id": 1, "text": "测试", "done": False, "priority": "high"}

        # Act
        todo = TodoItem.from_dict(data)

        # Assert
        assert todo.priority == "high", "from_dict 应正确解析 priority"

    def test_from_dict_without_priority_defaults_to_medium(self):
        """测试：from_dict 缺少 priority 时应默认为 medium"""
        # Arrange
        data = {"id": 1, "text": "测试", "done": False}

        # Act
        todo = TodoItem.from_dict(data)

        # Assert
        assert todo.priority == "medium", "缺少 priority 时应默认为 'medium'"
