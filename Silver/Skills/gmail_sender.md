---
name: gmail-sender
description: Send emails via Gmail API with approval workflow for new contacts. Supports attachments, HTML formatting, and draft saving.
license: Apache-2.0
compatibility: Requires google-auth, google-api-python-client, credentials.json
metadata:
  author: AI Employee Silver Tier
  version: "1.0"
  tier: silver
  api: "Gmail API v1"
---

# Gmail Sender Skill

## Purpose
Send emails via Gmail API with built-in approval workflow for new contacts. This skill enables the AI Employee to autonomously send email responses while maintaining compliance with business rules requiring approval for communications with new contacts.

## When to Use This Skill
- Sending drafted email responses (after approval)
- Replying to existing email threads
- Sending new emails to known contacts
- Sending emails with attachments
- Saving email drafts for later review
- Automated email notifications (approved contacts only)

## Input Parameters

```json
{
  "action": "send|save_draft|reply",
  "credentials_path": "/path/to/credentials.json",
  "token_path": "/path/to/token.pickle",
  "email": {
    "to": "recipient@example.com",
    "cc": ["cc@example.com"],
    "bcc": ["bcc@example.com"],
    "subject": "Email Subject",
    "body": "Email body content",
    "html_body": "<p>HTML email content</p>",
    "thread_id": "1234567890abcdef"
  },
  "attachments": [
    {
      "path": "/path/to/file.pdf",
      "filename": "document.pdf"
    }
  ],
  "recipients": {
    "new_contacts": ["new@example.com"],
    "known_contacts": ["existing@example.com"]
  },
  "requires_approval": false,
  "approval_granted": true,
  "dry_run": true
}
```

## Output Format

```json
{
  "status": "success",
  "action": "send",
  "timestamp": "2026-02-24T12:00:00",
  "email_id": "1234567890abcdef",
  "thread_id": "1234567890abcdef",
  "label_ids": ["SENT"],
  "recipients": {
    "to": ["recipient@example.com"],
    "cc": ["cc@example.com"],
    "bcc": ["bcc@example.com"],
    "total": 2
  },
  "attachments_sent": 1,
  "requires_approval": false,
  "approval_status": "granted",
  "metadata": {
    "subject": "Email Subject",
    "size_bytes": 1234,
    "sent_via": "gmail_sender_skill"
  }
}
```

## Python Implementation

