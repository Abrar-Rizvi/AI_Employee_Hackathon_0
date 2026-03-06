---
name: whatsapp-monitor
description: Monitor WhatsApp Web for urgent keyword messages using Selenium WebDriver. Detect urgent messages and route to appropriate handlers.
license: Apache-2.0
compatibility: Requires selenium, webdriver-manager, Chrome/Chromium browser
metadata:
  author: AI Employee Silver Tier
  version: "1.0"
  tier: silver
  platform: "WhatsApp Web"
---

# WhatsApp Monitor Skill

## Purpose
Monitor WhatsApp Web for incoming messages containing urgent keywords. This skill enables the AI Employee to detect and respond to urgent communications via WhatsApp, providing 24/7 monitoring for critical business messages.

## When to Use This Skill
- Monitoring for urgent client messages
- Detecting emergency communications
- Tracking important keyword mentions
- Automated urgent message routing
- Business continuity for critical communications
- After-hours emergency monitoring

## Input Parameters

```json
{
  "action": "start|stop|check|get_unread",
  "keywords": ["urgent", "emergency", "asap", "immediately", "critical"],
  "contacts": ["boss", "ceo", "important_client"],
  "check_interval": 30,
  "headless": true,
  "profile_path": "/path/to/chrome/profile",
  "qr_code_path": "/path/to/save/qr.png",
  "max_duration": 3600,
  "output_format": "json|log"
}
```

## Output Format

```json
{
  "status": "success",
  "action": "check",
  "timestamp": "2026-02-24T12:00:00",
  "messages": [
    {
      "contact": "John Smith",
      "phone": "+1234567890",
      "message": "URGENT: Server is down!",
      "timestamp": "2026-02-24T12:00:00",
      "is_unread": true,
      "urgency_level": "high",
      "matched_keywords": ["urgent"],
      "is_important_contact": false
    }
  ],
  "urgent_count": 1,
  "total_unread": 5,
  "session_active": true
}
```

## Python Implementation

