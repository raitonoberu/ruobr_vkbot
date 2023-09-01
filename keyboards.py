from time import time
from vkbottle import Keyboard, Callback


def children_kb(login, password, children):
    kb = Keyboard(inline=True)
    for i, child in enumerate(children):
        kb.add(
            Callback(str(i + 1)),
            {
                "type": "children",
                "id": child["id"],
                "login": login,
                "password": password,
                "time": time(),
            },
        )
    return kb.get_json()


def _moving_kb(user, type, **args):
    kb = Keyboard(inline=True)
    pl1 = {
        "type": type,
        "direction": -1,
        "id": user.ruobr_id,
        "time": time(),
    }
    pl1.update(args)
    pl2 = pl1.copy()
    pl2["direction"] = 1

    kb.add(Callback("<", pl1))
    kb.add(Callback(">", pl2))

    return kb.get_json()


def marks_kb(user, date0, date1):
    date0 = date0.strftime("%Y-%m-%d")
    date1 = date1.strftime("%Y-%m-%d")
    return _moving_kb(user, "marks", date0=date0, date1=date1)


def mail_kb(user, index):
    return _moving_kb(user, "mail", index=index)


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
