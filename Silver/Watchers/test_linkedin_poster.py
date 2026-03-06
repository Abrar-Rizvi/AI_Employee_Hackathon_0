#!/usr/bin/env python3
"""
Test helper for LinkedIn Poster
Run this to test the LinkedIn automation in dry-run mode.
"""

import sys
from pathlib import Path

# Add Watchers directory to path
watchers_dir = Path(__file__).parent
sys.path.insert(0, str(watchers_dir))

from linkedin_poster import LinkedInPoster


def test_login():
    """Test LinkedIn login only."""
    print("=" * 60)
    print("Testing LinkedIn Login")
    print("=" * 60)

    poster = LinkedInPoster()

    # Check if session exists
    if poster._has_session():
        print("✓ Existing session found")
    else:
        print("✗ No session found - will login (browser will open)")

    # Test login
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

    with sync_playwright() as p:
        headless = poster._has_session() and poster.headless

        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(poster.session_path),
            headless=headless,
            args=['--disable-blink-features=AutomationControlled'],
            ignore_https_errors=True,
            viewport={'width': 1920, 'height': 1080}
        )

        try:
            if len(browser.pages) > 0:
                page = browser.pages[0]
            else:
                page = browser.new_page()

            page.set_default_timeout(60000)

            # Login if needed
            if not poster._has_session():
                print("\n🔐 Logging in to LinkedIn...")
                print("   Browser will open - complete login manually if prompted")
                success = poster._login(page)

                if success:
                    print("✓ Login successful!")
                    poster._save_session(browser)
                else:
                    print("✗ Login failed")
                    browser.close()
                    return False
            else:
                print("\n✓ Using existing session")
                poster._load_session(browser)

            # Test navigation to feed
            print("\n🌐 Navigating to feed...")
            page.goto(
                poster.feed_url,
                wait_until="domcontentloaded",
                timeout=90000
            )

            print(f"✓ Successfully loaded feed: {page.url[:50]}...")

            # Check for security verification
            if poster._check_for_security_verification(page):
                print("\n⚠️  Security verification required!")
                print("   Please complete it in the browser window")
                input("Press Enter after completing verification...")
                poster._save_session(browser)

            print("\n✓ Login test PASSED")
            return True

        except Exception as e:
            print(f"\n✗ Error: {e}")
            return False

        finally:
            input("\nPress Enter to close browser...")
            browser.close()


def test_folder_check():
    """Test folder checking."""
    print("\n" + "=" * 60)
    print("Testing Folder Structure")
    print("=" * 60)

    poster = LinkedInPoster()

    print(f"\n✓ Vault path: {poster.vault_path}")
    print(f"✓ Approved folder: {poster.approved_path}")
    print(f"✓ Done folder: {poster.done_path}")
    print(f"✓ Session folder: {poster.session_path}")
    print(f"✓ Logs folder: {poster.logs_path}")

    # Check for approved posts
    approved_files = poster.check_approved_folder()

    print(f"\n📋 Approved LinkedIn posts: {len(approved_files)}")
    for f in approved_files:
        print(f"   - {f.name}")

    if len(approved_files) == 0:
        print("\n💡 No approved posts found.")
        print("   To create a test post:")
        print("   1. Create a .md file in Pending_Approval/")
        print("   2. Add frontmatter: type: linkedin_post")
        print("   3. Move it to Approved/")
        print("   4. Run this script again")

    return len(approved_files) > 0


def test_dry_run():
    """Test posting in dry-run mode."""
    print("\n" + "=" * 60)
    print("Testing Dry-Run Post")
    print("=" * 60)

    poster = LinkedInPoster()
    poster.dry_run = True  # Force dry run

    # Check for approved posts
    approved_files = poster.check_approved_folder()

    if not approved_files:
        print("\n✗ No approved posts found. Create one first.")
        return False

    print(f"\n📋 Found {len(approved_files)} approved post(s)")

    # Process first file
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        headless = poster._has_session() and poster.headless

        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(poster.session_path),
            headless=headless,
            args=['--disable-blink-features=AutomationControlled'],
            ignore_https_errors=True,
            viewport={'width': 1920, 'height': 1080}
        )

        try:
            if len(browser.pages) > 0:
                page = browser.pages[0]
            else:
                page = browser.new_page()

            page.set_default_timeout(60000)

            # Login if needed
            if not poster._has_session():
                print("\n🔐 Logging in...")
                if not poster._login(page):
                    print("✗ Login failed")
                    return False
                poster._save_session(browser)
            else:
                poster._load_session(browser)

            # Navigate to feed
            page.goto(poster.feed_url, wait_until="domcontentloaded", timeout=90000)

            # Process file
            file_path = approved_files[0]
            print(f"\n📝 Processing: {file_path.name}")

            result = poster.process_file(file_path, page)

            if result['status'] == 'dry_run':
                print("✓ Dry-run successful!")
                print(f"  File: {result['file_name']}")
                print(f"  Preview: {result.get('content_preview', '')[:100]}...")
                return True
            else:
                print(f"✗ Failed: {result.get('error', 'Unknown error')}")
                return False

        finally:
            browser.close()


def main():
    """Main test runner."""
    print("\n🔧 LinkedIn Poster Test Helper")
    print("=" * 60)

    import argparse

    parser = argparse.ArgumentParser(description="Test LinkedIn Poster")
    parser.add_argument(
        '--test',
        choices=['login', 'folder', 'dry-run', 'all'],
        default='all',
        help='Which test to run'
    )

    args = parser.parse_args()

    results = []

    if args.test in ['login', 'all']:
        results.append(('Login', test_login()))

    if args.test in ['folder', 'all']:
        results.append(('Folder Check', test_folder_check()))

    if args.test in ['dry-run', 'all']:
        # Only run dry-run if we have approved posts
        if args.test == 'all':
            poster = LinkedInPoster()
            if poster.check_approved_folder():
                results.append(('Dry-Run', test_dry_run()))
        else:
            results.append(('Dry-Run', test_dry_run()))

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