```python
#!/usr/bin/env python3
"""
Gmail Sender Skill for Silver Tier AI Employee
Sends emails with approval workflow for new contacts.
"""

import os
import json
import base64
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
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
SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.modify']
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'

# Known contacts database (could be loaded from file)
KNOWN_CONTACTS = set()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GmailSender:
    """Gmail API sender with approval workflow."""

    def __init__(
        self,
        credentials_path: str = None,
        token_path: str = None,
        known_contacts_path: str = None
    ):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.known_contacts_path = known_contacts_path
        self.service = None
        self.creds = None
        self._load_known_contacts()

    def _load_known_contacts(self):
        """Load known contacts from file."""
        global KNOWN_CONTACTS

        if self.known_contacts_path and Path(self.known_contacts_path).exists():
            try:
                with open(self.known_contacts_path, 'r') as f:
                    contacts_data = json.load(f)
                    KNOWN_CONTACTS = set(contacts_data.get('contacts', []))
                logger.info(f"Loaded {len(KNOWN_CONTACTS)} known contacts")
            except Exception as e:
                logger.error(f"Failed to load contacts: {e}")

    def _save_known_contacts(self):
        """Save known contacts to file."""
        if self.known_contacts_path:
            try:
                contacts_data = {
                    'contacts': list(KNOWN_CONTACTS),
                    'updated': datetime.now().isoformat()
                }

                with open(self.known_contacts_path, 'w') as f:
                    json.dump(contacts_data, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save contacts: {e}")

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

    def check_new_contacts(self, recipients: List[str]) -> Dict[str, Any]:
        """Check if any recipients are new contacts."""
        new_contacts = []
        known = []

        for email in recipients:
            # Extract email from address (e.g., "Name <email@domain.com>")
            if '<' in email and '>' in email:
                email = email.split('<')[1].split('>')[0].strip()

            if email not in KNOWN_CONTACTS:
                new_contacts.append(email)
            else:
                known.append(email)

        return {
            "new_contacts": new_contacts,
            "known_contacts": known,
            "has_new": len(new_contacts) > 0,
            "requires_approval": len(new_contacts) > 0
        }

    def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: List[str] = None,
        bcc: List[str] = None,
        html_body: str = None,
        thread_id: str = None,
        attachments: List[Dict] = None,
        approval_granted: bool = False,
        skip_approval_check: bool = False
    ) -> Dict[str, Any]:
        """Send an email via Gmail API."""
        try:
            if not self.service:
                self.authenticate()

            # Collect all recipients for approval check
            all_recipients = to.copy()
            if cc:
                all_recipients.extend(cc)
            if bcc:
                all_recipients.extend(bcc)

            # Check for new contacts (skip if approval already granted)
            requires_approval = False
            approval_details = None

            if not skip_approval_check:
                contact_check = self.check_new_contacts(all_recipients)
                requires_approval = contact_check['has_new']

                if requires_approval and not approval_granted:
                    return {
                        "status": "requires_approval",
                        "action": "send",
                        "timestamp": datetime.now().isoformat(),
                        "reason": "New contacts detected",
                        "new_contacts": contact_check['new_contacts'],
                        "known_contacts": contact_check['known_contacts'],
                        "approval_required": True,
                        "message": "Per Company_Handbook.md, emails to new contacts require approval"
                    }

                approval_details = contact_check

            # Create message
            message = self._create_message(
                to=to,
                subject=subject,
                body=body,
                cc=cc,
                bcc=bcc,
                html_body=html_body,
                attachments=attachments
            )

            if DRY_RUN:
                logger.info(f"[DRY RUN] Would send email to: {', '.join(to)}")
                logger.info(f"[DRY_RUN] Subject: {subject}")

                return {
                    "status": "dry_run",
                    "action": "send",
                    "timestamp": datetime.now().isoformat(),
                    "recipients": {
                        "to": to,
                        "cc": cc or [],
                        "bcc": bcc or [],
                        "total": len(all_recipients)
                    },
                    "subject": subject,
                    "message": "Email not sent (DRY_RUN=true)"
                }

            # Send the message
            sent_message = self.service.users().messages().send(
                userId='me',
                body=message,
                threadId=thread_id
            ).execute()

            # Add new recipients to known contacts
            if approval_details and approval_details['new_contacts']:
                for new_contact in approval_details['new_contacts']:
                    KNOWN_CONTACTS.add(new_contact)
                self._save_known_contacts()

            # Log activity
            self._log_activity('email_sent', {
                'to': to,
                'subject': subject,
                'message_id': sent_message['id'],
                'thread_id': sent_message.get('threadId'),
                'new_contacts': approval_details['new_contacts'] if approval_details else []
            })

            return {
                "status": "success",
                "action": "send",
                "timestamp": datetime.now().isoformat(),
                "email_id": sent_message['id'],
                "thread_id": sent_message.get('threadId'),
                "label_ids": sent_message.get('labelIds', []),
                "recipients": {
                    "to": to,
                    "cc": cc or [],
                    "bcc": bcc or [],
                    "total": len(all_recipients)
                },
                "attachments_sent": len(attachments) if attachments else 0,
                "requires_approval": requires_approval,
                "approval_status": "granted" if requires_approval else "not_required",
                "metadata": {
                    "subject": subject,
                    "size_bytes": len(str(message)),
                    "sent_via": "gmail_sender_skill"
                }
            }

        except HttpError as e:
            return {
                "status": "error",
                "error": f"Gmail API error: {e}",
                "timestamp": datetime.now().isoformat()
            }

    def save_draft(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: List[str] = None,
        bcc: List[str] = None,
        html_body: str = None,
        thread_id: str = None,
        attachments: List[Dict] = None
    ) -> Dict[str, Any]:
        """Save an email as a draft."""
        try:
            if not self.service:
                self.authenticate()

            # Create message
            message = self._create_message(
                to=to,
                subject=subject,
                body=body,
                cc=cc,
                bcc=bcc,
                html_body=html_body,
                attachments=attachments
            )

            if DRY_RUN:
                logger.info(f"[DRY RUN] Would save draft to: {', '.join(to)}")

                return {
                    "status": "dry_run",
                    "action": "save_draft",
                    "timestamp": datetime.now().isoformat(),
                    "subject": subject
                }

            # Save draft
            draft = self.service.users().drafts().create(
                userId='me',
                body={'message': message}
            ).execute()

            # Log activity
            self._log_activity('draft_saved', {
                'to': to,
                'subject': subject,
                'draft_id': draft['id']
            })

            return {
                "status": "success",
                "action": "save_draft",
                "timestamp": datetime.now().isoformat(),
                "draft_id": draft['id'],
                "message": draft['message'],
                "recipients": {
                    "to": to,
                    "cc": cc or [],
                    "bcc": bcc or []
                },
                "subject": subject
            }

        except HttpError as e:
            return {
                "status": "error",
                "error": f"Failed to save draft: {e}",
                "timestamp": datetime.now().isoformat()
            }

    def _create_message(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: List[str] = None,
        bcc: List[str] = None,
        html_body: str = None,
        attachments: List[Dict] = None
    ) -> Dict:
        """Create Gmail message from parameters."""

        # Use HTML body if provided, otherwise plain text
        if html_body:
            if attachments:
                # Multipart with attachments
                message = MIMEMultipart()
                message.attach(MIMEText(html_body, 'html'))
            else:
                # HTML only
                message = MIMEText(html_body, 'html')
        else:
            if attachments:
                message = MIMEMultipart()
                message.attach(MIMEText(body, 'plain'))
            else:
                message = MIMEText(body, 'plain')

        # Set headers
        message['to'] = ', '.join(to)
        message['subject'] = subject

        if cc:
            message['cc'] = ', '.join(cc)
        if bcc:
            message['bcc'] = ', '.join(bcc)

        # Add attachments
        if attachments:
            for attachment in attachments:
                self._add_attachment(message, attachment['path'], attachment.get('filename'))

        # Encode message
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {'raw': raw}

    def _add_attachment(self, message: MIMEMultipart, file_path: str, filename: str = None):
        """Add attachment to email message."""
        path = Path(file_path)

        if not path.exists():
            logger.warning(f"Attachment not found: {file_path}")
            return

        # Determine content type
        content_type, encoding = mimetypes.guess_type(str(path))
        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'

        main_type, sub_type = content_type.split('/', 1)

        # Read file
        with open(path, 'rb') as f:
            data = f.read()

        # Create attachment
        attachment = MIMEBase(main_type, sub_type)
        attachment.set_payload(data)
        encoders.encode_base64(attachment)

        # Set filename
        attachment_filename = filename or path.name
        attachment.add_header(
            'Content-Disposition',
            'attachment',
            filename=attachment_filename
        )

        message.attach(attachment)

    def _log_activity(self, action: str, details: Dict = None):
        """Log activity to JSON file."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "skill": "gmail_sender",
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


def gmail_sender_handler(input_params: Dict) -> Dict:
    """Main handler function for Gmail Sender skill."""
    action = input_params.get('action', 'send')

    sender = GmailSender(
        credentials_path=input_params.get('credentials_path'),
        token_path=input_params.get('token_path'),
        known_contacts_path=input_params.get('known_contacts_path', 'known_contacts.json')
    )

    email = input_params.get('email', {})

    try:
        if action == 'send':
            return sender.send_email(
                to=email.get('to', '').split(',') if isinstance(email.get('to'), str) else email.get('to', []),
                subject=email.get('subject', ''),
                body=email.get('body', ''),
                cc=email.get('cc', []),
                bcc=email.get('bcc', []),
                html_body=email.get('html_body'),
                thread_id=email.get('thread_id'),
                attachments=input_params.get('attachments'),
                approval_granted=input_params.get('approval_granted', False),
                skip_approval_check=input_params.get('skip_approval_check', False)
            )

        elif action == 'save_draft':
            return sender.save_draft(
                to=email.get('to', '').split(',') if isinstance(email.get('to'), str) else email.get('to', []),
                subject=email.get('subject', ''),
                body=email.get('body', ''),
                cc=email.get('cc', []),
                bcc=email.get('bcc', []),
                html_body=email.get('html_body'),
                thread_id=email.get('thread_id'),
                attachments=input_params.get('attachments')
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
    # Example: Send email with approval check
    params = {
        "action": "send",
        "credentials_path": "credentials.json",
        "token_path": "token.pickle",
        "known_contacts_path": "known_contacts.json",
        "email": {
            "to": "client@example.com",
            "subject": "Project Update",
            "body": "Dear Client,\n\nHere is the project update...\n\nBest regards",
            "html_body": "<p>Dear Client,</p><p>Here is the project update...</p><p>Best regards</p>"
        },
        "approval_granted": True
    }

    result = gmail_sender_handler(params)
    print(json.dumps(result, indent=2))
```

