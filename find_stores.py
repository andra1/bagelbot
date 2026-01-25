import requests
import gzip
import json
import re
from io import BytesIO

COMMON_CRAWL_INDEX = "https://index.commoncrawl.org/CC-MAIN-2024-10-index"

HOTPLATE_PATTERN = re.compile(r"https://hotplate\.com/[a-zA-Z0-9_-]+$")


def fetch_commoncrawl_urls():
    params = {
        "url": "hotplate.com/*",
        "output": "json"
    }

    r = requests.get(COMMON_CRAWL_INDEX, params=params, stream=True)
    r.raise_for_status()

    urls = set()

    for line in r.iter_lines():
        if not line:
            continue
        data = json.loads(line)
        url = data.get("url")
        if url and HOTPLATE_PATTERN.match(url):
            urls.add(url)

    return urls


def validate_storefront(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return False
        text = r.text.lower()
        return any(x in text for x in [
            "powered by hotplate",
            "pickup",
            "preorder",
            "sold out"
        ])
    except Exception:
        return False


def main():
    candidates = fetch_commoncrawl_urls()
    print(f"Found {len(candidates)} candidates in Common Crawl")

    valid = []

    for url in sorted(candidates):
        if validate_storefront(url):
            valid.append({
                "vendor": url.split("/")[-1],
                "storefront_url": url
            })

    with open("hotplate_storefronts.json", "w") as f:
        json.dump({
            "count": len(valid),
            "storefronts": valid
        }, f, indent=2)


if __name__ == "__main__":
    main()
