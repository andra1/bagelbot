
import argparse, yaml, os, json
from auth import login_or_load_session
from menu import fetch_menu, resolve_items
from order import build_cart, checkout
from scheduler import sleep_until

def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def run(vendor_cfg_path, order_cfg_path, trigger_time=None, dry_run=False):
    vendor_cfg = load_yaml(vendor_cfg_path)
    order_cfg = load_yaml(order_cfg_path)

    if trigger_time:
        print(f"[BagelBot] Waiting until {trigger_time} ...")
        sleep_until(trigger_time)

    session = login_or_load_session()
    print("[BagelBot] Session loaded.")

    menu = fetch_menu(session)
    resolved = resolve_items(menu, order_cfg)
    print("[BagelBot] Items resolved:", json.dumps(resolved, indent=2))

    cart = build_cart(resolved, order_cfg)
    if dry_run:
        print("[BagelBot] Dry run — cart payload:")
        print(json.dumps(cart, indent=2))
        return

    receipt = checkout(session, cart)
    print("[BagelBot] Order placed! Receipt:")
    print(json.dumps(receipt, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BagelBot — minimal Hotplate auto-ordering scaffold")
    parser.add_argument("--vendor", default="bagelshop", help="Vendor key (unused in stub)")
    parser.add_argument("--time", dest="trigger_time", default=None, help="Trigger time HH:MM[:SS]")
    parser.add_argument("--dry-run", action="store_true", help="Do everything except final checkout")
    parser.add_argument("--vendor-config", default="./config/vendor.yaml", help="Path to vendor config YAML")
    parser.add_argument("--order-config", default="./config/order.yaml", help="Path to order config YAML")
    args = parser.parse_args()

    run(args.vendor_config, args.order_config, args.trigger_time, args.dry_run)
