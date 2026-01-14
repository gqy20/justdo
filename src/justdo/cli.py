"""CLI 命令行接口

提供命令行参数解析和用户交互
"""

import sys
import os
import argparse
from .manager import TodoManager


def _update_profile(todo, action: str):
    """更新用户画像

    Args:
        todo: TodoItem 对象
        action: 动作 ('add', 'complete', 'delete')
    """
    try:
        from .user_profile import get_profile_path, UserProfile
        profile_path = get_profile_path()
        profile = UserProfile(profile_path)
        profile.record_task(todo, action)
        profile.save()
    except Exception:
        # 静默忽略，不影响主要功能
        pass


def _handle_ai_import_error() -> None:
    """处理 AI 导入错误的辅助函数"""
    print("错误: AI 功能需要安装 openai 库：uv pip install openai", file=sys.stderr)
    sys.exit(1)


def parse_ids(id_strings):
    """解析 ID 字符串列表，支持范围语法

    Args:
        id_strings: ID 字符串列表，如 ['1', '2-4', '7']

    Returns:
        展开后的 ID 列表，如 [1, 2, 3, 4, 7]

    Raises:
        ValueError: 如果 ID 格式无效
    """
    ids = []
    for s in id_strings:
        if "-" in s:
            # 范围语法: 1-3
            try:
                start, end = s.split("-")
                start_id = int(start)
                end_id = int(end)
                if start_id > end_id:
                    raise ValueError(f"范围无效: {s} (起始值不能大于结束值)")
                ids.extend(range(start_id, end_id + 1))
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(f"无效的范围格式: {s}")
                raise
        else:
            # 单个 ID
            try:
                ids.append(int(s))
            except ValueError:
                raise ValueError(f"无效的 ID: {s}")
    return ids


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description="Todo CLI - 命令行待办事项工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.3"
    )
    parser.add_argument(
        "--chat",
        help="AI 对话模式"
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # add 命令
    add_parser = subparsers.add_parser("add", help="添加新任务")
    add_parser.add_argument("text", help="任务文本")
    add_parser.add_argument(
        "-l", "--level",
        type=int,
        choices=[1, 2, 3],
        default=2,
        help="优先级: 1=高, 2=中, 3=低 (默认 2)"
    )
    add_parser.add_argument(
        "--ai",
        action="store_true",
        help="使用 AI 优化任务描述（需 OPENAI_API_KEY 环境变量）"
    )

    # list 命令
    list_parser = subparsers.add_parser("list", help="列出所有任务")
    list_parser.add_argument(
        "-s", "--sort",
        choices=["p", "i"],
        default="i",
        help="排序: p=优先级, i=ID (默认 i)"
    )
    list_parser.add_argument(
        "--done",
        action="store_true",
        help="只显示已完成的任务"
    )
    list_parser.add_argument(
        "--undone",
        action="store_true",
        help="只显示未完成的任务"
    )

    # done 命令
    done_parser = subparsers.add_parser("done", help="标记任务为完成")
    done_parser.add_argument("ids", nargs="+", help="任务 ID（支持多个，如 1 2-5 7）")

    # delete 命令
    delete_parser = subparsers.add_parser("delete", help="删除任务")
    delete_parser.add_argument("ids", nargs="+", help="任务 ID（支持多个，如 1 2-5 7）")

    # clear 命令
    subparsers.add_parser("clear", help="清除所有已完成任务")

    # suggest 命令
    suggest_parser = subparsers.add_parser("suggest", help="建议下一步做什么")
    suggest_parser.add_argument(
        "--ai",
        action="store_true",
        help="使用 AI 智能建议（需 OPENAI_API_KEY 环境变量）"
    )

    args = parser.parse_args()

    # 处理 --chat 对话模式
    if args.chat:
        if not os.getenv("OPENAI_API_KEY"):
            print("错误: --chat 需要 OPENAI_API_KEY 环境变量", file=sys.stderr)
            sys.exit(1)
        try:
            from .ai import get_ai_handler
            ai = get_ai_handler()
            manager = TodoManager()
            todos = manager.list()
            # 流式输出
            for chunk in ai.chat_stream(args.chat, todos):
                print(chunk, end="", flush=True)
            print()  # 换行
        except ImportError:
            _handle_ai_import_error()
        except Exception as e:
            print(f"AI 错误: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    manager = TodoManager()

    try:
        if args.command == "add":
            # CLI 层处理空格
            text = args.text.strip()

            # AI 优化任务描述
            if args.ai:
                if not os.getenv("OPENAI_API_KEY"):
                    print("错误: --ai 需要 OPENAI_API_KEY 环境变量", file=sys.stderr)
                    sys.exit(1)
                try:
                    from .ai import get_ai_handler
                    ai = get_ai_handler()
                    original_text = text
                    text = ai.enhance_input(text)
                    # 提供更清晰的反馈
                    if text == original_text:
                        print(f"→ AI 已处理: {text} (原文已足够好)")
                    else:
                        print(f"→ AI 优化: {original_text} → {text}")
                except ImportError:
                    _handle_ai_import_error()
                except Exception as e:
                    print(f"错误: AI 优化失败 - {e}", file=sys.stderr)
                    # 继续使用原始文本
                    text = original_text

            # 数字转换为优先级字符串
            priority_map = {1: "high", 2: "medium", 3: "low"}
            todo = manager.add(text, priority=priority_map[args.level])
            print(f"→ 任务 [{todo.id}]: {todo.text}")

            # 更新用户画像
            _update_profile(todo, 'add')

        elif args.command == "list":
            todos = manager.list()
            # 状态过滤
            if getattr(args, "done", False):
                todos = [t for t in todos if t.done]
            elif getattr(args, "undone", False):
                todos = [t for t in todos if not t.done]

            if not todos:
                print("暂无任务")
            else:
                # 按指定方式排序
                if args.sort == "p":
                    todos = sorted(todos, key=lambda t: (-t.priority_weight, t.id))
                else:  # sort == "i"
                    todos = sorted(todos, key=lambda t: t.id)

                for todo in todos:
                    status = "✓" if todo.done else " "
                    emoji = todo.priority_emoji
                    print(f"[{todo.id}] [{status}] {emoji} {todo.text}")

        elif args.command == "done":
            todo_ids = parse_ids(args.ids)
            all_todos = manager.list()

            # 先标记所有任务为完成，并记录到用户画像
            for todo_id in todo_ids:
                todo = next((t for t in all_todos if t.id == todo_id), None)
                manager.mark_done(todo_id)
                if todo:
                    _update_profile(todo, 'complete')

            # 使用统一的 AI 反馈（1次调用）
            if os.getenv("OPENAI_API_KEY"):
                try:
                    from .emotion import trigger_cli_feedback
                    for todo_id in todo_ids:
                        todo = next((t for t in all_todos if t.id == todo_id), None)
                        completed_todos = [t for t in all_todos if t.done and t.id in todo_ids]
                        remaining_count = len([t for t in all_todos if not t.done])

                        feedback = trigger_cli_feedback(
                            scenario="task_completed",
                            task_text=todo.text if todo else "",
                            task_priority=todo.priority if todo else "",
                            today_completed=len(completed_todos),
                            today_total=len(all_todos),
                            remaining_count=remaining_count,
                        )
                        print(f"✓ {feedback}")
                except Exception:
                    for todo_id in todo_ids:
                        print(f"→ 任务 [{todo_id}] 已标记为完成")
            else:
                for todo_id in todo_ids:
                    print(f"→ 任务 [{todo_id}] 已标记为完成")

        elif args.command == "delete":
            todo_ids = parse_ids(args.ids)
            all_todos = manager.list()

            for todo_id in todo_ids:
                todo = next((t for t in all_todos if t.id == todo_id), None)
                manager.delete(todo_id)
                if todo:
                    _update_profile(todo, 'delete')
                print(f"→ 任务 [{todo_id}] 已删除")

        elif args.command == "clear":
            todos_before = manager.list()
            completed_count = len([t for t in todos_before if t.done])
            manager.clear()

            todos_after = manager.list()
            if not todos_after and os.getenv("OPENAI_API_KEY"):
                try:
                    from .emotion import trigger_cli_feedback
                    celebration = trigger_cli_feedback(
                        scenario="list_cleared",
                        completed_count=completed_count,
                    )
                    print(celebration)
                except Exception:
                    print("→ 已清除所有已完成任务")
            elif not todos_after:
                print("→ 已清除所有已完成任务")
            else:
                print("→ 已清除所有已完成任务")

        elif args.command == "suggest":
            # 获取未完成任务
            todos = [t for t in manager.list() if not t.done]

            if not todos:
                print("→ 所有任务已完成")
            elif args.ai:
                # AI 智能建议（流式输出）
                if not os.getenv("OPENAI_API_KEY"):
                    print("错误: --ai 需要 OPENAI_API_KEY 环境变量", file=sys.stderr)
                    sys.exit(1)
                try:
                    from .emotion import trigger_cli_feedback_stream

                    # 格式化任务列表
                    todos_text = "\n".join([
                        f"- [{t.id}] {t.text} (优先级: {t.priority})"
                        for t in todos
                    ])

                    # 统计信息
                    incomplete_count = len(todos)
                    high_priority_count = len([t for t in todos if t.priority == "high"])

                    # 使用流式输出
                    print("💡 ", end="", flush=True)
                    for chunk in trigger_cli_feedback_stream(
                        incomplete_count=incomplete_count,
                        high_priority_count=high_priority_count,
                        today_completed=len([t for t in manager.list() if t.done]),
                        tasks_list=todos_text,
                    ):
                        print(chunk, end="", flush=True)
                    print()  # 换行
                except ImportError:
                    _handle_ai_import_error()
            else:
                # 按优先级排序显示
                sorted_todos = sorted(todos, key=lambda t: (-t.priority_weight, t.id))
                print("建议按优先级处理：")
                for todo in sorted_todos:
                    print(f"  [{todo.id}] {todo.text}")

    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
