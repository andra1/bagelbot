"""
Vendor polling helper for Hotplate vendor drops.

Usage:
    from vendor_poll import poll_for_vendor_drop

    result = poll_for_vendor_drop(
        "https://hotplate.example.com/api/vendor/123",
        interval=5,
        timeout=600,
        session=my_requests_session,   # optional requests.Session
        check_fn=None,                 # optional custom check function
        on_activate=lambda resp: print("Activated!")
    )

Returns a dict:
    {
        "activated": bool,
        "attempts": int,
        "last_status_code": int,
        "last_text": str
    }
"""
import time
import json
from typing import Callable, Optional, Dict, Any
import requests

def _default_check_fn(resp: requests.Response) -> bool:
    """Return True if response indicates vendor is active.

    Tries JSON heuristics first, then falls back to simple HTML/text checks.
    """
    # Try JSON heuristics
    try:
        j = resp.json()
        # common keys that might indicate activation
        candidates = []
        if isinstance(j, dict):
            candidates.append(j)
            # flatten one-level nested dicts
            for v in j.values():
                if isinstance(v, dict):
                    candidates.append(v)

        for obj in candidates:
            # boolean flags
            for key in ("active", "is_active", "is_open", "open", "available"):
                if key in obj:
                    val = obj[key]
                    if isinstance(val, bool) and val:
                        return True
                    if isinstance(val, (int, float)) and val != 0:
                        return True
                    if isinstance(val, str) and val.lower() in ("1", "true", "yes", "open", "available"):
                        return True
            # status strings
            if "status" in obj:
                s = str(obj["status"]).lower()
                if any(k in s for k in ("active", "open", "live", "available", "on")):
                    return True
    except ValueError:
        # not JSON
        pass
    except Exception:
        # treat parse errors as non-activation, continue to text checks
        pass

    # Text/HTML heuristics
    txt = resp.text.lower()
    if any(token in txt for token in ("drop live", "order now", "add to cart", "open for orders", "open now", "now available", "available now")):
        return True

    # No obvious activation indicator
    return False

def poll_for_vendor_drop(
    url: str,
    interval: float = 5.0,
    timeout: Optional[float] = 600.0,
    session: Optional[requests.Session] = None,
    check_fn: Optional[Callable[[requests.Response], bool]] = None,
    on_activate: Optional[Callable[[requests.Response], Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Poll `url` every `interval` seconds until check_fn(response) returns True or timeout is reached.

    - url: full URL to poll
    - interval: seconds between polls
    - timeout: maximum seconds to wait (None for infinite)
    - session: optional requests.Session (if omitted, a transient requests session is used)
    - check_fn: function(resp) -> bool; if omitted, uses _default_check_fn
    - on_activate: optional callback(resp) called once when activation detected
    - headers/params: optional request headers & query params

    Returns dict with activation result and last response snapshot.
    Raises requests.RequestException for network errors that bubble up.
    """
    checker = check_fn or _default_check_fn
    sess = session or requests.Session()
    start = time.monotonic()
    attempts = 0

    while True:
        attempts += 1
        try:
            resp = sess.get(url, headers=headers, params=params, timeout=10)
        except requests.RequestException:
            # For transient network errors, continue polling until timeout
            if timeout is not None and (time.monotonic() - start) >= timeout:
                return {
                    "activated": False,
                    "attempts": attempts,
                    "last_status_code": None,
                    "last_text": "",
                }
            time.sleep(interval)
            continue

        activated = False
        try:
            activated = bool(checker(resp))
        except Exception:
            # If custom checker throws, treat as not activated and continue
            activated = False

        if activated:
            if on_activate:
                try:
                    on_activate(resp)
                except Exception:
                    # swallow exceptions from callback
                    pass
            return {
                "activated": True,
                "attempts": attempts,
                "last_status_code": resp.status_code,
                "last_text": resp.text,
            }

        # check timeout
        if timeout is not None and (time.monotonic() - start) >= timeout:
            return {
                "activated": False,
                "attempts": attempts,
                "last_status_code": resp.status_code,
                "last_text": resp.text,
            }

        time.sleep(interval)