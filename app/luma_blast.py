import json
import os
import re
import subprocess
import time

import requests
import weave

from app.config import PLATFORM_EMAIL, PLATFORM_PASSWORD, LUMA_EVENT_URL
from app.fourthwall import _pw, _snapshot, _find_ref, _find_all_refs, _current_url


@weave.op()
def send_blast(event_url, storefront_url):
    """Send a Luma blast to all event attendees with the merch store link."""
    try:
        # Step 1: Log in to Luma
        print("  Logging in to Luma...")
        _luma_login()
        time.sleep(3)

        # Step 2: Get the event API ID and navigate to manage page
        print("  Navigating to event manage page...")
        event_api_id = _get_event_api_id(event_url)
        _navigate_to_manage(event_api_id)
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
# Get event API ID from Luma API
# ---------------------------------------------------------------------------

def _get_event_api_id(event_url):
    """Extract the event slug and get the internal event API ID from Luma's API.

    The manage page URL uses the internal API ID (evt-xxx), not the slug (hh5k4ahp).
    """
    # Extract slug from URL (e.g., "hh5k4ahp" from "https://luma.com/hh5k4ahp")
    slug = event_url.rstrip("/").split("/")[-1]

    resp = requests.get(
        f"https://api.lu.ma/event/get?event_api_id={slug}",
        timeout=15,
    )
    if resp.status_code == 200:
        data = resp.json()
        # The event API ID is at the top level, not nested under "event"
        api_id = data.get("api_id")
        if api_id:
            print(f"    Event API ID: {api_id}")
            return api_id

    raise RuntimeError(f"Could not get event API ID for slug '{slug}' (status {resp.status_code})")


# ---------------------------------------------------------------------------
# Luma login
# ---------------------------------------------------------------------------

def _luma_login():
    """Log in to Luma via browser automation.

    Flow: lu.ma/signin -> enter email -> Continue with Email -> enter password -> Continue
    """
    _pw("open", "https://lu.ma/signin")
    time.sleep(5)

    snap = _snapshot()

    # Fill email
    email_ref = _find_ref(snap, "email", "textbox")
    if not email_ref:
        email_ref = _find_ref(snap, "email")
    if not email_ref:
        raise RuntimeError("Could not find email field on Luma login page")

    _pw("fill", email_ref, PLATFORM_EMAIL)
    time.sleep(1)

    # Click "Continue with Email"
    snap = _snapshot()
    continue_ref = (
        _find_ref(snap, "continue with email", "button")
        or _find_ref(snap, "continue with email")
        or _find_ref(snap, "continue", "button")
    )
    if continue_ref:
        _pw("click", continue_ref)
        time.sleep(3)

    # Fill password — the textbox on the password page has no label,
    # it's just "textbox [active]", so find it by looking for the active textbox
    snap = _snapshot()
    pass_ref = (
        _find_ref(snap, "textbox", "active")
        or _find_ref(snap, "password", "textbox")
        or _find_ref(snap, "textbox")
    )
    if not pass_ref:
        raise RuntimeError("Password field not found after email submission")

    _pw("fill", pass_ref, PLATFORM_PASSWORD)
    time.sleep(1)

    # Click Continue
    snap = _snapshot()
    login_ref = (
        _find_ref(snap, "continue", "button")
        or _find_ref(snap, "log in", "button")
        or _find_ref(snap, "sign in", "button")
    )
    if login_ref:
        _pw("click", login_ref)
        time.sleep(5)

    # Verify login by checking page content (URL may still show /signin
    # due to client-side routing, but page content changes to logged-in state)
    snap = _snapshot()

    # Dismiss passkey dialog if it appears
    if "create a passkey" in snap.lower() or "not now" in snap.lower():
        not_now_ref = _find_ref(snap, "not now", "button") or _find_ref(snap, "not now")
        if not_now_ref:
            _pw("click", not_now_ref)
        else:
            _pw("press", "Escape")
        time.sleep(2)
        snap = _snapshot()

    # Check for logged-in indicators in page content
    logged_in = (
        "create event" in snap.lower()
        or "events" in snap.lower() and "calendars" in snap.lower()
        or "/home" in snap.lower()
    )

    if not logged_in:
        raise RuntimeError("Login failed — page does not show logged-in state")

    print("    Logged in to Luma")


# ---------------------------------------------------------------------------
# Navigation to manage page
# ---------------------------------------------------------------------------

def _navigate_to_manage(event_api_id):
    """Navigate to the event management page using the internal event API ID.

    The correct URL pattern is: https://luma.com/event/manage/{event_api_id}
    NOT: https://lu.ma/{slug}/manage/blasts (this shows the public event page)
    """
    manage_url = f"https://luma.com/event/manage/{event_api_id}"
    _pw("goto", manage_url)
    time.sleep(5)

    # Verify we're on the manage page
    snap = _snapshot()
    url = _current_url()

    # Check for manage page indicators
    has_manage = (
        "send a blast" in snap.lower()
        or "blasts" in snap.lower()
        or "/manage/" in url.lower()
    )

    if not has_manage:
        raise RuntimeError(f"Failed to reach manage page. URL: {url}")

    print(f"    On manage page: {url}")


