
import os
import pickle
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

COOKIE_JAR = os.getenv("VENDOR_COOKIE_JAR", "./data/cookies.pkl")

class Session:
    def __init__(self, cookies: Optional[dict] = None):
        self.cookies = cookies or {}

def login_or_load_session() -> Session:
    """Load cookies if present; otherwise perform a stub login and save cookies.

    Replace this stub with a real Hotplate login (or headful browser flow).
    """
    if os.path.exists(COOKIE_JAR):
        try:
            with open(COOKIE_JAR, "rb") as f:
                cookies = pickle.load(f)
            return Session(cookies=cookies)
        except Exception:
            pass

    # Stub: generate a fake cookie dict
    session = Session(cookies={"session": "stub-session-token"})
    os.makedirs(os.path.dirname(COOKIE_JAR), exist_ok=True)
    with open(COOKIE_JAR, "wb") as f:
        pickle.dump(session.cookies, f)
    return session
