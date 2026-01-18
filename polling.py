"""Utilities for retrieving Holey Dough drop information.
1. I can make direct API calls to the shop.getEvent endpoint to get drop info for past events
2. Need to repeatedly poll endpoint to check for new events
3. Once a new event is detected, create a Post request to place order
"""

import requests
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table

BASE_URL = "https://bets.hotplate.com/trpc/shop.getEvent"
console = Console()

def get_drop_info():
    url = "https://bets.hotplate.com/trpc/shop.getEvent"
    params = {
        "input": json.dumps({
            "eventId": "458ea76e-1f07-44ed-b6d5-451287f8e10b",
            "fulfillmentType": "PICKUP",
            "cartId": "67665a31-9b71-455d-84f6-2727fb08e618"
        })
    }

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "Origin": "https://www.hotplate.com",
        "Referer": "https://www.hotplate.com/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        print("Status Code:", response.status_code)
        print("Response JSON (first 500 ", json.dumps(data, indent=2))
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def poll_for_new_drops(url: str, params: dict, headers: dict):
    """Poll the Holey Dough shop.getEvent endpoint for new drops. """
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        print("Status Code:", response.status_code)
        print("Response JSON (first 500 ", json.dumps(data, indent=2))
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    # Implementation of polling logic goes here

def format_timestamp(ms: int) -> str:
    """Convert millisecond timestamp to readable date string."""
    if not ms:
        return "N/A"
    dt = datetime.fromtimestamp(ms / 1000)
    return dt.strftime("%m/%d %I:%M%p").lower()


def get_old_drop_event_ids() -> list[dict]:
    """Get event IDs and titles from past Holey Dough drops.

    Returns:
        List of dictionaries containing:
        - id: The event ID (UUID string)
        - title: The event title (e.g., "Saturday Pickup (1/17/26)")
        - go_live_time: When orders opened (millisecond timestamp)
        - order_cutoff_time: When orders closed (millisecond timestamp)
    """
    data = get_old_drops()
    past_events = data.get("result", {}).get("data", {}).get("pastEvents", [])

    return [
        {
            "id": event.get("id"),
            "title": event.get("title"),
            "go_live_time": event.get("goLiveTime"),
            "order_cutoff_time": event.get("orderCutoffTime"),
        }
        for event in past_events
    ]


def get_old_drops():
    """Fetch and display past drop information from Holey Dough."""
    url = "https://bets.hotplate.com/trpc/shop.getPublicPastEvents"
    params = {
        "input": json.dumps({
            "chefId": "holeydoughandco",
            "direction": "forward"
        })
    }
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "Origin": "https://www.hotplate.com",
        "Referer": "https://www.hotplate.com/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error fetching drops: {e}[/red]")
    return data
    
def display_drops(data: dict):
    """Display past drop information in a formatted table."""
    past_events = data.get("result", {}).get("data", {}).get("pastEvents", [])
    if not past_events:
        console.print("[yellow]No past drops found.[/yellow]")
        return

    # Get location from first event (same for all Holey Dough drops)
    first_event = past_events[0]
    time_windows = first_event.get("timeWindows", {})
    location = "Unknown"
    if time_windows:
        first_window = next(iter(time_windows.values()))
        loc_data = first_window.get("location", {})
        if loc_data:
            location = loc_data.get("title", "Unknown")

    console.print(f"\n[bold cyan]Holey Dough - Past Drops[/bold cyan]")
    console.print(f"[dim]Location: {location}[/dim]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Title", style="cyan", no_wrap=True)
    table.add_column("Opens", style="green", no_wrap=True)
    table.add_column("Cutoff", style="yellow", no_wrap=True)
    table.add_column("Pickup", style="white", no_wrap=True)

    for event in past_events:
        title = event.get("title", "Untitled")
        go_live = format_timestamp(event.get("goLiveTime"))
        cutoff = format_timestamp(event.get("orderCutoffTime"))

        # Extract pickup window from timeWindows
        pickup_time = "N/A"
        time_windows = event.get("timeWindows", {})
        if time_windows:
            first_window = next(iter(time_windows.values()))
            start = first_window.get("startTime")
            end = first_window.get("endTime")
            if start and end:
                start_dt = datetime.fromtimestamp(start / 1000)
                end_dt = datetime.fromtimestamp(end / 1000)
                pickup_time = f"{start_dt.strftime('%I:%M%p').lower()}-{end_dt.strftime('%I:%M%p').lower()}"

        table.add_row(title, go_live, cutoff, pickup_time)
    console.print(table)


