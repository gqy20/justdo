"""FastAPI Web API

提供 RESTful API 接口访问 Todo 功能
"""

import os
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from .manager import TodoManager
from .user_profile import get_profile_path, UserProfile, guess_category
from .trash import get_trash_path, TrashManager
from .emotion import _get_time_context


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


# 画像分析响应模型
class ProfileUserTypeResponse(BaseModel):
    """用户类型分析"""
    execution_pattern: str
    time_preference: str
    activity_pattern: str


class ProfileSWResponse(BaseModel):
    """优势短板分析"""
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]


class ProfileRiskAlert(BaseModel):
    """风险预警"""
    level: str
    type: str
    message: str


class ProfileStatsResponse(BaseModel):
    """用户画像统计"""
    total_tasks: int
    completed_tasks: int
    completion_rate: float
    current_streak: int
    longest_streak: int


class ProfileFullResponse(BaseModel):
    """完整画像响应"""
    stats: ProfileStatsResponse
    user_type: ProfileUserTypeResponse
    strengths_weaknesses: ProfileSWResponse
    risk_alerts: List[ProfileRiskAlert]
    summary: str


# 回收站响应模型
class TrashItemResponse(BaseModel):
    """回收站项目"""
    id: int
    text: str
    priority: str
    category: str
    created_at: str
    deleted_at: str
    days_in_trash: int


class TrashStatsResponse(BaseModel):
    """回收站统计"""
    total_items: int
    by_category: Dict[str, int]
    by_priority: Dict[str, int]
    avg_days_in_trash: float
    will_auto_delete: int


class TrashListResponse(BaseModel):
    """回收站列表响应"""
    items: List[TrashItemResponse]
    stats: TrashStatsResponse


# ============================================================================
# FastAPI 应用
# ============================================================================

