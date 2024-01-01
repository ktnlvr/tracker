from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from emoji import emojize
import re

priority_regex = re.compile(r"(!+)")
time24_regex = re.compile(r"([0-9]{1,2}:[0-9]{2})")


class Task(BaseModel):
    text: Optional[str]
    priority: Optional[int]
    at: Optional[datetime]

    def __str__(self):
        return f"{self.text}".strip()


def task_from_text(text: str):
    matched_priority = priority_regex.search(text)
    priority = len(matched_priority.group(0)) if matched_priority else None
    return Task(text=text, priority=priority, at=None)


def descriptor_from_task(task: Task) -> str:
    out = ""
    if task.at != None:
        out += ":alarm_clock:"
    return emojize(out)
