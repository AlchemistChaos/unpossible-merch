import json
import os
import re
import subprocess
import time

from app.config import PLATFORM_EMAIL, PLATFORM_PASSWORD, LUMA_EVENT_URL
from app.fourthwall import _pw, _snapshot, _find_ref, _find_all_refs, _current_url


def send_blast(event_url, storefront_url):
    """Send a Luma blast to all event attendees with the merch store link.

    Uses playwright-cli browser automation to:
    1. Log in to Luma
    2. Navigate to event > Manage Event > Blasts
    3. Compose a blast with the storefront URL
    4. Send to all 'Going' attendees

    Args:
        event_url: The Luma event URL (e.g., https://luma.com/hh5k4ahp)
        storefront_url: The Fourthwall storefront URL to share.

    Returns:
        Dict with blast status and details.
    """
    try:
        # Step 1: Log in to Luma
        print("  Logging in to Luma...")
        _luma_login()
        time.sleep(3)

        # Step 2: Navigate to event management / blasts page
        print("  Navigating to event blasts page...")
        _navigate_to_blasts(event_url)
        time.sleep(3)

        # Step 3: Compose and send the blast
        print("  Composing and sending blast...")
        blast_result = _compose_and_send_blast(storefront_url)

        return {
            "status": "success",
            "event_url": event_url,
            "storefront_url": storefront_url,
            "blast_details": blast_result,
        }

    except Exception as e:
        print(f"  Blast failed: {e}")
        return {
            "status": "error",
            "event_url": event_url,
            "storefront_url": storefront_url,
            "error": str(e),
        }
    finally:
        try:
            _pw("close")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Luma login
# ---------------------------------------------------------------------------

def _luma_login():
    """Log in to Luma via browser automation."""
    _pw("open", "https://lu.ma/signin")
    time.sleep(5)

    snap = _snapshot()

    # Find email field
    email_ref = (
        _find_ref(snap, "email", "textbox")
        or _find_ref(snap, "email")
    )
    if email_ref:
        _pw("fill", email_ref, PLATFORM_EMAIL)
        time.sleep(1)
    else:
        raise RuntimeError("Could not find email field on Luma login page")

    # Click continue / sign in button
    snap = _snapshot()
    continue_ref = (
        _find_ref(snap, "continue", "button")
        or _find_ref(snap, "log in", "button")
        or _find_ref(snap, "sign in", "button")
        or _find_ref(snap, "continue")
        or _find_ref(snap, "log in")
        or _find_ref(snap, "sign in")
    )
    if continue_ref:
        _pw("click", continue_ref)
        time.sleep(3)

    # Fill password if a password field appears
    snap = _snapshot()
    pass_ref = (
        _find_ref(snap, "password", "textbox")
        or _find_ref(snap, "password")
    )
    if pass_ref:
        _pw("fill", pass_ref, PLATFORM_PASSWORD)
        time.sleep(1)

        # Click log in / continue
        snap = _snapshot()
        login_ref = (
            _find_ref(snap, "log in", "button")
            or _find_ref(snap, "sign in", "button")
            or _find_ref(snap, "continue", "button")
            or _find_ref(snap, "log in")
            or _find_ref(snap, "sign in")
            or _find_ref(snap, "continue")
        )
        if login_ref:
            _pw("click", login_ref)
            time.sleep(5)

    # Verify login by checking URL changed away from signin
    url = _current_url()
    if "signin" in url.lower():
        # Try pressing Enter as fallback
        _pw("press", "Enter")
        time.sleep(5)

    print("    Logged in to Luma")


# ---------------------------------------------------------------------------
# Navigation to blasts
# ---------------------------------------------------------------------------

def _navigate_to_blasts(event_url):
    """Navigate to the event's blast page in Luma manage view.

    Luma manage URL pattern: event_url + '/manage/blasts'
    e.g., https://lu.ma/hh5k4ahp -> https://lu.ma/hh5k4ahp/manage/blasts
    """
    # Normalize event URL to lu.ma format
    base_url = event_url.rstrip("/")
    # Handle both luma.com and lu.ma URLs
    base_url = base_url.replace("https://luma.com/", "https://lu.ma/")
    base_url = base_url.replace("http://luma.com/", "https://lu.ma/")

    blasts_url = f"{base_url}/manage/blasts"
    _pw("goto", blasts_url)
    time.sleep(5)

    # Verify we're on the blasts page
    snap = _snapshot()
    url = _current_url()

    # If redirected to event page, try finding "Manage Event" link
    if "manage" not in url.lower():
        manage_ref = (
            _find_ref(snap, "manage event")
            or _find_ref(snap, "manage")
        )
        if manage_ref:
            _pw("click", manage_ref)
            time.sleep(3)

        # Then navigate to blasts tab
        snap = _snapshot()
        blasts_ref = (
            _find_ref(snap, "blasts")
            or _find_ref(snap, "blast")
        )
        if blasts_ref:
            _pw("click", blasts_ref)
            time.sleep(3)

    print(f"    On blasts page: {_current_url()}")


