"""单元测试：CLI 命令行接口

测试命令行参数解析和输出
"""

import pytest
from unittest.mock import patch, MagicMock
from io import StringIO
from todo.cli import main


class TestCLIAddCommand:
    """测试 add 命令"""

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "add", "学习 Python"])
    def test_add_command_calls_manager_add(self, mock_manager_class):
        """测试：add 命令应调用 manager.add()"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Act
        with patch("sys.stdout", new_callable=StringIO):
            main()

        # Assert
        mock_manager.add.assert_called_once_with("学习 Python", priority="medium")

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "add", "  空格测试  "])
    def test_add_trims_whitespace(self, mock_manager_class):
        """测试：add 应去除文本首尾空格"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_manager.add.return_value = MagicMock(id=1, text="空格测试")

        # Act
        with patch("sys.stdout", new_callable=StringIO):
            main()

        # Assert
        mock_manager.add.assert_called_once_with("空格测试", priority="medium")

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "add", "紧急任务", "-l", "1"])
    def test_add_with_high_priority_level(self, mock_manager_class):
        """测试：add -l 1 应调用 manager.add(text, priority='high')"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Act
        with patch("sys.stdout", new_callable=StringIO):
            main()

        # Assert
        mock_manager.add.assert_called_once_with("紧急任务", priority="high")

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "add", "任务", "-l", "3"])
    def test_add_with_low_priority_level(self, mock_manager_class):
        """测试：add -l 3 应调用 manager.add(text, priority='low')"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Act
        with patch("sys.stdout", new_callable=StringIO):
            main()

        # Assert
        mock_manager.add.assert_called_once_with("任务", priority="low")

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "add", "写报告", "--ai"])
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("todo.ai.AIHandler")
    def test_add_with_ai_flag_enhances_input(self, mock_ai_handler, mock_manager_class):
        """测试：add --ai 应使用 AI 优化任务描述"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_manager.add.return_value = MagicMock(id=1, text="写 2024 年度报告", priority_emoji="🔴")

        mock_ai = MagicMock()
        mock_ai_handler.return_value = mock_ai
        mock_ai.enhance_input.return_value = "写 2024 年度报告"

        # Act
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()

        # Assert - AI 应被调用优化输入
        mock_ai.enhance_input.assert_called_once_with("写报告")
        # manager.add 应使用优化后的文本
        mock_manager.add.assert_called_once_with("写 2024 年度报告", priority="medium")
        assert "AI 优化" in output or "已添加" in output

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "add", "写报告", "--ai"])
    @patch.dict("os.environ", {}, clear=True)
    def test_add_with_ai_flag_missing_key_shows_error(self, mock_manager_class):
        """测试：add --ai 但缺少 API key 应显示错误"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Act & Assert
        with pytest.raises(SystemExit):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                main()
                output = mock_stderr.getvalue()
                # 应该显示关于 API key 的错误信息
                assert "OPENAI_API_KEY" in output or "AI" in output


class TestCLIListCommand:
    """测试 list 命令"""

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "list"])
    def test_list_displays_all_todos(self, mock_manager_class):
        """测试：list 命令应显示所有任务"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_todo1 = MagicMock(id=1, text="任务 1", done=False)
        mock_todo2 = MagicMock(id=2, text="任务 2", done=True)
        mock_manager.list.return_value = [mock_todo1, mock_todo2]

        # Act
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()

        # Assert
        assert "任务 1" in output
        assert "任务 2" in output

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "list"])
    def test_list_empty_shows_message(self, mock_manager_class):
        """测试：空列表应显示提示信息"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_manager.list.return_value = []

        # Act
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()

        # Assert
        assert "暂无任务" in output or "empty" in output.lower()

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "list", "--done"])
    def test_list_with_done_filter(self, mock_manager_class):
        """测试：list --done 只显示已完成的任务"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_todo1 = MagicMock(id=1, text="未完成", done=False)
        mock_todo2 = MagicMock(id=2, text="已完成", done=True)
        mock_manager.list.return_value = [mock_todo1, mock_todo2]

        # Act
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()

        # Assert - 只显示已完成的任务
        assert "已完成" in output
        assert "未完成" not in output

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "list", "--undone"])
    def test_list_with_undone_filter(self, mock_manager_class):
        """测试：list --undone 只显示未完成的任务"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_todo1 = MagicMock(id=1, text="未完成", done=False)
        mock_todo2 = MagicMock(id=2, text="已完成", done=True)
        mock_manager.list.return_value = [mock_todo1, mock_todo2]

        # Act
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()

        # Assert - 只显示未完成的任务
        assert "未完成" in output
        assert "已完成" not in output


