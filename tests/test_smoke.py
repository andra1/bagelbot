
import yaml
from menu import fetch_menu, resolve_items
from auth import login_or_load_session
from order import build_cart

def test_smoke():
    session = login_or_load_session()
    menu = fetch_menu(session)
    cfg = {
        "items": [{"name": "Everything Bagel", "options": {"spread": "Cream Cheese", "toasted": True}, "quantity": 1}],
        "tip_percent": 10
    }
    resolved = resolve_items(menu, cfg)
    cart = build_cart(resolved, cfg)
    assert cart["items"][0]["sku"].startswith("SKU_")
