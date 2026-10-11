from datetime import datetime, time

START_HOUR = 6   # 6:00 AM
END_HOUR = 18   # 6:00 PM

def is_within_active_hours() -> bool:
    """Returns True if current local time is between 6:00 AM and 6:00 PM."""
    now = datetime.now().time()
    return time(START_HOUR, 0) <= now < time(END_HOUR, 0)