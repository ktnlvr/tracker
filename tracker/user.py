from .task import Task
from pydantic import BaseModel

class User(BaseModel):
    name: str
    active_tasks: list[Task]
