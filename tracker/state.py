from collections import defaultdict
from typing import Optional
from pydantic import BaseModel
import os
import pickle
import weakref

from .task import Task
from .user import User


class State():
    instance = None

    def __init__(self):
        self.users = []

    def check_user(self, name: str) -> bool:
        for user in self.users:
            if user.name == name:
                return True
        return False

    def add_user(self, name: str) -> User:
        self.users.append(User(name=name, active_tasks=[]))

    def add_user_task(self, user: User, task: Task):
        assert user in self.users
        user.active_tasks.append(task)
        user.active_tasks.sort(key=lambda t: -(t.priority or 0))

    def get_user_tasks(self, user: User) -> list[Task]:
        return user.active_tasks or []

    def delete_user_task(self, user: User, idx: int) -> Task:
        task = user.active_tasks[idx]
        del user.active_tasks[idx]
        return task


    def get_user(self, name: str) -> Optional[User]:
        for user in self.users:
            if user.name == name:
                return user
        return None


def state() -> State:
    if State.instance:
        return State.instance

    if os.path.exists("state.pickle"):
        with open("state.pickle", "rb") as pkl:
            State.instance = pickle.load(pkl)
    else:
        State.instance = State()
    return State.instance


weakref.finalize(
    state(),
    lambda: pickle.dump(
        state(), open("state.pickle", "wb+"), protocol=pickle.HIGHEST_PROTOCOL
    ),
)
