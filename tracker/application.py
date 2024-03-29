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

from tracker.lang import get_text

from .env import TOKEN
from .context import ChatData, Context
from .reminders import dequeue_reminder, enqueue_reminder
from .task import task_from_text
from .tz import ntp_time_offset, refresh_ntp_time_offset, true_now

tz_finder = TimezoneFinder()


async def new_msg(update: Update, context: Context) -> None:
    from re import compile

    lang = update.effective_user.language_code
    chat = context.chat_data

    remove_item_matcher = compile(r"-[0-9]+")

    text = update.effective_message.text

    # TODO: refactor this
    if all(map(lambda substr: remove_item_matcher.match(substr), text.split())):
        indices = list(map(lambda t: int(t[1:]), text.split()))

        for idx in indices:
            if idx > len(chat.active_tasks):
                await update.message.reply_markdown(
                    get_text("task_does_not_exist", idx=idx, lang=lang)
                )
                return

        for i, idx in enumerate(indices):
            task = chat.delete_task(idx - i - 1)
            dequeue_reminder(context, task)

        removed_tasks = ", ".join(list(map(lambda x: f"`{x}`", indices)))
        task_text = get_text(
            "task_removed" if len(indices) == 1 else "tasks_removed",
            removed=removed_tasks,
            lang=lang,
        )

        await update.message.reply_markdown(task_text)
        return

    task = task_from_text(update.message.text, tz=chat.tz)

    if task.at != None:
        if task.at < true_now(task.at.tzinfo):
            await update.message.reply_markdown(get_text("task_in_the_past", lang=lang))
            return

        if chat.tz != None:
            enqueue_reminder(task, context.application, update.effective_chat.id)
        else:
            await update.message.reply_markdown(get_text("timezone_missing", lang=lang))

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


async def list_all(update: Update, context: Context):
    lang = update.effective_user.language_code
    fmt = lambda t: f"`{t[0] + 1}.` {t[1].as_markdown_str()}\n"
    tasks = context.chat_data.active_tasks
    if tasks:
        await update.message.reply_markdown_v2(
            f"\n{''.join(map(fmt, enumerate(tasks)))}"
        )
    else:
        await update.message.reply_text(get_text("no_tasks", lang=lang))


async def start(update: Update, _) -> int:
    lang = update.effective_user.language_code
    await update.message.reply_markdown(get_text("start", lang=lang))
    return 0


async def help(update: Update, _):
    lang = update.effective_user.language_code
    await update.message.reply_markdown(get_text("help", lang=lang))


async def msg_to_tz(update: Update, context: Context) -> int:
    lang = update.effective_user.language_code

    if update.message.location != None:
        location = update.message.location
        tz_name = tz_finder.timezone_at(lat=location.latitude, lng=location.longitude)
    else:
        tz_name = update.effective_message.text

    if tz_name not in all_timezones:
        await update.message.reply_markdown(
            get_text("timezone_not_found", tz=tz_name, lang=lang)
        )
        return 0

    tz = timezone(tz_name)
    context.chat_data.tz = tz

    await update.message.reply_markdown(get_text("timezone_set", tz=tz_name, lang=lang))
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

    application.add_handler(CommandHandler("help", help))
    application.add_handler(tz_conversation)
    application.add_handler(CommandHandler("list", list_all))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, new_msg))
    return application
