from emoji import emojize
from os.path import join as path_join, pardir, abspath, basename
import os
import sys

# importing resources is a mess, use this for now
_vocabulary: dict[str, dict[str]] = {
    "en": {
        "help": """Hello! I am a bot for your todo list.
Use /help to view this list.

Send me a message to add it as a task to your todo list. The more exclamation marks it has, the higher it will appear on the list.

You can include references to time (like 10:45 or 4pm), a day of the week (Mon, Wednesday) or a date (like `dd.mm.yyyy` or `mm/dd/yy`).
The reminder will be automatically scheduled if the timezone is set.

Use /list to view all the entire list.

To remove an item from the list simply type -1, replacing 1 with the number of the item in the list. Keep in mind, the order of the items automatically changed upon insertions.
""",
        "start": "Hello! I am a bot for keeping your todo list. Please send your timezone name (like `Europe/Berlin`) or your location for automatic inference. Later you can use /help to view all commands.",
        "timezone_missing": ":fire::warning: Hey, timezone not configured! No timers will be scheduled",
        "timezone_set": "Your timezone is set to {tz}, all the timers will adjust accordingly.",
        "timezone_not_found": "Sorry, timezone `{tz}` not found. Please make sure the timezone is formatted according to the timezone name like `UTC` or `Europe/Berlin`.",
        "task_in_the_past": "Can not schedule a task in the past",
        "task_does_not_exist": "Task at index {idx} does not exist",
        "task_removed": "Task {removed} removed",
        "tasks_removed": "Tasks {removed} removed",
        "no_tasks": "You don't have any tasks!",
    },
    "ru": {
        "timezone_set": "Установлен часовой пояс {tz}, все напоминания будут перенесены."
    },
}


# use IETF language tag
def get_text(
    phrase: str,
    lang: str,
    **kwargs,
):
    lang_vocab: dict = _vocabulary.get(lang[:2]) or _vocabulary["en"]
    phrase: str = lang_vocab[phrase]
    return emojize(phrase.format(**kwargs)).strip()
