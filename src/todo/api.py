"""FastAPI Web API

提供 RESTful API 接口访问 Todo 功能
"""

import os
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .manager import TodoManager


# ============================================================================
# 静态文件路径
# ============================================================================

STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)


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
    feedback: Optional[str] = None  # AI 反馈（完成/添加时的鼓励）
    original_text: Optional[str] = None  # AI 优化前的原始文本


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


# 默认端口配置
DEFAULT_PORT = 8848


# ============================================================================
# 静态文件和首页
# ============================================================================

@app.get("/")
async def root():
    """首页 - 返回单页应用"""
    # 动态查找 static 目录
    import todo.api
    static_dir = Path(todo.api.__file__).parent / "static"
    index_file = static_dir / "index.html"

    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "JustDo API - 访问 /docs 查看 API 文档", "static_dir": str(static_dir)}


# 挂载静态文件（需要在路由之后，否则会覆盖 / 路由）
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")


def get_manager() -> TodoManager:
    """获取 TodoManager 实例"""
    return TodoManager()


def todo_to_response(todo) -> TodoResponse:
    """将 TodoItem 转换为 TodoResponse

    Args:
        todo: TodoItem 对象

    Returns:
        TodoResponse 对象
    """
    return TodoResponse(
        id=todo.id,
        text=todo.text,
        priority=todo.priority,
        done=todo.done
    )


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

    return [todo_to_response(t) for t in todos]


@app.post("/api/todos", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(todo: TodoCreate, ai: bool = False):
    """创建新任务

    Args:
        todo: 任务创建请求
        ai: 是否使用 AI 优化任务描述

    Returns:
        创建的任务
    """
    manager = get_manager()
    try:
        text = todo.text
        original_text = None

        # AI 优化任务描述
        if ai and os.getenv("OPENAI_API_KEY"):
            try:
                from .ai import get_ai_handler
                ai_handler = get_ai_handler()
                original_text = text
                text = ai_handler.enhance_input(text)
            except ImportError:
                pass  # AI 功能不可用时静默回退
            except Exception:
                pass  # AI 失败时使用原始文本

        result = manager.add(text, todo.priority)
        response = todo_to_response(result)

        # 设置原始文本（如果经过 AI 优化）
        if original_text and original_text != text:
            response.original_text = original_text

        # 生成添加任务的鼓励反馈（如果配置了 OPENAI_API_KEY）
        if os.getenv("OPENAI_API_KEY"):
            try:
                from .emotion import EMOTION_SCENARIOS, trigger_emotion
                all_todos = manager.list()
                feedback = trigger_emotion(
                    EMOTION_SCENARIOS["task_added"],
                    task_text=result.text,
                    task_priority=result.priority,
                    total_count=len(all_todos),
                    incomplete_count=len([t for t in all_todos if not t.done]),
                )
                response.feedback = feedback
            except Exception:
                pass  # AI 失败时静默回退

        return response
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
            response = todo_to_response(todo)

            # 生成 AI 反馈（如果配置了 OPENAI_API_KEY）
            if os.getenv("OPENAI_API_KEY"):
                try:
                    from .emotion import EMOTION_SCENARIOS, trigger_emotion
                    feedback = trigger_emotion(
                        EMOTION_SCENARIOS["task_completed"],
                        task_text=todo.text,
                        task_priority=todo.priority,
                        today_completed=len([t for t in todos if t.done]),
                        today_total=len(todos),
                        remaining_count=len([t for t in todos if not t.done]),
                    )
                    response.feedback = feedback
                except Exception:
                    pass  # AI 失败时静默回退

            return response
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(status_code=404, detail="Task not found")
        raise HTTPException(status_code=400, detail=str(e))
    raise HTTPException(status_code=404, detail="Task not found")


@app.post("/api/todos/{todo_id}/toggle", response_model=TodoResponse)
def toggle_todo(todo_id: int):
    """切换任务完成状态

    Args:
        todo_id: 任务 ID

    Returns:
        更新后的任务，包含 AI 反馈
    """
    manager = get_manager()
    try:
        new_done_status = manager.toggle(todo_id)
        todos = manager.list()
        todo = next((t for t in todos if t.id == todo_id), None)
        if todo:
            response = todo_to_response(todo)

            # 只在标记为完成时生成 AI 反馈（如果配置了 OPENAI_API_KEY）
            if new_done_status and os.getenv("OPENAI_API_KEY"):
                try:
                    from .emotion import EMOTION_SCENARIOS, trigger_emotion
                    feedback = trigger_emotion(
                        EMOTION_SCENARIOS["task_completed"],
                        task_text=todo.text,
                        task_priority=todo.priority,
                        today_completed=len([t for t in todos if t.done]),
                        today_total=len(todos),
                        remaining_count=len([t for t in todos if not t.done]),
                    )
                    response.feedback = feedback
                except Exception:
                    pass  # AI 失败时静默回退

            return response
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

    return SuggestResponse(todos=[todo_to_response(t) for t in sorted_todos])


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


# ============================================================================
# 命令行入口
# ============================================================================

def main():
    """启动 Web 服务器

    运行 'jd-web' 命令时调用
    """
    import uvicorn
    uvicorn.run(
        "todo.api:app",
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )
