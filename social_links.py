import requests
import json
import re
import time

COMMON_CRAWL_INDEX = "https://index.commoncrawl.org/CC-MAIN-2024-10-index"

BIO_DOMAINS = [
    "linktr.ee",
    "beacons.ai",
    "carrd.co",
    "solo.to",
    "bio.site",
    "taplink.cc"
]

HOTPLATE_REGEX = re.compile(r"https://hotplate\.com/[a-zA-Z0-9_-]+")


def query_commoncrawl(domain):
    params = {
        "url": f"{domain}/*",
        "output": "json"
    }
    r = requests.get(COMMON_CRAWL_INDEX, params=params, stream=True)
    r.raise_for_status()
    return r.iter_lines()


def extract_hotplate_links():
    found = set()

    for domain in BIO_DOMAINS:
        print(f"Scanning {domain}")
        try:
            for line in query_commoncrawl(domain):
                if not line:
                    continue
                data = json.loads(line)
                url = data.get("url", "")
                match = HOTPLATE_REGEX.search(url)
                if match:
                    found.add(match.group())
        except Exception as e:
            print(f"Error scanning {domain}: {e}")

        time.sleep(1)

    return found


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
    candidates = extract_hotplate_links()
    print(f"Discovered {len(candidates)} Hotplate links from social bios")

    valid = []

    for url in sorted(candidates):
        if validate_storefront(url):
            valid.append({
                "vendor": url.split("/")[-1],
                "storefront_url": url
            })

    output = {
        "count": len(valid),
        "storefronts": valid
    }

    with open("hotplate_storefronts_social.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Validated {len(valid)} storefronts")


if __name__ == "__main__":
    main()
