# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BagelBot is a Python automation tool for securing orders from Holey Dough bagel shop in Chicago during their limited-availability drops. The shop uses HotPlate as their storefront platform, which operates on a TRPC API.

### Core Problem
Holey Dough releases ordering windows ("drops") at specific times that sell out within seconds. Manual ordering is nearly impossible due to:
- Extremely high demand (sells out in <10 seconds)
- Limited inventory
- Multiple steps required (menu selection, cart creation, checkout)

### Solution Approach
Build an automated system that:
1. **Monitors** for new drop events via API polling
2. **Detects** when a drop goes live (based on `goLiveTime` timestamp)
3. **Executes** order placement automatically:
   - Create cart
   - Add pre-configured items with options
   - Complete checkout with saved payment/customer info
4. **Optimizes** for speed (sub-second execution time)

## Technical Architecture

### API Pattern
HotPlate uses TRPC endpoints with this structure:
- Base URL: `https://bets.hotplate.com/trpc/`
- Pattern: `namespace.action` (e.g., `shop.getEvent`, `cart.create`)
- Request format: GET with JSON-encoded `input` parameter
- Response format: `{"result": {"data": {...}}}`

### Current Implementation Status

#### ✅ Completed Functions (in `polling.py`)
- `get_old_drops()` - Fetch past drop events
- `get_old_drop_event_ids()` - Extract event IDs and metadata
- `display_drops()` - Pretty-print drop history
- `get_menu_items()` - Fetch basic menu for an event
- `get_all_menu_items()` - Fetch detailed menu with options/inventory
- `display_all_menu_items()` - Pretty-print full menu with options
- `validate_carts()` - Test cart API endpoints for validity
- `display_cart_validation_results()` - Display endpoint test results
- `get_upcoming_drops()` - Fetch upcoming drop events
- `monitor_for_new_event()` - Poll for upcoming events and detect when drops go live
- `display_upcoming_events()` - Pretty-print upcoming events with status

#### 🚧 In Progress
- `create_cart()` - Initialize shopping cart session

#### ⏳ Not Started
- `add_item_to_cart()` - Add items with option selections to cart
- `get_cart()` - Retrieve current cart state
- `select_time_window()` - Choose pickup time slot
- `checkout()` - Complete order with payment
- `wait_until_go_live()` - Precision timing to execute at drop time
- Main orchestration/bot script

## Development Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # If exists

# Run current functions
python polling.py

# Test cart endpoint discovery
python -c "from polling import validate_carts; validate_carts()"
```
