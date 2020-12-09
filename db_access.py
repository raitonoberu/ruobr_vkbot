import asyncpg
from collections import namedtuple

User = namedtuple("User", "vk_id username password name ruobr_id marks status")

CREATE_SCRIPT = """
CREATE TABLE "USERS"
(
  VK_ID bigint NOT NULL,
  USERNAME text NOT NULL,
  PASSWORD text NOT NULL,
  NAME text NOT NULL,
  RUOBR_ID bigint NOT NULL,
  MARKS text,
  STATUS boolean DEFAULT false NOT NULL
);

ALTER TABLE "USERS" ADD CONSTRAINT PK_USERS
  PRIMARY KEY (VK_ID);
"""


class Database(object):
    """Доступ к базе данных пользователей"""

    def __init__(self, database):
        self.database = database

    async def connect(self):
        self.pool = await asyncpg.create_pool(self.database)

    async def close(self):
        await self.pool.close()

    async def is_exists(self):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'USERS')"
            )
        return bool(row[0])

    async def create_table(self):
        async with self.pool.acquire() as conn:
            await conn.execute(CREATE_SCRIPT)

    async def get_users(self, status=True):
        """Получаем список активных пользователей"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('SELECT * FROM "USERS" WHERE STATUS = $1', status)
        return [User(*user) for user in rows]

    async def get_user(self, vk_id):
        """Получаем пользователя по VK_ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('SELECT * FROM "USERS" WHERE VK_ID = $1', vk_id)
        if row:
            return User(*row)
        return None

    async def add_user(self, vk_id, username, password, name, ruobr_id):
        """Добавляем пользователя в базу"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'INSERT INTO "USERS" VALUES ($1, $2, $3, $4, $5)',
                vk_id,
                username,
                password,
                name,
                ruobr_id,
            )

    async def update_marks(self, vk_id, marks):
        """Обновляем оценки"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'UPDATE "USERS" SET MARKS = $1 WHERE VK_ID = $2', marks, vk_id
            )

    async def remove_user(self, vk_id):
        async with self.pool.acquire() as conn:
            await conn.execute('DELETE FROM "USERS" WHERE VK_ID = $1', vk_id)

    async def update_status(self, vk_id, status):
        """Обновляем статус пользователя"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'UPDATE "USERS" SET STATUS = $1 WHERE VK_ID = $2', status, vk_id
            )