app = FastAPI(
    title="JustDo API",
    description="简单的待办事项管理 API（支持画像分析和回收站）",
    version="0.2.0",
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
    import justdo.api
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


def get_profile() -> UserProfile:
    """获取 UserProfile 实例"""
    return UserProfile(get_profile_path())


def get_trash() -> TrashManager:
    """获取 TrashManager 实例"""
    return TrashManager(get_trash_path())


def update_profile(todo, action: str, category: str = "other"):
    """更新用户画像

    Args:
        todo: TodoItem 对象
        action: 动作类型 ('add', 'complete', 'delete')
        category: 任务类别
    """
    try:
        profile = get_profile()
        profile.record_task(todo, action, category)
        profile.save()
    except Exception:
        # 画像更新失败不影响主流程
        pass


def update_trash(todo, category: str, reason: str = ""):
    """更新回收站

    Args:
        todo: TodoItem 对象
        category: 任务类别
        reason: 删除原因
    """
    try:
        trash = get_trash()
        trash.add(todo, category, reason)
        trash.save()
    except Exception:
        # 回收站更新失败不影响主流程
        pass


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
# 任务管理路由
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

        # 猜测任务类别
        category = guess_category(text)

        # 更新用户画像
        update_profile(result, 'add', category)

        response = todo_to_response(result)

        # 设置原始文本（如果经过 AI 优化）
        if original_text and original_text != text:
            response.original_text = original_text

        # 生成添加任务的鼓励反馈（如果配置了 OPENAI_API_KEY）
        if os.getenv("OPENAI_API_KEY"):
            try:
                from .emotion import trigger_unified_analysis
                all_todos = manager.list()
                profile = get_profile()

                # 准备用户数据
                stats = profile.data['stats']
                completion_rate = profile.get_completion_rate()

                result_analysis = trigger_unified_analysis(
                    total_tasks=stats['total_tasks'],
                    completed_tasks=stats['completed_tasks'],
                    completion_rate=completion_rate,
                    current_streak=stats['current_streak'],
                    longest_streak=stats['longest_streak'],
                    category_stats=profile._get_category_stats_text(),
                    hourly_activity=profile._get_hourly_activity_text(),
                    deletion_rate=stats['deleted_tasks'] / stats['total_tasks'] if stats['total_tasks'] > 0 else 0,
                    recent_7d_deletions=profile._get_recent_deletions_count(7),
                    task_text=result.text,
                    task_priority=result.priority,
                    time_context=_get_time_context(),
                    today_completed=0,  # 刚添加，尚未完成
                    today_total=len(all_todos),
                    remaining_count=len([t for t in all_todos if not t.done]),
                )
                response.feedback = result_analysis.get("task_feedback")
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
            # 猜测类别并更新画像
            category = guess_category(todo.text)
            update_profile(todo, 'complete', category)

            response = todo_to_response(todo)

            # 生成 AI 反馈（如果配置了 OPENAI_API_KEY）
            if os.getenv("OPENAI_API_KEY"):
                try:
                    from .emotion import trigger_unified_analysis
                    profile = get_profile()

                    stats = profile.data['stats']
                    completion_rate = profile.get_completion_rate()

                    result_analysis = trigger_unified_analysis(
                        total_tasks=stats['total_tasks'],
                        completed_tasks=stats['completed_tasks'],
                        completion_rate=completion_rate,
                        current_streak=stats['current_streak'],
                        longest_streak=stats['longest_streak'],
                        category_stats=profile._get_category_stats_text(),
                        hourly_activity=profile._get_hourly_activity_text(),
                        deletion_rate=stats['deleted_tasks'] / stats['total_tasks'] if stats['total_tasks'] > 0 else 0,
                        recent_7d_deletions=profile._get_recent_deletions_count(7),
                        task_text=todo.text,
                        task_priority=todo.priority,
                        time_context=_get_time_context(),
                        today_completed=len([t for t in todos if t.done]),
                        today_total=len(todos),
                        remaining_count=len([t for t in todos if not t.done]),
                    )
                    response.feedback = result_analysis.get("task_feedback")
                except Exception:
                    pass  # AI 失败时静默回退

            return response
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(status_code=404, detail="Task not found")
        raise HTTPException(status_code=400, detail=str(e))
    raise HTTPException(status_code=404, detail="Task not found")


@app.post("/api/todos/{todo_id}/toggle")
async def toggle_todo(todo_id: int):
    """切换任务完成状态（流式响应）

    Args:
        todo_id: 任务 ID

    Returns:
        流式响应：先返回任务状态，再流式返回 AI 反馈
    """
    manager = get_manager()
    try:
        new_done_status = manager.toggle(todo_id)
        todos = manager.list()
        todo = next((t for t in todos if t.id == todo_id), None)
        if todo:
            # 猜测类别并更新用户画像（完成任务时）
            category = guess_category(todo.text)
            if new_done_status:
                update_profile(todo, 'complete', category)

            # 基础响应数据
            response_data = todo_to_response(todo)

            # 流式生成器
            async def generate_stream():
                # 第一步：立即发送任务状态数据
                yield f"data: {json.dumps({'type': 'status', 'data': response_data.dict()})}\n\n"

                # 第二步：如果标记为完成且有 AI，流式生成反馈
                if new_done_status and os.getenv("OPENAI_API_KEY"):
                    try:
                        from .emotion import trigger_feedback_stream
                        profile = get_profile()

                        stats = profile.data['stats']
                        completion_rate = profile.get_completion_rate()

                        # 流式生成反馈
                        feedback = ""
                        for chunk in trigger_feedback_stream(
                            total_tasks=stats['total_tasks'],
                            completed_tasks=stats['completed_tasks'],
                            completion_rate=completion_rate,
                            current_streak=stats['current_streak'],
                            longest_streak=stats['longest_streak'],
                            category_stats=profile._get_category_stats_text(),
                            hourly_activity=profile._get_hourly_activity_text(),
                            deletion_rate=stats['deleted_tasks'] / stats['total_tasks'] if stats['total_tasks'] > 0 else 0,
                            recent_7d_deletions=profile._get_recent_deletions_count(7),
                            task_text=todo.text,
                            task_priority=todo.priority,
                            time_context=_get_time_context(),
                            today_completed=len([t for t in todos if t.done]),
                            today_total=len(todos),
                            remaining_count=len([t for t in todos if not t.done]),
                        ):
                            feedback += chunk
                            yield f"data: {json.dumps({'type': 'feedback_chunk', 'data': chunk})}\n\n"
                    except Exception:
                        # AI 失败，发送占位符
                        yield f"data: {json.dumps({'type': 'feedback_chunk', 'data': ''})}\n\n"

            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
                }
            )
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(status_code=404, detail="Task not found")
        raise HTTPException(status_code=400, detail=str(e))
    raise HTTPException(status_code=404, detail="Task not found")


