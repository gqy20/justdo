"""FastAPI Web API

提供 RESTful API 接口访问 Todo 功能
"""

import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from .manager import TodoManager


# ============================================================================
# 请求/响应模型
# ============================================================================

class TodoCreate(BaseModel):
    """创建任务请求"""
    text: str = Field(..., min_length=1, description="任务文本")
    priority: str = Field("medium", pattern="^(high|medium|low)$", description="优先级")


class TodoResponse(BaseModel):
    """任务响应"""
    id: int
    text: str
    priority: str
    done: bool


class ChatRequest(BaseModel):
    """AI 对话请求"""
    message: str = Field(..., min_length=1, description="用户消息")


class ChatResponse(BaseModel):
    """AI 对话响应"""
    response: str


class ClearResponse(BaseModel):
    """清空响应"""
    cleared: int


class SuggestResponse(BaseModel):
    """建议响应"""
    todos: List[TodoResponse]


# ============================================================================
# FastAPI 应用
# ============================================================================

app = FastAPI(
    title="JustDo API",
    description="简单的待办事项管理 API",
    version="0.1.1",
)


def get_manager() -> TodoManager:
    """获取 TodoManager 实例"""
    return TodoManager()


# ============================================================================
# 路由
# ============================================================================

@app.get("/api/todos", response_model=List[TodoResponse])
def list_todos(done: Optional[bool] = None):
    """获取任务列表

    Args:
        done: 可选，过滤已完成/未完成任务

    Returns:
        任务列表
    """
    manager = get_manager()
    todos = manager.list()

    if done is not None:
        todos = [t for t in todos if t.done == done]

    return [
        TodoResponse(id=t.id, text=t.text, priority=t.priority, done=t.done)
        for t in todos
    ]


@app.post("/api/todos", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(todo: TodoCreate):
    """创建新任务

    Args:
        todo: 任务创建请求

    Returns:
        创建的任务
    """
    manager = get_manager()
    try:
        result = manager.add(todo.text, todo.priority)
        return TodoResponse(
            id=result.id,
            text=result.text,
            priority=result.priority,
            done=result.done
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/todos/{todo_id}/done", response_model=TodoResponse)
def mark_done(todo_id: int):
    """标记任务为完成

    Args:
        todo_id: 任务 ID

    Returns:
        更新后的任务
    """
    manager = get_manager()
    try:
        manager.mark_done(todo_id)
        # 获取更新后的任务
        todos = manager.list()
        todo = next((t for t in todos if t.id == todo_id), None)
        if todo:
            return TodoResponse(
                id=todo.id,
                text=todo.text,
                priority=todo.priority,
                done=todo.done
            )
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(status_code=404, detail="Task not found")
        raise HTTPException(status_code=400, detail=str(e))
    raise HTTPException(status_code=404, detail="Task not found")


@app.delete("/api/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int):
    """删除任务

    Args:
        todo_id: 任务 ID
    """
    manager = get_manager()
    try:
        manager.delete(todo_id)
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(status_code=404, detail="Task not found")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/clear", response_model=ClearResponse)
def clear_done():
    """清空所有已完成任务

    Returns:
        清空的任务数量
    """
    manager = get_manager()
    todos_before = manager.list()
    completed_count = len([t for t in todos_before if t.done])
    manager.clear()
    return ClearResponse(cleared=completed_count)


@app.get("/api/suggest", response_model=SuggestResponse)
def suggest():
    """获取智能建议

    Returns:
        按优先级排序的任务列表
    """
    manager = get_manager()
    todos = [t for t in manager.list() if not t.done]
    sorted_todos = sorted(todos, key=lambda t: (-t.priority_weight, t.id))

    return SuggestResponse(
        todos=[
            TodoResponse(
                id=t.id,
                text=t.text,
                priority=t.priority,
                done=t.done
            )
            for t in sorted_todos
        ]
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """AI 对话

    Args:
        request: 对话请求

    Returns:
        AI 响应
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY not configured"
        )

    try:
        from .ai import get_ai_handler
        ai = get_ai_handler()
        manager = get_manager()
        todos = manager.list()

        # 调用 AI 获取响应
        response_text = ai.chat(request.message, todos)
        return ChatResponse(response=response_text)

    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="AI features not available (openai not installed)"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
