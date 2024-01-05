from ntplib import NTPClient
from datetime import datetime, timedelta, timezone

from .logging import logger
from .env import NTP_SERVER

_ntp_time_offset = 0


def true_now(tz: timezone | None = None) -> datetime:
    return datetime.now(tz) + timedelta(seconds=_ntp_time_offset)


def refresh_ntp_time_offset():
    global _ntp_time_offset
    client = NTPClient()
    _ntp_time_offset = client.request(NTP_SERVER()).offset
    logger.debug(f"NTP Time Offset Refreshed: {_ntp_time_offset}")


def ntp_time_offset() -> float:
    global _ntp_time_offset
    return _ntp_time_offset
