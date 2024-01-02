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
        self.active_tasks.sort(key=lambda t: (t.priority or 0))
        self.active_tasks.reverse()

    def delete_task(self, task_idx: int) -> Task:
        task = self.active_tasks[task_idx]
        del self.active_tasks[task_idx]
        return task

    def delete_task_if_exists(self, task: Task) -> True:
        for i, t in enumerate(self.active_tasks):
            if t == task:
                self.delete_task(i)
                return True
        return False


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
