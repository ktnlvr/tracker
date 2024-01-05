from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from emoji import emojize
from telegram.helpers import escape_markdown
import re

from .tz import true_now

priority_regex = re.compile(r"((?:\\?!)+)")
time24_regex = re.compile(r"([0-9]{1,2}:[0-9]{2})")


class Task(BaseModel):
    text: Optional[str]
    priority: int
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

    def sort_key(self) -> tuple:
        return self.priority


def task_from_text(text: str, tz: timezone | None = None):
    text = escape_markdown(text, version=2)
    special_spans = []

    matched_priority = priority_regex.search(text)
    priority = matched_priority.group(0).count('!') if matched_priority else 0
    matched_time24 = time24_regex.search(text)
    time24 = matched_time24.group(0) if matched_time24 else None

    at = None
    if time24:
        special_spans.append(matched_time24.span())
        hours, minutes = map(int, time24.split(":"))

        # convert to true, system independent time
        now = true_now()
        at = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        if at < now:
            at += timedelta(days=1)

    return Task(
        text=text,
        priority=priority,
        at=at,
        message_id=None,
        special_spans=special_spans,
    )
