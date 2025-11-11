
from typing import List, Dict, Any

def fetch_menu(session) -> Dict[str, Any]:
    """Stub: return a simple menu. Replace with Hotplate API or DOM extraction."""
    # In real implementation, use session cookies + requests or a browser to fetch.
    return {
        "items": [
            {"sku": "SKU_EVERYTHING", "name": "Everything Bagel", "options": ["spread", "toasted"]},
            {"sku": "SKU_SESAME", "name": "Sesame Bagel", "options": ["spread", "toasted"]},
            {"sku": "SKU_GARLIC", "name": "Garlic Bagel", "options": ["spread", "toasted"]},
            {"sku": "SKU_PLAIN", "name": "Plain Bagel", "options": ["spread", "toasted"]},
        ]
    }

def resolve_items(menu: Dict[str, Any], order_cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Map human-readable names/options to SKUs and modifier payloads.
    Very naive resolution for starter scaffold.
    """
    name_to_sku = {i["name"].lower(): i["sku"] for i in menu.get("items", [])}
    resolved = []
    for line in order_cfg.get("items", []):
        name = line.get("name", "").lower()
        sku = name_to_sku.get(name)
        if not sku:
            # attempt substitutions
            for sub in order_cfg.get("substitutions", []):
                if sub.get("for", "").lower() == name:
                    for candidate in sub.get("try", []):
                        cand = name_to_sku.get(candidate.lower())
                        if cand:
                            sku = cand
                            break
                if sku:
                    break
        if not sku:
            raise ValueError(f"Unable to resolve SKU for '{line.get('name')}'.")
        resolved.append({
            "sku": sku,
            "qty": line.get("quantity", 1),
            "modifiers": line.get("options", {}),
            "notes": order_cfg.get("notes", ""),
        })
    return resolved
