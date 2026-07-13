#!/usr/bin/env python3
"""Dify Memory Plugin 单元测试"""

import json
import sys
import time

sys.path.insert(0, ".")

from dify_memory_plugin.memory_store import store, query, clear, get_info
from dify_memory_plugin.api import store_memory, query_memory, clear_memory, get_memory_info


def test_basic_operations():
    """测试基本存储和查询"""
    key = f"test_{int(time.time())}"

    # 存储对话
    assert store(key, "user", "你好") == True
    assert store(key, "assistant", "你好！有什么可以帮你的？") == True
    assert store(key, "user", "今天天气怎么样？") == True
    assert store(key, "assistant", "今天天气晴朗，适合出行。") == True

    # 查询
    result = query(key, size=2)
    data = json.loads(result)

    assert len(data) == 4  # 2轮对话 = 4条消息
    assert data[0]["role"] == "assistant"  # 最新消息在前
    assert data[0]["content"] == "今天天气晴朗，适合出行。"

    # 清理
    clear(key)
    print("✅ test_basic_operations 通过")


def test_api_functions():
    """测试 API 封装函数"""
    key = f"test_api_{int(time.time())}"

    # store_memory 一次存储用户输入和助手回复
    result = store_memory(key, "我想了解北京", "北京是中国的首都")
    data = json.loads(result)
    assert data["success"] == True

    # 查询
    result = query_memory(key, size=5)
    data = json.loads(result)
    assert len(data) == 2  # 1轮对话 = 2条消息

    # 获取信息
    result = get_memory_info(key)
    data = json.loads(result)
    assert data["exists"] == True
    assert data["turns"] == 2

    # 清除
    result = clear_memory(key)
    data = json.loads(result)
    assert data["success"] == True

    print("✅ test_api_functions 通过")


def test_empty_query():
    """测试空查询"""
    key = f"test_empty_{int(time.time())}"

    result = query(key, size=10)
    data = json.loads(result)
    assert data == []

    print("✅ test_empty_query 通过")


def test_clear():
    """测试清除功能"""
    key = f"test_clear_{int(time.time())}"

    store(key, "user", "测试")
    assert clear(key) == True
    assert clear(key) == True  # 重复清除也应该返回 True

    print("✅ test_clear 通过")


def test_get_info():
    """测试获取信息"""
    key = f"test_info_{int(time.time())}"

    store(key, "user", "测试内容")
    info = get_info(key)

    assert info["exists"] == True
    assert info["turns"] == 1
    assert info["created_at"] > 0
    assert info["updated_at"] > 0

    clear(key)
    print("✅ test_get_info 通过")


def test_memory_info_nonexistent():
    """测试不存在的记忆"""
    key = "nonexistent_key_12345"

    info = get_info(key)
    assert info["exists"] == False
    assert info["turns"] == 0

    print("✅ test_memory_info_nonexistent 通过")


if __name__ == "__main__":
    print("开始测试...\n")

    test_basic_operations()
    test_api_functions()
    test_empty_query()
    test_clear()
    test_get_info()
    test_memory_info_nonexistent()

    print("\n🎉 所有测试通过！")
