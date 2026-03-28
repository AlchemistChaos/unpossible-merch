import json
import os
import re
import subprocess
import time

import requests

from app.config import (
    FOURTHWALL_API_USERNAME,
    FOURTHWALL_API_PASSWORD,
    PLATFORM_EMAIL,
    PLATFORM_PASSWORD,
)

# T-shirt product template slug on Fourthwall
PRODUCT_TEMPLATE = "gildan-heavyweight-t-shirt-dtg"


def upload_designs(selected_briefs, image_results):
    """Upload designs to Fourthwall and create t-shirt products via browser automation.

    Args:
        selected_briefs: List of brief dicts from critique stage.
        image_results: List of image result dicts from design stage.

    Returns:
        Dict with products list, API verification, and counts.
    """
    # Get shop domain from API
    shop_domain = _get_shop_domain()

    # Match briefs with successful images
    image_map = {}
    for img in image_results:
        if img.get("status") == "success" and img.get("file"):
            image_map[img["brief_id"]] = img["file"]

    products = []
    try:
        print("  Logging in to Fourthwall...")
        _login(shop_domain)
        time.sleep(3)

        for i, brief in enumerate(selected_briefs):
            image_path = image_map.get(brief["id"])
            if not image_path or not os.path.exists(image_path):
                print(f"  Skipping {brief['id']}: no image available")
                products.append({
                    "brief_id": brief["id"],
                    "status": "skipped",
                    "reason": "no_image",
                })
                continue

            print(f"  Creating product {i + 1}/{len(selected_briefs)}: {brief['title']}")
            try:
                result = _create_product(brief, os.path.abspath(image_path), shop_domain)
                products.append(result)
                print(f"    -> {result['status']}")
            except Exception as e:
                print(f"    -> Failed: {e}")
                products.append({
                    "brief_id": brief["id"],
                    "status": "error",
                    "error": str(e),
                })

            time.sleep(2)
    finally:
        _pw("close")

    # Verify via API
    api_check = _verify_products_via_api()

    return {
        "products": products,
        "api_verification": api_check,
        "successful": sum(1 for p in products if p.get("status") == "success"),
        "failed": sum(1 for p in products if p.get("status") != "success"),
    }


# ---------------------------------------------------------------------------
# Playwright-cli helpers
# ---------------------------------------------------------------------------

def _pw(*args, timeout=30):
    """Run a playwright-cli command and return stdout."""
    cmd = ["playwright-cli"] + [str(a) for a in args]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.stdout.strip()


def _snapshot():
    """Take a page snapshot and return the YAML content with element refs."""
    raw = _pw("snapshot")
    # Extract YAML file path from snapshot output
    match = re.search(r'\[Snapshot\]\(([^)]+\.yml)\)', raw)
    if match:
        yml_path = match.group(1)
        try:
            with open(yml_path) as f:
                return f.read()
        except FileNotFoundError:
            pass
    return raw


def _find_ref(snapshot_text, *hints):
    """Find an element ref in the snapshot whose line contains ALL hints (case-insensitive)."""
    for line in snapshot_text.split("\n"):
        lower = line.lower()
        if all(h.lower() in lower for h in hints):
            match = re.search(r'\[ref=([\w]+)\]', line)
            if match:
                return match.group(1)
    return None


def _find_all_refs(snapshot_text, *hints):
    """Find all element refs matching hints."""
    refs = []
    for line in snapshot_text.split("\n"):
        lower = line.lower()
        if all(h.lower() in lower for h in hints):
            match = re.search(r'\[ref=([\w]+)\]', line)
            if match:
                refs.append(match.group(1))
    return refs


def _current_url():
    """Get the current page URL."""
    raw = _pw("eval", "window.location.href")
    url = raw.strip()
    for line in url.split("\n"):
        line = line.strip()
        if line.startswith('"') and line.endswith('"'):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                pass
        if line.startswith("http"):
            return line
    return url


