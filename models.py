from aiogram.filters.callback_data import CallbackData

class ActionCallback(CallbackData, prefix='action'):
    action: str

class Question():
    def __init__(self, id, question, used) -> None:
        self.id = id
        self.question = question
        self.used = used

class User():
    def __init__(self, id, username=None, first_name=None, last_name=None, is_bot=None, status=None) -> None:
        self.id = int(id)
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.is_bot = is_bot
        self.status = status