#!/usr/bin/env python3
"""
Hotplate Storefront Finder

Discovers valid hotplate.com storefronts using multiple methods:
1. Google dorking (via requests to Google)
2. Common Crawl index lookup
3. Referral link pattern extraction
4. Brute force validation of discovered slugs
"""

import requests
import re
import time
import json
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed

# Known valid slugs to seed the search
SEED_SLUGS = [
    "butterandcrumble",
    "stopdropnroll", 
    "zwiefelhoferfamilyfarm",
    "tthelittleladdbakery",
    "holeydoughandco",
]

# Paths that are NOT storefronts
EXCLUDED_PATHS = {
    "referrals", "portal", "pricing", "features", "blog", "help",
    "testimonials", "company", "login", "signup", "not-found",
    "terms", "privacy", "about", "contact", "faq", "support",
    "learn", "api", "docs", "settings", "events", "admin",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}


def extract_slugs_from_text(text: str) -> set[str]:
    """Extract potential hotplate slugs from text content."""
    slugs = set()
    
    # Direct URLs: hotplate.com/slug
    direct = re.findall(r'hotplate\.com/([a-zA-Z0-9_-]+)', text, re.IGNORECASE)
    slugs.update(s.lower() for s in direct)
    
    # Referral URLs: referral=slug
    referrals = re.findall(r'referral=([a-zA-Z0-9_-]+)', text, re.IGNORECASE)
    slugs.update(s.lower() for s in referrals)
    
    # Filter out non-storefront paths
    slugs = {s for s in slugs if s not in EXCLUDED_PATHS and len(s) > 2}
    
    return slugs


def validate_slug(slug: str) -> dict | None:
    """Check if a slug is a valid storefront and extract basic info."""
    url = f"https://www.hotplate.com/{slug}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        
        # Invalid if redirected to not-found or 404
        if "not-found" in resp.url or resp.status_code == 404:
            return None
        
        if resp.status_code == 200:
            # Extract storefront name from title or og:title
            title_match = re.search(r'<title>([^<]+)</title>', resp.text, re.IGNORECASE)
            og_match = re.search(r'og:title"\s+content="([^"]+)"', resp.text)
            
            name = None
            if og_match:
                name = og_match.group(1)
            elif title_match:
                name = title_match.group(1).replace(" | Hotplate", "").strip()
            
            # Check for active drop indicators
            has_active_drop = any(indicator in resp.text.lower() for indicator in [
                "add to cart",
                "orders open",
                "preorder",
                "pre-order", 
                "checkout",
                "sold out",  # still indicates an active/recent drop
            ])
            
            return {
                "slug": slug,
                "url": url,
                "name": name,
                "has_active_drop": has_active_drop,
                "status": "valid"
            }
    except requests.RequestException as e:
        print(f"  Error checking {slug}: {e}")
    
    return None


def search_common_crawl(limit: int = 100) -> set[str]:
    """Query Common Crawl index for hotplate.com URLs."""
    print("\n[*] Searching Common Crawl index...")
    slugs = set()
    
    # Try recent CC indexes
    indexes = [
        "CC-MAIN-2024-51",
        "CC-MAIN-2024-46", 
        "CC-MAIN-2024-42",
        "CC-MAIN-2024-38",
    ]
    
    for index in indexes:
        try:
            url = f"http://index.commoncrawl.org/{index}-index"
            params = {
                "url": "hotplate.com/*",
                "output": "json",
                "limit": limit
            }
            resp = requests.get(url, params=params, timeout=30)
            
            if resp.status_code == 200:
                for line in resp.text.strip().split("\n"):
                    if line:
                        try:
                            data = json.loads(line)
                            found = extract_slugs_from_text(data.get("url", ""))
                            slugs.update(found)
                        except json.JSONDecodeError:
                            continue
                            
            print(f"  Found {len(slugs)} slugs from {index}")
            
        except requests.RequestException as e:
            print(f"  Error querying {index}: {e}")
            continue
    
    return slugs


