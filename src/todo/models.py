"""数据模型定义

TodoItem - 单个待办事项数据模型
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class TodoItem:
    """待办事项数据模型"""

    id: int
    text: str
    done: bool = False

    def __post_init__(self):
        """创建后验证数据"""
        if self.id < 1:
            raise ValueError("ID 必须为正整数")
        if not self.text or not self.text.strip():
            raise ValueError("文本不能为空")

    def to_dict(self) -> Dict:
        """转换为字典格式

        Returns:
            包含 id, text, done 的字典
        """
        return {"id": self.id, "text": self.text, "done": self.done}

    @classmethod
    def from_dict(cls, data: Dict) -> "TodoItem":
        """从字典创建 TodoItem

        Args:
            data: 包含 id, text, done 的字典

        Returns:
            TodoItem 实例
        """
        return cls(id=data["id"], text=data["text"], done=data["done"])
