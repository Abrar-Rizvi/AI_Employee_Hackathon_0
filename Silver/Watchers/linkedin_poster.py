#!/usr/bin/env python3
"""
LinkedIn Poster for Silver Tier AI Employee
Watches Approved/ folder for LinkedIn posts and publishes them using Playwright.
"""

import os
import json
import time
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv not found. Install with: pip install python-dotenv")
    raise

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Error: playwright not found. Install with: pip install playwright && playwright install chromium")
    raise


class LinkedInPoster:
    """Post content to LinkedIn using Playwright automation."""

    def __init__(self, vault_path: str = None):
        # Set vault path
        self.vault_path = Path(vault_path or os.getenv('VAULT_PATH', '/mnt/d/AI_Employee_Hackathon_0/Silver'))

        # Load environment variables from .env in vault folder FIRST
        env_file = self.vault_path / '.env'
        if env_file.exists():
            load_dotenv(dotenv_path=env_file)
            self._env_loaded = True
        else:
            load_dotenv()  # Fallback to default locations
            self._env_loaded = False

        # Paths
        self.config_path = self.vault_path / "Config"
        self.logs_path = self.vault_path / "Logs"
        self.approved_path = self.vault_path / "Approved"
        self.done_path = self.vault_path / "Done"
        self.session_path = self.config_path / "linkedin_session"

        # Settings (AFTER loading .env)
        self.dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
        self.linkedin_email = os.getenv('LINKEDIN_EMAIL', '')
        self.linkedin_password = os.getenv('LINKEDIN_PASSWORD', '')
        self.headless = os.getenv('LINKEDIN_HEADLESS', 'true').lower() == 'true'

        # LinkedIn URLs
        self.linkedin_url = "https://www.linkedin.com"
        self.login_url = "https://www.linkedin.com/login"
        self.feed_url = "https://www.linkedin.com/feed/"

        # State tracking
        self.processed_files = set()
        self.state_file = self.config_path / "LinkedInPoster_state.json"

        # Setup logging
        self._setup_logging()

        # Ensure folders exist
        self._ensure_folders()

        # Log paths for debugging
        self.logger.info(f"=" * 60)
        self.logger.info(f"LinkedIn Poster Initialized")
        self.logger.info(f"=" * 60)
        self.logger.info(f"Vault path: {self.vault_path.absolute()}")
        self.logger.info(f"Approved path: {self.approved_path.absolute()}")
        self.logger.info(f"Done path: {self.done_path.absolute()}")
        self.logger.info(f"Config path: {self.config_path.absolute()}")
        self.logger.info(f"Logs path: {self.logs_path.absolute()}")
        self.logger.info(f"Session path: {self.session_path.absolute()}")
        self.logger.info(f"DRY_RUN: {self.dry_run}")
        self.logger.info(f"=" * 60)

        # Load state
        self._load_state()

    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.vault_path / 'Logs' / 'watcher.log')
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def _ensure_folders(self):
        """Ensure all required folders exist."""
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)
        self.approved_path.mkdir(parents=True, exist_ok=True)
        self.done_path.mkdir(parents=True, exist_ok=True)
        self.session_path.mkdir(parents=True, exist_ok=True)

    def _load_state(self):
        """Load previous state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.processed_files = set(state.get('processed_files', []))
                self.logger.info(f"Loaded state with {len(self.processed_files)} processed files")
            except Exception as e:
                self.logger.warning(f"Failed to load state: {e}")

    def _save_state(self):
        """Save current state to file."""
        try:
            state = {
                'processed_files': list(self.processed_files),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")

    def _log_activity(self, action: str, details: Dict = None):
        """Log activity to daily JSON log file."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "watcher": self.__class__.__name__,
            "action": action,
            "dry_run": self.dry_run
        }

        if details:
            log_entry.update(details)

        # Get daily log file
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_path / f"{today}.json"

        try:
            # Read existing logs
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []

            # Append new log
            logs.append(log_entry)

            # Write back
            if not self.dry_run:
                with open(log_file, 'w') as f:
                    json.dump(logs, f, indent=2)

            self.logger.info(f"Logged: {action}")

        except Exception as e:
            self.logger.error(f"Failed to log activity: {e}")

    def _has_session(self) -> bool:
        """Check if a valid session exists."""
        # Check if cookies.json exists in session folder
        cookies_file = self.session_path / "cookies.json"
        return cookies_file.exists()

    def _save_session(self, context):
        """Save session cookies for future use."""
        try:
            cookies = context.cookies()
            cookies_file = self.session_path / "cookies.json"

            with open(cookies_file, 'w') as f:
                json.dump(cookies, f, indent=2)

            self.logger.info("Session saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save session: {e}")

    def _load_session(self, context) -> bool:
        """Load session cookies from file."""
        try:
            cookies_file = self.session_path / "cookies.json"

            if not cookies_file.exists():
                return False

            with open(cookies_file, 'r') as f:
                cookies = json.load(f)

            context.add_cookies(cookies)
            self.logger.info("Session loaded successfully")
            return True

        except Exception as e:
            self.logger.warning(f"Failed to load session: {e}")
            return False

    def _login(self, page) -> bool:
        """Login to LinkedIn with smart login detection."""
        screenshot_path = self.logs_path / "login_debug.png"

        try:
            # Set default timeout for all page operations
            page.set_default_timeout(60000)

            self.logger.info("Navigating to LinkedIn login page...")

            # Navigate with domcontentloaded wait
            page.goto(
                self.login_url,
                wait_until="domcontentloaded",
                timeout=90000
            )

            # Wait for page to stabilize
            page.wait_for_timeout(3000)

            self.logger.info("Page loaded, checking login status...")

            # First check if already logged in by looking for feed elements
            logged_in_selectors = [
                "div.feed-identity-module",
                "div[data-control-name='identity_welcome_message']",
                "[data-control-name='nav_logo']",
                ".global-nav__logo",
                ".feed-shared-update-v2",  # Post in feed
                "div.scaffold-finite-scroll__content"  # Feed content
            ]

            already_logged_in = False
            for selector in logged_in_selectors:
                try:
                    element = page.wait_for_selector(selector, timeout=5000)
                    if element:
                        self.logger.info(f"✓ Already logged in - found: {selector}")
                        already_logged_in = True
                        break
                except:
                    continue

            # Check URL as well
            current_url = page.url
            self.logger.info(f"Current URL: {current_url}")

            if "feed" in current_url.lower() or already_logged_in:
                self.logger.info("✓ User is already logged in!")

                # Double-check by verifying we're not on login page
                has_login_form = False
                try:
                    page.wait_for_selector('input[name="session_key"]', timeout=2000)
                    has_login_form = True
                except:
                    pass

                if has_login_form:
                    self.logger.info("Login form found - proceeding with login")
                else:
                    self.logger.info("No login form - already authenticated")
                    return True

            # If we reach here, need to perform login
            self.logger.info("Login required - filling credentials...")

            # Wait for email input with explicit timeout
            try:
                page.wait_for_selector('input[name="session_key"]', timeout=10000)
                self.logger.info("✓ Email input found")
            except PlaywrightTimeout:
                # Might already be logged in, try to verify
                self.logger.warning("Email input not found, checking if already logged in...")
                if already_logged_in or "feed" in current_url.lower():
                    self.logger.info("✓ Appears to be logged in (no login form)")
                    return True

                self.logger.error("✗ Email input not found within timeout")
                page.screenshot(path=str(screenshot_path))
                self.logger.error(f"Screenshot saved to {screenshot_path}")
                return False

            # Wait for password input
            try:
                page.wait_for_selector('input[name="session_password"]', timeout=10000)
                self.logger.info("✓ Password input found")
            except PlaywrightTimeout:
                self.logger.error("✗ Password input not found within timeout")
                page.screenshot(path=str(screenshot_path))
                self.logger.error(f"Screenshot saved to {screenshot_path}")
                return False

            # Fill email
            self.logger.info("Filling email...")
            page.fill('input[name="session_key"]', self.linkedin_email)
            time.sleep(0.5)

            # Fill password
            self.logger.info("Filling password...")
            page.fill('input[name="session_password"]', self.linkedin_password)
            time.sleep(0.5)

            # Click sign in button
            self.logger.info("Clicking sign in button...")
            page.click('button[type="submit"]')

            # Wait for navigation to complete
            self.logger.info("Waiting for navigation after login...")

            # Wait for page to stabilize
            page.wait_for_timeout(3000)

            # Additional wait for URL change
            page.wait_for_url(
                re.compile(r".*linkedin\.com.*"),
                timeout=30000
            )

            # Check current URL
            current_url = page.url
            self.logger.info(f"After login, current URL: {current_url}")

            # Check if login was successful
            if "feed" in current_url or "checkpoint" not in current_url:
                # Verify we're actually logged in by checking for feed elements
                try:
                    # Look for a common feed element to confirm login
                    page.wait_for_selector('[data-control-name="nav_logo"], .global-nav__logo', timeout=10000)
                    self.logger.info("✓ Login successful - feed elements detected!")
                    return True
                except PlaywrightTimeout:
                    # We might be on a different page but still logged in
                    if "checkpoint" not in current_url:
                        self.logger.info("✓ Login appears successful (no checkpoint)")
                        return True
                    else:
                        self.logger.error("✗ Redirected to checkpoint page")
                        page.screenshot(path=str(screenshot_path))
                        self.logger.error(f"Screenshot saved to {screenshot_path}")
                        return False
            else:
                self.logger.error("✗ Login may have failed - unexpected URL")
                page.screenshot(path=str(screenshot_path))
                self.logger.error(f"Screenshot saved to {screenshot_path}")
                return False

        except PlaywrightTimeout as e:
            self.logger.error(f"Login timeout: {str(e)}")
            try:
                page.screenshot(path=str(screenshot_path))
                self.logger.error(f"Screenshot saved to {screenshot_path}")
            except:
                pass
            return False
        except Exception as e:
            self.logger.error(f"Login error: {str(e)}")
            try:
                page.screenshot(path=str(screenshot_path))
                self.logger.error(f"Screenshot saved to {screenshot_path}")
            except:
                pass
            return False

    def _extract_post_content(self, file_path: Path) -> Dict[str, Any]:
        """Extract post content from markdown file."""
        try:
            content = file_path.read_text()

            # Parse frontmatter
            frontmatter = {}
            body = content

            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    # Parse YAML frontmatter
                    frontmatter_text = parts[1]
                    body = parts[2].strip()

                    for line in frontmatter_text.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            frontmatter[key.strip()] = value.strip()

            return {
                'status': 'success',
                'frontmatter': frontmatter,
                'body': body,
                'file_path': file_path,
                'file_name': file_path.name
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'file_path': file_path
            }

    def _check_for_security_verification(self, page) -> bool:
        """Check if LinkedIn is asking for security verification."""
        try:
            # Check for common security verification elements
            if page.query_selector('[data-tracking-client-name="emailVerification"]'):
                return True
            if page.query_selector('input[name="pin"]'):
                return True
            if "checkpoint" in page.url.lower():
                return True
            return False
        except:
            return False

    def _post_to_linkedin(self, post_content: str, page) -> Dict[str, Any]:
        """Post content to LinkedIn with improved timeout handling."""
        screenshot_path = self.logs_path / "post_debug.png"

        try:
            self.logger.info("Navigating to LinkedIn feed...")
            page.goto(
                self.feed_url,
                wait_until="domcontentloaded",
                timeout=90000
            )

            # Wait for page to stabilize
            page.wait_for_timeout(3000)

            # Wait before looking for post button
            self.logger.info("Waiting for page to fully load...")
            page.wait_for_timeout(2000)

            # Wait for the post box button
            self.logger.info("Looking for 'Start a post' button...")

            post_clicked = False

            # Try Playwright's get_by_text first (most reliable)
            try:
                self.logger.info("Trying: get_by_text('Start a post')")
                post_button = page.get_by_text("Start a post", exact=True)
                if post_button:
                    post_button.click(timeout=10000)
                    self.logger.info("✅ Found and clicked using get_by_text()")
                    post_clicked = True
                    time.sleep(2)
            except Exception as e:
                self.logger.info(f"get_by_text failed: {e}")

            # If get_by_text didn't work, try CSS selectors
            if not post_clicked:
                # Updated selector strategies in priority order
                selectors_to_try = [
                    'button:has-text("Start a post")',
                    'div[role="button"]:has-text("Start a post")',
                    'span:has-text("Start a post")',
                    '.share-box-feed-entry__trigger',
                    'div.share-box-feed-entry__trigger',
                    '[data-control-name="share_box"]',
                    '#share-box-trigger'
                ]

                for selector in selectors_to_try:
                    try:
                        self.logger.info(f"Trying selector: {selector}")
                        post_button = page.wait_for_selector(selector, timeout=10000)

                        if post_button:
                            self.logger.info(f"✅ Found post button with selector: {selector}")
                            post_button.click()
                            post_clicked = True
                            time.sleep(2)
                            break
                    except Exception as e:
                        self.logger.debug(f"Selector {selector} failed: {e}")
                        continue

            if not post_clicked:
                # Fallback 1: Try clicking on text input area directly
                self.logger.warning("Could not find 'Start a post' button, trying fallback methods...")

                fallback_selectors = [
                    'div.share-box-feed-entry__trigger',
                    'div.share-box-first-update',
                    'div[role="textbox"]',
                    'div[contenteditable="true"]',
                    '.share-form__content',
                    '#global-nav-create'
                ]

                for fallback in fallback_selectors:
                    try:
                        self.logger.info(f"Trying fallback: {fallback}")
                        page.click(fallback, timeout=5000)
                        self.logger.info(f"✅ Clicked using fallback: {fallback}")
                        post_clicked = True
                        time.sleep(2)
                        break
                    except Exception as e:
                        self.logger.debug(f"Fallback {fallback} failed: {e}")
                        continue

            if not post_clicked:
                # All methods failed - save screenshot and return error
                page.screenshot(path=str(screenshot_path))
                self.logger.error(f"❌ Could not find or click post button")
                self.logger.error(f"Screenshot saved to {screenshot_path}")
                return {
                    'status': 'error',
                    'error': 'Could not find or click "Start a post" button - tried all selectors and fallbacks',
                    'retry': True
                }

            # Wait for text area with multiple selectors
            self.logger.info("Waiting for text editor to appear...")

            # Give editor time to appear
            page.wait_for_timeout(2000)

            text_area_selectors = [
                'div[contenteditable="true"][role="textbox"]',
                'div[contenteditable="true"]',
                'textarea[name="title"]',
                'textarea[placeholder*="What do you want to talk about?"]',
                'div.ql-editor',
                '#artdeco-hoverable-artdeco-entity-0',
                '.share-form__text',
                '[data-test-id="share-form-text"]'
            ]

            text_area = None
            for selector in text_area_selectors:
                try:
                    self.logger.info(f"Looking for text area with selector: {selector}")
                    text_area = page.wait_for_selector(selector, timeout=10000)
                    if text_area:
                        self.logger.info(f"✅ Found text area with selector: {selector}")
                        break
                except Exception as e:
                    self.logger.debug(f"Text area selector {selector} failed: {e}")
                    continue

            if not text_area:
                page.screenshot(path=str(screenshot_path))
                self.logger.error(f"Screenshot saved to {screenshot_path}")
                return {
                    'status': 'error',
                    'error': 'Could not find text editor',
                    'retry': True
                }

            # Type the post content
            self.logger.info("Typing post content...")
            text_area.fill(post_content)
            time.sleep(1)

            # Wait for LinkedIn to process
            page.wait_for_timeout(3000)

            # Find and click the post button
            self.logger.info("Looking for Post button...")

            post_submit_selectors = [
                'button[aria-label="Post"]',
                'button:has-text("Post")',
                '.share-actions__primary-action',
                'button[data-control-name="share.post"]'
            ]

            post_submit_button = None
            for selector in post_submit_selectors:
                try:
                    post_submit_button = page.wait_for_selector(selector, timeout=10000)
                    if post_submit_button:
                        self.logger.info(f"Found Post button with selector: {selector}")
                        break
                except:
                    continue

            if not post_submit_button:
                page.screenshot(path=str(screenshot_path))
                self.logger.error(f"Screenshot saved to {screenshot_path}")
                return {
                    'status': 'error',
                    'error': 'Could not find Post button',
                    'retry': True
                }

            # Check if button is disabled
            if post_submit_button.is_disabled():
                return {
                    'status': 'error',
                    'error': 'Post button is disabled - content may be too short or empty',
                    'retry': False
                }

            # Click post button
            self.logger.info("Clicking Post button...")
            post_submit_button.click()

            # Wait for post to be published
            page.wait_for_timeout(3000)

            # Check for success or error messages
            # LinkedIn shows both success and error messages in the same elements
            message_selectors = [
                '[role="alert"]',
                '.artdeco-inline-alert',
                '.artdeco-toast',
                '.artdeco-toast-item'
            ]

            success_indicators = ['post successful', 'view post', 'your post has been published', 'published']
            error_indicators = ['error', 'failed', 'couldn\'t', 'cannot', 'unable', 'please try again']

            for message_selector in message_selectors:
                try:
                    message_element = page.query_selector(message_selector)
                    if message_element and message_element.is_visible():
                        message_text = message_element.inner_text().lower()

                        self.logger.info(f"Found message: {message_text}")

                        # Check if it's a success message
                        if any(indicator in message_text for indicator in success_indicators):
                            self.logger.info("✅ Post successful! Found success message.")
                            return {
                                'status': 'success',
                                'timestamp': datetime.now().isoformat(),
                                'message': 'Post published successfully'
                            }

                        # Check if it's an error message
                        if any(indicator in message_text for indicator in error_indicators):
                            self.logger.error(f"❌ LinkedIn error: {message_text}")
                            return {
                                'status': 'error',
                                'error': f'LinkedIn error: {message_element.inner_text()}',
                                'retry': False
                            }

                        # Unknown message - log it but continue checking
                        self.logger.warning(f"⚠️  Unknown message type: {message_text}")

                except Exception as e:
                    self.logger.debug(f"Error checking selector {message_selector}: {e}")
                    continue

            # No error messages found - verify success by checking page state
            # Additional success indicators:
            # 1. Button text changed from "Post" to something else
            # 2. Feed updated with new post
            # 3. No error messages shown
            self.logger.info("✅ No error messages detected, assuming success!")

            # Final verification - check if we're still on feed page
            current_url = page.url
            if "feed" in current_url.lower():
                self.logger.info("✅ Still on feed page - post likely successful")
            else:
                self.logger.info(f"✅ Current URL: {current_url}")

            return {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'url': current_url
            }

        except PlaywrightTimeout as e:
            try:
                page.screenshot(path=str(screenshot_path))
                self.logger.error(f"Screenshot saved to {screenshot_path}")
            except:
                pass

            return {
                'status': 'error',
                'error': f'Timeout waiting for elements: {str(e)}',
                'retry': True
            }
        except Exception as e:
            try:
                page.screenshot(path=str(screenshot_path))
                self.logger.error(f"Screenshot saved to {screenshot_path}")
            except:
                pass

            return {
                'status': 'error',
                'error': str(e),
                'retry': False
            }

    def _move_to_done(self, file_path: Path) -> bool:
        """Move processed file to Done folder."""
        try:
            destination = self.done_path / file_path.name
            shutil.move(str(file_path), str(destination))
            self.logger.info(f"Moved {file_path.name} to Done/")
            return True
        except Exception as e:
            self.logger.error(f"Failed to move file to Done: {e}")
            return False

    def _is_already_processed(self, file_name: str) -> bool:
        """Check if file has already been processed."""
        return file_name in self.processed_files

    def _mark_as_processed(self, file_name: str):
        """Mark file as processed."""
        self.processed_files.add(file_name)
        self._save_state()

    def check_approved_folder(self) -> List[Path]:
        """Check Approved folder for LinkedIn post files."""
        try:
            # Log the absolute path being checked
            abs_path = str(self.approved_path.absolute())
            self.logger.info(f"🔍 Checking Approved folder: {abs_path}")

            # Check if folder exists
            if not self.approved_path.exists():
                self.logger.error(f"❌ Approved folder does not exist: {abs_path}")
                return []

            # List all .md files
            all_md_files = list(self.approved_path.glob("*.md"))
            self.logger.info(f"📁 Found {len(all_md_files)} total .md files in Approved/")

            approved_files = []

            for file_path in all_md_files:
                self.logger.info(f"🔎 Checking file: {file_path.name}")

                # Extract content to check frontmatter
                content_data = self._extract_post_content(file_path)

                if content_data['status'] == 'error':
                    self.logger.warning(f"⚠️  Failed to read {file_path.name}: {content_data.get('error')}")
                    continue

                frontmatter = content_data.get('frontmatter', {})
                post_type = frontmatter.get('type', 'unknown')

                self.logger.info(f"   Type: {post_type}")

                # Check if this is a LinkedIn post
                if frontmatter.get('type') == 'linkedin_post':
                    # Check if not already processed
                    if not self._is_already_processed(file_path.name):
                        self.logger.info(f"✅ Found approved LinkedIn post: {file_path.name}")
                        approved_files.append(file_path)
                    else:
                        self.logger.info(f"⏭️  Skipping already processed: {file_path.name}")

            self.logger.info(f"📊 Total approved LinkedIn posts: {len(approved_files)}")
            return approved_files

        except Exception as e:
            self.logger.error(f"❌ Error checking Approved folder: {e}")
            return []

    def process_file(self, file_path: Path, page) -> Dict[str, Any]:
        """Process a single LinkedIn post file."""
        file_name = file_path.name

        try:
            # Extract post content
            content_data = self._extract_post_content(file_path)

            if content_data['status'] == 'error':
                return content_data

            post_content = content_data['body']
            frontmatter = content_data['frontmatter']

            # Log the attempt
            self._log_activity('linkedin_post_attempt', {
                'file_name': file_name,
                'content_preview': post_content[:200] + '...' if len(post_content) > 200 else post_content
            })

            if self.dry_run:
                self.logger.info(f"[DRY RUN] Would post to LinkedIn:")
                self.logger.info(f"  File: {file_name}")
                self.logger.info(f"  Content: {post_content[:200]}...")

                # Move to done in dry run mode
                self._move_to_done(file_path)
                self._mark_as_processed(file_name)

                return {
                    'status': 'dry_run',
                    'file_name': file_name,
                    'content_preview': post_content[:200]
                }

            # Post to LinkedIn
            result = self._post_to_linkedin(post_content, page)

            if result['status'] == 'success':
                # Move to Done folder
                if self._move_to_done(file_path):
                    self._mark_as_processed(file_name)

                    self._log_activity('linkedin_posted', {
                        'file_name': file_name,
                        'success': True
                    })

                    return {
                        'status': 'success',
                        'file_name': file_name,
                        'moved_to_done': True
                    }
                else:
                    return {
                        'status': 'partial',
                        'file_name': file_name,
                        'error': 'Posted but failed to move file'
                    }
            else:
                # Log error
                self._log_activity('linkedin_post_failed', {
                    'file_name': file_name,
                    'error': result.get('error')
                })

                return result

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error processing file {file_name}: {error_msg}")

            self._log_activity('error', {
                'file_name': file_name,
                'error': error_msg
            })

            return {
                'status': 'error',
                'file_name': file_name,
                'error': error_msg
            }

    def run_once(self, max_retries: int = 3) -> Dict[str, Any]:
        """Run one iteration of checking and posting."""
        results = {
            'processed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }

        with sync_playwright() as p:
            # Determine headless mode
            headless = self.headless if self._has_session() else False

            if not self._has_session():
                self.logger.info("No session found - running in visible mode for login")

            # Launch browser with increased timeout
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(self.session_path),
                headless=headless,
                args=['--disable-blink-features=AutomationControlled'],
                # Ignore HTTPS errors for development
                ignore_https_errors=True,
                # Set viewport
                viewport={'width': 1920, 'height': 1080},
                # Set user agent
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            try:
                # Get or create page
                if len(browser.pages) > 0:
                    page = browser.pages[0]
                else:
                    page = browser.new_page()

                # Set default timeout for page operations
                page.set_default_timeout(60000)

                # Try to navigate to feed first and check if already logged in
                self.logger.info("Checking if already logged in...")
                try:
                    page.goto(
                        self.feed_url,
                        wait_until="domcontentloaded",
                        timeout=90000
                    )
                    page.wait_for_timeout(3000)

                    # Check if feed loaded (user is logged in)
                    logged_in_selectors = [
                        "div.feed-identity-module",
                        "div[data-control-name='identity_welcome_message']",
                        "[data-control-name='nav_logo']",
                        ".feed-shared-update-v2"
                    ]

                    is_logged_in = False
                    for selector in logged_in_selectors:
                        try:
                            element = page.query_selector(selector)
                            if element and element.is_visible():
                                self.logger.info(f"✓ Already logged in - found: {selector}")
                                is_logged_in = True
                                break
                        except:
                            continue

                    if is_logged_in and "feed" in page.url.lower():
                        self.logger.info("✓ Session is valid - already logged in!")
                        # Save/update session
                        self._save_session(browser)
                    else:
                        # Need to login
                        self.logger.info("Session not valid - attempting login...")
                        if not self._login(page):
                            results['errors'].append("Login failed")
                            return results

                        # Save session after successful login
                        self._save_session(browser)

                        # Wait for session to stabilize
                        time.sleep(2)

                except PlaywrightTimeout:
                    self.logger.warning("Feed navigation timeout, attempting login...")
                    # Try to login
                    if not self._login(page):
                        results['errors'].append("Login failed")
                        return results

                    # Save session after successful login
                    self._save_session(browser)

                    # Wait for session to stabilize
                    time.sleep(2)

                # Check for security verification
                if self._check_for_security_verification(page):
                    self.logger.error("LinkedIn requires security verification. Please complete it manually.")
                    results['errors'].append("Security verification required")

                    # Save screenshot for debugging
                    try:
                        page.screenshot(path=str(self.logs_path / "security_verification.png"))
                        self.logger.info("Screenshot saved to Logs/security_verification.png")
                    except:
                        pass

                    return results

                # Check Approved folder
                approved_files = self.check_approved_folder()

                if not approved_files:
                    self.logger.info("No approved LinkedIn posts found")
                    return results

                self.logger.info(f"Found {len(approved_files)} approved post(s)")

                # Process each file
                for file_path in approved_files:
                    retry_count = 0
                    success = False

                    while retry_count < max_retries and not success:
                        result = self.process_file(file_path, page)

                        if result['status'] == 'success' or result['status'] == 'dry_run':
                            results['processed'] += 1
                            success = True
                        elif result['status'] == 'error':
                            if result.get('retry') and retry_count < max_retries - 1:
                                retry_count += 1
                                self.logger.info(f"Retrying ({retry_count}/{max_retries})...")
                                time.sleep(5)
                            else:
                                results['failed'] += 1
                                results['errors'].append({
                                    'file': file_path.name,
                                    'error': result.get('error')
                                })
                                success = False  # Give up
                                break

            finally:
                browser.close()

        return results

    def run(self, check_interval: int = 60, max_iterations: int = None):
        """Run continuously watching for approved posts."""
        iteration = 0

        self.logger.info(f"Starting LinkedIn Poster")
        self.logger.info(f"Check interval: {check_interval} seconds")
        self.logger.info(f"DRY_RUN: {self.dry_run}")

        try:
            while True:
                if max_iterations and iteration >= max_iterations:
                    self.logger.info(f"Reached max iterations ({max_iterations})")
                    break

                iteration += 1
                self.logger.info(f"Iteration {iteration}")

                try:
                    results = self.run_once()

                    self.logger.info(f"Results: {results['processed']} processed, {results['failed']} failed")

                    if results['errors']:
                        for error in results['errors']:
                            self.logger.error(f"Error: {error}")

                except Exception as e:
                    self.logger.error(f"Error during iteration: {e}")
                    self._log_activity('error', {'error': str(e)})

                # Wait before next check
                if max_iterations is None or iteration < max_iterations:
                    self.logger.info(f"Waiting {check_interval} seconds...")
                    time.sleep(check_interval)

        except KeyboardInterrupt:
            self.logger.info("Stopped by user")
        finally:
            self._save_state()
            self.logger.info("LinkedIn Poster stopped")


def main():
    """Main entry point."""
    import sys

    # Parse command line arguments
    check_interval = 60
    max_iterations = 1  # Default to one iteration

    for arg in sys.argv[1:]:
        if arg.startswith('--interval='):
            check_interval = int(arg.split('=')[1])
        elif arg.startswith('--iterations='):
            max_iterations = int(arg.split('=')[1])
        elif arg == '--continuous':
            max_iterations = None

    # Create and run poster
    poster = LinkedInPoster()

    try:
        poster.run(
            check_interval=check_interval,
            max_iterations=max_iterations
        )
    except KeyboardInterrupt:
        poster.logger.info("Shutdown requested")


if __name__ == "__main__":
    main()