def search_google_dorking() -> set[str]:
    """
    Search for hotplate URLs via various public sources.
    Note: Direct Google scraping is blocked, so we use alternative methods.
    """
    print("\n[*] Searching public sources for hotplate links...")
    slugs = set()
    
    # Search DuckDuckGo HTML (more scrape-friendly than Google)
    search_queries = [
        "site:hotplate.com",
        '"hotplate.com/" bakery',
        '"hotplate.com/" cookies',
        '"hotplate.com/" preorder',
        '"hotplate.com/" drop',
    ]
    
    for query in search_queries:
        try:
            url = "https://html.duckduckgo.com/html/"
            resp = requests.post(url, data={"q": query}, headers=HEADERS, timeout=15)
            
            if resp.status_code == 200:
                found = extract_slugs_from_text(resp.text)
                slugs.update(found)
                print(f"  Query '{query}': found {len(found)} slugs")
            
            time.sleep(2)  # Rate limit
            
        except requests.RequestException as e:
            print(f"  Error searching '{query}': {e}")
            continue
    
    return slugs


def search_wayback_machine() -> set[str]:
    """Search Wayback Machine CDX API for historical hotplate URLs."""
    print("\n[*] Searching Wayback Machine...")
    slugs = set()
    
    try:
        url = "http://web.archive.org/cdx/search/cdx"
        params = {
            "url": "hotplate.com/*",
            "output": "json",
            "fl": "original",
            "collapse": "urlkey",
            "limit": 500
        }
        resp = requests.get(url, params=params, timeout=30)
        
        if resp.status_code == 200:
            data = resp.json()
            for row in data[1:]:  # Skip header row
                if row:
                    found = extract_slugs_from_text(row[0])
                    slugs.update(found)
                    
        print(f"  Found {len(slugs)} slugs from Wayback Machine")
        
    except requests.RequestException as e:
        print(f"  Error querying Wayback Machine: {e}")
    
    return slugs


def validate_slugs_parallel(slugs: set[str], max_workers: int = 10) -> list[dict]:
    """Validate multiple slugs in parallel."""
    print(f"\n[*] Validating {len(slugs)} potential slugs...")
    valid_storefronts = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_slug = {executor.submit(validate_slug, slug): slug for slug in slugs}
        
        for i, future in enumerate(as_completed(future_to_slug)):
            slug = future_to_slug[future]
            try:
                result = future.result()
                if result:
                    valid_storefronts.append(result)
                    print(f"  ✓ {slug}: {result.get('name', 'Unknown')}")
                else:
                    pass  # Invalid slug, skip silently
            except Exception as e:
                print(f"  Error validating {slug}: {e}")
            
            # Progress indicator
            if (i + 1) % 50 == 0:
                print(f"  ... checked {i + 1}/{len(slugs)}")
    
    return valid_storefronts


def main():
    print("=" * 60)
    print("Hotplate Storefront Finder")
    print("=" * 60)
    
    all_slugs = set(SEED_SLUGS)
    print(f"\n[*] Starting with {len(all_slugs)} seed slugs")
    
    # Method 1: Common Crawl
    try:
        cc_slugs = search_common_crawl()
        all_slugs.update(cc_slugs)
    except Exception as e:
        print(f"  Common Crawl search failed: {e}")
    
    # Method 2: Wayback Machine
    try:
        wb_slugs = search_wayback_machine()
        all_slugs.update(wb_slugs)
    except Exception as e:
        print(f"  Wayback Machine search failed: {e}")
    
    # Method 3: DuckDuckGo search
    try:
        ddg_slugs = search_google_dorking()
        all_slugs.update(ddg_slugs)
    except Exception as e:
        print(f"  DuckDuckGo search failed: {e}")
    
    print(f"\n[*] Total unique slugs to validate: {len(all_slugs)}")
    
    # Validate all discovered slugs
    valid_storefronts = validate_slugs_parallel(all_slugs)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"RESULTS: Found {len(valid_storefronts)} valid storefronts")
    print("=" * 60)
    
    # Sort by name
    valid_storefronts.sort(key=lambda x: x.get("name") or x["slug"])
    
    for store in valid_storefronts:
        drop_indicator = "🔥 ACTIVE" if store["has_active_drop"] else "  "
        print(f"{drop_indicator} {store['name'] or store['slug']}")
        print(f"         {store['url']}")
    
    # Save results
    output_file = "hotplate_storefronts.json"
    with open(output_file, "w") as f:
        json.dump(valid_storefronts, f, indent=2)
    print(f"\n[*] Results saved to {output_file}")
    
    # Also output just the active drops
    active_drops = [s for s in valid_storefronts if s["has_active_drop"]]
    if active_drops:
        print(f"\n[*] Storefronts with potential active drops: {len(active_drops)}")
        for store in active_drops:
            print(f"  - {store['url']}")
    
    return valid_storefronts


if __name__ == "__main__":
    main()
