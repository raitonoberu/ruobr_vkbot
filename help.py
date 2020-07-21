from datetime import timedelta


def convert_marks(marks):
    # {'Иностранный язык': [{'question_name': 'Ответ на уроке', 'question_id': 102494195, 'number': 1, 'question_type': 'Ответ на уроке', 'mark': '5'}], 'ОБЖ': [{'question_name': 'Ответ на уроке', 'question_id': 101356763, 'number': 1, 'question_type': 'Ответ на уроке', 'mark': '4'}]}
    marks = {key: [i['mark'] for i in marks[key]] for key in marks.keys()}
    return marks
    # [{'Иностранный язык': ['5'], 'ОБЖ': ['4']}]


def compare_marks(marks0, marks1):
    if marks0 == marks1:
        return {}
    result = marks1.copy()
    for subject, marks in marks0.items():
        try:
            if marks == marks1[subject]:
                result.pop(subject)
                continue
            for index, mark in enumerate(marks):
                if marks1[subject][index] == mark:
                    result[subject].pop(index)
        except (KeyError, IndexError):
            pass
    return result


def marks_to_str(marks):
    return "\n".join([f"{subject.strip()}: {', '.join(marks)}" for subject, marks in marks.items()])


def monday(date):
    while date.weekday() != 0:
        date -= timedelta(days=1)
    return date
