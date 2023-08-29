from time import time
from vkwave.bots.utils.keyboards import Keyboard


def children_kb(login, password, children):
    kb = Keyboard(one_time=True, inline=True)
    for i, child in enumerate(children):
        kb.add_text_button(
            i + 1,
            payload={
                "type": "children",
                "id": str(child["id"]),
                "login": login,
                "password": password,
                "time": str(time()),
            },
        )
    return kb.get_keyboard()


def _moving_kb(user, type, **args):
    kb = Keyboard(one_time=True, inline=True)
    pl1 = {
        "type": type,
        "direction": "-1",
        "id": str(user.ruobr_id),
        "time": str(time()),
    }
    pl1.update(args)
    pl2 = pl1.copy()
    pl2["direction"] = "1"

    kb.add_callback_button("<", payload=pl1)
    kb.add_callback_button(">", payload=pl2)

    return kb.get_keyboard()


def marks_kb(user, date0, date1):
    date0 = date0.strftime("%Y-%m-%d")
    date1 = date1.strftime("%Y-%m-%d")
    return _moving_kb(user, "marks", date0=date0, date1=date1)


def mail_kb(user, index):
    return _moving_kb(user, "mail", index=str(index))


# нижняя клавиатура
MAIN = """
{
  "buttons": [
    [
      {
        "action": {
          "type": "text",
          "label": "Оценки",
          "payload": ""
        },
        "color": "primary"
      },
      {
        "action": {
          "type": "text",
          "label": "ДЗ",
          "payload": ""
        },
        "color": "primary"
      },
      {
        "action": {
          "type": "text",
          "label": "Статистика",
          "payload": ""
        },
        "color": "primary"
      }
    ],
    [
      {
        "action": {
          "type": "text",
          "label": "Питание",
          "payload": ""
        },
        "color": "secondary"
      },
      {
        "action": {
          "type": "text",
          "label": "Почта",
          "payload": ""
        },
        "color": "secondary"
      },
      {
        "action": {
          "type": "text",
          "label": "Итоги",
          "payload": ""
        },
        "color": "secondary"
      }
    ]
  ]
}
"""
