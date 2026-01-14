"""单元测试：UserProfile 用户画像

测试简洁的用户画像系统，100天内不超过10KB
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

from todo.user_profile import UserProfile
from todo.models import TodoItem


class TestUserProfileInit:
    """测试 UserProfile 初始化"""

    def test_init_creates_new_profile(self):
        """测试：初始化应创建新画像"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "profile.json"

            # Act
            profile = UserProfile(str(path))

            # Assert
            assert profile.data['version'] == 1
            assert profile.data['stats']['total_tasks'] == 0
            assert profile.data['stats']['completed_tasks'] == 0
            assert profile.data['stats']['current_streak'] == 0

    def test_init_loads_existing_profile(self):
        """测试：应加载已存在的画像"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "profile.json"
            existing_data = {
                "version": 1,
                "created_at": "2025-01-01",
                "stats": {
                    "total_tasks": 10,
                    "completed_tasks": 8,
                    "current_streak": 3
                }
            }
            path.write_text(json.dumps(existing_data))

            # Act
            profile = UserProfile(str(path))

            # Assert
            assert profile.data['stats']['total_tasks'] == 10
            assert profile.data['stats']['completed_tasks'] == 8


class TestUserProfileRecordTask:
    """测试记录任务事件"""

    def test_record_add_increments_total(self):
        """测试：添加任务应增加总数"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "profile.json"
            profile = UserProfile(str(path))
            todo = TodoItem(id=1, text="测试任务", priority="medium")

            # Act
            profile.record_task(todo, 'add')

            # Assert
            assert profile.data['stats']['total_tasks'] == 1

    def test_record_complete_increments_completed(self):
        """测试：完成任务应增加完成数"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "profile.json"
            profile = UserProfile(str(path))
            todo = TodoItem(id=1, text="测试任务", priority="medium")

            # Act
            profile.record_task(todo, 'complete')

            # Assert
            assert profile.data['stats']['completed_tasks'] == 1

    @patch('todo.user_profile.datetime')
    def test_record_complete_updates_hourly_activity(self, mock_dt):
        """测试：完成应更新时段活动"""
        mock_dt.now.return_value.hour = 14

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "profile.json"
            profile = UserProfile(str(path))
            todo = TodoItem(id=1, text="测试任务", priority="medium")

            # Act
            profile.record_task(todo, 'complete')

            # Assert
            assert profile.data['hourly_activity'][14] == 1

    @patch('todo.user_profile.datetime')
    def test_record_complete_updates_streak(self, mock_dt):
        """测试：完成应更新连续天数"""
        mock_dt.now.return_value = datetime(2025, 1, 14, 14, 0, 0)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "profile.json"
            profile = UserProfile(str(path))
            todo = TodoItem(id=1, text="测试任务", priority="medium")

            # Act
            profile.record_task(todo, 'complete')

            # Assert
            assert profile.data['stats']['current_streak'] == 1

    def test_record_delete_decrements_total(self):
        """测试：删除任务应减少总数"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "profile.json"
            profile = UserProfile(str(path))
            todo = TodoItem(id=1, text="测试任务", priority="medium")
            profile.record_task(todo, 'add')

            # Act
            profile.record_task(todo, 'delete')

            # Assert
            assert profile.data['stats']['total_tasks'] == 0


class TestUserProfileSizeLimit:
    """测试大小限制"""

    def test_profile_size_under_10kb(self):
        """测试：画像大小应不超过10KB"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "profile.json"
            profile = UserProfile(str(path))

            # 添加100个任务（ID从1开始）
            for i in range(1, 101):
                todo = TodoItem(id=i, text=f"任务{i}", priority="medium")
                profile.record_task(todo, 'add')
                if i % 2 == 0:
                    profile.record_task(todo, 'complete')

            profile.save()

            # Assert
            size = path.stat().st_size
            assert size < 10 * 1024, f"Profile size {size} exceeds 10KB limit"


class TestUserProfileStatsCalc:
    """测试统计计算"""

    def test_get_completion_rate(self):
        """测试：计算完成率"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "profile.json"
            profile = UserProfile(str(path))

            # 添加10个任务，完成8个
            for i in range(1, 11):
                todo = TodoItem(id=i, text=f"任务{i}", priority="medium")
                profile.record_task(todo, 'add')
                if i <= 8:
                    profile.record_task(todo, 'complete')

            # Act
            rate = profile.get_completion_rate()

            # Assert
            assert rate == 0.8

    def test_get_peak_hours_empty(self):
        """测试：无数据时返回空列表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "profile.json"
            profile = UserProfile(str(path))

            # Act
            hours = profile.get_peak_hours()

            # Assert
            assert hours == []

    @patch('todo.user_profile.datetime')
    def test_get_peak_hours_returns_top_hours(self, mock_dt):
        """测试：返回活跃时段"""
        mock_dt.now.return_value.hour = 14

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "profile.json"
            profile = UserProfile(str(path))

            # 在不同时段完成任务
            for hour in [9, 9, 9, 14, 14, 14, 14, 15, 15]:
                mock_dt.now.return_value.hour = hour
                todo = TodoItem(id=hour, text=f"任务{hour}", priority="medium")
                profile.record_task(todo, 'complete')

            # Act
            hours = profile.get_peak_hours()

            # Assert
            assert hours == [14, 9, 15]


class TestUserProfileContext:
    """测试 AI 上下文生成"""

    @patch('todo.user_profile.datetime')
    def test_get_context_for_ai(self, mock_dt):
        """测试：生成 AI 上下文字符串"""
        mock_dt.now.return_value = datetime(2025, 1, 14, 14, 0, 0)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "profile.json"
            profile = UserProfile(str(path))

            todo = TodoItem(id=1, text="完成项目报告", priority="high")
            profile.record_task(todo, 'add')
            profile.record_task(todo, 'complete')

            # Act
            context = profile.get_context_for_ai()

            # Assert
            assert "完成率" in context
            assert "连续" in context
            assert "100.0%" in context


class TestUserProfilePersistence:
    """测试持久化"""

    def test_save_persists_to_disk(self):
        """测试：save 应写入磁盘"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "profile.json"
            profile = UserProfile(str(path))

            todo = TodoItem(id=1, text="测试任务", priority="medium")
            profile.record_task(todo, 'complete')
            profile.save()

            # Assert
            content = json.loads(path.read_text())
            assert content['stats']['completed_tasks'] == 1

    def test_save_updates_timestamp(self):
        """测试：save 应更新时间戳"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "profile.json"
            profile = UserProfile(str(path))

            import time
            time.sleep(0.01)  # 小延迟确保时间戳更新
            profile.save()

            # Assert - 只检查是否有更新，不精确比较
            assert profile.data['last_updated'] is not None
            assert 'T' in profile.data['last_updated']  # ISO格式包含T
