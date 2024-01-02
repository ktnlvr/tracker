from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from emoji import emojize
from telegram.helpers import escape_markdown
import re

priority_regex = re.compile(r"(!+)")
time24_regex = re.compile(r"([0-9]{1,2}:[0-9]{2})")


class Task(BaseModel):
    text: Optional[str]
    priority: Optional[int]
    at: Optional[datetime]
    message_id: Optional[int]
    special_spans: list[tuple[int, int]]

    def __str__(self) -> str:
        return f"{self.text}".strip()

    def as_markdown_str(self) -> str:
        offset = 0
        text = self.text
        for begin, end in self.special_spans:
            begin += offset
            end += offset
            text = text[:begin] + "__" + text[begin:end] + "__" + text[end:]
            offset += 4
        return text


def task_from_text(text: str):
    text = escape_markdown(text, version=2)
    special_spans = []

    matched_priority = priority_regex.search(text)
    priority = len(matched_priority.group(0)) if matched_priority else None
    matched_time24 = time24_regex.search(text)
    time24 = matched_time24.group(0) if matched_time24 else None

    at = None
    if time24:
        special_spans.append(matched_time24.span())
        hours, minutes = map(int, time24.split(":"))

        now = datetime.now()
        if now.hour * 60 + now.minute > hours * 60 + minutes:
            now += timedelta(days=1)
        at = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)

    return Task(text=text, priority=priority, at=at, message_id=None, special_spans=special_spans)


def descriptor_from_task(task: Task) -> str:
    out = ""
    if task.at != None:
        out += f":alarm_clock:"
    return emojize(out)
