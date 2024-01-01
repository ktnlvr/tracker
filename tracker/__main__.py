import logging
import os
from dotenv import load_dotenv
from telegram import Update

from .application import app


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


def main():
    app(TOKEN, WHITELIST).run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
