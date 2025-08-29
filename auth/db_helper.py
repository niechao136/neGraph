import asyncpg
from datetime import datetime, timezone
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthHelper:
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