def get_menu_items(event_id: str, cart_id: str = None) -> dict:
    """Fetch menu items for a specific event from the Holey Dough API.

    Args:
        event_id: The unique identifier for the drop event.
        cart_id: Optional cart ID for the session.

    Returns:
        Dictionary containing menu items data from the API response.
    """
    url = "https://bets.hotplate.com/trpc/shop.getEvent"

    input_data = {
        "eventId": event_id,
        "fulfillmentType": "PICKUP",
    }
    if cart_id:
        input_data["cartId"] = cart_id

    params = {
        "input": json.dumps(input_data)
    }

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "Origin": "https://www.hotplate.com",
        "Referer": "https://www.hotplate.com/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Extract menu items from the response
        event_data = data.get("result", {}).get("data", {})
        menu_items = event_data.get("menuItems", [])

        return {
            "event": event_data,
            "menu_items": menu_items
        }
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error fetching menu items: {e}[/red]")
        return {"event": {}, "menu_items": []}


def display_menu_items(menu_data: dict):
    """Display menu items in a formatted table."""
    menu_items = menu_data.get("menu_items", [])

    if not menu_items:
        console.print("[yellow]No menu items found.[/yellow]")
        return

    event = menu_data.get("event", {})
    event_title = event.get("title", "Unknown Event")

    console.print(f"\n[bold cyan]{event_title} - Menu[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Item", style="cyan")
    table.add_column("Price", style="green", justify="right")
    table.add_column("Available", style="yellow", justify="center")
    table.add_column("Description", style="white", max_width=40)

    for item in menu_items:
        name = item.get("name", "Unknown")
        price_cents = item.get("price", 0)
        price = f"${price_cents / 100:.2f}" if price_cents else "N/A"

        quantity_available = item.get("quantityAvailable")
        available = str(quantity_available) if quantity_available is not None else "Unlimited"

        description = item.get("description", "")[:40] if item.get("description") else ""

        table.add_row(name, price, available, description)

    console.print(table)


def get_all_menu_items(event_id: str, cart_id: str = None) -> list[dict]:
    """Fetch all menu items with their full details from a drop event.

    Args:
        event_id: The unique identifier for the drop event.
        cart_id: Optional cart ID for the session.

    Returns:
        List of menu item dictionaries containing:
        - id: Event menu item ID
        - menu_item_id: Base menu item ID
        - title: Item name
        - description: Item description
        - price: Price in dollars (float)
        - image: Image URL
        - section: Section name (e.g., "Bagels & Schmears", "Coffee")
        - section_index: Position within section
        - options: List of option categories with their choices
        - inventory: Availability information
        - is_tax_exempt: Whether item is tax exempt
    """
    url = "https://bets.hotplate.com/trpc/shop.getEvent"

    input_data = {
        "eventId": event_id,
        "fulfillmentType": "PICKUP",
    }
    if cart_id:
        input_data["cartId"] = cart_id

    params = {"input": json.dumps(input_data)}

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "Origin": "https://www.hotplate.com",
        "Referer": "https://www.hotplate.com/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error fetching menu items: {e}[/red]")
        return []

    event_data = data.get("result", {}).get("data", {})
    raw_items = event_data.get("eventMenuItemsWithComputedTypes", [])
    sections = event_data.get("eventMenuSections", [])

    # Build section lookup by ID
    section_lookup = {s["id"]: s.get("title", "Unknown") for s in sections}

    menu_items = []
    for item in raw_items:
        # Parse price from string to float
        price_str = item.get("price", "0")
        try:
            price = float(price_str) if price_str else 0.0
        except ValueError:
            price = 0.0

        # Parse option categories
        options = []
        for category in item.get("optionCategories", []):
            option_choices = []
            for opt in category.get("options", []):
                opt_price_str = opt.get("price", "")
                try:
                    opt_price = float(opt_price_str) if opt_price_str else 0.0
                except ValueError:
                    opt_price = 0.0

                option_choices.append({
                    "id": opt.get("id"),
                    "title": opt.get("title"),
                    "price": opt_price,
                })

            options.append({
                "id": category.get("id"),
                "title": category.get("title"),
                "type": category.get("type"),
                "min_selections": category.get("minimumSelections", 0),
                "max_selections": category.get("maximumSelections", 1),
                "is_numerical": category.get("isOptionSelectionNumerical", False),
                "choices": option_choices,
            })

        # Parse inventory info
        inv = item.get("inventoryInfo", {})
        inventory = {
            "available": inv.get("available"),
            "total": inv.get("total"),
            "sold": inv.get("sold", 0),
            "in_carts": inv.get("inCarts", 0),
            "restricted_by": inv.get("restrictedBy", "NONE"),
        }

        section_id = item.get("eventMenuSectionId")
        section_name = section_lookup.get(section_id, "Unknown")

        menu_items.append({
            "id": item.get("id"),
            "menu_item_id": item.get("menuItemId"),
            "title": item.get("title"),
            "description": item.get("description", ""),
            "price": price,
            "image": item.get("image"),
            "section": section_name,
            "section_index": item.get("sectionIndex", 0),
            "options": options,
            "inventory": inventory,
            "is_tax_exempt": item.get("isTaxExempt", False),
        })

    # Sort by section then section_index
    menu_items.sort(key=lambda x: (x["section"], x["section_index"]))

    return menu_items


