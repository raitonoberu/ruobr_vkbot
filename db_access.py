import aiosqlite
from collections import namedtuple

# TODO: use postgres github.com/MagicStack/asyncpg

User = namedtuple("User", "id vk_id username password name ruobr_id marks status")


class Database(object):
    """Доступ к базе данных пользователей"""

    def __init__(self, database):
        """Открываем базу"""
        self.database = database

    async def get_users(self, status=True):
        """Получаем список активных пользователей"""
        async with aiosqlite.connect(self.database) as db:
            async with db.execute(
                "SELECT * FROM `USERS` WHERE `status` = ?", (status,)
            ) as cursor:
                users = await cursor.fetchall()
                return [User(*user) for user in users]

    async def get_user(self, vk_id):
        """Получаем пользователя по VK_ID"""
        async with aiosqlite.connect(self.database) as db:
            async with db.execute(
                "SELECT * FROM `USERS` WHERE `VK_ID` = ?", (vk_id,)
            ) as cursor:
                user = await cursor.fetchall()
                if not user:
                    return None
                return User(*user[0])

    async def add_user(self, vk_id, username, password, name, ruobr_id):
        """Добавляем пользователя в базу"""
        async with aiosqlite.connect(self.database) as db:
            await db.execute(
                "INSERT INTO `USERS` (`VK_ID`, `USERNAME`, `PASSWORD`, `NAME`, `RUOBR_ID`) VALUES (?, ?, ?, ?, ?)",
                (vk_id, username, password, name, ruobr_id),
            )
            await db.commit()

    async def update_marks(self, vk_id, marks):
        """Обновляем оценки"""
        async with aiosqlite.connect(self.database) as db:
            await db.execute(
                "UPDATE `USERS` SET `MARKS` = ? WHERE `VK_ID` = ?", (marks, vk_id)
            )
            await db.commit()

    async def remove_user(self, vk_id):
        async with aiosqlite.connect(self.database) as db:
            await db.execute("DELETE FROM `USERS` WHERE `VK_ID` = ?", (vk_id,))
            await db.commit()

    async def update_status(self, vk_id, status):
        """Обновляем статус пользователя"""
        async with aiosqlite.connect(self.database) as db:
            await db.execute(
                "UPDATE `USERS` SET `STATUS` = ? WHERE `VK_ID` = ?", (status, vk_id)
            )
            await db.commit()
