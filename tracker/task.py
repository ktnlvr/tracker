from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from emoji import emojize
import re

priority_regex = re.compile(r"(!+)")
time24_regex = re.compile(r"([0-9]{1,2}:[0-9]{2})")


class Task(BaseModel):
    text: Optional[str]
    priority: Optional[int]
    at: Optional[datetime]
    message_id: Optional[int]

    def __str__(self):
        desc = descriptor_from_task(self)
        return f"{self.text} {f'({desc})' if desc else ''}".strip()


def task_from_text(text: str):
    matched_priority = priority_regex.search(text)
    priority = len(matched_priority.group(0)) if matched_priority else None
    matched_time24 = time24_regex.search(text)
    time24 = matched_time24.group(0) if matched_time24 else None

    at = None
    if time24:
        hours, minutes = map(int, time24.split(':'))

        now = datetime.now()
        if now.hour * 60 + now.minute > hours * 60 + minutes:
            now += timedelta(days=1)
        at = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)

    return Task(text=text, priority=priority, at=at, message_id=None)


def descriptor_from_task(task: Task) -> str:
    out = ""
    if task.at != None:
        # task.at.strftime('%H:%M %d/%m/%Y')
        out += f":alarm_clock: {task.at.strftime('%H:%M %d/%m/%Y')}"
    return emojize(out)
