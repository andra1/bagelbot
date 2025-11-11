
# BagelBot (Hotplate) — Starter Scaffold

A minimal, pragmatic repo for placing scheduled orders on a Hotplate-based bagel vendor.

## Quick Start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py --vendor bagelshop --time "07:59" --dry-run
```

## Structure

```
bagelbot/
  config/
    vendor.yaml        # storefront url, location id, mode (pickup/delivery), open times
    order.yaml         # items, options, quantities, tip
  auth.py              # login or load session cookie
  menu.py              # fetch menu, resolve items/options
  order.py             # build cart, checkout, store receipt
  scheduler.py         # schedule, warm-up, trigger, simple retry
  main.py              # CLI glue
  requirements.txt     # dependencies
  .env.example         # environment variables
  data/                # sqlite db / cookies / logs (gitignored)
  tests/               # basic unit tests
```

## Notes
- No real payment is performed here — stubs only.
- Keep it respectful of ToS and rate limits.
- Extend gradually: wallet tokens, richer retries, notifications.
