# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BagelBot is a Python automation scaffold for placing scheduled orders on Hotplate-based vendor platforms. The core flow is: authenticate → fetch menu → resolve items → build cart → checkout. Most API-interacting functions are currently stubs ready for real Hotplate integration.

## Development Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Run with dry-run (no actual checkout)
python main.py --vendor bagelshop --time "07:59" --dry-run

# Run tests
pytest tests/

# Run single test file
pytest tests/test_imessage.py

# Run specific test
pytest tests/test_imessage.py::test_fetch_messages_returns_entries
```

## Architecture

**Core Order Flow** (`main.py` orchestrates):
```
main.py → scheduler.py → auth.py → menu.py → order.py → SQLite
```

**Key Modules:**
- `auth.py` - Session management, loads/saves cookies to `data/cookies.pkl`
- `menu.py` - Menu fetching and item-to-SKU resolution with substitution fallback
- `order.py` - Cart building and checkout, stores orders to `data/orders.db` (SQLite)
- `scheduler.py` - `sleep_until()` waits for 24-hour local time trigger

**Auxiliary Modules:**
- `imessage.py` - Reads macOS Messages database (`~/Library/Messages/chat.db`) in read-only mode
- `polling.py` - Polls Hotplate API (`https://bets.hotplate.com/trpc/`) for drop events

**Configuration:**
- `config/vendor.yaml` - Storefront URL, location, pickup/delivery mode
- `config/order.yaml` - Items with options, quantities, tip, substitution preferences

## Key Implementation Notes

- Most core functions (`fetch_menu`, `checkout`, `login_or_load_session`) are stubs returning mock data
- Menu resolution in `menu.py:resolve_items()` implements smart substitution: if item unavailable, tries alternatives from `order.yaml` substitutions list
- iMessage module uses Apple's Core Data timestamp format (seconds since 2001-01-01) converted to Python datetime
- Polling module has hardcoded event/cart IDs for Holey Dough vendor; needs parameterization for other vendors
