from emoji import emojize
from telegram.ext import Application
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    PicklePersistence,
    ConversationHandler,
)
from timezonefinder import TimezoneFinder
from pytz import timezone, all_timezones
from datetime import datetime, timedelta

from .env import TOKEN
from .context import ChatData, Context
from .reminders import dequeue_reminder, enqueue_reminder
from .task import task_from_text
from .tz import ntp_time_offset, refresh_ntp_time_offset, true_now

tz_finder = TimezoneFinder()


async def new_msg(update: Update, context: Context) -> None:
    from re import compile

    chat = context.chat_data

    remove_item_matcher = compile(r"-[0-9]+")

    text = update.effective_message.text

    # TODO: refactor this
    if all(map(lambda substr: remove_item_matcher.match(substr), text.split())):
        indices = list(map(lambda t: int(t[1:]), text.split()))
        for i, idx in enumerate(indices):
            task = chat.delete_task(idx - i - 1)
            dequeue_reminder(context, task)

        await update.message.reply_markdown(
            f"{'Task' if len(indices) == 1 else 'Tasks'} {', '.join(list(map(lambda x: f'`{x}`', indices)))} removed"
        )
        return

    task = task_from_text(update.message.text, tz=chat.tz)

    if task.at != None:
        if task.at < true_now(task.at.tzinfo):
            await update.message.reply_markdown("Can't schedule a task in the past")
            return

        if chat.tz != None:
            enqueue_reminder(task, context.application, update.effective_chat.id)
        else:
            await update.message.reply_markdown(
                emojize(
                    ":fire::warning: Hey, timezone not configured! No timers will be scheduled"
                )
            )

    task.message_id = update.message.message_id
    chat.add_task(task)

    idx = 0
    for i, t in enumerate(chat.active_tasks):
        if t is task:
            idx = i
            break
    await update.message.reply_markdown_v2(
        f"`{i + 1}.` {task.as_markdown_str()}",
        disable_notification=True,
    )


async def list_all(update: Update, context: Context) -> None:
    fmt = lambda t: f"`{t[0] + 1}.` {t[1].as_markdown_str()}\n"
    tasks = context.chat_data.active_tasks
    if tasks:
        await update.message.reply_markdown_v2(
            f"\n{''.join(map(fmt, enumerate(tasks)))}"
        )
    else:
        await update.message.reply_text("You don't have any tasks!")


async def start(update: Update, context: Context) -> int:
    await update.message.reply_text("Hello, send ur location")
    return 0


async def msg_to_tz(update: Update, context: Context) -> int:
    if update.message.location != None:
        location = update.message.location
        tz = tz_finder.timezone_at(lat=location.latitude, lng=location.longitude)
    else:
        tz = update.effective_message.text

    if tz not in all_timezones:
        await update.message.reply_markdown(
            f"Sorry, timezone `{tz}` not found. Please make sure the timezone is formatted according to the timezone name like `UTC` or `Europe/Berlin`"
        )
        return 0

    tz = timezone(tz)
    context.chat_data.tz = tz

    time_on_server = datetime.now() + timedelta(seconds=ntp_time_offset())

    await update.message.reply_markdown(
        f"Your timezone is `{tz}`, all future timers will adjust accordingly. Time on the server: {time_on_server}"
    )
    return ConversationHandler.END


def app() -> Application:
    refresh_ntp_time_offset()
    context_types = ContextTypes(context=Context, chat_data=ChatData)
    persistence = PicklePersistence(filepath="state.pickle", update_interval=1)

    application = (
        Application.builder()
        .token(TOKEN())
        .context_types(context_types)
        .persistence(persistence)
        .build()
    )

    async def queue_timers(_ctx):
        chat_data = await application.persistence.get_chat_data()
        for chat_id, chat in chat_data.items():
            if chat.tz == None:
                continue

            for timed_task in filter(lambda t: t.at != None, chat.active_tasks):
                enqueue_reminder(timed_task, application, chat_id)

    application.job_queue.run_once(queue_timers, 0)

    tz_conversation = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={0: [MessageHandler(filters.LOCATION | filters.TEXT, msg_to_tz)]},
        fallbacks=[],
    )

    application.add_handler(tz_conversation)
    application.add_handler(CommandHandler("list", list_all))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, new_msg))
    return application
