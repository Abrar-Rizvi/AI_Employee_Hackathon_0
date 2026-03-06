#!/usr/bin/env python3
"""
Gmail Watcher for Silver Tier AI Employee
Monitors Gmail for unread important emails and creates task files.
"""

import os
import sys
import json
import time
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("Error: Google libraries not found. Install with:")
    print("pip install google-auth google-auth-oauthlib google-api-python-client")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("Warning: python-dotenv not found. Install with: pip install python-dotenv")
    sys.exit(1)

from base_watcher import BaseWatcher


class GmailWatcher(BaseWatcher):
    """Watch Gmail for unread important emails."""

    # Gmail API scopes
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(self, vault_path: str = None):
        # Load .env from Silver/ folder (parent of Watchers/)
        # __file__ is Watchers/gmail_watcher.py
        # parent is Watchers/, parent.parent is Silver/
        silver_folder = Path(__file__).parent.parent
        env_file = silver_folder / '.env'

        # Load .env file to get VAULT_PATH
        if env_file.exists():
            load_dotenv(dotenv_path=env_file)
            print(f"[DEBUG] Loaded .env from: {env_file}")
        else:
            print(f"[WARNING] .env file not found at: {env_file}")
            load_dotenv()  # Fallback to default locations

        # Get VAULT_PATH from environment or use Silver/ folder
        vault_path_from_env = os.getenv('VAULT_PATH')
        if vault_path_from_env:
            vault_path = Path(vault_path_from_env)
            print(f"[DEBUG] VAULT_PATH from env: {vault_path}")
        else:
            vault_path = vault_path or silver_folder
            print(f"[DEBUG] VAULT_PATH default: {vault_path}")

        # Build ABSOLUTE paths for credentials and token BEFORE calling super().__init__()
        # Use os.path.join() to ensure absolute paths
        vault_path_str = str(vault_path)
        self.credentials_path = os.path.join(vault_path_str, 'Config', 'gmail_credentials.json')
        self.token_path = os.path.join(vault_path_str, 'Config', 'gmail_token.json')

        # Override with env vars if explicitly set (for backward compatibility)
        self.credentials_path = os.getenv('GMAIL_CREDENTIALS', self.credentials_path)
        self.token_path = os.getenv('GMAIL_TOKEN', self.token_path)
        self.check_interval = int(os.getenv('GMAIL_CHECK_INTERVAL', '120'))

        # Call parent constructor with vault_path
        super().__init__(vault_path_str)

        # Log the paths for debugging
        print(f"[DEBUG] Credentials path: {self.credentials_path}")
        print(f"[DEBUG] Token path: {self.token_path}")
        print(f"[DEBUG] Config path: {self.config_path}")
        print(f"[DEBUG] Credentials exists: {Path(self.credentials_path).exists()}")
        print(f"[DEBUG] Token exists: {Path(self.token_path).exists()}")

        # Gmail service
        self.service = None
        self.creds = None

        # Retry settings
        self.max_retries = 3
        self.retry_delay = 5

        # Authenticate
        self._authenticate()

    def _authenticate(self) -> bool:
        """Authenticate with Gmail API using OAuth2."""
        try:
            # Load existing token if available
            if Path(self.token_path).exists():
                self.creds = Credentials.from_authorized_user_file(
                    self.token_path, self.SCOPES
                )
                self.logger.info(f"Loaded existing token from {self.token_path}")

            # If there are no (valid) credentials available, let the user log in
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.logger.info("Token expired, refreshing...")
                    self.creds.refresh(Request())
                    self.logger.info("Token refreshed successfully")
                elif Path(self.credentials_path).exists():
                    self.logger.info(f"No valid credentials, starting OAuth flow from {self.credentials_path}")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)
                else:
                    self.logger.error(f"Credentials file not found: {self.credentials_path}")
                    self.logger.error("Please download credentials.json from Google Cloud Console")
                    return False

                # Save the credentials for the next run
                if not self.dry_run:
                    with open(self.token_path, 'w') as token:
                        token.write(self.creds.to_json())
                    self.logger.info(f"Token saved to {self.token_path}")

            # Build the Gmail service
            self.service = build('gmail', 'v1', credentials=self.creds)
            self.logger.info("Successfully authenticated with Gmail API")
            return True

        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return False

    def _retry_on_error(self, func, *args, **kwargs):
        """Retry function call on error with exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except HttpError as e:
                if e.resp.status in [429, 500, 502, 503, 504]:  # Retryable errors
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)
                        self.logger.warning(f"API error (attempt {attempt + 1}/{self.max_retries}): {e}")
                        self.logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        raise
                else:
                    raise
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    self.logger.warning(f"Error (attempt {attempt + 1}/{self.max_retries}): {e}")
                    self.logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise

    def check_for_updates(self) -> List[Dict]:
        """Check for new unread emails in inbox."""
        if not self.service:
            self.logger.error("Not authenticated, cannot check for emails")
            return []

        try:
            # Build query for unread emails in inbox
            # Look for emails that are:
            # - Unread (is:unread)
            # - In Inbox (in:inbox)
            query = 'is:unread in:inbox'

            self.logger.info(f"Searching for emails with query: {query}")

            # List messages matching query
            result = self._retry_on_error(
                self.service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=10
                ).execute
            )

            messages = result.get('messages', [])

            if not messages:
                self.logger.info("No matching emails found")
                return []

            self.logger.info(f"Found {len(messages)} message(s) to process")

            # Fetch full details for each message
            emails = []
            for message in messages:
                try:
                    email_data = self._get_email_details(message['id'])
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    self.logger.error(f"Error fetching message {message['id']}: {e}")
                    continue

            return emails

        except HttpError as e:
            self.logger.error(f"Gmail API error: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")
            return []

    def _get_email_details(self, message_id: str) -> Optional[Dict]:
        """Get full email details including content."""
        try:
            # Get message with full payload
            message = self._retry_on_error(
                self.service.users().messages().get(
                    userId='me',
                    id=message_id,
                    format='full'
                ).execute
            )

            # Extract headers
            headers = {}
            for header in message['payload'].get('headers', []):
                headers[header['name'].lower()] = header['value']

            # Extract body
            body = self._extract_body(message['payload'])

            # Determine priority
            priority = self._determine_priority(headers, body)

            # Build email object
            email_data = {
                'id': message['id'],
                'thread_id': message.get('threadId', ''),
                'from': headers.get('from', ''),
                'to': headers.get('to', ''),
                'subject': headers.get('subject', '(No Subject)'),
                'date': headers.get('date', ''),
                'body': body,
                'snippet': message.get('snippet', ''),
                'priority': priority,
                'labels': message.get('labelIds', []),
                'timestamp': datetime.now().isoformat()
            }

            return email_data

        except Exception as e:
            self.logger.error(f"Error getting email details: {e}")
            return None

    def _extract_body(self, payload: Dict) -> str:
        """Extract email body from payload."""
        body = ""

        if 'body' in payload:
            if 'data' in payload['body']:
                # Base64 encoded body
                body_data = payload['body']['data']
                try:
                    body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                except:
                    body = body_data

        # Check multipart
        if 'parts' in payload:
            for part in payload['parts']:
                # Prefer plain text
                if part['mimeType'] == 'text/plain' and 'data' in part.get('body', {}):
                    body_data = part['body']['data']
                    try:
                        body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                        break  # Use plain text, don't check further
                    except:
                        continue

                # Fallback to HTML if no plain text found
                elif part['mimeType'] == 'text/html' and not body:
                    if 'data' in part.get('body', {}):
                        body_data = part['body']['data']
                        try:
                            body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                        except:
                            pass

        return body

    def _determine_priority(self, headers: Dict, body: str) -> str:
        """Determine email priority based on content."""
        subject = headers.get('subject', '').lower()
        from_addr = headers.get('from', '').lower()
        body_lower = body.lower()

        # High priority indicators
        high_priority_keywords = ['urgent', 'asap', 'emergency', 'immediately', 'critical']
        important_senders = ['boss', 'ceo', 'manager', 'director']

        # Check for urgent keywords
        if any(keyword in subject or keyword in body_lower for keyword in high_priority_keywords):
            return 'high'

        # Check for important senders
        if any(sender in from_addr for sender in important_senders):
            return 'high'

        # Check for starred/important labels
        if 'STARRED' in headers.get('labels', []):
            return 'high'

        # Check for common business keywords
        business_keywords = ['invoice', 'payment', 'contract', 'deadline']
        if any(keyword in subject or keyword in body_lower for keyword in business_keywords):
            return 'medium'

        return 'medium'

    def create_action_file(self, email: Dict) -> Dict:
        """Create an action file for the email."""
        try:
            email_id = email['id']
            subject = email['subject']

            # Clean subject for filename
            safe_subject = "".join(
                c if c.isalnum() or c in (' ', '-', '_') else '_'
                for c in subject
            )[:50]

            # Create filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"email_{timestamp}_{safe_subject}.md"
            filepath = self.needs_action_path / filename

            # Build frontmatter
            frontmatter = f"""---