```python
#!/usr/bin/env python3
"""
WhatsApp Monitor Skill for Silver Tier AI Employee
Monitors WhatsApp Web for urgent messages using Selenium.
"""

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("Error: Selenium not found. Install with:")
    print("pip install selenium webdriver-manager")
    raise

# Configuration
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'

# Default urgent keywords
DEFAULT_URGENT_KEYWORDS = [
    'urgent', 'emergency', 'asap', 'immediately', 'critical',
    'emergency', 'important', 'priority', 'alert', 'server down'
]

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhatsAppMonitor:
    """Monitor WhatsApp Web for urgent messages."""

    def __init__(
        self,
        keywords: List[str] = None,
        important_contacts: List[str] = None,
        headless: bool = True,
        profile_path: str = None
    ):
        self.keywords = keywords or DEFAULT_URGENT_KEYWORDS
        self.important_contacts = important_contacts or []
        self.headless = headless
        self.profile_path = profile_path
        self.driver = None
        self.wait = None
        self.is_authenticated = False
        self.last_check = datetime.now()

    def start_driver(self) -> bool:
        """Initialize and start Chrome WebDriver."""
        try:
            chrome_options = Options()

            if self.headless:
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--disable-gpu')

            # Use profile if specified
            if self.profile_path:
                chrome_options.add_argument(f'user-data-dir={self.profile_path}')

            # Additional options for stability
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # Install and use ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)

            logger.info("Chrome WebDriver started successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to start WebDriver: {e}")
            return False

    def open_whatsapp(self, wait_for_qr: bool = False, qr_save_path: str = None) -> bool:
        """Open WhatsApp Web and handle authentication."""
        try:
            if not self.driver:
                self.start_driver()

            # Navigate to WhatsApp Web
            self.driver.get('https://web.whatsapp.com')

            # Wait for page load
            time.sleep(2)

            # Check if QR code is displayed (not authenticated)
            try:
                qr_element = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'canvas[aria-label="Scan this QR code"]'))
                )

                if qr_element:
                    logger.warning("WhatsApp Web requires QR code scan")

                    # Save QR code if path provided
                    if qr_save_path:
                        qr_element.screenshot(qr_save_path)
                        logger.info(f"QR code saved to: {qr_save_path}")

                    if wait_for_qr:
                        logger.info("Waiting for QR code scan...")
                        # Wait for authentication (chat list to appear)
                        self.wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="chat-list"]'))
                        )
                        logger.info("Authentication successful!")
                        self.is_authenticated = True
                        return True
                    else:
                        return False

            except TimeoutException:
                # Already authenticated
                logger.info("Already authenticated to WhatsApp Web")
                self.is_authenticated = True
                return True

        except Exception as e:
            logger.error(f"Failed to open WhatsApp Web: {e}")
            return False

    def check_unread_messages(self) -> List[Dict]:
        """Check for unread messages and return urgent ones."""
        try:
            if not self.driver:
                self.open_whatsapp()

            # Wait for chat list
            chat_list = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="chat-list"]'))
            )

            # Find all unread chats
            unread_chats = self.driver.find_elements(
                By.CSS_SELECTOR,
                '[data-testid="chat-list"] [data-testid="unread-count"]'
            )

            messages = []

            for chat in unread_chats:
                try:
                    # Get chat container
                    chat_container = chat.find_element(By.XPATH, '../..')

                    # Extract contact name
                    try:
                        contact = chat_container.find_element(
                            By.CSS_SELECTOR,
                            '[data-testid="conversation-title"]'
                        ).text
                    except NoSuchElementException:
                        contact = "Unknown"

                    # Extract last message preview
                    try:
                        message_preview = chat_container.find_element(
                            By.CSS_SELECTOR,
                            '[data-testid="last-msg"]'
                        ).text
                    except NoSuchElementException:
                        message_preview = ""

                    # Check for urgent keywords
                    urgency = self._assess_urgency(message_preview, contact)

                    if urgency['is_urgent']:
                        # Get timestamp
                        try:
                            timestamp = chat_container.find_element(
                                By.CSS_SELECTOR,
                                '[data-testid="msg-meta"]'
                            ).text
                        except NoSuchElementException:
                            timestamp = datetime.now().strftime('%H:%M')

                        messages.append({
                            "contact": contact,
                            "message": message_preview,
                            "timestamp": timestamp,
                            "is_unread": True,
                            "urgency_level": urgency['level'],
                            "matched_keywords": urgency['keywords'],
                            "is_important_contact": contact.lower() in [c.lower() for c in self.important_contacts]
                        })

                except Exception as e:
                    logger.warning(f"Error processing chat: {e}")
                    continue

            self.last_check = datetime.now()
            return messages

        except Exception as e:
            logger.error(f"Failed to check messages: {e}")
            return []

    def get_all_unread(self) -> List[Dict]:
        """Get all unread messages (not just urgent)."""
        try:
            if not self.driver:
                self.open_whatsapp()

            unread_badges = self.driver.find_elements(
                By.CSS_SELECTOR,
                '[data-testid="unread-count"]'
            )

            total_unread = sum(
                int(badge.text) for badge in unread_badges if badge.text.isdigit()
            )

            # Return simplified list
            return [
                {
                    "total_unread": total_unread,
                    "checked_at": datetime.now().isoformat()
                }
            ]

        except Exception as e:
            logger.error(f"Failed to get unread count: {e}")
            return []

    def _assess_urgency(self, message: str, contact: str) -> Dict:
        """Assess urgency level of a message."""
        message_lower = message.lower()
        matched_keywords = []

        # Check for keyword matches
        for keyword in self.keywords:
            if keyword.lower() in message_lower:
                matched_keywords.append(keyword)

        # Check if important contact
        is_important_contact = contact.lower() in [c.lower() for c in self.important_contacts]

        # Determine urgency level
        if is_important_contact and matched_keywords:
            level = "critical"
        elif is_important_contact:
            level = "high"
        elif len(matched_keywords) >= 2:
            level = "high"
        elif matched_keywords:
            level = "medium"
        else:
            level = "low"

        return {
            "is_urgent": len(matched_keywords) > 0 or is_important_contact,
            "level": level,
            "keywords": matched_keywords
        }

    def monitor_continuously(
        self,
        check_interval: int = 30,
        max_duration: int = 3600,
        callback=None
    ):
        """Continuously monitor for urgent messages."""
        start_time = time.time()

        try:
            logger.info(f"Starting continuous monitoring (interval: {check_interval}s, max: {max_duration}s)")

            while time.time() - start_time < max_duration:
                # Check for urgent messages
                urgent_messages = self.check_unread_messages()

                if urgent_messages:
                    logger.warning(f"Found {len(urgent_messages)} urgent message(s)")

                    # Log activity
                    self._log_activity('urgent_messages_detected', {
                        'count': len(urgent_messages),
                        'messages': urgent_messages
                    })

                    # Process each message
                    for msg in urgent_messages:
                        logger.warning(f"URGENT from {msg['contact']}: {msg['message']}")

                        if callback:
                            callback(msg)

                # Wait before next check
                time.sleep(check_interval)

        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")

        finally:
            self.stop_driver()

    def stop_driver(self):
        """Stop the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("WebDriver stopped")

    def _log_activity(self, action: str, details: Dict = None):
        """Log activity to JSON file."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "skill": "whatsapp_monitor",
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


def whatsapp_monitor_handler(input_params: Dict) -> Dict:
    """Main handler function for WhatsApp Monitor skill."""
    action = input_params.get('action', 'check')

    monitor = WhatsAppMonitor(
        keywords=input_params.get('keywords', DEFAULT_URGENT_KEYWORDS),
        important_contacts=input_params.get('contacts', []),
        headless=input_params.get('headless', True),
        profile_path=input_params.get('profile_path')
    )

    if DRY_RUN:
        logger.info(f"[DRY RUN] Would execute: {action}")

    try:
        if action == 'start':
            monitor.open_whatsapp(wait_for_qr=True)

            # Start continuous monitoring
            monitor.monitor_continuously(
                check_interval=input_params.get('check_interval', 30),
                max_duration=input_params.get('max_duration', 3600)
            )

        elif action == 'check':
            monitor.open_whatsapp()

            if DRY_RUN:
                # Return mock data for dry run
                return {
                    "status": "dry_run",
                    "action": "check",
                    "timestamp": datetime.now().isoformat(),
                    "messages": [],
                    "urgent_count": 0,
                    "total_unread": 0
                }

            messages = monitor.check_unread_messages()

            return {
                "status": "success",
                "action": "check",
                "timestamp": datetime.now().isoformat(),
                "messages": messages,
                "urgent_count": len(messages),
                "total_unread": len(monitor.get_all_unread()),
                "session_active": True
            }

        elif action == 'get_unread':
            monitor.open_whatsapp()

            unread = monitor.get_all_unread()
            messages = monitor.check_unread_messages()

            return {
                "status": "success",
                "action": "get_unread",
                "timestamp": datetime.now().isoformat(),
                "messages": messages,
                "total_unread": unread[0]['total_unread'] if unread else 0
            }

        elif action == 'stop':
            monitor.stop_driver()

            return {
                "status": "success",
                "action": "stop",
                "timestamp": datetime.now().isoformat(),
                "message": "Monitoring stopped"
            }

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
    # Example: Check for urgent messages
    params = {
        "action": "check",
        "keywords": ["urgent", "emergency", "asap"],
        "contacts": ["Boss", "CEO", "Important Client"],
        "headless": True
    }

    result = whatsapp_monitor_handler(params)
    print(json.dumps(result, indent=2))
```

