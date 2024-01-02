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

from .context import ChatData, Context
from .reminders import dequeue_reminder, enqueue_reminder
from .task import task_from_text
from .tz import refresh_ntp_time_offset

tz_finder = TimezoneFinder()


async def new_msg(update: Update, context: Context) -> None:
    from re import compile

    data = context.chat_data

    remove_item_matcher = compile(r"-[0-9]+")

    text = update.message.text

    # TODO: refactor this
    if all(map(lambda substr: remove_item_matcher.match(substr), text.split())):
        indices = list(map(lambda t: int(t[1:]), text.split()))
        for i, idx in enumerate(indices):
            task = data.delete_task(idx - i - 1)
            dequeue_reminder(context, task)

        await update.message.reply_markdown(
            f"{'Task' if len(indices) == 1 else 'Tasks'} {', '.join(list(map(lambda x: f'`{x}`', indices)))} removed"
        )
        return

    task = task_from_text(update.message.text, tz=data.tz)
    task.message_id = update.message.message_id
    data.add_task(task)

    if task.at != None:
        enqueue_reminder(task, context.application, update.effective_chat.id)

    idx = 0
    for i, t in enumerate(data.active_tasks):
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
        # TODO: timezone not found
        return 0
    tz = timezone(tz)
    context.chat_data.tz = tz

    await update.message.reply_markdown(
        f"Your timezone is `{tz}`, all the timers will adjust accordingly"
    )
    return ConversationHandler.END


def app(token: str, whitelist: list[str]) -> Application:
    refresh_ntp_time_offset()
    context_types = ContextTypes(context=Context, chat_data=ChatData)
    persistence = PicklePersistence(filepath="state.pickle", update_interval=1)

    application = (
        Application.builder()
        .token(token)
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
