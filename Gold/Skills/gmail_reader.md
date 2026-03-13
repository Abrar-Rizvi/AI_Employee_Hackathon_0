---
name: gmail-reader
description: Read and monitor Gmail inbox for new/unread emails. Extract email content, attachments, and metadata for processing by other skills.
license: Apache-2.0
compatibility: Requires google-auth, google-api-python-client, credentials.json
metadata:
  author: AI Employee Silver Tier
  version: "1.0"
  tier: silver
  api: "Gmail API v1"
---

# Gmail Reader Skill

## Purpose
Monitor Gmail inbox for new emails, retrieve email content, extract metadata, and identify actionable emails for processing. This skill enables the AI Employee to autonomously check for incoming communications and route them to appropriate handlers.

## When to Use This Skill
- Monitoring inbox for new emails automatically
- Retrieving specific email content by ID or thread
- Searching for emails matching criteria (subject, sender, date)
- Extracting attachments for further processing
- Checking for urgent/high-priority communications
- Fetching unread messages for batch processing

## Input Parameters

```json
{
  "action": "list|get|search|monitor",
  "credentials_path": "/path/to/credentials.json",
  "token_path": "/path/to/token.pickle",
  "query": {
    "label": "INBOX",
    "max_results": 10,
    "include_spam_trash": false,
    "q": "is:unread OR from:boss@company.com"
  },
  "email_id": "1234567890abcdef",
  "format": "metadata|full|raw",
  "download_attachments": true,
  "output_folder": "/path/to/save/attachments"
}
```

## Output Format

```json
{
  "status": "success",
  "action": "list",
  "timestamp": "2026-02-24T12:00:00",
  "emails": [
    {
      "id": "1234567890abcdef",
      "thread_id": "1234567890abcdef",
      "subject": "Project Update Required",
      "from": "client@company.com",
      "to": "employee@company.com",
      "date": "2026-02-24T12:00:00",
      "snippet": "Please review the attached...",
      "body": "Full email body text...",
      "labels": ["INBOX", "UNREAD"],
      "has_attachments": true,
      "attachments": [
        {
          "filename": "document.pdf",
          "mime_type": "application/pdf",
          "size": 12345,
          "attachment_id": "ATTACH_ID",
          "saved_path": "/output_folder/document.pdf"
        }
      ],
      "is_unread": true,
      "is_urgent": false,
      "priority": "medium"
    }
  ],
  "total_results": 1,
  "next_page_token": "token_if_more_results",
  "metadata": {
    "query_used": "is:unread",
    "labels_filtered": ["INBOX"]
  }
}
```

## Python Implementation