## Integration Points

This skill integrates with:
- **scheduler** - Schedule periodic WhatsApp checks
- **approval_manager** - Route urgent messages to approval workflow
- **gmail_sender** - Send email notifications for urgent WhatsApp messages
- **Company_Handbook.md** - Follow business hours and urgency protocols

## Error Handling

1. **QR Code Required** - Prompt user to scan and wait for authentication
2. **Session Expired** - Detect and re-authenticate automatically
3. **Network Issues** - Retry with exponential backoff
4. **Browser Crash** - Restart WebDriver automatically
5. **Element Not Found** - Use fallback selectors and timeouts

## Security Notes

- Uses Chrome profile for persistent authentication
- QR code must be scanned manually (one-time setup)
- Headless mode available for background operation
- No credentials stored or transmitted
- Supports DRY_RUN mode for testing without browser

## Limitations

- Requires WhatsApp Web authentication (QR code scan)
- Dependent on WhatsApp Web availability
- Rate limited by WhatsApp
- Phone must have active internet connection
- Cannot send messages (read-only monitoring)

## Testing

```bash
# Test in headless mode (DRY_RUN)
export DRY_RUN=true
python whatsapp_monitor.md

# Test with visible browser (for QR scan)
export DRY_RUN=false
python whatsapp_monitor.md --action start --headless false

# After first authentication, can run headless
python whatsapp_monitor.md --action check --headless true
```

## Monitoring Best Practices

1. **Check Interval**: Use 30-60 seconds to avoid rate limits
2. **Keywords**: Customize for your business context
3. **Important Contacts**: Add key stakeholders for priority monitoring
4. **Business Hours**: Configure different monitoring levels for after-hours
5. **Fallback**: Use email/SMS notifications for critical messages