def display_all_menu_items(menu_items: list[dict]):
    """Display all menu items in a formatted table with options."""
    if not menu_items:
        console.print("[yellow]No menu items found.[/yellow]")
        return

    console.print(f"\n[bold cyan]Menu Items ({len(menu_items)} items)[/bold cyan]\n")

    current_section = None
    for item in menu_items:
        # Print section header when section changes
        if item["section"] != current_section:
            current_section = item["section"]
            console.print(f"\n[bold magenta]── {current_section} ──[/bold magenta]\n")

        # Item header
        avail = item["inventory"]["available"]
        avail_str = str(avail) if avail not in (None, "Infinity") else "∞"
        console.print(f"[bold cyan]{item['title']}[/bold cyan] - [green]${item['price']:.2f}[/green] (Available: {avail_str})")

        if item["description"]:
            console.print(f"  [dim]{item['description'][:80]}{'...' if len(item['description']) > 80 else ''}[/dim]")

        # Options
        for opt_cat in item["options"]:
            req = "required" if opt_cat["min_selections"] > 0 else "optional"
            console.print(f"  [yellow]{opt_cat['title']}[/yellow] ({req}, select {opt_cat['min_selections']}-{opt_cat['max_selections']}):")
            for choice in opt_cat["choices"]:
                price_str = f" +${choice['price']:.2f}" if choice["price"] > 0 else ""
                console.print(f"    • {choice['title']}{price_str}")

        console.print()


