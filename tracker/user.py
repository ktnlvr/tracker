from .task import Task
from pydantic import BaseModel

class User(BaseModel):
    name: str
    chat_id: int
    active_tasks: list[Task]