class TestCLISuggestCommand:
    """测试 suggest 命令"""

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "suggest"])
    def test_suggest_shows_priority_order(self, mock_manager_class):
        """测试：suggest 应按优先级排序显示任务"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_todo1 = MagicMock(id=1, text="高优先级", done=False, priority_weight=3, priority_emoji="🔴")
        mock_todo2 = MagicMock(id=2, text="低优先级", done=False, priority_weight=1, priority_emoji="🟢")
        mock_todo3 = MagicMock(id=3, text="中优先级", done=False, priority_weight=2, priority_emoji="🟡")
        mock_manager.list.return_value = [mock_todo1, mock_todo2, mock_todo3]

        # Act
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()

        # Assert
        # 应按优先级排序：高(1,weight=3) → 中(3,weight=2) → 低(2,weight=1)
        lines = [line for line in output.split('\n') if line.strip()]
        # 找到包含各 ID 的行索引
        line_1_idx = next(i for i, line in enumerate(lines) if "[1]" in line)
        line_3_idx = next(i for i, line in enumerate(lines) if "[3]" in line)
        line_2_idx = next(i for i, line in enumerate(lines) if "[2]" in line)
        # 验证顺序：1 在 3 之前，3 在 2 之前
        assert line_1_idx < line_3_idx < line_2_idx

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "suggest", "--ai"])
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("todo.ai.AIHandler")
    def test_suggest_with_ai_uses_ai_suggestion(self, mock_ai_handler, mock_manager_class):
        """测试：suggest --ai 应使用 AI 建议下一步"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_todo = MagicMock(id=1, text="写报告", done=False, priority="high")
        mock_manager.list.return_value = [mock_todo]

        mock_ai = MagicMock()
        mock_ai_handler.return_value = mock_ai
        mock_ai.suggest_next.return_value = "建议优先完成写报告任务"

        # Act
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()

        # Assert - AI 应被调用
        mock_ai.suggest_next.assert_called_once()
        assert "建议优先完成写报告任务" in output


