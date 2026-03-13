#!/usr/bin/env python3
"""
Instagram Poster - Gold Tier AI Employee
Automatically posts approved content to Instagram via Meta Business Suite
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
INSTAGRAM_HEADLESS = os.getenv('INSTAGRAM_HEADLESS', 'false').lower() == 'true'
DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'

# Directory paths
CONFIG_PATH = VAULT_PATH / 'Config'
SESSION_PATH = CONFIG_PATH / 'facebook_session'
STATE_PATH = CONFIG_PATH / 'InstagramPoster_state.json'
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


class InstagramPoster:
    """
    Instagram Poster - Posts approved content to Instagram via Meta Business Suite
    """

    def __init__(self):
        self.email = FB_EMAIL
        self.password = FB_PASSWORD
        self.headless = INSTAGRAM_HEADLESS
        self.dry_run = DRY_RUN
        self.session_path = SESSION_PATH

        # Load state
        self.state = self._load_state()

        logger.info(f"Instagram Poster initialized - Dry Run: {self.dry_run}, Headless: {self.headless}")

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

    def _extract_post_content(self, file_path: Path) -> tuple[Optional[str], Optional[Path]]:
        """
        Extract post content and image path from markdown file
        Looks for content after '## Post Content' header
        Also looks for 'image: /path/to/image.jpg' line
        Returns tuple of (content, image_path)
        """
        try:
            content = file_path.read_text()
            lines = content.split('\n')

            post_content = []
            in_content_section = False
            image_path = None

            for line in lines:
                # Check for image path
                if line.strip().lower().startswith('image:') or line.strip().lower().startswith('image :'):
                    # Extract the path after "image:" or "image :"
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        img_path = parts[1].strip()
                        # Resolve relative paths relative to the file location
                        img_path_obj = Path(img_path)
                        if not img_path_obj.is_absolute():
                            # If relative, resolve from the file's directory
                            img_path_obj = file_path.parent / img_path_obj
                        if img_path_obj.exists():
                            image_path = img_path_obj
                            logger.info(f"Found image: {image_path}")
                        continue

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
            return post_text, image_path

        except Exception as e:
            logger.error(f"Error extracting content from {file_path}: {e}")
            return None, None

    def _post_to_instagram(self, page: Page, content: str, image_path: Optional[Path] = None) -> bool:
        """
        Post content to Instagram via Meta Business Suite
        Returns True if successful, False otherwise
        """
        try:
            if self.dry_run:
                logger.info(f"DRY RUN: Would post to Instagram: {content[:100]}...")
                return True

            # Navigate to Meta Business Suite composer
            logger.info("Navigating to Meta Business Suite composer...")
            page.goto(
                'https://business.facebook.com/latest/composer/',
                wait_until='domcontentloaded',
                timeout=90000
            )

            # Wait for page to fully load
            logger.info("Waiting for Meta Business Suite to load...")
            page.wait_for_timeout(5000)

            # Take screenshot to verify current state
            page.screenshot(path=str(CONFIG_PATH / "composer_loaded.png"))
            logger.info("Screenshot saved: composer_loaded.png")

            # Close any popup
            logger.info("Closing popup...")
            popup_closed = False

            # First try clicking the X button on popup
            try:
                close_button = page.locator('div[aria-label="Close"]')
                if close_button.count() > 0:
                    logger.info("Found X close button - clicking to close popup")
                    close_button.first.click()
                    popup_closed = True
            except Exception as e:
                logger.debug(f"X button not found: {e}")

            # If not found, try Escape key
            if not popup_closed:
                try:
                    logger.info("Trying Escape key to close popup")
                    page.keyboard.press("Escape")
                    popup_closed = True
                except Exception as e:
                    logger.debug(f"Escape key failed: {e}")

            # Wait after closing popup
            page.wait_for_timeout(3000)

            # Take screenshot after closing popup
            page.screenshot(path=str(CONFIG_PATH / "after_popup_close.png"))
            logger.info("Screenshot saved: after_popup_close.png")

            # Upload image
            logger.info("Uploading image...")
            try:
                page.keyboard.press("Escape")
                page.wait_for_timeout(2000)

                # Click Add photo dropdown
                page.locator('[role="button"]:has-text("Add photo")').first.click(timeout=5000)
                page.wait_for_timeout(2000)

                # Click "Upload from desktop" with file chooser
                with page.expect_file_chooser(timeout=10000) as fc_info:
                    page.locator('text=Upload from desktop').first.click(timeout=5000)

                fc_info.value.set_files("/mnt/d/AI_Employee_Hackathon_0/Gold/Config/ig_default_image.png")
                logger.info("Image uploaded via Upload from desktop!")
                page.wait_for_timeout(5000)
                page.screenshot(path=str(VAULT_PATH / "Config" / "after_image_upload.png"))
            except Exception as e:
                logger.warning(f"Image upload failed: {e}")
                page.screenshot(path=str(VAULT_PATH / "Config" / "upload_debug.png"))

            # Find text input
            logger.info("Looking for text input...")
            try:
                text_input = page.locator('div[contenteditable="true"]').last
                if text_input.count() > 0:
                    logger.info("Found text input")
                    text_input.click()
                    page.wait_for_timeout(1000)
                    # Use keyboard.type() for emoji support
                    page.keyboard.type(content)
                    logger.info(f"Content typed ({len(content)} characters)")
                else:
                    logger.error("Could not find text input")
                    self._take_screenshot(page, 'text_input_not_found')
                    return False
            except Exception as e:
                logger.error(f"Error finding or filling text input: {e}")
                self._take_screenshot(page, 'text_input_error')
                return False

            # Click Publish button
            logger.info("Looking for Publish button...")
            try:
                page.get_by_role("button", name="Publish").click()
                logger.info("Publish button clicked!")
                page.wait_for_timeout(5000)
            except Exception as e:
                logger.error(f"Could not find or click Publish button: {e}")
                self._take_screenshot(page, 'publish_button_not_found')
                return False

            # Take screenshot after publishing
            page.screenshot(path=str(CONFIG_PATH / "after_publish.png"))
            logger.info("Screenshot saved: after_publish.png")

            # Log current URL after posting
            current_url = page.url
            logger.info(f"Current URL after posting: {current_url}")

            # Check for success/error messages
            success_indicators = ['published', 'successfully posted', 'post created']
            error_indicators = ['error', 'failed', 'couldn\'t', 'cannot', 'unable', 'something went wrong']

            page_text = page.inner_text('body').lower()

            if any(indicator in page_text for indicator in error_indicators):
                logger.error("Post may have failed - detected error message on page")
                self._take_screenshot(page, 'post_error')
                return False

            if any(indicator in page_text for indicator in success_indicators):
                logger.info("Post successful - confirmed with success message!")
                return True

            # If no clear indicator, assume success
            logger.info("Post completed (no explicit confirmation, assuming success)")
            return True

        except Exception as e:
            logger.error(f"Error posting to Instagram: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def check_approved_folder(self) -> List[Path]:
        """
        Check for approved IG posts
        Returns list of files to process
        """
        try:
            approved_files = list(APPROVED_DIR.glob('IG_*.md'))

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

            # Extract post content and image path
            content, image_path = self._extract_post_content(file_path)
            if not content:
                logger.error(f"Could not extract content from {file_path.name}")
                return False

            # Post to Instagram
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

                    # Post content with image
                    if self._post_to_instagram(page, content, image_path):
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
        logger.info("Instagram Poster - Starting check")

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

            logger.info("Instagram Poster - Check complete")

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

    parser = argparse.ArgumentParser(description='Instagram Poster - Gold Tier AI Employee')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--interval', type=int, default=5, help='Check interval in minutes (default: 5)')
    parser.add_argument('--dry-run', action='store_true', help='Enable dry run mode (no actual posts)')

    args = parser.parse_args()

    # Override dry run if specified
    global DRY_RUN
    if args.dry_run:
        DRY_RUN = True

    # Create poster instance
    poster = InstagramPoster()

    if args.once:
        poster.run_once()
    else:
        poster.run(interval_minutes=args.interval)


if __name__ == '__main__':
    main()