def validate_carts(event_id: str = None, test_item_id: str = None) -> dict:
    """Test various cart-related endpoints to determine which are valid.

    Tests multiple potential cart creation and management endpoints to see
    which ones return successful responses. This helps identify the correct
    API endpoints for cart operations.

    Args:
        event_id: Optional event ID to use in test requests.
        test_item_id: Optional menu item ID to use for add-to-cart tests.

    Returns:
        Dictionary containing test results for each endpoint:
        {
            "endpoint_name": {
                "status_code": int,
                "success": bool,
                "response": dict or str,
                "error": str (if applicable)
            }
        }
    """
    import uuid

    # Generate a test cart ID
    test_cart_id = str(uuid.uuid4())

    # Common headers used across all requests
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "Origin": "https://www.hotplate.com",
        "Referer": "https://www.hotplate.com/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    # Define endpoints to test
    endpoints = {
        "shop.createCart": {
            "url": "https://bets.hotplate.com/trpc/shop.createCart",
            "method": "POST",
            "input": {
                "eventId": event_id or "test-event-id",
                "fulfillmentType": "PICKUP"
            }
        },
        "shop.addToCart": {
            "url": "https://bets.hotplate.com/trpc/shop.addToCart",
            "method": "POST",
            "input": {
                "cartId": test_cart_id,
                "eventMenuItemId": test_item_id or "test-item-id",
                "quantity": 1
            }
        },
        "shop.getCart": {
            "url": "https://bets.hotplate.com/trpc/shop.getCart",
            "method": "GET",
            "input": {
                "cartId": test_cart_id
            }
        },
        "shop.updateCart": {
            "url": "https://bets.hotplate.com/trpc/shop.updateCart",
            "method": "POST",
            "input": {
                "cartId": test_cart_id,
                "items": []
            }
        },
        "cart.create": {
            "url": "https://bets.hotplate.com/trpc/cart.create",
            "method": "POST",
            "input": {
                "eventId": event_id or "test-event-id"
            }
        },
        "cart.addItem": {
            "url": "https://bets.hotplate.com/trpc/cart.addItem",
            "method": "POST",
            "input": {
                "cartId": test_cart_id,
                "itemId": test_item_id or "test-item-id",
                "quantity": 1
            }
        },
        "cart.get": {
            "url": "https://bets.hotplate.com/trpc/cart.get",
            "method": "GET",
            "input": {
                "cartId": test_cart_id
            }
        }
    }

    results = {}

    console.print("\n[bold cyan]Testing Cart API Endpoints[/bold cyan]\n")
    console.print(f"[dim]Test Cart ID: {test_cart_id}[/dim]\n")

    for endpoint_name, config in endpoints.items():
        console.print(f"Testing [yellow]{endpoint_name}[/yellow]... ", end="")

        try:
            url = config["url"]
            method = config["method"]
            input_data = config["input"]

            if method == "GET":
                params = {"input": json.dumps(input_data)}
                response = requests.get(url, params=params, headers=headers, timeout=10)
            else:  # POST
                response = requests.post(url, json={"input": input_data}, headers=headers, timeout=10)

            # Parse response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = response.text

            # Determine success (2xx status codes or specific API success patterns)
            is_success = 200 <= response.status_code < 300

            results[endpoint_name] = {
                "status_code": response.status_code,
                "success": is_success,
                "response": response_data,
                "url": url,
                "method": method
            }

            # Display result
            if is_success:
                console.print("[green]✓ SUCCESS[/green]", f"({response.status_code})")
            else:
                console.print("[red]✗ FAILED[/red]", f"({response.status_code})")

        except requests.exceptions.Timeout:
            results[endpoint_name] = {
                "status_code": None,
                "success": False,
                "error": "Request timeout",
                "url": config["url"],
                "method": config["method"]
            }
            console.print("[red]✗ TIMEOUT[/red]")

        except requests.exceptions.RequestException as e:
            results[endpoint_name] = {
                "status_code": None,
                "success": False,
                "error": str(e),
                "url": config["url"],
                "method": config["method"]
            }
            console.print(f"[red]✗ ERROR[/red] ({str(e)[:50]})")

    return results


def display_cart_validation_results(results: dict):
    """Display cart validation results in a formatted table.

    Args:
        results: Dictionary returned from validate_carts()
    """
    console.print("\n[bold cyan]Cart Validation Results[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Endpoint", style="cyan", no_wrap=True)
    table.add_column("Method", style="white", no_wrap=True)
    table.add_column("Status", style="yellow", justify="center")
    table.add_column("Result", style="white")
    table.add_column("Details", style="dim", max_width=40)

    for endpoint_name, result in results.items():
        method = result.get("method", "N/A")
        status_code = result.get("status_code")
        status_str = str(status_code) if status_code else "N/A"

        if result.get("success"):
            result_str = "[green]✓ Valid[/green]"
            details = "Endpoint is functional"
        else:
            result_str = "[red]✗ Invalid[/red]"
            error = result.get("error", "")
            if error:
                details = error[:40]
            else:
                response = result.get("response", "")
                if isinstance(response, dict):
                    error_msg = response.get("error", {}).get("message", "")
                    details = error_msg[:40] if error_msg else "Request failed"
                else:
                    details = str(response)[:40] if response else "Request failed"

        table.add_row(endpoint_name, method, status_str, result_str, details)

    console.print(table)

    # Summary
    successful = sum(1 for r in results.values() if r.get("success"))
    total = len(results)
    console.print(f"\n[bold]Summary:[/bold] {successful}/{total} endpoints validated successfully")

    if successful > 0:
        console.print("\n[green]Valid endpoints found:[/green]")
        for endpoint_name, result in results.items():
            if result.get("success"):
                console.print(f"  • {endpoint_name} ({result['method']}) - {result['url']}")


