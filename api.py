"""
Dify Memory Plugin API
用于 Dify Workflow 的 API 调用封装
"""

import json
from .memory_store import store, query, clear, get_info, MAX_TURNS


def store_memory(key: str, query_content: str, llm_response: str = "") -> str:
    """
    存储对话记忆

    Args:
        key: 唯一标识（建议使用会话ID或用户ID）
        query_content: 用户输入
        llm_response: 助手回复（可选，用于连续存储）

    Returns:
        str: JSON {"success": bool, "message": str}
    """
    try:
        # 存储用户输入
        ok1 = store(key, "user", query_content)

        # 存储助手回复（如果提供）
        ok2 = True
        if llm_response:
            ok2 = store(key, "assistant", llm_response)

        success = ok1 and ok2
        return json.dumps({
            "success": success,
            "message": "存储成功" if success else "存储失败",
            "key": key
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"存储异常: {str(e)}",
            "key": key
        }, ensure_ascii=False)


def query_memory(key: str, size: int = 10) -> str:
    """
    查询对话记忆

    Args:
        key: 唯一标识
        size: 对话轮数（每轮=1个user+1个assistant），默认10

    Returns:
        str: JSON数组字符串，按时间倒序
        示例: [{"role":"user","content":"你好","timestamp":123456},{"role":"assistant","content":"你好！","timestamp":123457},...]
    """
    try:
        if size <= 0:
            size = 10
        if size > MAX_TURNS:
            size = MAX_TURNS

        return query(key, size)

    except Exception as e:
        return json.dumps([], ensure_ascii=False)


def clear_memory(key: str) -> str:
    """
    清除对话记忆

    Args:
        key: 唯一标识

    Returns:
        str: JSON {"success": bool, "message": str}
    """
    try:
        success = clear(key)
        return json.dumps({
            "success": success,
            "message": "清除成功" if success else "清除失败"
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"清除异常: {str(e)}"
        }, ensure_ascii=False)


def get_memory_info(key: str) -> str:
    """
    获取记忆状态（调试用）

    Args:
        key: 唯一标识

    Returns:
        str: JSON对象
    """
    try:
        info = get_info(key)
        return json.dumps(info, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
