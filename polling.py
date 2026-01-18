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


if __name__ == "__main__":
    #data = get_old_drops()
    #display_drops(data)
    #menu_data = get_menu_items("458ea76e-1f07-44ed-b6d5-451287f8e10b")
    #display_menu_items(menu_data)
    #get_drop_info()
    items = get_all_menu_items("458ea76e-1f07-44ed-b6d5-451287f8e10b")
    display_all_menu_items(items)
    