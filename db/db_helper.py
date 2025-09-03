import asyncpg
from datetime import datetime, timezone
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class DBHelper:
    def __init__(self, dsn: str):
        """
        dsn 例如: "postgresql://user:password@localhost:5432/mydb"
        """
        self.dsn = dsn
        self._pool: asyncpg.Pool | None = None  # 显式声明 _pool 属性

    async def _get_conn(self):
        if not self._pool:
            self._pool = await asyncpg.create_pool(dsn=self.dsn)
        return self._pool

    async def register(self, username: str, password: str, email: str):
        hashed_password = pwd_context.hash(password)
        pool = await self._get_conn()
        async with pool.acquire() as conn:
            # 检查用户名是否已存在
            exists = await conn.fetchval("SELECT 1 FROM users WHERE username=$1", username)
            if exists:
                return None
            row = await conn.fetchrow(
                """
                INSERT INTO users (username, email, password, created_at)
                VALUES ($1, $2, $3, $4) RETURNING id, username
                """, username, email, hashed_password, datetime.now(timezone.utc))
            user_id = row["id"]
            return user_id

    async def login(self, username: str, password: str):
        pool = await self._get_conn()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT id, username, password FROM users WHERE username=$1", username)
            if not row or not pwd_context.verify(password, row["password"]):
                return None
            user_id = row["id"]
            return user_id

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

    async def conversation_list(self, user_id: str, limit: int = 10, before: str | None = None):
        """
        基于游标的增量获取会话（cursor-based pagination）
        返回格式：
        {
            "limit": 20,
            "has_more": false,
            "data": [...]
        }

        参数:
            user_id: 当前用户
            limit: 本次请求最大条数
            before: 上一页最后一条 created_at (ISO8601 字符串)，下一页传这个参数
        """
        pool = await self._get_conn()
        async with pool.acquire() as conn:
            if before:
                # 转换成 timestamptz
                rows = await conn.fetch(
                    """
                    SELECT id, summary, created_at
                    FROM conversations
                    WHERE user_id = $1
                      AND created_at < $2
                    ORDER BY created_at DESC
                        LIMIT $3
                    """,
                    user_id,
                    before,
                    limit + 1,  # 多取一条用于判断 has_more
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT id, summary, created_at
                    FROM conversations
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                        LIMIT $2
                    """,
                    user_id,
                    limit + 1,
                )

        has_more = len(rows) > limit
        result_rows = rows[:limit]
        return {
            "limit": limit,
            "has_more": has_more,
            "data": [
                {
                    "conversation_id": str(r["id"]),
                    "summary": r["summary"],
                    "created_at": r["created_at"].isoformat(),
                }
                for r in result_rows
            ],
        }


helper = DBHelper(dsn="postgresql://root:158818@150.109.15.178:5432/neGraph")

