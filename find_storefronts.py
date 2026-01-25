import requests
import json
import re
from bs4 import BeautifulSoup

def get_old_drops(chef_id):
    """Fetch past events for a chef to validate if exists."""
    url = "https://bets.hotplate.com/trpc/shop.getPublicPastEvents"
    params = {
        "input": json.dumps({
            "chefId": chef_id,
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
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException:
        return None

def is_valid_chef(chef_id):
    """Check if a chef ID is valid by attempting to fetch past events."""
    data = get_old_drops(chef_id)
    if data and 'result' in data and 'data' in data['result'] and 'pastEvents' in data['result']['data']:
        return True
    return False

def get_candidates_from_homepage():
    """Scrape hotplate.com homepage for chef links."""
    url = "https://www.hotplate.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/chef/' in href:
                match = re.search(r'/chef/([^/?]+)', href)
                if match:
                    links.append(match.group(1))
        return list(set(links))
    except requests.exceptions.RequestException:
        return []

def get_candidates_from_google():
    """Scrape Google search results for hotplate chef URLs."""
    search_url = "https://www.google.com/search?q=site:hotplate.com+/chef/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'hotplate.com/chef/' in href:
                match = re.search(r'hotplate\.com/chef/([^/?]+)', href)
                if match:
                    links.append(match.group(1))
        return list(set(links))
    except requests.exceptions.RequestException:
        return []

def main():
    print("Discovering candidate chef IDs...")
    candidates = set()
    
    # From homepage
    homepage_candidates = get_candidates_from_homepage()
    candidates.update(homepage_candidates)
    print(f"Found {len(homepage_candidates)} candidates from homepage")
    
    # From Google search
    google_candidates = get_candidates_from_google()
    candidates.update(google_candidates)
    print(f"Found {len(google_candidates)} candidates from Google search")
    
    # Add known examples
    known_candidates = ['holeydoughandco', 'a-to-z-creamery', 'mrs-saradough']
    candidates.update(known_candidates)
    print(f"Added {len(known_candidates)} known candidates")
    
    print(f"Total unique candidates: {len(candidates)}")
    
    print("Validating chef IDs...")
    valid_storefronts = []
    for i, chef_id in enumerate(candidates):
        print(f"Validating {i+1}/{len(candidates)}: {chef_id}")
        if is_valid_chef(chef_id):
            url = f"https://www.hotplate.com/chef/{chef_id}"
            valid_storefronts.append({"chef_id": chef_id, "url": url})
            print(f"  ✓ Valid: {url}")
        else:
            print(f"  ✗ Invalid")
    
    print(f"Found {len(valid_storefronts)} valid storefronts")
    
    # Save to JSON
    with open('storefronts.json', 'w') as f:
        json.dump(valid_storefronts, f, indent=2)
    
    print("Saved to storefronts.json")

if __name__ == "__main__":
    main()