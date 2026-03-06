# Silver Tier Watchers

This directory contains automated watchers that monitor external services and create action files when new items are detected.

## Available Watchers

### Gmail Watcher (`gmail_watcher.py`)
Monitors Gmail inbox for unread important emails and creates task files.

**Features:**
- Checks for unread important emails every 120 seconds
- Creates `.md` task files in `Needs_Action/` folder
- Tracks processed email IDs to avoid duplicates
- Logs all activities to `Logs/` folder in JSON format
- Supports DRY_RUN mode for testing
- Retry logic with exponential backoff
- BaseWatcher pattern for extensibility

### LinkedIn Poster (`linkedin_poster.py`)
Automatically posts approved content to LinkedIn using Playwright automation.

**Features:**
- Watches `Approved/` folder for `linkedin_post` type files
- Uses Playwright with Chromium for LinkedIn Web automation
- Persistent session storage for automatic login
- Human-in-the-loop approval workflow (move from Pending_Approval to Approved)
- Moves completed posts to `Done/` folder
- DRY_RUN mode for testing without posting
- Handles LinkedIn security verification
- Comprehensive error logging with retry logic

## Setup

### 1. Install Dependencies

```bash
pip install google-auth google-auth-oauthlib google-api-python-client python-dotenv
```

### 2. Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials:
   - Go to Credentials → Create Credentials → OAuth client ID
   - Application type: Desktop app
   - Download credentials JSON
5. Save credentials as `Config/gmail_credentials.json`

### 3. Configure Environment

Edit `.env` file:
```bash
VAULT_PATH=/mnt/d/AI_Employee_Hackathon_0/Silver
DRY_RUN=true
GMAIL_CHECK_INTERVAL=120
```

## Running Watchers

### Gmail Watcher

```bash
# Test in dry-run mode
cd /mnt/d/AI_Employee_Hackathon_0/Silver/Watchers
python gmail_watcher.py

# Run with actual operations
DRY_RUN=false python gmail_watcher.py
```

## Output Format

When a new email is detected, an action file is created in `Needs_Action/`:

```markdown
---
type: email
from: sender@example.com
subject: Email Subject
received: Date
priority: high
status: pending
email_id: 1234567890abcdef
thread_id: 1234567890abcdef
---

# Email: Email Subject

**From:** sender@example.com
**To:** recipient@example.com
**Date:** Date
**Priority:** HIGH

## Email Body

Email content here...

## Actions Required

- [ ] Review email content
- [ ] Determine appropriate response
- [ ] Check Company_Handbook.md for approval requirements
- [ ] Draft response if needed
```

## State Management

Watchers maintain state in `Config/` folder:
- `gmail_token.json` - OAuth authentication token
- `GmailWatcher_state.json` - Processed email IDs

## Logging

All activities logged to `Logs/` folder:
- `YYYY-MM-DD.json` - Daily activity logs in JSON format
- `watcher.log` - General watcher logs

## Extending

To create a new watcher:

1. Extend `BaseWatcher` class
2. Implement `check_for_updates()` method
3. Implement `create_action_file()` method
4. Add authentication logic if needed

Example:
```python
from base_watcher import BaseWatcher

class MyWatcher(BaseWatcher):
    def check_for_updates(self):
        # Return list of items to process
        return []

    def create_action_file(self, item):
        # Create action file and return result
        return {'status': 'success'}
```

## LinkedIn Poster Usage

### Setup

1. **Install Playwright:**
```bash
pip install playwright
playwright install chromium
```

2. **Configure .env:**
```bash
LINKEDIN_EMAIL=your_email@gmail.com
LINKEDIN_PASSWORD=your_password
LINKEDIN_HEADLESS=true
DRY_RUN=true  # Start with true for testing
```

### Creating LinkedIn Posts

Create a markdown file in `Pending_Approval/` with the following format:

```markdown
---
type: linkedin_post
status: pending
created: 2026-03-03
---

# Your Post Title Here

Your post content goes here. Write something engaging!

## Key Points
- Point 1
- Point 2
- Point 3

#Tags #For #Visibility
```

### Approval Workflow

1. **Create Draft:** Add post to `Pending_Approval/` folder with `type: linkedin_post`
2. **Review:** Check the content in Obsidian or your editor
3. **Approve:** Move file from `Pending_Approval/` to `Approved/`
4. **Post:** The LinkedIn Poster will automatically detect and post it
5. **Done:** Successfully posted files are moved to `Done/`

### Running

```bash
# Test in dry-run mode (recommended first)
cd /mnt/d/AI_Employee_Hackathon_0/Silver/Watchers
python linkedin_poster.py

# Run with actual posting
export DRY_RUN=false
python linkedin_poster.py

# Run continuously
python linkedin_poster.py --continuous --interval=60

# Run single iteration
python linkedin_poster.py --iterations=1
```

### Testing with Test Helper

A test helper script is available to verify your setup:

```bash
# Test login only
python test_linkedin_poster.py --test login

# Test folder structure
python test_linkedin_poster.py --test folder

# Test dry-run posting
python test_linkedin_poster.py --test dry-run

# Run all tests
python test_linkedin_poster.py --test all
```

**Recommended Testing Flow:**
1. Run `--test login` to verify login works (browser will open)
2. Run `--test folder` to check folder structure and find approved posts
3. Run `--test dry-run` to test posting without actually posting
4. When ready, set `DRY_RUN=false` in `.env` and run the main script

### Session Management

The LinkedIn Poster automatically handles sessions:

- **First Run:** Runs in visible mode (headless=False) for you to complete login
- **Session Saved:** After successful login, session is saved to `Config/linkedin_session/`
- **Subsequent Runs:** Uses saved session, runs in headless mode

If you encounter security verification:
1. The script will pause and ask you to complete verification manually
2. Complete the verification in the browser window
3. The session will be saved for future use

### Troubleshooting

**Login Issues:**
- Delete `Config/linkedin_session/` folder and try again
- Make sure credentials are correct in `.env`
- Check for security verification prompts

**Post Button Not Found:**
- LinkedIn may have changed their UI
- The script uses multiple selectors to find elements
- Check the logs for specific errors

**Session Not Persisting:**
- Ensure `Config/linkedin_session/` has write permissions
- Check if cookies.json is being created
- LinkedIn may require re-authentication after some time

## Troubleshooting

### Authentication Error
- Verify `gmail_credentials.json` exists
- Check Gmail API is enabled in Google Cloud Console
- Delete `gmail_token.json` and re-authenticate

### No Emails Detected
- Check Gmail inbox for unread important emails
- Verify query filters in `check_for_updates()`
- Check `watcher.log` for errors

### Permission Errors
- Ensure correct OAuth scopes are configured
- Verify credentials file permissions
