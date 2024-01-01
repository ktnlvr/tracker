from telegram.ext import Application
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    PicklePersistence,
)

from .context import ChatData, Context
from .task import task_from_text


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
        await update.message.reply_markdown(
            f"{'Task' if len(indices) == 1 else 'Tasks'} {', '.join(list(map(lambda x: f'`{x}`', indices)))} removed"
        )
        return

    task = task_from_text(update.message.text)
    data.add_task(task)

    idx = 0
    for i, t in enumerate(data.active_tasks):
        if t is task:
            idx = i
            break
    await update.message.reply_markdown(f"`{i + 1}.` {task}")


async def list_all(update: Update, context: Context) -> None:
    fmt = lambda t: f"`{t[0] + 1}.` {t[1]}\n"
    tasks = context.chat_data.active_tasks
    if tasks:
        await update.message.reply_markdown(f"\n{''.join(map(fmt, enumerate(tasks)))}")
    else:
        await update.message.reply_text("You don't have any tasks!")


async def reminder_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    from emoji import emojize

    job = context.job
    await context.bot.send_message(
        job.chat_id, text=emojize(f":alarm_clock: {job.data}")
    )


def app(token: str, whitelist: list[str]) -> Application:
    context_types = ContextTypes(context=Context, chat_data=ChatData)
    persistence = PicklePersistence(filepath="state.pickle", update_interval=1)

    application = (
        Application.builder()
        .token(token)
        .context_types(context_types)
        .persistence(persistence)
        .build()
    )

    application.add_handler(CommandHandler("list", list_all))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, new_msg))
    return application
