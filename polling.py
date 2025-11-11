"""Utilities for retrieving Holey Dough drop information."""

from html.parser import HTMLParser
from typing import Optional

import requests

DEFAULT_HOLEY_DOUGH_URL = "https://www.tryhotplate.com/holley-dough"


class _NextDropParser(HTMLParser):
    """Extract the text immediately following the "Next Holey Drop" label."""

    def __init__(self) -> None:
        super().__init__()
        self._label_seen = False
        self.next_drop: Optional[str] = None

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return

        lowered = text.lower()
        if self._label_seen:
            if self.next_drop is None and lowered != "next holey drop":
                self.next_drop = text
            return

        if "next holey drop" in lowered:
            self._label_seen = True


def poll_for_vendor_drop(url: str = DEFAULT_HOLEY_DOUGH_URL) -> Optional[str]:
    """Return the text shown directly beneath "Next Holey Drop" on the Holey Dough page."""

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    parser = _NextDropParser()
    parser.feed(response.text)
    return parser.next_drop
