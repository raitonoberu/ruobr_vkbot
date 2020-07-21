from ruobr_api import *
from help import *
import logging
from httpx import ConnectTimeout


class AsyncRuobr(AsyncRuobr):
    async def _get(self, target):
        while True:
            try:
                return await super()._get(target)
            except ConnectTimeout as e:
                logging.info("timeout, trying again")


async def get_marks(user, date1, date2):
    ruobr = AsyncRuobr(user.username, user.password)
    ruobr.user = {"id": user.ruobr_id}
    marks = await ruobr.getMarks(date1, date2)
    return convert_marks(marks)
