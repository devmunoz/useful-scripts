# YouTube Takeout Resubscribe 📺

A Python automation script using **Playwright** to seamlessly transfer your YouTube channel subscriptions to a new Google account using the CSV export from **Google Takeout**.

Unlike solutions that rely on the official YouTube Data API (which enforces strict daily quota limits that restrict you to only a few subscriptions per day), this script automates a real browser (**Brave**, **Chrome**, or **Chromium**). This allows you to log in manually, handles bot detection gracefully, and applies anti-rate-limit delays.

---

## 🚀 Features

- **Interactive & Secure Login**: Launches a real browser window so you can safely log into your new Google/YouTube account.
- **Automatic Login Detection**: Automatically detects when you have successfully logged in (or press `Enter` in the console).
- **Persistent Session**: Saves browser profile and session cookies locally (`.browser_data/`), so you never need to log in again on future runs.
- **Safe Test Mode by Default**: Subscribes to only 1 channel on the first run to verify the flow before processing your entire list.
- **Resumable / Idempotent**: Tracks processed channels in `subscribed_channels.txt`. If interrupted, it seamlessly picks up right where it left off.
- **Human-like Delays**: Configurable random intervals between subscription actions to protect your account against YouTube spam flags and rate limits.
- **Cross-Platform**: Works smoothly on macOS, Linux, and Windows.

---

## 📋 Prerequisites

- **Python 3.8+**
- **Brave Browser** or **Google Chrome** installed (strongly recommended to avoid Google's "Insecure browser" block on automated sessions).

---

## 📦 Step 1: Export Subscriptions via Google Takeout

1. Visit [Google Takeout](https://takeout.google.com/) while logged into your **old account** (the one with your current subscriptions).
2. Click **"Deselect all"**.
3. Scroll down to find **"YouTube and YouTube Music"** and select it.
4. Click **"All YouTube data included"**:
   - Click **"Deselect all"**.
   - Select only **"subscriptions"**.
   - Click **"OK"**.
5. Click **"Next step"**, choose delivery method / download link, and click **"Create export"**.
6. Download and extract the `.zip` archive.
7. Inside `Takeout/YouTube and YouTube Music/subscriptions/`, locate **`subscriptions.csv`**.
8. Copy `subscriptions.csv` into this script's directory.

---

## 🛠️ Step 2: Environment Setup

Open your terminal in this directory and run:

### 1. Create and activate a virtual environment (`.venv`):

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies:
```bash
pip install -r requirements.txt
```

*(Optional: only if you do not have Brave or Chrome installed and want Playwright to download bundled Chromium):*
```bash
playwright install chromium
```

---

## 💻 Step 3: Usage

### 1. Initial Test Run (1 Channel)

By default, the script runs in test mode and subscribes to **only 1 channel**:

```bash
python subscribe.py
```

**What happens:**
1. A browser window opens on YouTube.
2. If this is your first run, click **"Sign in"** and log in with your **new account**.
3. As soon as you log in, the script detects your avatar/session and notifies you in the terminal.
4. It navigates to the first channel in the CSV and clicks the subscribe button.
5. You will see a success confirmation, and the browser closes while preserving your login session.

### 2. Subscribing to All Remaining Channels

Once you've verified that the test subscription succeeded, process all remaining channels:

```bash
python subscribe.py --all
```

The script will automatically skip channels that were already processed and subscribe to the rest, pausing for 3 to 6 seconds between each channel.

---

## ⚙️ Command-Line Options

You can customize execution using flags:

| Argument | Default | Description |
|---|---|---|
| `--all` | `False` | Process **all** pending channels in the CSV. |
| `--limit N` | `1` | Process at most `N` channels in this run. |
| `--csv PATH` | `subscriptions.csv` | Custom path to the subscriptions CSV file. |
| `--delay-min SECS` | `3.0` | Minimum delay between subscriptions in seconds. |
| `--delay-max SECS` | `6.0` | Maximum delay between subscriptions in seconds. |
| `--browser TYPE` | `auto` | Preferred browser: `auto`, `brave`, `chrome`, or `chromium`. |
| `--user-data-dir PATH` | `./.browser_data` | Directory where browser session data and cookies are stored. |

### Examples:

Process 10 channels with longer safety delays:
```bash
python subscribe.py --limit 10 --delay-min 5.0 --delay-max 10.0
```

Specify a custom path to your CSV:
```bash
python subscribe.py --all --csv /path/to/my_takeout/subscriptions.csv
```

---

## 📁 Generated Files

- `.browser_data/`: Persistent browser profile directory storing your logged-in Google/YouTube session.
- `subscribed_channels.txt`: Record of channel IDs successfully processed. To reset progress, simply delete this file.

---

## ❓ FAQ & Troubleshooting

#### Google blocks login with "This browser or app may not be secure"
This error occurs when using standard unbranded automated Chromium. This script uses **Brave** or **Google Chrome** with `--disable-blink-features=AutomationControlled` to replicate a genuine user session. Ensure Brave or Google Chrome is installed on your machine.

#### What if my connection drops or I stop the script midway?
No problem! The script records every completed subscription in `subscribed_channels.txt`. Running `python subscribe.py --all` again will pick up right where it stopped without duplicating subscriptions.

#### Can I speed it up by removing delays?
Not recommended. YouTube detects unusually rapid subscription bursts and will temporarily lock the subscribe action on your account. The default 3 to 6 second pause is safe and reliable.
