import asyncio
import json
import api as ruobr_api
from vkbottle import API
from datetime import datetime
import pytz
from config import WAIT_IN_MINS, TIMEZONE
from utils import compare_marks, marks_to_str
import logging

tz = pytz.timezone(TIMEZONE)


class Notifier(object):
    def __init__(self, api: API, db):
        self.api = api
        self.db = db

    def run(self):
        asyncio.ensure_future(self._loop())

    async def _loop(self):
        while True:
            try:
                users = await self.db.get_users()
                tasks = [self.check_user(user) for user in users]
                await asyncio.gather(*tasks)
                await asyncio.sleep(WAIT_IN_MINS * 60)
            except:
                logging.exception("")
                await asyncio.sleep(1)

    async def send_msg(self, text, vk_id):
        try:
            await self.api.messages.send(peer_id=vk_id, message=text, random_id=0)
        except Exception as e:
            # TODO: handle blacklisting
            logging.error(f"{vk_id}: {e}")

    async def check_user(self, user):
        marks = user.marks
        if marks:
            marks = json.loads(marks)
        else:  # новый день / инициация
            marks = {}
        date = datetime.now(tz)
        try:
            new_marks = await ruobr_api.get_marks(user, date, date)
        except ruobr_api.AuthenticationException:
            await self.send_msg("Проверьте логин и/или пароль.", user.vk_id)
            await self.db.remove_user(user.vk_id)
            return
        if new_marks != {}:
            delta = compare_marks(marks, new_marks)
            if not delta:
                return
            await self.send_msg(
                "Вы получили оценки:\n" + marks_to_str(delta), user.vk_id
            )
        elif marks == {}:  # не трогать бд если всё ещё нет оценок
            return
        await self.db.update_marks(user.vk_id, json.dumps(new_marks))
