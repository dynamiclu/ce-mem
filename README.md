# Dify CE Memory Plugin

用于 Dify Workflow 的多轮对话记忆插件。

## 功能

- **存储对话**: 将 user/assistant 消息存入记忆
- **查询记忆**: 按时间倒序获取历史对话
- **自动压缩**: 超过 100 条对话时压缩旧记忆
- **LRU 缓存**: 内存缓存加速查询

## 文件结构

```
dify_memory_plugin/
├── manifest.yaml      # 插件元数据
├── main.py            # 入口模块
├── memory_store.py    # 核心存储引擎
├── api.py             # HTTP API 封装
├── provider/          # Provider 定义
│   ├── provider.yaml
│   └── provider.py
├── tools/             # Tool 定义
│   ├── store_memory.yaml
│   ├── query_memory.yaml
│   ├── clear_memory.yaml
│   └── get_memory_info.yaml
└── PRIVACY.md
```

## 安装

```bash
pip install .
```

## Dify Workflow 集成

在 Dify Workflow 中通过 HTTP Request 节点或 Code 节点调用：

### HTTP 调用

```python
from dify_memory_plugin.api import store_memory, query_memory

store_memory(key="session_123", query_content="用户输入", llm_response="助手回复")
result = query_memory(key="session_123", size=10)
```

### Code 节点调用

```python
from dify_memory_plugin.memory_store import store, query

store("session_123", "user", "你好")
result = query("session_123", size=5)
```
