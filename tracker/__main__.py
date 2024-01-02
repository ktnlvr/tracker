import logging
from telegram import Update

from .application import app
from .logging import logger
from .env import TOKEN

if not TOKEN():
    logger.error("No token environmental variable")
    exit(-1)


def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    logger.setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.DEBUG)

    app().run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
