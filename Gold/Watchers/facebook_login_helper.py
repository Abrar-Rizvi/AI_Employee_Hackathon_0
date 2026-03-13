#!/usr/bin/env python3
"""
Facebook Login Helper - Gold Tier AI Employee
Manually login to Facebook to save session for automated posting
This handles 2FA, CAPTCHA, and other verification challenges
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load environment variables from parent directory
ENV_PATH = Path(__file__).parent.parent / '.env'
load_dotenv(ENV_PATH)

# Configuration from environment
VAULT_PATH = Path(os.getenv('VAULT_PATH', Path(__file__).parent.parent.resolve()))
SESSION_PATH = VAULT_PATH / 'Config' / 'facebook_session'

# Ensure session directory exists
SESSION_PATH.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("Facebook Login Helper")
print("=" * 60)
print(f"Session will be saved to: {SESSION_PATH}")
print()

with sync_playwright() as p:
    print("Launching browser (headless=False)...")
    browser = p.chromium.launch_persistent_context(
        str(SESSION_PATH),
        headless=False,
        viewport={'width': 1280, 'height': 800}
    )

    # Create new page
    page = browser.new_page()

    print("Navigating to Facebook login page...")
    page.goto('https://www.facebook.com/login')

    print()
    print("PLEASE COMPLETE YOUR LOGIN MANUALLY")
    print("- Handle any 2FA, CAPTCHA, or security checks")
    print("- Make sure you reach your Facebook feed/home page")
    print()
    print(f"Waiting 60 seconds for you to login...")

    # Wait for user to complete login
    import time
    for i in range(60, 0, -10):
        remaining = i if i < 60 else 60
        print(f"  {remaining} seconds remaining...")
        time.sleep(10)

    print()
    print("Session saved! You can now run facebook_poster.py")
    print("=" * 60)

    browser.close()

print("Login helper complete!")