# ---------------------------------------------------------------------------
# Compose and send blast
# ---------------------------------------------------------------------------

def _compose_and_send_blast(storefront_url):
    """Open the blast compose dialog, fill in subject + message, and send."""
    snap = _snapshot()

    # Click "Send a Blast" button on the manage page
    blast_btn = (
        _find_ref(snap, "send a blast", "button")
        or _find_ref(snap, "send a blast")
        or _find_ref(snap, "send blast")
    )
    if not blast_btn:
        raise RuntimeError("Could not find 'Send a Blast' button on manage page")

    _pw("click", blast_btn)
    time.sleep(3)

    # Verify the compose dialog opened
    snap = _snapshot()
    if "send blast" not in snap.lower() and "subject" not in snap.lower():
        raise RuntimeError("Blast compose dialog did not open")

    # Fill subject
    blast_subject = "Your exclusive Ralphathon merch is here!"
    subject_ref = (
        _find_ref(snap, "subject", "textbox")
        or _find_ref(snap, "subject")
    )
    if subject_ref:
        _pw("fill", subject_ref, blast_subject)
        time.sleep(1)

    # Fill message body — the message field is a textbox (not contenteditable)
    # that contains a placeholder paragraph "Share a message with your guests…"
    blast_body = (
        "Hey Ralphathon crew! We made custom t-shirt designs just for this event. "
        f"Check out the merch store and grab yours before they're gone: {storefront_url}"
    )

    # Find the message textbox — it's an unlabeled textbox near "Message" label
    # We need the textbox that contains the "Share a message" placeholder
    snap = _snapshot()

    # Find all textbox refs, the message one is after the subject one
    all_textbox_refs = _find_all_refs(snap, "textbox")
    body_ref = None
    if len(all_textbox_refs) >= 2:
        # Second textbox in the dialog (first is subject)
        body_ref = all_textbox_refs[-1]  # Last textbox is the message body
    if not body_ref:
        body_ref = _find_ref(snap, "share a message")

    if body_ref:
        _pw("click", body_ref)
        time.sleep(0.5)
        _pw("fill", body_ref, blast_body)
        time.sleep(1)
    else:
        raise RuntimeError("Could not find message body field")

    # Verify the message was filled
    snap = _snapshot()
    if storefront_url.lower() not in snap.lower() and "merch" not in snap.lower():
        raise RuntimeError("Message body does not appear to be filled")

    # Click Send button — must find the one inside the blast dialog (ref=e360),
    # NOT the "Send a Blast" button on the manage page (ref=e78).
    # The dialog's Send button has text "Send" (not "Send a Blast")
    # Find it by looking for a button whose line has "Send" but NOT "Blast"
    send_ref = None
    for line in snap.split("\n"):
        lower = line.lower()
        if 'button' in lower and '[ref=' in lower:
            # Match "Send" button but not "Send a Blast"
            if 'send' in lower and 'blast' not in lower and 'share' not in lower:
                match = re.search(r'\[ref=([\w]+)\]', line)
                if match:
                    send_ref = match.group(1)
                    break

    if not send_ref:
        raise RuntimeError("Could not find Send button in blast compose dialog")

    print(f"    Clicking Send (ref={send_ref})")
    _pw("click", send_ref)
    time.sleep(3)

    # Handle confirmation dialog if one appears
    snap = _snapshot()
    confirm_ref = (
        _find_ref(snap, "confirm", "button")
        or _find_ref(snap, "yes", "button")
        or _find_ref(snap, "send", "button")
    )
    if confirm_ref:
        _pw("click", confirm_ref)
        time.sleep(3)

    # Verify send succeeded
    # After sending, the dialog should close and we should be back on manage page
    # or there should be a success indicator
    time.sleep(2)
    snap = _snapshot()
    final_url = _current_url()

    # Check for real success: the blast compose dialog should be gone,
    # and we should see the blast in the sent list, or a success toast
    blast_dialog_gone = "subject" not in snap.lower() or "share a message" not in snap.lower()
    has_sent_indicator = (
        "sent" in snap.lower()
        or "delivered" in snap.lower()
        or "success" in snap.lower()
    )

    # Also navigate to the Blasts tab to verify
    blasts_tab = _find_ref(snap, "blasts", "link")
    if blasts_tab:
        _pw("click", blasts_tab)
        time.sleep(3)
        snap = _snapshot()
        # Check if our subject appears in the blasts list
        has_blast_in_list = blast_subject.lower() in snap.lower() or "ralphathon merch" in snap.lower()
    else:
        has_blast_in_list = False

    sent = blast_dialog_gone or has_sent_indicator or has_blast_in_list

    if not sent:
        print(f"    WARNING: Could not confirm blast was sent. URL: {final_url}")

    return {
        "subject": blast_subject,
        "body": blast_body,
        "final_url": final_url,
        "blast_dialog_closed": blast_dialog_gone,
        "sent_indicator_found": has_sent_indicator,
        "blast_in_sent_list": has_blast_in_list,
        "verified_sent": sent,
    }


if __name__ == "__main__":
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