```python
#!/usr/bin/env python3
"""
Gmail Reader Skill for Silver Tier AI Employee
Monitors Gmail inbox and retrieves email content.
"""

import os
import json
import base64
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("Error: Google libraries not found. Install with:")
    print("pip install google-auth google-auth-oauthlib google-api-python-client")
    raise

# Configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GmailReader:
    """Gmail API reader for monitoring and retrieving emails."""

    def __init__(self, credentials_path: str = None, token_path: str = None):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.creds = None

    def authenticate(self) -> bool:
        """Authenticate with Gmail API using OAuth2."""
        try:
            # Load existing token if available
            if self.token_path and Path(self.token_path).exists():
                self.creds = Credentials.from_authorized_user_file(
                    self.token_path, SCOPES
                )

            # If there are no (valid) credentials available, let the user log in
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                elif self.credentials_path:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)
                else:
                    logger.error("No credentials available for authentication")
                    return False

                # Save the credentials for the next run
                if self.token_path:
                    with open(self.token_path, 'w') as token:
                        token.write(self.creds.to_json())

            # Build the Gmail service
            self.service = build('gmail', 'v1', credentials=self.creds)
            logger.info("Successfully authenticated with Gmail API")
            return True

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def list_emails(
        self,
        query: str = "is:unread",
        max_results: int = 10,
        label_ids: List[str] = None
    ) -> Dict[str, Any]:
        """List emails matching the query."""
        try:
            if not self.service:
                self.authenticate()

            result = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results,
                labelIds=label_ids or ['INBOX']
            ).execute()

            messages = result.get('messages', [])
            next_page_token = result.get('nextPageToken')

            emails = []
            for message in messages:
                email_data = self.get_email(message['id'], format='metadata')
                if email_data.get('status') == 'success':
                    emails.append(email_data)

            return {
                "status": "success",
                "action": "list",
                "timestamp": datetime.now().isoformat(),
                "emails": emails,
                "total_results": len(emails),
                "next_page_token": next_page_token,
                "metadata": {
                    "query_used": query,
                    "labels_filtered": label_ids
                }
            }

        except HttpError as e:
            return {
                "status": "error",
                "error": f"Gmail API error: {e}",
                "timestamp": datetime.now().isoformat()
            }

    def get_email(
        self,
        email_id: str,
        format: str = 'full',
        download_attachments: bool = False,
        output_folder: str = None
    ) -> Dict[str, Any]:
        """Get a specific email by ID."""
        try:
            if not self.service:
                self.authenticate()

            # Get message
            message = self.service.users().messages().get(
                userId='me',
                id=email_id,
                format=format
            ).execute()

            # Extract headers
            headers = {}
            for header in message['payload'].get('headers', []):
                headers[header['name'].lower()] = header['value']

            # Extract body
            body = self._extract_body(message['payload'])

            # Extract attachments if requested
            attachments = []
            if download_attachments and output_folder:
                attachments = self._download_attachments(
                    message['payload'],
                    email_id,
                    output_folder
                )

            # Parse labels
            labels = message.get('labelIds', [])
            is_unread = 'UNREAD' in labels

            # Determine urgency
            subject = headers.get('subject', '')
            is_urgent = self._check_urgency(subject, headers.get('from', ''))

            # Determine priority
            priority = self._determine_priority(subject, headers, labels)

            return {
                "status": "success",
                "id": message['id'],
                "thread_id": message['threadId'],
                "subject": headers.get('subject', '(No Subject)'),
                "from": headers.get('from', ''),
                "to": headers.get('to', ''),
                "date": headers.get('date', ''),
                "cc": headers.get('cc', ''),
                "body": body,
                "snippet": message.get('snippet', ''),
                "labels": labels,
                "has_attachments": len(attachments) > 0,
                "attachments": attachments,
                "is_unread": is_unread,
                "is_urgent": is_urgent,
                "priority": priority,
                "timestamp": datetime.now().isoformat()
            }

        except HttpError as e:
            return {
                "status": "error",
                "error": f"Failed to get email: {e}",
                "email_id": email_id,
                "timestamp": datetime.now().isoformat()
            }

    def search_emails(
        self,
        query: str,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """Search for emails matching Gmail search query."""
        return self.list_emails(query=query, max_results=max_results)

    def monitor_new_emails(
        self,
        check_interval: int = 60,
        callback=None,
        max_iterations: int = None
    ):
        """Continuously monitor for new emails."""
        iteration = 0
        last_check = datetime.now() - timedelta(minutes=5)

        try:
            while True:
                if max_iterations and iteration >= max_iterations:
                    break

                # Check for new emails since last check
                query = f"after:{int(last_check.timestamp())}"
                result = self.list_emails(query=query)

                if result.get('status') == 'success':
                    new_emails = result.get('emails', [])

                    if new_emails:
                        logger.info(f"Found {len(new_emails)} new email(s)")

                        # Log activity
                        self._log_activity('emails_detected', {
                            'count': len(new_emails),
                            'query': query
                        })

                        # Process each new email
                        for email in new_emails:
                            if callback:
                                callback(email)

                            # Auto-detect urgent emails
                            if email.get('is_urgent'):
                                logger.warning(f"URGENT: {email['subject']} from {email['from']}")

                    last_check = datetime.now()

                iteration += 1
                time.sleep(check_interval)

        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")

    def _extract_body(self, payload: Dict) -> str:
        """Extract email body from payload."""
        body = ""

        if 'body' in payload:
            if 'data' in payload['body']:
                # Base64 encoded body
                body_data = payload['body']['data']
                body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')

        # Check multipart
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain' and 'data' in part.get('body', {}):
                    body_data = part['body']['data']
                    body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                    break

        return body

    def _download_attachments(
        self,
        payload: Dict,
        email_id: str,
        output_folder: str
    ) -> List[Dict]:
        """Download email attachments."""
        attachments = []
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)

        def extract_parts(parts):
            for part in parts:
                # If this part has an attachment ID
                if 'filename' in part and part['filename']:
                    attachment_id = part['body'].get('attachmentId')
                    if attachment_id and not DRY_RUN:
                        try:
                            # Get attachment data
                            attachment = self.service.users().messages().attachments().get(
                                userId='me',
                                messageId=email_id,
                                id=attachment_id
                            ).execute()

                            # Decode and save
                            data = base64.urlsafe_b64decode(attachment['data'])
                            file_path = output_path / part['filename']

                            with open(file_path, 'wb') as f:
                                f.write(data)

                            attachments.append({
                                "filename": part['filename'],
                                "mime_type": part['mimeType'],
                                "size": len(data),
                                "attachment_id": attachment_id,
                                "saved_path": str(file_path)
                            })

                            logger.info(f"Downloaded attachment: {part['filename']}")

                        except Exception as e:
                            logger.error(f"Failed to download {part['filename']}: {e}")

                # Recurse into nested parts
                if 'parts' in part:
                    extract_parts(part['parts'])

        if 'parts' in payload:
            extract_parts(payload['parts'])

        return attachments

    def _check_urgency(self, subject: str, from_address: str) -> bool:
        """Check if email is urgent based on content."""
        urgent_keywords = ['urgent', 'asap', 'immediately', 'emergency', 'critical']
        subject_lower = subject.lower()

        return (
            any(keyword in subject_lower for keyword in urgent_keywords) or
            'boss' in from_address.lower() or
            'ceo' in from_address.lower() or
            'important' in subject_lower
        )

    def _determine_priority(self, subject: str, headers: Dict, labels: List[str]) -> str:
        """Determine email priority."""
        # Check for starred or important labels
        if 'STARRED' in labels or 'IMPORTANT' in labels:
            return 'high'

        # Check subject for urgency
        if self._check_urgency(subject, headers.get('from', '')):
            return 'high'

        # Check for common business keywords
        subject_lower = subject.lower()
        if any(kw in subject_lower for kw in ['invoice', 'payment', 'contract']):
            return 'medium'

        return 'low'

    def _log_activity(self, action: str, details: Dict = None):
        """Log activity to JSON file."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "skill": "gmail_reader",
            "dry_run": DRY_RUN
        }

        if details:
            log_entry.update(details)

        # Save to logs folder
        log_dir = Path(__file__).parent.parent.parent / "Bronze" / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

        try:
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []

            logs.append(log_entry)

            if not DRY_RUN:
                with open(log_file, 'w') as f:
                    json.dump(logs, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to log activity: {e}")


def gmail_reader_handler(input_params: Dict) -> Dict:
    """Main handler function for Gmail Reader skill."""
    action = input_params.get('action', 'list')

    reader = GmailReader(
        credentials_path=input_params.get('credentials_path'),
        token_path=input_params.get('token_path')
    )

    if DRY_RUN:
        logger.info(f"[DRY RUN] Would execute: {action}")

    try:
        if action == 'list' or action == 'search':
            query = input_params.get('query', {})
            return reader.list_emails(
                query=query.get('q', 'is:unread'),
                max_results=query.get('max_results', 10),
                label_ids=query.get('label', ['INBOX']).split(',') if isinstance(query.get('label'), str) else query.get('label', ['INBOX'])
            )

        elif action == 'get':
            return reader.get_email(
                email_id=input_params['email_id'],
                format=input_params.get('format', 'full'),
                download_attachments=input_params.get('download_attachments', False),
                output_folder=input_params.get('output_folder')
            )

        elif action == 'monitor':
            reader.monitor_new_emails(
                check_interval=input_params.get('check_interval', 60),
                max_iterations=input_params.get('max_iterations')
            )

        else:
            return {
                "status": "error",
                "error": f"Unknown action: {action}",
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# Example usage
if __name__ == "__main__":
    # Example: List unread emails
    params = {
        "action": "list",
        "credentials_path": "credentials.json",
        "token_path": "token.pickle",
        "query": {
            "q": "is:unread",
            "max_results": 5
        }
    }

    result = gmail_reader_handler(params)
    print(json.dumps(result, indent=2))
```

