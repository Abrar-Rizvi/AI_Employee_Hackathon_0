#!/usr/bin/env python3
"""
Facebook Poster - Gold Tier AI Employee
Automatically posts approved content to Facebook pages
"""

import os
import json
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Browser, Page

# Load environment variables from parent directory
ENV_PATH = Path(__file__).parent.parent / '.env'
load_dotenv(ENV_PATH)

# Configuration from environment
VAULT_PATH = Path(os.getenv('VAULT_PATH', Path(__file__).parent.parent.resolve()))
FB_EMAIL = os.getenv('FACEBOOK_EMAIL')
FB_PASSWORD = os.getenv('FACEBOOK_PASSWORD')
FB_PAGE_ID = os.getenv('FACEBOOK_PAGE_ID')
LINKEDIN_HEADLESS = os.getenv('FACEBOOK_HEADLESS', 'false').lower() == 'true'
DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'

# Directory paths
CONFIG_PATH = VAULT_PATH / 'Config'
SESSION_PATH = CONFIG_PATH / 'facebook_session'
STATE_PATH = CONFIG_PATH / 'FacebookPoster_state.json'
APPROVED_DIR = VAULT_PATH / 'Approved'
DONE_DIR = VAULT_PATH / 'Done'
LOGS_DIR = VAULT_PATH / 'Logs'

# Ensure directories exist
CONFIG_PATH.mkdir(parents=True, exist_ok=True)
SESSION_PATH.mkdir(parents=True, exist_ok=True)
APPROVED_DIR.mkdir(parents=True, exist_ok=True)
DONE_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Setup JSON logging
log_file = LOGS_DIR / f'{datetime.now().strftime("%Y-%m-%d")}.json'
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_data)


# Add JSON file handler
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(JSONFormatter())
logger.addHandler(file_handler)


