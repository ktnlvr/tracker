from datetime import datetime
from telegram.ext import (
    Application,
    CallbackContext,
    ExtBot,
)

from typing import Optional
from .task import Task


class ChatData:
    def __init__(self):
        self.active_tasks: list[Task] = []
        self.tz: Optional[datetime] = None

    def add_task(self, task: Task):
        self.active_tasks.append(task)

    def delete_task(self, task_idx: int) -> Task:
        task = self.active_tasks[task_idx]
        del self.active_tasks[task_idx]
        return task


class Context(CallbackContext[ExtBot, dict, ChatData, dict]):
    def __init__(
        self,
        application: Application,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ):
        super().__init__(application=application, chat_id=chat_id, user_id=user_id)

    def is_whitelisted(self, user: str):
        return True
