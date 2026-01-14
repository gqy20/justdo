"""单元测试：任务分析模块

测试任务分类、时段感知和情绪检测功能
"""

import pytest
from datetime import datetime
from unittest.mock import patch
from todo.task_analyzer import (
    TaskCategory,
    TaskAnalyzer,
    categorize_task,
    detect_emotion,
    get_time_context,
)


class TestCategorizeTask:
    """测试任务分类功能"""

    def test_categorize_work_task(self):
        """测试：识别工作任务"""
        # Act
        category = categorize_task("完成项目报告")

        # Assert
        assert category == TaskCategory.WORK

    def test_categorize_study_task(self):
        """测试：识别学习任务"""
        # Act
        category = categorize_task("阅读第3章")

        # Assert
        assert category == TaskCategory.STUDY

    def test_categorize_exercise_task(self):
        """测试：识别运动任务"""
        # Act
        category = categorize_task("晨跑3公里")

        # Assert
        assert category == TaskCategory.EXERCISE

    def test_categorize_life_task(self):
        """测试：识别生活任务"""
        # Act
        category = categorize_task("去超市购物")

        # Assert
        assert category == TaskCategory.LIFE

    def test_categorize_unknown_task(self):
        """测试：未知任务类型"""
        # Act
        category = categorize_task("随便做点什么")

        # Assert
        assert category == TaskCategory.OTHER

    def test_categorize_handles_chinese_keywords(self):
        """测试：支持中文关键词"""
        # Assert
        assert categorize_task("开会被取消") == TaskCategory.WORK
        assert categorize_task("修复登录bug") == TaskCategory.WORK
        assert categorize_task("学习Python基础") == TaskCategory.STUDY
        assert categorize_task("健身30分钟") == TaskCategory.EXERCISE
        assert categorize_task("做饭") == TaskCategory.LIFE


class TestDetectEmotion:
    """测试情绪检测功能"""

    def test_detect_anxiety_from_urgent_keywords(self):
        """测试：从紧急关键词检测焦虑"""
        # Act
        emotion = detect_emotion("必须今天完成否则死定了")

        # Assert
        assert emotion.anxiety_level > 0.5
        assert "必须" in emotion.keywords

    def test_detect_anxiety_from_pressure_words(self):
        """测试：从压力词检测焦虑"""
        # Act
        emotion = detect_emotion("来不及了快来不及")

        # Assert
        assert emotion.anxiety_level > 0.5

    def test_no_anxiety_in_normal_task(self):
        """测试：正常任务无焦虑"""
        # Act
        emotion = detect_emotion("写报告")

        # Assert
        assert emotion.anxiety_level < 0.3

    def test_detect_anxiety_multiple_keywords(self):
        """测试：多个焦虑关键词累加"""
        # Act
        emotion = detect_emotion("必须紧急完成这个任务")

        # Assert
        assert emotion.anxiety_level > 0.7

    def test_emotion_keywords_extraction(self):
        """测试：提取情绪关键词"""
        # Act
        emotion = detect_emotion("必须马上完成")

        # Assert
        assert len(emotion.keywords) > 0
        assert any(k in ["必须", "马上"] for k in emotion.keywords)


class TestGetTimeContext:
    """测试时段感知功能"""

    @patch('todo.task_analyzer.datetime')
    def test_morning_context(self, mock_datetime):
        """测试：早晨时段（6-9点）"""
        # Arrange
        mock_datetime.now.return_value.hour = 7

        # Act
        context = get_time_context()

        # Assert
        assert context == "早晨"

    @patch('todo.task_analyzer.datetime')
    def test_late_night_context(self, mock_datetime):
        """测试：深夜时段（22点后）"""
        # Arrange
        mock_datetime.now.return_value.hour = 23

        # Act
        context = get_time_context()

        # Assert
        assert context == "深夜"

    @patch('todo.task_analyzer.datetime')
    def test_afternoon_context(self, mock_datetime):
        """测试：下午时段（14-18点）"""
        # Arrange
        mock_datetime.now.return_value.hour = 15

        # Act
        context = get_time_context()

        # Assert
        assert context == "下午"


class TestTaskAnalyzer:
    """测试任务分析器集成"""

    def test_analyze_task_returns_complete_context(self):
        """测试：分析任务返回完整上下文"""
        # Arrange
        analyzer = TaskAnalyzer()

        # Act
        context = analyzer.analyze("完成项目报告")

        # Assert
        assert "category" in context
        assert "emotion" in context
        assert "time_context" in context
        assert context["category"] == TaskCategory.WORK

    @patch('todo.task_analyzer.datetime')
    def test_analyze_includes_time_context(self, mock_datetime):
        """测试：分析包含时段上下文"""
        # Arrange
        mock_datetime.now.return_value.hour = 10
        analyzer = TaskAnalyzer()

        # Act
        context = analyzer.analyze("学习Python")

        # Assert
        assert context["time_context"] == "上午"
        assert context["category"] == TaskCategory.STUDY

    def test_analyze_detects_emotion(self):
        """测试：分析检测情绪"""
        # Arrange
        analyzer = TaskAnalyzer()

        # Act
        context = analyzer.analyze("必须完成这个任务")

        # Assert
        assert context["emotion"].anxiety_level > 0.5
        assert "必须" in context["emotion"].keywords
