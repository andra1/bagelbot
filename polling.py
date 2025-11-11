"""Utilities for retrieving Holey Dough drop information."""


import requests
import json

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