def discover_add_to_cart_payload(event_id: str, cart_id: str, menu_item: dict) -> dict:
    """Discover the correct payload structure for adding items to cart.

    Tests multiple payload variations against the shop.addToCart endpoint
    to determine the exact structure HotPlate expects.

    Args:
        event_id: The event ID for the drop.
        cart_id: An existing cart ID (from shop.createCart).
        menu_item: A menu item dict from get_all_menu_items() with options.

    Returns:
        Dictionary containing:
        - working_payload: The payload structure that worked (if found)
        - test_results: Results from each payload variation tested
        - error_analysis: Analysis of error messages to infer structure
    """
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "Origin": "https://www.hotplate.com",
        "Referer": "https://www.hotplate.com/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    # Build sample option selections from the menu item
    sample_options = []
    sample_options_flat = []
    sample_options_by_category = {}

    for opt_cat in menu_item.get("options", []):
        if opt_cat.get("choices"):
            first_choice = opt_cat["choices"][0]
            # Format 1: Array of {optionCategoryId, selectedChoiceIds}
            sample_options.append({
                "optionCategoryId": opt_cat["id"],
                "selectedChoiceIds": [first_choice["id"]]
            })
            # Format 2: Flat array of choice IDs
            sample_options_flat.append(first_choice["id"])
            # Format 3: Object keyed by category ID
            sample_options_by_category[opt_cat["id"]] = [first_choice["id"]]

    # Define payload variations to test
    event_menu_item_id = menu_item["id"]
    base_menu_item_id = menu_item.get("menu_item_id")

    payload_variations = [
        # Variation 1: Basic with eventMenuItemId (most likely based on code)
        {
            "name": "basic_eventMenuItemId",
            "payload": {
                "cartId": cart_id,
                "eventMenuItemId": event_menu_item_id,
                "quantity": 1
            }
        },
        # Variation 2: With selectedOptions array
        {
            "name": "with_selectedOptions_array",
            "payload": {
                "cartId": cart_id,
                "eventMenuItemId": event_menu_item_id,
                "quantity": 1,
                "selectedOptions": sample_options
            }
        },
        # Variation 3: Options as flat array of choice IDs
        {
            "name": "with_options_flat",
            "payload": {
                "cartId": cart_id,
                "eventMenuItemId": event_menu_item_id,
                "quantity": 1,
                "options": sample_options_flat
            }
        },
        # Variation 4: Options as object keyed by category
        {
            "name": "with_options_by_category",
            "payload": {
                "cartId": cart_id,
                "eventMenuItemId": event_menu_item_id,
                "quantity": 1,
                "options": sample_options_by_category
            }
        },
        # Variation 5: Using menuItemId instead
        {
            "name": "with_menuItemId",
            "payload": {
                "cartId": cart_id,
                "menuItemId": base_menu_item_id,
                "quantity": 1,
                "selectedOptions": sample_options
            }
        },
        # Variation 6: Using itemId (common TRPC pattern)
        {
            "name": "with_itemId",
            "payload": {
                "cartId": cart_id,
                "itemId": event_menu_item_id,
                "quantity": 1,
                "selectedOptions": sample_options
            }
        },
        # Variation 7: Including eventId
        {
            "name": "with_eventId",
            "payload": {
                "cartId": cart_id,
                "eventId": event_id,
                "eventMenuItemId": event_menu_item_id,
                "quantity": 1,
                "selectedOptions": sample_options
            }
        },
        # Variation 8: Nested item object
        {
            "name": "nested_item_object",
            "payload": {
                "cartId": cart_id,
                "item": {
                    "eventMenuItemId": event_menu_item_id,
                    "quantity": 1,
                    "selectedOptions": sample_options
                }
            }
        },
        # Variation 9: With optionSelections (alternative naming)
        {
            "name": "with_optionSelections",
            "payload": {
                "cartId": cart_id,
                "eventMenuItemId": event_menu_item_id,
                "quantity": 1,
                "optionSelections": sample_options
            }
        },
        # Variation 10: Simple choices array
        {
            "name": "with_choices",
            "payload": {
                "cartId": cart_id,
                "eventMenuItemId": event_menu_item_id,
                "quantity": 1,
                "choices": sample_options_flat
            }
        },
    ]

    results = {
        "working_payload": None,
        "test_results": [],
        "error_analysis": [],
        "sample_options_used": sample_options
    }

    console.print(f"\n[bold cyan]Discovering Add-to-Cart Payload Structure[/bold cyan]")
    console.print(f"[dim]Testing {len(payload_variations)} payload variations...[/dim]\n")
    console.print(f"Item: {menu_item['title']} ({event_menu_item_id})")
    console.print(f"Cart: {cart_id}\n")

    url = "https://bets.hotplate.com/trpc/shop.addToCart"

    for variation in payload_variations:
        name = variation["name"]
        payload = variation["payload"]

        console.print(f"Testing [yellow]{name}[/yellow]... ", end="")

        try:
            response = requests.post(
                url,
                json={"input": payload},
                headers=headers,
                timeout=10
            )

            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"raw": response.text}

            is_success = 200 <= response.status_code < 300
            has_error = "error" in response_data

            result = {
                "name": name,
                "payload": payload,
                "status_code": response.status_code,
                "success": is_success and not has_error,
                "response": response_data
            }
            results["test_results"].append(result)

            if is_success and not has_error:
                console.print("[green]✓ SUCCESS[/green]")
                results["working_payload"] = payload
                # Analyze successful response structure
                console.print(f"  [green]Found working payload![/green]")
                console.print(f"  Response: {json.dumps(response_data, indent=2)[:500]}")
            else:
                console.print(f"[red]✗ FAILED[/red] ({response.status_code})")
                # Analyze error for clues about expected structure
                error_msg = ""
                if isinstance(response_data, dict):
                    error_obj = response_data.get("error", {})
                    if isinstance(error_obj, dict):
                        error_msg = error_obj.get("message", "")
                        # Look for validation errors that hint at expected fields
                        if "data" in error_obj:
                            zodError = error_obj.get("data", {}).get("zodError", {})
                            if zodError:
                                results["error_analysis"].append({
                                    "variation": name,
                                    "zodError": zodError
                                })
                                console.print(f"    [dim]Zod validation hint: {zodError}[/dim]")

        except requests.exceptions.Timeout:
            results["test_results"].append({
                "name": name,
                "payload": payload,
                "status_code": None,
                "success": False,
                "error": "Timeout"
            })
            console.print("[red]✗ TIMEOUT[/red]")

        except requests.exceptions.RequestException as e:
            results["test_results"].append({
                "name": name,
                "payload": payload,
                "status_code": None,
                "success": False,
                "error": str(e)
            })
            console.print(f"[red]✗ ERROR[/red] ({str(e)[:30]})")

    # Summary
    console.print(f"\n[bold]Discovery Summary:[/bold]")
    if results["working_payload"]:
        console.print(f"[green]✓ Found working payload structure![/green]")
        console.print(f"Payload: {json.dumps(results['working_payload'], indent=2)}")
    else:
        console.print(f"[yellow]No working payload found. Analyze error messages for clues.[/yellow]")
        if results["error_analysis"]:
            console.print(f"\n[bold]Validation Error Hints:[/bold]")
            for hint in results["error_analysis"]:
                console.print(f"  {hint['variation']}: {hint['zodError']}")

    return results


