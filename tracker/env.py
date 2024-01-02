import os
from dotenv import load_dotenv

load_dotenv()


def TOKEN() -> str:
    if tok := os.environ.get("TG_TOKEN"):
        return tok
    else:
        raise Exception("No token provided")


def NTP_SERVER() -> str:
    if ntp := os.environ.get("TG_NTP_SERVER"):
        return ntp
    else:
        raise Exception("No NTP server defined")
