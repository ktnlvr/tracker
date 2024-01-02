from ntplib import NTPClient

_ntp_time_offset = 0


def refresh_ntp_time_offset():
    global _ntp_time_offset
    client = NTPClient()
    _ntp_time_offset = client.request("pool.ntp.org").offset
    print(f"NTP Time Offset Refreshed: {_ntp_time_offset}")


def ntp_time_offset() -> float:
    global _ntp_time_offset
    return _ntp_time_offset