class FacebookPoster:
    """
    Facebook Poster - Posts approved content to Facebook pages
    """

    def __init__(self):
        self.email = FB_EMAIL
        self.password = FB_PASSWORD
        self.page_id = FB_PAGE_ID
        self.headless = LINKEDIN_HEADLESS
        self.dry_run = DRY_RUN
        self.session_path = SESSION_PATH

        # Load state
        self.state = self._load_state()

        logger.info(f"Facebook Poster initialized - Dry Run: {self.dry_run}, Headless: {self.headless}")

    def _load_state(self) -> Dict:
        """Load processing state from file"""
        if STATE_PATH.exists():
            try:
                data = json.loads(STATE_PATH.read_text())
                logger.info(f"Loaded state with {len(data.get('processed_files', []))} processed files")
                return data
            except Exception as e:
                logger.warning(f"Could not load state file: {e}")

        return {
            'processed_files': [],
            'last_updated': datetime.utcnow().isoformat()
        }

    def _save_state(self):
        """Save current state to file"""
        self.state['last_updated'] = datetime.utcnow().isoformat()
        STATE_PATH.write_text(json.dumps(self.state, indent=2))
        logger.debug("State saved")

    def _is_file_processed(self, filename: str) -> bool:
        """Check if file has already been processed"""
        return filename in self.state.get('processed_files', [])

    def _mark_file_processed(self, filename: str):
        """Mark file as processed in state"""
        if 'processed_files' not in self.state:
            self.state['processed_files'] = []

        if filename not in self.state['processed_files']:
            self.state['processed_files'].append(filename)
            self._save_state()
            logger.info(f"Marked {filename} as processed")

    def _take_screenshot(self, page: Page, name: str):
        """Take a screenshot for debugging"""
        screenshot_path = CONFIG_PATH / f'{name}.png'
        try:
            page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info(f"Screenshot saved: {screenshot_path}")
        except Exception as e:
            logger.warning(f"Could not take screenshot: {e}")

    def _login_to_facebook(self, page: Page) -> bool:
        """
        Login to Facebook using credentials
        Returns True if login successful, False otherwise
        """
        try:
            logger.info("Navigating to Facebook login page...")
            page.goto(
                'https://www.facebook.com/login',
                wait_until='domcontentloaded',
                timeout=90000
            )
            page.wait_for_timeout(3000)

            # Check if already logged in by looking for feed or home elements
            logged_in_selectors = [
                '[aria-label="Your profile"]',
                '[data-pagelet="FeedUnit0"]',
                '[role="feed"]',
                'div[role="feed"]',
                '[data-visualcompletion="ignore-dynamic"]'
            ]

            already_logged_in = False
            for selector in logged_in_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        already_logged_in = True
                        logger.info("Already logged in to Facebook!")
                        break
                except:
                    continue

            if already_logged_in:
                return True

            # Attempt login
            logger.info("Logging in to Facebook...")

            # Wait for page to fully load
            page.wait_for_timeout(3000)

            # Try multiple selectors for email
            email_filled = False
            for selector in ['input[name="email"]', 'input[type="email"]', '#email']:
                try:
                    if page.locator(selector).count() > 0:
                        page.locator(selector).first.fill(FB_EMAIL)
                        email_filled = True
                        logger.info(f'Email filled using selector: {selector}')
                        break
                except:
                    continue

            if not email_filled:
                # Try placeholder
                try:
                    page.get_by_placeholder("Email address or mobile number").fill(FB_EMAIL)
                    email_filled = True
                except:
                    pass

            if not email_filled:
                logger.error('Email input not found')
                page.screenshot(path=str(CONFIG_PATH / 'email_not_found.png'))
                return False

            page.wait_for_timeout(1000)

            # Password - try multiple selectors
            password_filled = False
            for selector in ['input[name="pass"]', 'input[type="password"]', '#pass']:
                try:
                    if page.locator(selector).count() > 0:
                        page.locator(selector).first.fill(FB_PASSWORD)
                        password_filled = True
                        logger.info(f'Password filled using selector: {selector}')
                        break
                except:
                    continue

            if not password_filled:
                # Try placeholder
                try:
                    page.get_by_placeholder("Password").fill(FB_PASSWORD)
                    password_filled = True
                except:
                    pass

            if not password_filled:
                logger.error('Password input not found')
                page.screenshot(path=str(CONFIG_PATH / 'password_not_found.png'))
                return False

            page.wait_for_timeout(1000)

            # Login button - try multiple selectors
            login_clicked = False
            for selector in ['button[name="login"]', 'button[type="submit"]', '[data-testid="royal_login_button"]']:
                try:
                    if page.locator(selector).count() > 0:
                        page.locator(selector).first.click()
                        login_clicked = True
                        logger.info(f'Login button clicked using selector: {selector}')
                        break
                except:
                    continue

            if not login_clicked:
                # Try by role
                try:
                    page.get_by_role("button", name="Log in").click()
                    login_clicked = True
                except:
                    pass

            if not login_clicked:
                logger.error('Login button not found')
                page.screenshot(path=str(CONFIG_PATH / 'login_button_not_found.png'))
                return False

            # Wait for navigation after login (6 seconds as requested)
            logger.info("Waiting 6 seconds for login to complete...")
            page.wait_for_timeout(6000)

            # Check if login was successful
            current_url = page.url
            logger.info(f"After login URL: {current_url}")

            # Check for common login failure indicators
            error_indicators = [
                'login',
                'password',
                'incorrect',
                'invalid'
            ]

            if any(indicator in current_url.lower() for indicator in error_indicators):
                # Still on login page - login may have failed
                if 'login' in current_url.lower():
                    logger.warning("Still on login page - checking for errors...")

                    # Look for error messages
                    error_selectors = [
                        '[data-testid="error"]',
                        '.fsl',
                        '[role="alert"]'
                    ]

                    error_found = False
                    for selector in error_selectors:
                        try:
                            error_elem = page.locator(selector).first
                            if error_elem.count() > 0:
                                error_text = error_elem.inner_text()
                                if any(word in error_text.lower() for word in ['incorrect', 'invalid', 'wrong']):
                                    logger.error(f"Login failed: {error_text}")
                                    self._take_screenshot(page, 'login_failed')
                                    error_found = True
                                    break
                        except:
                            continue

                    if not error_found:
                        # Might be a 2FA or security check
                        logger.warning("Login may require additional verification")
                        self._take_screenshot(page, 'login_verification')

                return False

            logger.info("Login successful!")
            return True

        except Exception as e:
            logger.error(f"Error during login: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def _extract_post_content(self, file_path: Path) -> Optional[str]:
        """
        Extract post content from markdown file
        Looks for content after '## Post Content' header
        """
        try:
            content = file_path.read_text()
            lines = content.split('\n')

            post_content = []
            in_content_section = False

            for line in lines:
                if line.strip() == '## Post Content':
                    in_content_section = True
                    continue

                if in_content_section:
                    # Stop if we hit another header
                    if line.startswith('##'):
                        break
                    post_content.append(line)

            post_text = '\n'.join(post_content).strip()

            if not post_text:
                # If no Post Content section found, use entire content
                logger.warning(f"No '## Post Content' section found in {file_path.name}, using full content")
                post_text = content.strip()

            logger.info(f"Extracted {len(post_text)} characters from {file_path.name}")
            return post_text

        except Exception as e:
            logger.error(f"Error extracting content from {file_path}: {e}")
            return None

    def _post_to_facebook(self, page: Page, content: str) -> bool:
        """
        Post content to Facebook page
        Returns True if successful, False otherwise
        """
        try:
            if self.dry_run:
                logger.info(f"DRY RUN: Would post to Facebook: {content[:100]}...")
                return True

            # Navigate to the Facebook page as page identity
            logger.info(f"Navigating to Facebook page wall: {self.page_id}")
            page.goto(
                f'https://www.facebook.com/profile.php?id={self.page_id}&sk=wall',
                wait_until='domcontentloaded',
                timeout=90000
            )

            # Wait for page to fully load
            logger.info("Waiting 5 seconds for page to fully load...")
            page.wait_for_timeout(5000)

            # Close any popups by pressing Escape
            logger.info("Closing any popups by pressing Escape...")
            page.keyboard.press("Escape")

            # Wait 2 seconds
            logger.info("Waiting 2 seconds...")
            page.wait_for_timeout(2000)

            # Scroll down 500px
            logger.info("Scrolling down 500px...")
            page.evaluate("window.scrollBy(0, 500)")

            # Wait 3 seconds
            logger.info("Waiting 3 seconds...")
            page.wait_for_timeout(3000)

            # Click Switch Now if present
            try:
                page.wait_for_timeout(2000)
                all_buttons = page.locator('div[role="button"]').all()
                for btn in all_buttons:
                    txt = btn.inner_text()
                    if "Switch Now" in txt:
                        btn.click()
                        logger.info("Switch Now clicked!")
                        page.wait_for_timeout(4000)
                        break
            except Exception as e:
                logger.warning(f"Switch: {e}")

            # Take screenshot to verify current state
            page.screenshot(path=str(CONFIG_PATH / "before_post_box.png"))

            # Look for the post creation box/button
            logger.info("Looking for post creation box...")

            # Try multiple selectors for the "What's on your mind?" button/box
            post_box_found = False

            # Try each selector in order
            selectors_to_try = [
                ('page.get_by_placeholder("What\'s on your mind?")', lambda: page.get_by_placeholder("What's on your mind?")),
                ('page.locator("[aria-label=\'What\'s on your mind?\']")', lambda: page.locator('[aria-label="What\'s on your mind?"]')),
                ('page.get_by_role("button", name="What\'s on your mind?")', lambda: page.get_by_role("button", name="What's on your mind?")),
                ('page.locator("div[contenteditable=\\"true\\"]").first', lambda: page.locator('div[contenteditable="true"]').first),
            ]

            for selector_name, selector_func in selectors_to_try:
                try:
                    if selector_func().count() > 0:
                        logger.info(f"Found post box with selector: {selector_name}")
                        element = selector_func().first

                        # Try multiple click methods
                        click_success = False

                        # Method 1: Direct click
                        try:
                            logger.debug("Trying method 1: Direct element.click()")
                            element.click()
                            click_success = True
                            logger.info("Click successful with method 1: Direct click")
                        except Exception as e1:
                            logger.debug(f"Method 1 failed: {e1}")

                            # Method 2: JavaScript click
                            try:
                                logger.debug("Trying method 2: JavaScript click")
                                page.evaluate("arguments[0].click()", element)
                                click_success = True
                                logger.info("Click successful with method 2: JavaScript click")
                            except Exception as e2:
                                logger.debug(f"Method 2 failed: {e2}")

                                # Method 3: Click coordinates
                                try:
                                    logger.debug("Trying method 3: Click coordinates")
                                    box = element.bounding_box()
                                    if box:
                                        x = box['x'] + box['width'] / 2
                                        y = box['y'] + box['height'] / 2
                                        page.mouse.click(x, y)
                                        click_success = True
                                        logger.info(f"Click successful with method 3: Coordinates ({x}, {y})")
                                except Exception as e3:
                                    logger.debug(f"Method 3 failed: {e3}")

                        if not click_success:
                            logger.error("All click methods failed for this selector")
                            continue

                        # Wait after clicking
                        page.wait_for_timeout(3000)

                        # Take screenshot after clicking
                        screenshot_path = CONFIG_PATH / 'after_click.png'
                        page.screenshot(path=str(screenshot_path), full_page=True)
                        logger.info(f"Screenshot saved after click: {screenshot_path}")

                        post_box_found = True
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector_name} failed: {e}")
                    continue

            if not post_box_found:
                logger.error("Could not find or click post creation box")
                self._take_screenshot(page, 'post_box_not_found')
                return False

            # Type the content using keyboard
            logger.info("Typing post content using keyboard...")
            page.keyboard.type(content)
            logger.info(f"Content typed ({len(content)} characters)")

            page.wait_for_timeout(2000)

            # Press Escape to close "Add to your post" sub-menu (keeps main composer open)
            logger.info("Pressing Escape to close 'Add to your post' sub-menu...")
            page.keyboard.press("Escape")
            page.wait_for_timeout(2000)

            # Take screenshot after pressing Escape
            screenshot_path = CONFIG_PATH / 'after_escape.png'
            page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info(f"Screenshot saved: {screenshot_path}")

            # Click Next button (Facebook Pages require Next before Post)
            logger.info("Looking for Next button...")
            next_button = page.get_by_role("button", name="Next")
            if next_button.count() > 0:
                next_button.click()
                logger.info("Next button clicked!")
                page.wait_for_timeout(3000)

                # Take screenshot after clicking Next
                screenshot_path = CONFIG_PATH / 'after_next.png'
                page.screenshot(path=str(screenshot_path), full_page=True)
                logger.info(f"Screenshot saved: {screenshot_path}")
            else:
                logger.warning("Next button not found - proceeding directly to Post button")

            # Click Post button
            logger.info("Looking for Post button...")
            try:
                page.get_by_role("button", name="Post", exact=True).last.click()
                logger.info("Post button clicked!")
                page.wait_for_timeout(5000)
            except Exception as e:
                logger.error(f"Could not find or click Post button: {e}")
                page.screenshot(path=str(CONFIG_PATH / 'post_button_not_found.png'))
                return False

            # Wait for post to complete
            logger.info("Waiting for post to complete...")
            page.wait_for_timeout(8000)

            # Take screenshot after posting
            logger.info("Taking screenshot after posting...")
            screenshot_path = CONFIG_PATH / 'after_post.png'
            page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info(f"Screenshot saved: {screenshot_path}")

            # Log current URL after posting
            current_url = page.url
            logger.info(f"Current URL after posting: {current_url}")

            # Check for success/error messages
            success_indicators = ['post successful', 'your post has been published', 'published']
            error_indicators = ['error', 'failed', 'couldn\'t', 'cannot', 'unable', 'something went wrong']

            page_text = page.inner_text('body').lower()

            if any(indicator in page_text for indicator in error_indicators):
                logger.error("Post may have failed - detected error message on page")
                self._take_screenshot(page, 'post_error')
                return False

            if any(indicator in page_text for indicator in success_indicators):
                logger.info("Post successful - confirmed with success message!")
                return True

            # If no clear success/error indicator, check if URL changed (redirect to post)
            logger.info("No explicit success/error message found")
            logger.info(f"Checking if URL indicates successful post (URL: {current_url})")

            # If URL contains post-related patterns, consider it successful
            if any(pattern in current_url.lower() for pattern in ['posts', 'story', 'permalink']):
                logger.info("Post successful - URL indicates post was created!")
                return True

            # If no clear indicator, assume success
            logger.info("Post completed (no explicit confirmation, assuming success)")
            return True

        except Exception as e:
            logger.error(f"Error posting to Facebook: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def check_approved_folder(self) -> List[Path]:
        """
        Check for approved FB posts
        Returns list of files to process
        """
        try:
            approved_files = list(APPROVED_DIR.glob('FB_*.md'))

            # Filter out already processed files
            new_files = [
                f for f in approved_files
                if not self._is_file_processed(f.name)
            ]

            logger.info(f"Found {len(new_files)} new approved posts (total: {len(approved_files)})")
            return new_files

        except Exception as e:
            logger.error(f"Error checking approved folder: {e}")
            return []

    def process_file(self, file_path: Path) -> bool:
        """
        Process a single approved post file
        Returns True if successful, False otherwise
        """
        try:
            logger.info(f"Processing file: {file_path.name}")

            # Extract post content
            content = self._extract_post_content(file_path)
            if not content:
                logger.error(f"Could not extract content from {file_path.name}")
                return False

            # Post to Facebook
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    str(self.session_path),
                    headless=self.headless,
                    args=['--no-sandbox', '--disable-setuid-sandbox'],
                    viewport={'width': 1280, 'height': 800}
                )

                # Get or create page
                if len(browser.pages) > 0:
                    page = browser.pages[0]
                else:
                    page = browser.new_page()

                try:
                    # Login if needed
                    if not self._login_to_facebook(page):
                        logger.error("Login failed, cannot post")
                        browser.close()
                        return False

                    # Post content
                    if self._post_to_facebook(page, content):
                        logger.info(f"Successfully posted {file_path.name}")

                        # Move to Done folder
                        done_path = DONE_DIR / file_path.name
                        shutil.move(str(file_path), str(done_path))
                        logger.info(f"Moved {file_path.name} to Done folder")

                        # Mark as processed
                        self._mark_file_processed(file_path.name)

                        browser.close()
                        return True
                    else:
                        logger.error(f"Failed to post {file_path.name}")
                        browser.close()
                        return False

                except Exception as e:
                    logger.error(f"Error during posting: {e}")
                    self._take_screenshot(page, 'posting_error')
                    browser.close()
                    return False

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def run_once(self):
        """Run one iteration of checking and posting"""
        logger.info("=" * 60)
        logger.info("Facebook Poster - Starting check")

        if self.dry_run:
            logger.info("DRY RUN MODE - No actual posts will be made")

        try:
            # Check for new approved posts
            approved_files = self.check_approved_folder()

            if not approved_files:
                logger.info("No new approved posts to process")
                return

            # Process each file
            for file_path in approved_files:
                try:
                    self.process_file(file_path)
                except Exception as e:
                    logger.error(f"Failed to process {file_path.name}: {e}")
                    continue

            logger.info("Facebook Poster - Check complete")

        except Exception as e:
            logger.error(f"Error in run_once: {e}")
            import traceback
            logger.error(traceback.format_exc())

        logger.info("=" * 60)

    def run(self, interval_minutes: int = 5):
        """
        Continuous run loop
        Checks for new posts every interval_minutes
        """
        logger.info(f"Starting continuous run (checking every {interval_minutes} minutes)")
        logger.info("Press Ctrl+C to stop")

        try:
            while True:
                self.run_once()

                logger.info(f"Sleeping for {interval_minutes} minutes...")
                import time
                time.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            logger.info("Stopped by user")
        except Exception as e:
            logger.error(f"Error in continuous run: {e}")
            import traceback
            logger.error(traceback.format_exc())


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Facebook Poster - Gold Tier AI Employee')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--interval', type=int, default=5, help='Check interval in minutes (default: 5)')
    parser.add_argument('--dry-run', action='store_true', help='Enable dry run mode (no actual posts)')

    args = parser.parse_args()

    # Override dry run if specified
    global DRY_RUN
    if args.dry_run:
        DRY_RUN = True

    # Create poster instance
    poster = FacebookPoster()

    if args.once:
        poster.run_once()
    else:
        poster.run(interval_minutes=args.interval)


if __name__ == '__main__':
    main()
