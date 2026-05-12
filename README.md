# Dify CE Memory Plugin

用于 Dify Workflow 的多轮对话记忆插件。

## 功能

- **存储对话**: 将 user/assistant 消息存入记忆
- **查询记忆**: 按时间倒序获取历史对话
- **自动压缩**: 超过100条对话时压缩旧记忆
- **毫秒级响应**: LRU内存缓存加速查询

## 使用方式

```python
from ce_memory.api import store_memory, query_memory

# 存储对话
store_memory(key="session_123", query_content="用户输入", llm_response="助手回复")

# 查询记忆
result = query_memory(key="session_123", size=10)
```

## 文件结构

```
ce_memory/
├── manifest.yaml      # 插件元数据
├── provider/          # Dify Provider 实现
│   ├── provider.yaml  # Provider 定义
│   └── provider.py    # Provider 代码
├── memory_store.py    # 核心存储引擎
├── api.py             # API 封装
└── test.py            # 测试
```

## 安装

```bash
pip install ce_memory
```

## Dify Workflow 集成

在 Dify Workflow 中通过 HTTP Request 节点调用：

- 存储节点: `POST /memory/store`
- 查询节点: `GET /memory/query?key=xxx&size=10`
