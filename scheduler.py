
import time
from datetime import datetime

def sleep_until(target_str: str):
    """Sleep until HH:MM or 'HH:MM:SS'. 24h local time."""
    now = datetime.now()
    parts = [int(p) for p in target_str.split(":")]
    hh, mm = parts[0], parts[1]
    ss = parts[2] if len(parts) > 2 else 0
    target = now.replace(hour=hh, minute=mm, second=ss, microsecond=0)
    if target <= now:
        target = target.replace(day=now.day)  # same day; if already passed, just run immediately
    delta = (target - now).total_seconds()
    if delta > 0:
        time.sleep(delta)