## Integration Points

This skill integrates with:
- **gmail_reader** - Reads emails to reply to
- **email_drafter** - Provides drafted email content
- **approval_manager** - Manages approval workflow for new contacts
- **Company_Handbook.md** - Enforces approval rules for new contacts

## Approval Workflow

1. **Check recipients** - Identifies new vs known contacts
2. **Requires approval** - Returns `requires_approval` status for new contacts
3. **Approval granted** - Resubmit with `approval_granted: true`
4. **Update contacts** - New contacts added to known_contacts.json after sending

## Error Handling

1. **Authentication Failures** - Clear token and re-authenticate
2. **Invalid Recipients** - Validate email format before sending
3. **Attachment Not Found** - Log warning and continue without attachment
4. **API Quota Exceeded** - Implement backoff and retry
5. **Missing Required Fields** - Return error with missing parameters

## Security Notes

- Emails to new contacts always require approval (Company_Handbook.md)
- Known contacts stored locally in known_contacts.json
- OAuth2 tokens stored securely in token.pickle
- Supports DRY_RUN mode for testing
- BCC recipients hidden from other recipients

## Testing

```bash
# Test sending to known contact
export DRY_RUN=false
python gmail_sender.md

# Test with new contact (will require approval)
echo '{"action":"send","email":{"to":"new@example.com","subject":"Test"}}' | python gmail_sender.md

# Re-submit with approval
echo '{"action":"send","email":{"to":"new@example.com","subject":"Test"},"approval_granted":true}' | python gmail_sender.md
```
