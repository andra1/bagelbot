"""Utilities for retrieving Holey Dough drop information.
1. I can make diret API calls to the shop.getEvent endpoint to get drop info for past events
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
        return

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

if __name__ == "__main__":
    get_old_drops()
    
