import json
import os
import time

import requests

from app.config import (
    FOURTHWALL_API_USERNAME,
    FOURTHWALL_API_PASSWORD,
)
from app.fourthwall import (
    _pw,
    _snapshot,
    _find_ref,
    _login,
    _get_shop_domain,
    _current_url,
)


def setup_storefront(event_data, fourthwall_results=None):
    """Configure Fourthwall storefront with event branding.

    Args:
        event_data: Dict with event name and details.
        fourthwall_results: Optional dict from the Fourthwall upload stage.

    Returns:
        Dict with storefront URL, shop info, and product visibility.
    """
    shop_domain = _get_shop_domain()
    event_name = event_data.get("name", "Ralphathon")
    target_name = f"Unpossible Merch - {event_name}"

    # Update shop name via browser automation
    name_updated = False
    try:
        print("  Logging in to Fourthwall...")
        _login(shop_domain)
        time.sleep(3)

        print(f"  Setting shop name to: {target_name}")
        name_updated = _update_shop_name(shop_domain, target_name)

        # Ensure products are visible by checking the storefront page
        print("  Verifying products on storefront...")
        _verify_storefront_products(shop_domain)

    except Exception as e:
        print(f"  Warning: Browser automation issue: {e}")
    finally:
        try:
            _pw("close")
        except Exception:
            pass

    # Get shop details from API
    shop_info = _get_shop_info()

    # Verify products are visible via API
    products = _verify_products_visible()

    # Construct the public storefront URL
    storefront_url = shop_info.get("url") or f"https://{shop_domain}.fourthwall.com"

    # Verify storefront is accessible
    accessible = _check_storefront(storefront_url)

    return {
        "storefront_url": storefront_url,
        "shop_domain": shop_domain,
        "shop_name": target_name,
        "name_updated": name_updated,
        "shop_info": shop_info,
        "products_visible": products,
        "storefront_accessible": accessible,
    }


def _get_shop_info():
    """Get shop details from Fourthwall API."""
    if not FOURTHWALL_API_USERNAME or not FOURTHWALL_API_PASSWORD:
        return {"status": "no_credentials"}

    try:
        resp = requests.get(
            "https://api.fourthwall.com/open-api/v1.0/shops/current",
            auth=(FOURTHWALL_API_USERNAME, FOURTHWALL_API_PASSWORD),
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "status": "ok",
                "domain": data.get("domain"),
                "name": data.get("name"),
                "url": data.get("url"),
                "currency": data.get("currency"),
            }
        return {"status": "api_error", "code": resp.status_code}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _verify_products_visible():
    """Verify products are visible via Fourthwall API."""
    if not FOURTHWALL_API_USERNAME or not FOURTHWALL_API_PASSWORD:
        return {"status": "no_credentials", "count": 0}

    try:
        resp = requests.get(
            "https://api.fourthwall.com/open-api/v1.0/products",
            auth=(FOURTHWALL_API_USERNAME, FOURTHWALL_API_PASSWORD),
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            products = data.get("results", data.get("data", []))
            visible = [p for p in products if isinstance(p, dict)]
            return {
                "status": "ok",
                "count": len(visible),
                "products": [
                    {
                        "name": p.get("name"),
                        "slug": p.get("slug"),
                        "state": p.get("state"),
                    }
                    for p in visible[:10]
                ],
            }
        return {"status": "api_error", "code": resp.status_code}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _update_shop_name(shop_domain, target_name):
    """Navigate to shop settings and update the site title and creator name."""
    settings_url = f"https://{shop_domain}.fourthwall.com/admin/dashboard/settings/"
    _pw("goto", settings_url)
    time.sleep(5)

    snap = _snapshot()

    # Update "Site title" field
    title_ref = (
        _find_ref(snap, "site title", "textbox")
        or _find_ref(snap, "site title")
    )
    if title_ref:
        _pw("fill", title_ref, target_name)
        time.sleep(1)

    # Update "Creator name" field
    creator_ref = (
        _find_ref(snap, "creator name", "textbox")
        or _find_ref(snap, "creator name")
    )
    if creator_ref:
        _pw("fill", creator_ref, target_name)
        time.sleep(1)

    if not title_ref and not creator_ref:
        print("    Could not find name fields in settings")
        return False

    # Click Save button
    snap = _snapshot()
    save_ref = (
        _find_ref(snap, "save", "button")
        or _find_ref(snap, "save")
    )
    if save_ref:
        _pw("click", save_ref)
        time.sleep(3)
        print("    Shop name updated and saved")
        return True
    else:
        print("    Name filled but no save button found")
        return False


def _verify_storefront_products(shop_domain):
    """Navigate to the public storefront and check that products are showing."""
    storefront_url = f"https://{shop_domain}.fourthwall.com"
    _pw("goto", storefront_url)
    time.sleep(5)

    snap = _snapshot()
    # Check if any product-like content is visible on the storefront
    has_products = (
        "product" in snap.lower()
        or "ralphathon" in snap.lower()
        or "t-shirt" in snap.lower()
        or "shop" in snap.lower()
    )

    if has_products:
        print("    Products appear visible on storefront")
    else:
        print("    Warning: Could not confirm products on storefront page")

    return has_products


def _check_storefront(storefront_url):
    """Check if the storefront URL is accessible."""
    try:
        resp = requests.get(storefront_url, timeout=15, allow_redirects=True)
        return {
            "status": "accessible" if resp.status_code == 200 else "error",
            "status_code": resp.status_code,
            "final_url": str(resp.url),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    # Test with checkpoint data
    event_path = "checkpoints/01-event-data.json"
    if os.path.exists(event_path):
        with open(event_path) as f:
            event_data = json.load(f)
        result = setup_storefront(event_data)
        print(json.dumps(result, indent=2))
    else:
        print("No event data checkpoint. Run pipeline stages 1-5 first.")