type: email
from: {email['from']}
subject: {subject}
received: {email['date']}
priority: {email['priority']}
status: pending
email_id: {email_id}
thread_id: {email['thread_id']}
---

"""

            # Build content
            content = f"""# Email: {subject}

**From:** {email['from']}
**To:** {email['to']}
**Date:** {email['date']}
**Priority:** {email['priority'].upper()}

## Email Body

{email['body'][:2000]}{'...' if len(email['body']) > 2000 else ''}

## Actions Required

- [ ] Review email content
- [ ] Determine appropriate response
- [ ] Check Company_Handbook.md for approval requirements
- [ ] Draft response if needed

## Metadata

- **Email ID:** {email_id}
- **Thread ID:** {email['thread_id']}
- **Labels:** {', '.join(email.get('labels', []))}
- **Detected:** {email['timestamp']}

---

*This email was automatically detected by Gmail Watcher*
"""

            full_content = frontmatter + content

            if self.dry_run:
                self.logger.info(f"[DRY RUN] Would create action file: {filename}")
                self.logger.info(f"[DRY RUN] From: {email['from']}")
                self.logger.info(f"[DRY_RUN] Subject: {subject}")
            else:
                # Write action file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(full_content)

                self.logger.info(f"Created action file: {filename}")

            # Log activity
            self._log_activity('email_detected', {
                'email_id': email_id,
                'from': email['from'],
                'subject': subject,
                'priority': email['priority'],
                'action_file': str(filepath) if not self.dry_run else None
            })

            return {
                'status': 'success',
                'email_id': email_id,
                'action_file': str(filepath),
                'subject': subject
            }

        except Exception as e:
            self.logger.error(f"Error creating action file: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'email_id': email.get('id', 'unknown')
            }

    def run(self, check_interval: int = None, max_iterations: int = None):
        """Run the Gmail watcher."""
        check_interval = check_interval or self.check_interval
        self.logger.info(f"Gmail Watcher starting (check interval: {check_interval}s)")

        # Call parent run method
        super().run(check_interval=check_interval, max_iterations=max_iterations)


def main():
    """Main entry point for Gmail Watcher."""
    # Find Silver/ folder relative to script location
    # __file__ is Watchers/gmail_watcher.py
    # parent is Watchers/, parent.parent is Silver/
    silver_folder = Path(__file__).parent.parent
    env_file = silver_folder / '.env'

    # Load environment variables from .env in Silver/ folder
    if env_file.exists():
        load_dotenv(dotenv_path=env_file)
        print(f"[INFO] Loaded .env from: {env_file}")
    else:
        print(f"[WARNING] .env file not found at: {env_file}")
        print(f"[INFO] Loading .env from default locations...")
        load_dotenv()  # Fallback to default locations

    # Get vault path from environment or use Silver/ folder
    vault_path_from_env = os.getenv('VAULT_PATH')
    if vault_path_from_env:
        vault_path = Path(vault_path_from_env)
    else:
        vault_path = silver_folder

    print(f"[INFO] VAULT_PATH: {vault_path}")

    # Get settings
    check_interval = int(os.getenv('GMAIL_CHECK_INTERVAL', '120'))
    max_iterations = int(os.getenv('MAX_ITERATIONS', '0')) or None

    # Create and run watcher
    watcher = GmailWatcher(vault_path=str(vault_path))

    try:
        watcher.run(
            check_interval=check_interval,
            max_iterations=max_iterations
        )
    except KeyboardInterrupt:
        watcher.logger.info("Stopped by user")
    finally:
        watcher.stop()


if __name__ == "__main__":
    main()