@app.delete("/api/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, reason: str = ""):
    """删除任务（移至回收站）

    Args:
        todo_id: 任务 ID
        reason: 删除原因（可选）
    """
    manager = get_manager()
    try:
        # 先获取任务用于更新画像和回收站
        todos = manager.list()
        todo = next((t for t in todos if t.id == todo_id), None)

        manager.delete(todo_id)

        if todo:
            # 猜测类别
            category = guess_category(todo.text)

            # 更新用户画像
            update_profile(todo, 'delete', category)

            # 添加到回收站
            update_trash(todo, category, reason)

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
# 用户画像分析路由
# ============================================================================

@app.get("/api/profile/stats", response_model=ProfileStatsResponse)
def get_profile_stats():
    """获取用户画像基础统计

    Returns:
        用户统计数据
    """
    profile = get_profile()
    stats = profile.data['stats']
    completion_rate = profile.get_completion_rate()

    return ProfileStatsResponse(
        total_tasks=stats['total_tasks'],
        completed_tasks=stats['completed_tasks'],
        completion_rate=completion_rate,
        current_streak=stats['current_streak'],
        longest_streak=stats['longest_streak'],
    )


@app.get("/api/profile/user-type", response_model=ProfileUserTypeResponse)
def get_user_type():
    """分析用户类型

    Returns:
        用户类型分析结果
    """
    profile = get_profile()
    result = profile.analyze_user_type()

    return ProfileUserTypeResponse(
        execution_pattern=result.get('execution_pattern', '未知'),
        time_preference=result.get('time_preference', '未知'),
        activity_pattern=result.get('activity_pattern', '未知'),
    )


@app.get("/api/profile/strengths-weaknesses", response_model=ProfileSWResponse)
def get_strengths_weaknesses():
    """分析优势和短板

    Returns:
        优势短板分析结果
    """
    profile = get_profile()
    result = profile.analyze_strengths_and_weaknesses()

    return ProfileSWResponse(
        strengths=result.get('strengths', []),
        weaknesses=result.get('weaknesses', []),
        suggestions=result.get('suggestions', []),
    )


@app.get("/api/profile/risk-alerts", response_model=List[ProfileRiskAlert])
def get_risk_alerts():
    """获取风险预警

    Returns:
        风险预警列表
    """
    profile = get_profile()
    alerts = profile.get_risk_alerts()

    return [
        ProfileRiskAlert(
            level=alert.get('level', 'info'),
            type=alert.get('type', 'unknown'),
            message=alert.get('message', ''),
        )
        for alert in alerts
    ]


@app.get("/api/profile/full", response_model=ProfileFullResponse)
def get_full_profile():
    """获取完整用户画像

    Returns:
        包含统计、类型分析、优势短板、风险预警的完整画像
    """
    profile = get_profile()
    stats = profile.data['stats']
    completion_rate = profile.get_completion_rate()

    user_type = profile.analyze_user_type()
    sw = profile.analyze_strengths_and_weaknesses()
    alerts = profile.get_risk_alerts()
    summary = profile.get_user_summary()

    return ProfileFullResponse(
        stats=ProfileStatsResponse(
            total_tasks=stats['total_tasks'],
            completed_tasks=stats['completed_tasks'],
            completion_rate=completion_rate,
            current_streak=stats['current_streak'],
            longest_streak=stats['longest_streak'],
        ),
        user_type=ProfileUserTypeResponse(
            execution_pattern=user_type.get('execution_pattern', '未知'),
            time_preference=user_type.get('time_preference', '未知'),
            activity_pattern=user_type.get('activity_pattern', '未知'),
        ),
        strengths_weaknesses=ProfileSWResponse(
            strengths=sw.get('strengths', []),
            weaknesses=sw.get('weaknesses', []),
            suggestions=sw.get('suggestions', []),
        ),
        risk_alerts=[
            ProfileRiskAlert(
                level=alert.get('level', 'info'),
                type=alert.get('type', 'unknown'),
                message=alert.get('message', ''),
            )
            for alert in alerts
        ],
        summary=summary,
    )


@app.get("/api/profile/summary")
def get_profile_summary():
    """获取用户画像总结（纯文本）

    Returns:
        画像总结文本
    """
    profile = get_profile()
    return {"summary": profile.get_user_summary()}


# ============================================================================
# 回收站管理路由
# ============================================================================

@app.get("/api/trash", response_model=TrashListResponse)
def list_trash(limit: Optional[int] = None, category: Optional[str] = None):
    """列出回收站项目

    Args:
        limit: 限制返回数量
        category: 按类别过滤

    Returns:
        回收站项目列表和统计
    """
    trash = get_trash()
    items = trash.list(limit=limit, category=category)
    stats = trash.get_statistics()

    return TrashListResponse(
        items=[
            TrashItemResponse(
                id=item.id,
                text=item.text,
                priority=item.priority,
                category=item.category,
                created_at=item.created_at,
                deleted_at=item.deleted_at,
                days_in_trash=item.days_in_trash,
            )
            for item in items
        ],
        stats=TrashStatsResponse(
            total_items=stats['total_items'],
            by_category=stats['by_category'],
            by_priority=stats['by_priority'],
            avg_days_in_trash=stats['avg_days_in_trash'],
            will_auto_delete=stats['will_auto_delete'],
        ),
    )


@app.get("/api/trash/stats", response_model=TrashStatsResponse)
def get_trash_stats():
    """获取回收站统计

    Returns:
        回收站统计数据
    """
    trash = get_trash()
    stats = trash.get_statistics()

    return TrashStatsResponse(
        total_items=stats['total_items'],
        by_category=stats['by_category'],
        by_priority=stats['by_priority'],
        avg_days_in_trash=stats['avg_days_in_trash'],
        will_auto_delete=stats['will_auto_delete'],
    )


@app.post("/api/trash/{todo_id}/restore")
def restore_from_trash(todo_id: int):
    """从回收站恢复任务

    Args:
        todo_id: 任务 ID

    Returns:
        恢复的任务信息
    """
    trash = get_trash()
    manager = get_manager()

    restored = trash.restore(todo_id)
    if restored is None:
        raise HTTPException(status_code=404, detail="Item not found in trash")

    try:
        # 重新创建任务
        todo = manager.add(restored['text'], restored['priority'])

        return {
            "id": todo.id,
            "text": todo.text,
            "priority": todo.priority,
            "message": "任务已恢复"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/trash/{todo_id}")
def delete_from_trash(todo_id: int):
    """从回收站永久删除

    Args:
        todo_id: 任务 ID
    """
    trash = get_trash()
    success = trash.delete_permanently(todo_id)

    if not success:
        raise HTTPException(status_code=404, detail="Item not found in trash")

    return None


@app.post("/api/trash/clear")
def clear_trash():
    """清空回收站

    Returns:
        清空的项目数量
    """
    trash = get_trash()
    count = trash.clear()
    return {"cleared": count}


@app.post("/api/trash/cleanup")
def cleanup_trash(days: Optional[int] = None):
    """清理回收站中的旧项目

    Args:
        days: 清理 N 天前的项目，默认使用自动删除天数

    Returns:
        清理的项目数量
    """
    trash = get_trash()
    count = trash.cleanup_old(days)
    return {"cleaned": count}


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
