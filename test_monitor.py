#!/usr/bin/env python3
"""Test script for monitoring upcoming drop events."""

from polling import get_upcoming_drops, display_upcoming_events, monitor_for_new_event
from rich.console import Console

console = Console()

def main():
    console.print("[bold cyan]Testing Upcoming Drops Functionality[/bold cyan]\n")

    # Test 1: Fetch upcoming drops
    console.print("[yellow]Test 1: Fetching upcoming drops...[/yellow]")
    data = get_upcoming_drops()

    if data:
        upcoming_events = data.get("result", {}).get("data", {}).get("upcomingEvents", [])
        console.print(f"[green]✓ Successfully fetched {len(upcoming_events)} upcoming events[/green]\n")

        # Display the events
        if upcoming_events:
            display_upcoming_events(upcoming_events)
        else:
            console.print("[dim]No upcoming events found at this time.[/dim]\n")
    else:
        console.print("[red]✗ Failed to fetch upcoming drops[/red]\n")
        return

    # Test 2: Monitor for new events (limited iterations)
    console.print("\n[yellow]Test 2: Testing monitor_for_new_event() with max 3 iterations...[/yellow]")

    def on_event_detected(event):
        console.print(f"\n[bold green]Callback triggered for event: {event.get('title')}[/bold green]\n")

    result = monitor_for_new_event(
        poll_interval=2,
        callback=on_event_detected,
        max_iterations=3
    )

    if result:
        console.print(f"\n[green]✓ Live event detected: {result.get('title')}[/green]")
    else:
        console.print("\n[dim]No live events detected during test period (this is normal)[/dim]")

    console.print("\n[bold cyan]Tests completed![/bold cyan]")

if __name__ == "__main__":
    main()
