#!/usr/bin/env python3
"""
YouTube Subscriptions Migrator (Takeout -> New Account)
Automates subscribing to YouTube channels from a Google Takeout CSV export
using Playwright and a real browser (Brave / Chrome).
"""

import argparse
import csv
import os
import platform
import random
import select
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

DEFAULT_CSV = "subscriptions.csv"
DEFAULT_USER_DATA = "./.browser_data"
DONE_FILE = "subscribed_channels.txt"

def find_browser_executable(preferred="auto"):
    """Locates Brave or Google Chrome executable based on the operating system."""
    os_name = platform.system()
    
    candidates = []
    if preferred in ("auto", "brave"):
        if os_name == "Darwin":
            candidates.extend([
                "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
                os.path.expanduser("~/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
            ])
        elif os_name == "Linux":
            candidates.extend([
                "/usr/bin/brave-browser",
                "/usr/bin/brave",
                "/snap/bin/brave",
            ])
        elif os_name == "Windows":
            candidates.extend([
                os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
                os.path.expandvars(r"%PROGRAMFILES%\BraveSoftware\Brave-Browser\Application\brave.exe"),
            ])

    if preferred in ("auto", "chrome"):
        if os_name == "Darwin":
            candidates.extend([
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            ])
        elif os_name == "Linux":
            candidates.extend([
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
            ])
        elif os_name == "Windows":
            candidates.extend([
                os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            ])

    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None

def load_channels(csv_path):
    if not os.path.exists(csv_path):
        print(f"❌ Error: CSV file not found at '{csv_path}'.")
        print("   Please copy your 'subscriptions.csv' here or specify the path with --csv.")
        return []

    channels = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row.get("Channel Id") or row.get("channel_id") or row.get("Channel ID")
            url = row.get("Channel Url") or row.get("channel_url") or row.get("Channel URL")
            title = row.get("Channel Title") or row.get("channel_title") or row.get("Channel Name")
            if url:
                channels.append({
                    "id": cid.strip() if cid else "",
                    "url": url.strip(),
                    "title": title.strip() if title else ""
                })
    return channels

def load_completed_ids():
    if not os.path.exists(DONE_FILE):
        return set()
    with open(DONE_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def mark_completed(channel_id):
    if not channel_id:
        return
    with open(DONE_FILE, "a", encoding="utf-8") as f:
        f.write(f"{channel_id}\n")

def is_logged_in(page):
    try:
        if "youtube.com" not in page.url:
            return False
        
        # Check avatar icon in masthead
        avatar = page.locator("#avatar-btn, button#avatar-btn, ytd-topbar-menu-button-renderer img#avatar")
        if avatar.count() > 0 and avatar.first.is_visible():
            return True
            
        # Check if sign-in button is absent while header is present
        signin = page.locator("a[href*='ServiceLogin'], a[aria-label*='Sign in'], a[aria-label*='Acceder']")
        masthead = page.locator("ytd-masthead")
        if masthead.count() > 0 and masthead.first.is_visible() and signin.count() == 0:
            return True
    except Exception:
        pass
    return False

def check_stdin():
    if not sys.stdin.isatty():
        return False
    try:
        r, _, _ = select.select([sys.stdin], [], [], 0)
        if r:
            sys.stdin.readline()
            return True
    except Exception:
        pass
    return False

def wait_for_login(page, max_seconds=300):
    print("\n" + "="*65)
    print("👉 Open the browser window and SIGN IN to your YouTube account.")
    print("   The script will automatically detect once you are logged in.")
    print("   (You can also press [ENTER] in this terminal when ready)")
    print("="*65 + "\n")
    
    start_time = time.time()
    last_print = 0
    while time.time() - start_time < max_seconds:
        if check_stdin():
            print("\n✅ Manual confirmation received.")
            return True

        if is_logged_in(page):
            print("\n✅ Logged in successfully!")
            return True

        time.sleep(1.5)
        elapsed = int(time.time() - start_time)
        if elapsed - last_print >= 15:
            last_print = elapsed
            remaining = int(max_seconds - elapsed)
            print(f"⏳ Waiting for login... ({remaining}s remaining)")
            
    print("⚠️ Login timeout exceeded.")
    return False

def subscribe_to_channel(page, channel):
    url = channel["url"]
    title = channel["title"] or url
    print(f"\n📺 Processing channel: {title}")
    print(f"   URL: {url}")
    
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        print(f"  ❌ Error loading page: {e}")
        return False

    page.wait_for_timeout(2500)
    
    # 1. Check if already subscribed
    already_subscribed_selectors = [
        "button[aria-label*='Subscribed']",
        "button[aria-label*='Suscrito']",
        "button[aria-label*='Cancelar suscripción']",
        "button[aria-label*='Unsubscribe']",
        "yt-button-shape:has-text('Subscribed')",
        "yt-button-shape:has-text('Suscrito')",
        "ytd-subscribe-button-renderer[subscribed]",
    ]
    
    for sel in already_subscribed_selectors:
        try:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                print(f"  ℹ️ Already subscribed to this channel.")
                return True
        except Exception:
            pass

    # 2. Look for Subscribe button
    subscribe_selectors = [
        "ytd-subscribe-button-renderer button:has-text('Subscribe')",
        "ytd-subscribe-button-renderer button:has-text('Suscribirse')",
        "button[aria-label*='Subscribe to']",
        "button[aria-label*='Suscribirse a']",
        "button[aria-label*='Suscribirme']",
        "yt-button-shape button:has-text('Subscribe')",
        "yt-button-shape button:has-text('Suscribirse')",
        "ytd-subscribe-button-renderer button",
    ]

    btn = None
    for sel in subscribe_selectors:
        try:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                btn = loc.first
                break
        except Exception:
            pass

    if not btn:
        print(f"  ⚠️ Subscribe button not found (channel may be inactive or custom URL changed).")
        return False

    try:
        btn.click()
        page.wait_for_timeout(2000)
        print(f"  🎉 Subscribed successfully!")
        return True
    except Exception as e:
        print(f"  ❌ Failed to click subscribe button: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="YouTube Subscriptions Migrator using Google Takeout CSV and Playwright."
    )
    parser.add_argument("--csv", type=str, default=DEFAULT_CSV, help="Path to subscriptions CSV file (default: subscriptions.csv).")
    parser.add_argument("--limit", type=int, default=1, help="Number of channels to process in this run (default: 1 for test mode).")
    parser.add_argument("--all", action="store_true", help="Process ALL remaining channels in the CSV.")
    parser.add_argument("--delay-min", type=float, default=3.0, help="Minimum seconds to wait between subscriptions (default: 3.0).")
    parser.add_argument("--delay-max", type=float, default=6.0, help="Maximum seconds to wait between subscriptions (default: 6.0).")
    parser.add_argument("--browser", choices=["auto", "brave", "chrome", "chromium"], default="auto", help="Preferred browser (default: auto).")
    parser.add_argument("--user-data-dir", type=str, default=DEFAULT_USER_DATA, help="Browser profile directory (default: ./.browser_data).")
    args = parser.parse_args()

    channels = load_channels(args.csv)
    if not channels:
        return

    completed_ids = load_completed_ids()
    remaining_channels = [c for c in channels if c["id"] not in completed_ids]

    print(f"📊 Current status:")
    print(f"   - Total channels in CSV: {len(channels)}")
    print(f"   - Already processed: {len(completed_ids)}")
    print(f"   - Pending channels: {len(remaining_channels)}")

    if not remaining_channels:
        print("✨ All channels have already been processed!")
        return

    channels_to_process = remaining_channels if args.all else remaining_channels[:args.limit]
    mode_text = f"ALL remaining channels ({len(channels_to_process)})" if args.all else f"TEST MODE (1 channel: {channels_to_process[0]['title']})"
    print(f"🎯 Execution mode: {mode_text}\n")

    executable_path = None
    if args.browser != "chromium":
        executable_path = find_browser_executable(args.browser)

    if executable_path:
        print(f"🌐 Detected browser: {executable_path}")
    else:
        print("🌐 Browser: Default Playwright Chromium.")

    user_data_path = Path(args.user_data_dir).resolve()
    user_data_path.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        launch_args = {
            "user_data_dir": str(user_data_path),
            "headless": False,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
            ],
            "no_viewport": True,
        }
        if executable_path:
            launch_args["executable_path"] = executable_path

        context = p.chromium.launch_persistent_context(**launch_args)
        page = context.pages[0] if context.pages else context.new_page()

        print("Navigating to YouTube...")
        page.goto("https://www.youtube.com", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        # Accept cookies if banner is present
        try:
            consent_btn = page.locator("button:has-text('Accept all'), button:has-text('Aceptar todo'), button:has-text('Reject all'), button:has-text('Rechazar todo')")
            if consent_btn.count() > 0 and consent_btn.first.is_visible():
                consent_btn.first.click()
                page.wait_for_timeout(1000)
        except Exception:
            pass

        # Check or wait for user login
        if not is_logged_in(page):
            if not wait_for_login(page, max_seconds=300):
                print("❌ Login was not completed. Closing browser...")
                context.close()
                return
        else:
            print("✅ Active session found in browser profile.")

        print("\n🚀 Starting subscription process...")
        for idx, channel in enumerate(channels_to_process, 1):
            print(f"\n[{idx}/{len(channels_to_process)}]", end=" ")
            success = subscribe_to_channel(page, channel)
            if success:
                mark_completed(channel["id"])
            
            # Random delay between channels
            if idx < len(channels_to_process):
                delay = random.uniform(args.delay_min, args.delay_max)
                print(f"⏳ Safety pause of {delay:.1f}s...")
                time.sleep(delay)

        print("\n" + "="*65)
        if not args.all and len(remaining_channels) > len(channels_to_process):
            print(f"🏁 Test completed ({len(channels_to_process)} channel processed).")
            print("If the test succeeded, process all remaining channels by running:")
            print("  python subscribe.py --all")
        else:
            print("🎉 All selected channels have been processed!")
        print("="*65)

        page.wait_for_timeout(3000)
        context.close()

if __name__ == "__main__":
    main()
