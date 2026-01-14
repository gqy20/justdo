"""CLI 命令行接口

提供命令行参数解析和用户交互
"""

import sys
import os
import argparse
from .manager import TodoManager


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
        version="%(prog)s 0.1.1"
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
            response = ai.chat(args.chat, todos)
            print(response)
        except ImportError:
            print("错误: AI 功能需要安装 openai 库：uv pip install openai", file=sys.stderr)
            sys.exit(1)
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
                    print(f"AI 优化: {original_text} → {text}")
                except ImportError:
                    print("错误: AI 功能需要安装 openai 库：uv pip install openai", file=sys.stderr)
                    sys.exit(1)

            # 数字转换为优先级字符串
            priority_map = {1: "high", 2: "medium", 3: "low"}
            todo = manager.add(text, priority=priority_map[args.level])
            emoji = todo.priority_emoji
            print(f"✓ 已添加任务 [{todo.id}] {emoji}: {todo.text}")

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
            for todo_id in todo_ids:
                manager.mark_done(todo_id)
                print(f"✓ 任务 [{todo_id}] 已标记为完成")

        elif args.command == "delete":
            todo_ids = parse_ids(args.ids)
            for todo_id in todo_ids:
                manager.delete(todo_id)
                print(f"✓ 任务 [{todo_id}] 已删除")

        elif args.command == "clear":
            manager.clear()
            print("✓ 已清除所有已完成任务")

        elif args.command == "suggest":
            # 获取未完成任务
            todos = [t for t in manager.list() if not t.done]

            if not todos:
                print("✓ 所有任务已完成，干得好！🎉")
            elif args.ai:
                # AI 智能建议
                if not os.getenv("OPENAI_API_KEY"):
                    print("错误: --ai 需要 OPENAI_API_KEY 环境变量", file=sys.stderr)
                    sys.exit(1)
                try:
                    from .ai import get_ai_handler
                    ai = get_ai_handler()
                    suggestion = ai.suggest_next(todos)
                    print(f"💡 AI 建议: {suggestion}")
                except ImportError:
                    print("错误: AI 功能需要安装 openai 库：uv pip install openai", file=sys.stderr)
                    sys.exit(1)
            else:
                # 按优先级排序显示
                sorted_todos = sorted(todos, key=lambda t: (-t.priority_weight, t.id))
                print("📋 建议按优先级处理：")
                for todo in sorted_todos:
                    emoji = todo.priority_emoji
                    print(f"  [{todo.id}] {emoji} {todo.text}")

    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