# ---------------------------------------------------------------------------
# Compose and send blast
# ---------------------------------------------------------------------------

def _compose_and_send_blast(storefront_url):
    """Compose a merch announcement blast and send it."""
    snap = _snapshot()

    # Look for "New Blast" or "Create Blast" or "Send Blast" button
    new_blast_ref = (
        _find_ref(snap, "new blast")
        or _find_ref(snap, "create blast")
        or _find_ref(snap, "send blast")
        or _find_ref(snap, "new blast", "button")
        or _find_ref(snap, "compose")
        or _find_ref(snap, "create", "button")
    )
    if new_blast_ref:
        _pw("click", new_blast_ref)
        time.sleep(3)

    # Compose the blast message
    blast_subject = "Your exclusive Ralphathon merch is here!"
    blast_body = (
        "Hey Ralphathon crew! We made custom t-shirt designs just for this event. "
        f"Check out the merch store and grab yours before they're gone: {storefront_url}"
    )

    snap = _snapshot()

    # Fill subject if there's a subject field
    subject_ref = (
        _find_ref(snap, "subject", "textbox")
        or _find_ref(snap, "subject")
        or _find_ref(snap, "title", "textbox")
    )
    if subject_ref:
        _pw("fill", subject_ref, blast_subject)
        time.sleep(1)

    # Fill body/message content
    body_ref = (
        _find_ref(snap, "message", "textbox")
        or _find_ref(snap, "body", "textbox")
        or _find_ref(snap, "content", "textbox")
        or _find_ref(snap, "message")
        or _find_ref(snap, "body")
        or _find_ref(snap, "write", "textbox")
    )
    if body_ref:
        _pw("fill", body_ref, blast_body)
        time.sleep(1)
    else:
        # Try typing into any focused/editable area
        # Luma blast editor might be a contenteditable div
        _pw("eval", f"""
            const editors = document.querySelectorAll('[contenteditable="true"]');
            if (editors.length > 0) {{
                editors[editors.length - 1].innerText = `{blast_body}`;
            }}
        """)
        time.sleep(1)

    # Select recipients - target "Going" attendees
    snap = _snapshot()
    going_ref = (
        _find_ref(snap, "going")
        or _find_ref(snap, "all attendees")
        or _find_ref(snap, "attendees")
    )
    if going_ref:
        _pw("click", going_ref)
        time.sleep(1)

    # Click Send
    snap = _snapshot()
    send_ref = (
        _find_ref(snap, "send blast", "button")
        or _find_ref(snap, "send", "button")
        or _find_ref(snap, "send blast")
        or _find_ref(snap, "send")
    )
    if send_ref:
        _pw("click", send_ref)
        time.sleep(3)

    # Confirm send if there's a confirmation dialog
    snap = _snapshot()
    confirm_ref = (
        _find_ref(snap, "confirm", "button")
        or _find_ref(snap, "yes", "button")
        or _find_ref(snap, "send", "button")
        or _find_ref(snap, "confirm")
    )
    if confirm_ref:
        _pw("click", confirm_ref)
        time.sleep(3)

    # Check final state
    final_url = _current_url()
    final_snap = _snapshot()

    # Look for success indicators
    sent = (
        "sent" in final_snap.lower()
        or "success" in final_snap.lower()
        or "delivered" in final_snap.lower()
        or "blast" in final_snap.lower()
    )

    return {
        "subject": blast_subject,
        "body": blast_body,
        "final_url": final_url,
        "sent_indicator_found": sent,
    }


if __name__ == "__main__":
    # Test with checkpoint data if available
    storefront_path = "checkpoints/06-storefront.json"
    event_url = LUMA_EVENT_URL

    if os.path.exists(storefront_path):
        with open(storefront_path) as f:
            storefront_data = json.load(f)
        storefront_url = storefront_data.get("storefront_url", "")
        result = send_blast(event_url, storefront_url)
        print(json.dumps(result, indent=2))
    else:
        print("No storefront checkpoint. Run pipeline stages 1-6 first.")