def _get_shop_domain():
    """Get the shop domain from Fourthwall API."""
    if not FOURTHWALL_API_USERNAME or not FOURTHWALL_API_PASSWORD:
        return "unpossible-merch-shop"
    try:
        resp = requests.get(
            "https://api.fourthwall.com/open-api/v1.0/shops/current",
            auth=(FOURTHWALL_API_USERNAME, FOURTHWALL_API_PASSWORD),
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json().get("domain", "unpossible-merch-shop")
    except Exception:
        pass
    return "unpossible-merch-shop"


# ---------------------------------------------------------------------------
# Login flow
# ---------------------------------------------------------------------------

def _login(shop_domain):
    """Log in to Fourthwall via browser automation.

    Navigates to the shop admin dashboard which redirects to auth.fourthwall.com.
    Fills email/password and clicks Log in.
    """
    dashboard_url = f"https://{shop_domain}.fourthwall.com/admin/dashboard"
    _pw("open", dashboard_url)
    time.sleep(5)

    snap = _snapshot()

    # Find email field (auth.fourthwall.com login form)
    email_ref = (
        _find_ref(snap, "email", "textbox")
        or _find_ref(snap, "email")
    )
    if email_ref:
        _pw("fill", email_ref, PLATFORM_EMAIL)

    # Find password field
    pass_ref = (
        _find_ref(snap, "password", "textbox")
        or _find_ref(snap, "password")
    )
    if pass_ref:
        _pw("fill", pass_ref, PLATFORM_PASSWORD)

    time.sleep(1)
    snap = _snapshot()

    # Click Log in button
    login_ref = (
        _find_ref(snap, "log in", "button")
        or _find_ref(snap, "log in")
        or _find_ref(snap, "sign in")
    )
    if login_ref:
        _pw("click", login_ref)

    time.sleep(8)

    # Verify login succeeded
    url = _current_url()
    if "auth.fourthwall.com" in url:
        _pw("press", "Enter")
        time.sleep(5)

    print("    Logged in to Fourthwall")


# ---------------------------------------------------------------------------
# Product creation flow
# ---------------------------------------------------------------------------

def _create_product(brief, image_path, shop_domain):
    """Create a single t-shirt product on Fourthwall.

    Flow:
    1. Navigate to product template page
    2. Click "Design now" to open editor
    3. Upload design image
    4. Click uploaded image to place on design
    5. Click "Next" to go to product details
    6. Fill in name and price
    7. Click "Publish now"
    """
    # Step 1: Navigate to product template
    template_url = f"https://{shop_domain}.fourthwall.com/admin/products/{PRODUCT_TEMPLATE}"
    _pw("goto", template_url)
    time.sleep(4)

    # Step 2: Click "Design now"
    snap = _snapshot()
    design_ref = _find_ref(snap, "design now")
    if not design_ref:
        design_ref = _find_ref(snap, "design")
    if design_ref:
        _pw("click", design_ref)
        time.sleep(5)
    else:
        raise RuntimeError("Could not find 'Design now' button")

    # Step 3: Upload design image
    snap = _snapshot()
    upload_ref = _find_ref(snap, "upload image")
    if not upload_ref:
        upload_ref = _find_ref(snap, "upload")
    if upload_ref:
        _pw("click", upload_ref)
        time.sleep(1)
        _pw("upload", image_path)
        time.sleep(5)
    else:
        raise RuntimeError("Could not find 'Upload image' button")

    # Step 4: Click uploaded image thumbnail to place on design
    snap = _snapshot()
    # The uploaded image appears as a button in "Your uploads" section
    uploads_refs = _find_all_refs(snap, "your uploads")
    # Find the button after "Your uploads" label
    found_uploads = False
    for line in snap.split("\n"):
        if "your uploads" in line.lower():
            found_uploads = True
            continue
        if found_uploads:
            match = re.search(r'button \[ref=([\w]+)\]', line)
            if match:
                _pw("click", match.group(1))
                time.sleep(3)
                break

    # Step 5: Click "Next"
    snap = _snapshot()
    next_ref = _find_ref(snap, "next")
    if next_ref:
        _pw("click", next_ref)
        time.sleep(5)
    else:
        raise RuntimeError("Could not find 'Next' button (is image placed on design?)")

    # Step 6: Fill product details
    snap = _snapshot()

    # Product name
    title = f"Ralphathon - {brief['title']}"
    name_ref = _find_ref(snap, "product name", "textbox")
    if not name_ref:
        name_ref = _find_ref(snap, "product name")
    if name_ref:
        _pw("fill", name_ref, title)

    # Price (default is $15.00, set to $25.00)
    price_ref = _find_ref(snap, "selling price", "spinbutton")
    if not price_ref:
        price_ref = _find_ref(snap, "selling price")
    if not price_ref:
        price_ref = _find_ref(snap, "price")
    if price_ref:
        _pw("fill", price_ref, "25.00")

    time.sleep(2)

    # Step 7: Click "Publish now"
    snap = _snapshot()
    publish_ref = _find_ref(snap, "publish now")
    if not publish_ref:
        publish_ref = _find_ref(snap, "publish")
    if publish_ref:
        _pw("click", publish_ref)
        time.sleep(6)
    else:
        # Try "Save as hidden" as fallback
        save_ref = _find_ref(snap, "save as hidden")
        if save_ref:
            _pw("click", save_ref)
            time.sleep(6)

    # Get product URL from current page
    product_url = _current_url()

    return {
        "brief_id": brief["id"],
        "title": title,
        "status": "success",
        "product_url": product_url,
    }


# ---------------------------------------------------------------------------
# API verification
# ---------------------------------------------------------------------------

def _verify_products_via_api():
    """Verify created products via Fourthwall read-only API."""
    if not FOURTHWALL_API_USERNAME or not FOURTHWALL_API_PASSWORD:
        return {"status": "skipped", "reason": "no_api_credentials"}

    try:
        response = requests.get(
            "https://api.fourthwall.com/open-api/v1.0/products",
            auth=(FOURTHWALL_API_USERNAME, FOURTHWALL_API_PASSWORD),
            timeout=15,
        )
        if response.status_code == 200:
            data = response.json()
            products = data.get("results", data.get("data", []))
            return {
                "status": "verified",
                "product_count": len(products) if isinstance(products, list) else 0,
                "products": [
                    {"id": p.get("id"), "name": p.get("name"), "slug": p.get("slug")}
                    for p in (products[:10] if isinstance(products, list) else [])
                ],
            }
        else:
            return {
                "status": "api_error",
                "code": response.status_code,
                "body": response.text[:200],
            }
    except Exception as e:
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    # Test with checkpoint data if available
    briefs_path = "checkpoints/03-selected-briefs.json"
    images_path = "checkpoints/04-images.json"

    if os.path.exists(briefs_path) and os.path.exists(images_path):
        with open(briefs_path) as f:
            briefs = json.load(f)
        with open(images_path) as f:
            images = json.load(f)
        result = upload_designs(briefs, images)
        print(json.dumps(result, indent=2))
    else:
        print("No checkpoint data found. Run pipeline stages 1-4 first.")
