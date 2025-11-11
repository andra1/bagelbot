
import os, sqlite3, json, time, uuid
from typing import Dict, Any, List

DB_PATH = os.getenv("DB_PATH", "./data/orders.db")

def _ensure_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            created_at TEXT,
            payload TEXT,
            total_cents INTEGER,
            confirmation_id TEXT
        )
        """)
        conn.commit()

def build_cart(menu_resolved: List[Dict[str, Any]], order_cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Create a minimal cart payload. Replace pricing with real values later."""
    cart_id = str(uuid.uuid4())
    return {
        "cart_id": cart_id,
        "items": menu_resolved,
        "tip_percent": order_cfg.get("tip_percent", 0),
        "pickup_time": order_cfg.get("pickup_time"),
    }

def checkout(session, cart: Dict[str, Any]) -> Dict[str, Any]:
    """Stub checkout: simulate a success."""
    confirmation_id = f"CONF-{int(time.time())}"
    receipt = {
        "confirmation_id": confirmation_id,
        "total_cents": 1299,  # placeholder
        "cart_id": cart.get("cart_id"),
        "pickup_time": cart.get("pickup_time"),
    }
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO orders (id, created_at, payload, total_cents, confirmation_id) VALUES (?, datetime('now'), ?, ?, ?)",
            (cart["cart_id"], json.dumps(cart), receipt["total_cents"], receipt["confirmation_id"])
        )
        conn.commit()
    return receipt