def add_item_to_cart(
    cart_id: str,
    event_menu_item_id: str,
    quantity: int = 1,
    selected_options: list[dict] = None
) -> dict:
    """Add an item to the cart with selected options.

    Args:
        cart_id: UUID of the cart (from create_cart).
        event_menu_item_id: The event-specific menu item ID (from get_all_menu_items).
        quantity: Number of items to add.
        selected_options: List of option selections, each containing:
            - optionCategoryId: The option category ID
            - selectedChoiceIds: List of selected choice IDs

    Returns:
        Dictionary with the API response or error details.

    Example:
        >>> options = [
        ...     {"optionCategoryId": "cat1", "selectedChoiceIds": ["choice1"]},
        ...     {"optionCategoryId": "cat2", "selectedChoiceIds": ["choice2", "choice3"]}
        ... ]
        >>> result = add_item_to_cart("cart-uuid", "item-uuid", 2, options)
    """
    url = "https://bets.hotplate.com/trpc/shop.addToCart"

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "Origin": "https://www.hotplate.com",
        "Referer": "https://www.hotplate.com/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    # Build the payload - structure based on discovery testing
    # Most likely: selectedOptions as array of {optionCategoryId, selectedChoiceIds}
    payload = {
        "cartId": cart_id,
        "eventMenuItemId": event_menu_item_id,
        "quantity": quantity,
    }

    if selected_options:
        payload["selectedOptions"] = selected_options

    try:
        response = requests.post(
            url,
            json={"input": payload},
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        return {
            "success": True,
            "status_code": response.status_code,
            "data": response.json()
        }
    except requests.exceptions.RequestException as e:
        error_data = {}
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
            except (json.JSONDecodeError, AttributeError):
                error_data = {"raw": e.response.text if e.response else str(e)}

        return {
            "success": False,
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
            "error": str(e),
            "error_data": error_data
        }


def build_options_for_item(menu_item: dict, selections: dict) -> list[dict]:
    """Build selectedOptions array from human-readable selections.

    Args:
        menu_item: Menu item dict from get_all_menu_items().
        selections: Dict mapping option category titles to selected choice titles.
            Example: {"Schmear Type": "Cream Cheese", "Add-ons": ["Lox", "Capers"]}

    Returns:
        List of option selections formatted for add_item_to_cart().

    Example:
        >>> item = get_all_menu_items(event_id)[0]
        >>> options = build_options_for_item(item, {
        ...     "Schmear Type": "Cream Cheese",
        ...     "Toppings": ["Lox", "Capers"]
        ... })
        >>> add_item_to_cart(cart_id, item["id"], 1, options)
    """
    formatted_options = []

    for opt_category in menu_item.get("options", []):
        cat_title = opt_category["title"]

        if cat_title not in selections:
            # Skip categories not in selections
            # Note: Required categories (min_selections > 0) must be included!
            continue

        selected = selections[cat_title]
        # Normalize to list
        if isinstance(selected, str):
            selected = [selected]

        # Map choice titles to IDs
        choice_ids = []
        for choice in opt_category.get("choices", []):
            if choice["title"] in selected:
                choice_ids.append(choice["id"])

        if choice_ids:
            formatted_options.append({
                "optionCategoryId": opt_category["id"],
                "selectedChoiceIds": choice_ids
            })

    return formatted_options


def validate_item_options(menu_item: dict, selected_options: list[dict]) -> tuple[bool, list[str]]:
    """Validate that selected options meet item requirements.

    Args:
        menu_item: Menu item dict from get_all_menu_items().
        selected_options: List of option selections to validate.

    Returns:
        Tuple of (is_valid, list of error messages).
    """
    errors = []

    # Build lookup of selected options by category ID
    selections_by_cat = {
        opt["optionCategoryId"]: opt["selectedChoiceIds"]
        for opt in (selected_options or [])
    }

    for opt_category in menu_item.get("options", []):
        cat_id = opt_category["id"]
        cat_title = opt_category["title"]
        min_sel = opt_category.get("min_selections", 0)
        max_sel = opt_category.get("max_selections", 1)

        selected = selections_by_cat.get(cat_id, [])
        num_selected = len(selected)

        # Check minimum selections
        if num_selected < min_sel:
            errors.append(
                f"'{cat_title}' requires at least {min_sel} selection(s), got {num_selected}"
            )

        # Check maximum selections
        if num_selected > max_sel:
            errors.append(
                f"'{cat_title}' allows at most {max_sel} selection(s), got {num_selected}"
            )

        # Validate choice IDs exist
        valid_choice_ids = {c["id"] for c in opt_category.get("choices", [])}
        for choice_id in selected:
            if choice_id not in valid_choice_ids:
                errors.append(
                    f"Invalid choice ID '{choice_id}' for category '{cat_title}'"
                )

    return (len(errors) == 0, errors)


if __name__ == "__main__":
    import sys

    # Parse command line arguments
    command = sys.argv[1] if len(sys.argv) > 1 else "help"

    if command == "help":
        console.print("\n[bold cyan]BagelBot - Holey Dough Automation[/bold cyan]\n")
        console.print("Usage: python polling.py <command>\n")
        console.print("[bold]Commands:[/bold]")
        console.print("  drops        - Display past drop events")
        console.print("  menu         - Display menu items for most recent drop")
        console.print("  validate     - Test cart API endpoints")
        console.print("  discover     - Discover add-to-cart payload structure")
        console.print("  help         - Show this help message\n")
        sys.exit(0)

    # Test API connectivity first
    console.print("[bold cyan]Testing API connectivity...[/bold cyan]")
    try:
        response = requests.get("https://bets.hotplate.com/trpc/shop.getEvent", timeout=5)
        console.print(f"[green]✓ API is accessible[/green] (status: {response.status_code})\n")
    except Exception as e:
        console.print(f"[red]✗ API connectivity issue: {e}[/red]\n")
        console.print("[yellow]Network restriction detected. Run with network access.[/yellow]\n")
        sys.exit(1)

    if command == "drops":
        data = get_old_drops()
        display_drops(data)

    elif command == "menu":
        events = get_old_drop_event_ids()
        if events:
            event_id = events[0]["id"]
            console.print(f"[dim]Using event: {events[0]['title']}[/dim]\n")
            items = get_all_menu_items(event_id)
            display_all_menu_items(items)
        else:
            console.print("[red]No events found[/red]")

    elif command == "validate":
        events = get_old_drop_event_ids()
        event_id = events[0]["id"] if events else "458ea76e-1f07-44ed-b6d5-451287f8e10b"
        results = validate_carts(event_id=event_id)
        display_cart_validation_results(results)

    elif command == "discover":
        # Discover the correct add-to-cart payload structure
        console.print("[bold cyan]Add-to-Cart Payload Discovery[/bold cyan]\n")

        # Step 1: Get an event
        events = get_old_drop_event_ids()
        if not events:
            console.print("[red]No events found[/red]")
            sys.exit(1)

        event_id = events[0]["id"]
        console.print(f"Event: {events[0]['title']}")

        # Step 2: Get menu items
        menu_items = get_all_menu_items(event_id)
        if not menu_items:
            console.print("[red]No menu items found[/red]")
            sys.exit(1)

        # Find an item with options for better testing
        test_item = None
        for item in menu_items:
            if item.get("options"):
                test_item = item
                break
        if not test_item:
            test_item = menu_items[0]

        console.print(f"Test item: {test_item['title']}")

        # Step 3: We need a cart ID - first try to create one
        console.print("\n[bold]Step 1: Creating test cart...[/bold]")
        import uuid
        test_cart_id = str(uuid.uuid4())

        headers = {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Origin": "https://www.hotplate.com",
            "Referer": "https://www.hotplate.com/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        # Try to create a cart
        try:
            create_response = requests.post(
                "https://bets.hotplate.com/trpc/shop.createCart",
                json={"input": {"eventId": event_id, "fulfillmentType": "PICKUP"}},
                headers=headers,
                timeout=10
            )
            cart_data = create_response.json()
            console.print(f"Create cart response: {json.dumps(cart_data, indent=2)[:500]}")

            # Extract cart ID from response if available
            if "result" in cart_data and "data" in cart_data["result"]:
                cart_info = cart_data["result"]["data"]
                if isinstance(cart_info, dict) and "id" in cart_info:
                    test_cart_id = cart_info["id"]
                    console.print(f"[green]Got cart ID: {test_cart_id}[/green]")
                elif isinstance(cart_info, str):
                    test_cart_id = cart_info
                    console.print(f"[green]Got cart ID: {test_cart_id}[/green]")
        except Exception as e:
            console.print(f"[yellow]Could not create cart: {e}[/yellow]")
            console.print(f"[dim]Using generated UUID: {test_cart_id}[/dim]")

        # Step 4: Run discovery
        console.print("\n[bold]Step 2: Testing payload variations...[/bold]")
        results = discover_add_to_cart_payload(event_id, test_cart_id, test_item)

        # Step 5: Show results
        console.print("\n[bold]Discovery Results:[/bold]")
        if results["working_payload"]:
            console.print("\n[green]✓ SUCCESS! Working payload structure found:[/green]")
            console.print(json.dumps(results["working_payload"], indent=2))
        else:
            console.print("\n[yellow]No working payload found. Error analysis:[/yellow]")
            for result in results["test_results"][:3]:  # Show first 3
                console.print(f"\n[cyan]{result['name']}:[/cyan]")
                resp = result.get("response", {})
                if isinstance(resp, dict) and "error" in resp:
                    console.print(f"  Error: {json.dumps(resp['error'], indent=2)[:300]}")

    else:
        console.print(f"[red]Unknown command: {command}[/red]")
        console.print("Run 'python polling.py help' for usage.")
    