class TestCLIDoneCommand:
    """测试 done 命令"""

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "done", "1"])
    def test_mark_done_calls_manager(self, mock_manager_class):
        """测试：done 命令应调用 manager.mark_done()"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Act
        with patch("sys.stdout", new_callable=StringIO):
            main()

        # Assert
        mock_manager.mark_done.assert_called_once_with(1)

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "done", "abc"])
    def test_done_with_invalid_id_shows_error(self, mock_manager_class):
        """测试：done 命令使用无效 ID 应显示错误（argparse 处理）"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Act & Assert - argparse 会阻止无效的 int 参数
        with pytest.raises(SystemExit):
            with patch("sys.stderr", new_callable=StringIO):
                main()

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "done", "1", "2", "3"])
    def test_done_with_multiple_ids(self, mock_manager_class):
        """测试：done 命令支持多个 ID"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Act
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()

        # Assert - 应调用三次 mark_done
        assert mock_manager.mark_done.call_count == 3
        mock_manager.mark_done.assert_any_call(1)
        mock_manager.mark_done.assert_any_call(2)
        mock_manager.mark_done.assert_any_call(3)
        # 验证输出
        assert "已标记为完成" in output or "标记" in output

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "done", "1-3"])
    def test_done_with_id_range(self, mock_manager_class):
        """测试：done 命令支持 ID 范围语法 1-3"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Act
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()

        # Assert - 应展开为 1, 2, 3
        assert mock_manager.mark_done.call_count == 3
        mock_manager.mark_done.assert_any_call(1)
        mock_manager.mark_done.assert_any_call(2)
        mock_manager.mark_done.assert_any_call(3)

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "done", "1", "3-5", "7"])
    def test_done_with_mixed_ids_and_ranges(self, mock_manager_class):
        """测试：done 命令支持混合 ID 和范围"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Act
        with patch("sys.stdout", new_callable=StringIO):
            main()

        # Assert - 1, 3, 4, 5, 7 共 5 个
        assert mock_manager.mark_done.call_count == 5
        mock_manager.mark_done.assert_any_call(1)
        mock_manager.mark_done.assert_any_call(3)
        mock_manager.mark_done.assert_any_call(4)
        mock_manager.mark_done.assert_any_call(5)
        mock_manager.mark_done.assert_any_call(7)


class TestCLIDeleteCommand:
    """测试 delete 命令"""

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "delete", "2"])
    def test_delete_calls_manager(self, mock_manager_class):
        """测试：delete 命令应调用 manager.delete()"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Act
        with patch("sys.stdout", new_callable=StringIO):
            main()

        # Assert
        mock_manager.delete.assert_called_once_with(2)

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "delete", "999"])
    def test_delete_nonexistent_shows_error(self, mock_manager_class):
        """测试：删除不存在的任务应显示错误"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_manager.delete.side_effect = ValueError("任务不存在")

        # Act & Assert - 应该捕获 SystemExit
        with pytest.raises(SystemExit):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                main()
                output = mock_stderr.getvalue()
                assert "错误" in output

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "delete", "1", "2", "3"])
    def test_delete_with_multiple_ids(self, mock_manager_class):
        """测试：delete 命令支持多个 ID"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Act
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()

        # Assert - 应调用三次 delete
        assert mock_manager.delete.call_count == 3
        mock_manager.delete.assert_any_call(1)
        mock_manager.delete.assert_any_call(2)
        mock_manager.delete.assert_any_call(3)
        # 验证输出
        assert "已删除" in output or "删除" in output

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "delete", "1-3"])
    def test_delete_with_id_range(self, mock_manager_class):
        """测试：delete 命令支持 ID 范围语法 1-3"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Act
        with patch("sys.stdout", new_callable=StringIO):
            main()

        # Assert - 应展开为 1, 2, 3
        assert mock_manager.delete.call_count == 3
        mock_manager.delete.assert_any_call(1)
        mock_manager.delete.assert_any_call(2)
        mock_manager.delete.assert_any_call(3)

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "delete", "1", "3-5"])
    def test_delete_with_mixed_ids_and_ranges(self, mock_manager_class):
        """测试：delete 命令支持混合 ID 和范围"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Act
        with patch("sys.stdout", new_callable=StringIO):
            main()

        # Assert - 1, 3, 4, 5 共 4 个
        assert mock_manager.delete.call_count == 4
        mock_manager.delete.assert_any_call(1)
        mock_manager.delete.assert_any_call(3)
        mock_manager.delete.assert_any_call(4)
        mock_manager.delete.assert_any_call(5)


class TestCLIClearCommand:
    """测试 clear 命令"""

    @patch("todo.cli.TodoManager")
    @patch("sys.argv", ["todo.py", "clear"])
    def test_clear_calls_manager(self, mock_manager_class):
        """测试：clear 命令应调用 manager.clear()"""
        # Arrange
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Act
        with patch("sys.stdout", new_callable=StringIO):
            main()

        # Assert
        mock_manager.clear.assert_called_once()


class TestCLIInvalidCommand:
    """测试无效命令"""

    @patch("sys.argv", ["todo.py", "invalid"])
    def test_invalid_command_shows_help(self):
        """测试：无效命令应显示帮助信息"""
        # Act & Assert
        with pytest.raises(SystemExit):
            with patch("sys.stdout", new_callable=StringIO):
                main()
