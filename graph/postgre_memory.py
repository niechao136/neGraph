import asyncpg
from datetime import datetime, timezone
import json
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.base import BaseCheckpointSaver


class PostgresMemory:
    def __init__(self, dsn: str):
        """
        dsn 例如: "postgresql://user:password@localhost:5432/mydb"
        """
        self.dsn = dsn

    async def _get_conn(self):
        return await asyncpg.connect(self.dsn)

    async def new_conversation(self, user_id: str, summary: str = None) -> str:
        """
        新建会话，并返回 conversation_id (UUID)
        """
        async with await self._get_conn() as conn:
            row = await conn.fetchrow("""
                INSERT INTO conversations (user_id, summary)
                VALUES ($1, $2)
                RETURNING id
            """, user_id, summary)
            return str(row["id"])

    async def load_history(self, conversation_id: str):
        """
        从数据库加载历史消息，返回 LangChain/LangGraph 格式的消息列表
        """
        if conversation_id is None:
            return []

        async with await self._get_conn() as conn:
            rows = await conn.fetch("""
                SELECT sender, message, context, timestamp
                FROM messages
                WHERE conversation_id = $1
                ORDER BY timestamp ASC
            """, conversation_id)

        history = []
        for row in rows:
            if row["sender"] == "user":
                history.append(HumanMessage(content=row["message"]))
            else:
                history.append(AIMessage(content=row["message"]))
        return history

    async def save_message(self, conversation_id: str, sender: str, message: str, context=None):
        """
        保存一条新消息
        """
        async with await self._get_conn() as conn:
            await conn.execute("""
                INSERT INTO messages (conversation_id, sender, message, timestamp, context)
                VALUES ($1, $2, $3, $4, $5)
            """, conversation_id, sender, message, datetime.now(timezone.utc), json.dumps(context or {}))

    async def save_tool_call(self, message_id: str, conversation_id: str, tool_name: str,
                             tool_input: dict, tool_output: dict = None) -> str:
        """
        保存工具调用
        """
        async with await self._get_conn() as conn:
            row = await conn.fetchrow("""
                INSERT INTO tool_calls (message_id, conversation_id, tool_name, input, output, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, message_id, conversation_id, tool_name,
                 json.dumps(tool_input), json.dumps(tool_output) if tool_output else None,
                 datetime.now(timezone.utc))
            return str(row["id"])


class PostgresSaver(BaseCheckpointSaver):
    def __init__(self, dsn: str):
        super().__init__()
        self.dsn = dsn
        self._pool: asyncpg.Pool | None = None  # 显式声明 _pool 属性

    async def _get_conn(self):
        if not self._pool:
            self._pool = await asyncpg.create_pool(dsn=self.dsn)
        return self._pool

    # -----------------------------
    # put：保存 checkpoint
    # -----------------------------
    async def put(self, config: dict, checkpoint: dict, metadata=None, **kwargs):
        """
        保存一条 checkpoint：
        - checkpoint["values"]["messages"] 包含 HumanMessage / AIMessage 列表
        - 每条消息可包含 tool_calls
        :param config:
        :param checkpoint:
        :param metadata:
        """
        conversation_id = config.get("thread_id")
        user_id = config.get("user_id")
        messages = checkpoint["values"].get("messages", [])

        pool = await self._get_conn()
        async with pool.acquire() as conn:
            for msg in messages:
                msg_id = getattr(msg, "id", None) or None
                sender = "user" if isinstance(msg, HumanMessage) else "assistant"
                msg_context = msg.additional_kwargs.get("context")
                msg_action = msg.additional_kwargs.get("action")

                # 保存消息（增量）
                row = await conn.fetchrow(
                    """
                    INSERT INTO messages (id, conversation_id, user_id, sender, message, context, action, timestamp)
                    VALUES (COALESCE($1, gen_random_uuid()), $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT(id) DO NOTHING RETURNING id
                    """, msg_id, conversation_id, user_id, sender, msg.content,
                    json.dumps(msg_context) if msg_context else None,
                    json.dumps(msg_action) if msg_action else None,
                    datetime.now(timezone.utc))

                message_id = row["id"] if row else msg_id

                # 保存工具调用
                tool_calls = msg.additional_kwargs.get("tool_calls", [])
                for order, tc in enumerate(tool_calls):
                    await conn.execute(
                        """
                        INSERT INTO tool_calls (message_id, conversation_id, user_id, tool_name, input, output, timestamp, call_order)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8) ON CONFLICT(id) DO NOTHING
                        """, message_id, conversation_id, user_id, tc["tool_name"],
                        json.dumps(tc.get("input")), json.dumps(tc.get("output")),
                        datetime.now(timezone.utc), order)

    # -----------------------------
    # get：恢复 checkpoint
    # -----------------------------
    async def get(self, config: dict, checkpoint_id: str | None = None):
        """
        返回 LangGraph 可继续运行的 checkpoint
        """
        conversation_id = config.get("thread_id")
        user_id = config.get("user_id")

        pool = await self._get_conn()
        async with pool.acquire() as conn:
            # 读取消息
            rows = await conn.fetch(
                """
                SELECT id, sender, message, context, action, timestamp
                FROM messages
                WHERE conversation_id = $1 AND user_id = $2
                ORDER BY timestamp ASC
                """, conversation_id, user_id)

            # 读取工具调用
            tool_rows = await conn.fetch(
                """
                SELECT message_id, tool_name, input, output, timestamp, call_order
                FROM tool_calls
                WHERE conversation_id = $1 AND user_id = $2
                ORDER BY call_order ASC
                """, conversation_id, user_id)

        # 工具调用按消息分组
        tool_map = {}
        for r in tool_rows:
            tool_map.setdefault(str(r["message_id"]), []).append({
                "tool_name": r["tool_name"],
                "input": r["input"],
                "output": r["output"],
                "timestamp": r["timestamp"].isoformat(),
                "call_order": r["call_order"]
            })

        # 构造 messages
        messages = []
        for row in rows:
            if row["sender"] == "user":
                msg = HumanMessage(content=row["message"])
            else:
                msg = AIMessage(content=row["message"])

            msg.id = str(row["id"])
            msg.additional_kwargs = {
                "context": row["context"],
                "action": row["action"],
                "tool_calls": tool_map.get(str(row["id"]), [])
            }
            messages.append(msg)

        # 返回 checkpoint 结构
        return {
            "id": str(conversation_id),
            "config": config,
            "metadata": {"conversation_id": conversation_id},
            "values": {"messages": messages},
            "pending_sends": None
        }

    # -----------------------------
    # list：列出历史 checkpoint 元信息
    # -----------------------------
    async def list(self, config: dict, limit: int = 20, before: str | None = None, **kwargs):
        """
        返回该用户的会话列表（只返回 metadata，不加载全部消息）
        :param config:
        :param limit:
        :param before:
        """
        user_id = config.get("user_id")

        pool = await self._get_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, summary, created_at
                FROM conversations
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """, user_id, limit)

        return [
            {
                "checkpoint": None,
                "metadata": {
                    "conversation_id": str(r["id"]),
                    "summary": r["summary"],
                    "created_at": r["created_at"].isoformat()
                }
            }
            for r in rows
        ]

    async def new_conversation(self, user_id: str, summary: str = None) -> str:
        """
        新建会话，并返回 conversation_id (UUID)
        """
        pool = await self._get_conn()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO conversations (user_id, summary)
                VALUES ($1, $2)
                RETURNING id
            """, user_id, summary)
            return str(row["id"])


