"""
Dify Memory Plugin API
用于 Dify Workflow 的 HTTP 调用封装
"""

import json
from memory import store, query, clear, get_info


def store_memory(key: str, query_content: str, llm_response: str = "") -> str:
    """存储对话记忆"""
    try:
        ok1 = store(key, "user", query_content)
        ok2 = store(key, "assistant", llm_response) if llm_response else True
        return json.dumps({
            "success": ok1 and ok2,
            "message": "存储成功" if ok1 and ok2 else "存储失败",
            "key": key
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "message": f"存储异常: {e}", "key": key}, ensure_ascii=False)


def query_memory(key: str, size: int = 10) -> str:
    """查询对话记忆（时间倒序）"""
    try:
        size = max(1, min(size, 100))
        return query(key, size)
    except Exception:
        return json.dumps([], ensure_ascii=False)


def clear_memory(key: str) -> str:
    """清除对话记忆"""
    try:
        return json.dumps({"success": clear(key), "message": "清除成功" if clear(key) else "清除失败"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "message": f"清除异常: {e}"}, ensure_ascii=False)


def get_memory_info(key: str) -> str:
    """获取记忆状态"""
    try:
        return json.dumps(get_info(key), ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