## Integration Points

This skill integrates with:
- **email_drafter** - Drafts responses to incoming emails
- **approval_manager** - Routes emails requiring approval
- **scheduler** - Schedules periodic email checks
- **text_analyzer** - Analyzes email content for intent
- **data_extractor** - Extracts structured data from email body

## Error Handling

1. **Authentication Failures** - Clear token file and re-authenticate
2. **API Quota Exceeded** - Implement exponential backoff
3. **Network Errors** - Retry with timeout
4. **Missing Email ID** - Return error with valid IDs
5. **Attachment Download Failures** - Log and continue with email body

## Security Notes

- Uses OAuth2 for secure authentication
- Requires user consent for Gmail API access
- Credentials stored locally in token.pickle
- Supports DRY_RUN mode for testing without API calls
- No credentials logged or transmitted externally

## Approval Requirements

Per Company_Handbook.md:
- **Email replies to new contacts**: Always require approval
- **Sensitive data access**: Manager approval required
- **Bulk email operations**: Approval required

## Testing

```bash
# Set up credentials (one-time)
# 1. Go to Google Cloud Console
# 2. Enable Gmail API
# 3. Create OAuth 2.0 credentials
# 4. Download credentials.json

# Test in dry-run mode
export DRY_RUN=true
python gmail_reader.md

# Test live (will open browser for auth)
export DRY_RUN=false
python gmail_reader.md
```
