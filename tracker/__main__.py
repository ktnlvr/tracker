import logging
import os
from dotenv import load_dotenv
from telegram import ForceReply, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .state import state
from .task import task_from_text


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.environ.get("TG_TOKEN")
WHITELIST = (os.environ.get("TG_WHITELIST") or "").strip(",")

if not TOKEN:
    logger.error("No token environmental variable")
    exit(-1)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.name not in WHITELIST:
        await update.message.reply_html(
            rf"Access denied, you are not whitelisted.",
        )
    else:
        if not state().check_user(user.name):
            state().add_user(user.name)

        await update.message.reply_html(
            rf"Hi {user.mention_html()}!",
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Help!")


async def new_msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from re import compile

    remove_item_matcher = compile(r"-[0-9]+")

    text = update.message.text
    user = state().get_user(update.effective_user.name)
    assert user

    if remove_item_matcher.match(text):
        idx = int(text[1:]) - 1
        task = state().delete_user_task(user, idx)
        await update.message.reply_markdown(f"Task `{task}` removed")
        return

    task = task_from_text(update.message.text)
    state().add_user_task(user, task)
    await update.message.reply_markdown(f"`+`{task}")


async def list_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = state().get_user(update.effective_user.name)
    fmt = lambda t: f"`{t[0] + 1}:` {t[1]}\n"
    tasks = state().get_user_tasks(user)
    if tasks:
        await update.message.reply_markdown(f"\n{''.join(map(fmt, enumerate(tasks)))}")
    else:
        await update.message.reply_text("You don't have any tasks!")


def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list", list_all))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, new_msg))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
