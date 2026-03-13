# Gold Tier - Personal AI Employee

The Gold Tier is the advanced level of the Personal AI Employee Hackathon. It provides cross-platform social media automation, advanced AI reasoning with orchestrator coordination, multi-poster capabilities, and comprehensive error handling using Claude Code and Obsidian.

## What Gold Tier Does

- **Monitors Gmail inbox** for important emails using OAuth2 authentication
- **Watches file system** for incoming documents and tasks from Drop_Folder
- **Automatically posts to Facebook** to AI Employee Services Facebook Page using Playwright
- **Automatically posts to Instagram** via Meta Business Suite using Playwright
- **Processes tasks autonomously** using Claude Code reasoning engine
- **Coordinates multiple posters** for different social media platforms
- **Sends emails via MCP** server for external communication
- **Maintains human approval workflow** for all sensitive actions
- **Runs scheduled tasks** via cron or continuous execution
- **Logs all activities** to JSON files for complete audit trails
- **Persists sessions** for Facebook/Instagram to avoid repeated logins

## Folder Structure

```
Gold/
├── Dashboard.md                 # Live dashboard with stats and activities
├── Company_Handbook.md          # Business rules and approval thresholds
├── Needs_Action/                # Incoming tasks waiting to be processed
├── Plans/                       # Step-by-step plans created by Claude
├── Approved/                    # Tasks and posts approved for execution
├── Rejected/                     # Tasks and posts rejected by human
├── Pending_Approval/          # Items awaiting human review
├── Done/                        # Completed tasks and sent posts
├── Logs/                        # Daily JSON logs and error logs
├── Briefings/                   # Generated CEO weekly briefings
├── Accounting/                   # Financial records and reports
├── Drop_Folder/                 # Drop location for manual file input
├── Skills/                      # Documentation of Claude's skills
├── Config/                      # System configuration and credentials
├── Watchers/                    # Autonomous monitoring and automation scripts
│   ├── base_watcher.py         # Base class for all watchers
│   ├── gmail_watcher.py        # Monitors Gmail for important emails
│   ├── filesystem_watcher.py   # Monitors Drop_Folder for new files
│   ├── facebook_login_helper.py  # Facebook login utilities
│   ├── facebook_poster.py      # Posts to Facebook page
│   └── instagram_poster.py     # Posts to Instagram via Meta Business Suite
├── MCP/                          # Model Context Protocol servers
│   └── gmail_send_server/      # MCP server for sending emails
│       ├── index.js            # Main MCP server
│       ├── package.json        # Dependencies
│       ├── test-email.js       # Test script
│       ├── setup.sh            # Installation helper
│       └── README.md           # MCP documentation
├── orchestrator.py             # Main task processor and coordinator
├── .env                         # Environment configuration
└── README.md                   # This file
```

## How to Run

### Prerequisites

### System Requirements
- **Python 3.10+** for Python scripts and orchestrator
- **Node.js 18+** for MCP server
- **Google Cloud Project** with Gmail API enabled
- **Facebook/Instagram Account** with Business Suite access to AI Employee page
- **Claude Code** CLI tool installed and configured
- **Playwright** browsers installed

### Python Dependencies
```bash
pip install watchdog python-dotenv playwright google-api-python-client google-auth-oauthlib google-auth-httplib2
```

### Playwright Installation
```bash
pip install playwright
playwright install chromium
```

### Node.js Dependencies
```bash
cd MCP/gmail_send_server
npm install
```

## How to Setup

### 1. Gmail API Setup

1. **Create Google Cloud Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project

2. **Enable Gmail API:**
   - Go to APIs & Services → Library
   - Search for "Gmail API"
   - Click "Enable"

3. **Create OAuth Credentials:**
   - Go to APIs & Services → Credentials
   - Create credentials → OAuth client ID
   - Application type: Desktop app
   - Add authorized redirect URIs (for local testing)

4. **Download and Save Credentials:**
   - Download the JSON file
   - Save to `Gold/Config/gmail_credentials.json`

5. **Generate Initial Token:**
   - Run any Gmail watcher script once
   - Complete OAuth flow in browser
   - Token will be saved to `Config/gmail_token.json`

### 2. Facebook/Instagram Setup

1. **Create Facebook Business Manager Account:**
   - Go to [business.facebook.com](https://business.facebook.com/)
   - Create business account (if needed)

2. **Add AI Employee Page:**
   - Create a Facebook Page for your AI Employee
   - Add the page to your Business Manager
   - Note the Page ID (e.g., 61585008727787)

3. **Connect Instagram to Meta Business Suite:**
   - In Business Manager, go to Accounts → Instagram Accounts
   - Add your Instagram business account
   - Grant posting permissions

4. **Save Credentials to .env:**
   ```bash
   FACEBOOK_EMAIL=your-email@example.com
   FACEBOOK_PASSWORD=your-password
   FACEBOOK_PAGE_ID=61585008727787
   INSTAGRAM_BUSINESS_ID=your-business-id
   INSTAGRAM_HEADLESS=false
   ```

### 3. MCP Server Setup

1. **Install Gmail Send MCP Server:**
   ```bash
   cd Gold/MCP/gmail_send_server
   npm install
   ```

2. **Configure Claude Code for MCP:**
   - Edit `~/.config/claude-code/mcp.json`
   ```json
   {
     "servers": [
       {
         "name": "gmail",
         "command": "node",
         "args": ["/absolute/path/to/Gold/MCP/gmail_send_server/index.js"],
         "env": {
           "GMAIL_CREDENTIALS": "/absolute/path/to/Gold/Config/gmail_credentials.json"
         }
       }
     ]
   }
   ```

3. **Restart Claude Code** to load new MCP configuration

### 4. Environment Configuration

Create/Edit `Gold/.env` file:
```bash
# Vault Path
VAULT_PATH=/mnt/d/AI_Employee_Hackathon_0/Gold

# Dry Run Mode (set to 'false' for production)
DRY_RUN=false

# Log Level
LOG_LEVEL=INFO

# Gmail Configuration
GMAIL_CREDENTIALS=/mnt/d/AI_Employee_Hackathon_0/Gold/Config/gmail_credentials.json
GMAIL_TOKEN=/mnt/d/AI_Employee_Hackathon_0/Gold/Config/gmail_token.json
GMAIL_REFRESH_TOKEN=/mnt/d/AI_Employee_Hackathon_0/Gold/Config/gmail_refresh_token.json
GMAIL_USER_EMAIL=your-email@gmail.com
GMAIL_CHECK_INTERVAL=30
MAX_ITERATIONS=0

# Facebook/Instagram Configuration
FACEBOOK_EMAIL=your-facebook-email@example.com
FACEBOOK_PASSWORD=your-facebook-password
FACEBOOK_PAGE_ID=61585008727787
INSTAGRAM_BUSINESS_ID=your-business-id
INSTAGRAM_HEADLESS=false
INSTAGRAM_ACCOUNT=your-instagram-username

# Browser Configuration
BROWSER_HEADLESS=false
BROWSER_TIMEOUT=30000
VIEWPORT_WIDTH=1280
VIEWPORT_HEIGHT=800

# Watcher Configuration
CHECK_INTERVAL=60
```

## How to Run

### Option 1: Run Individual Components (Development/Testing)

You need multiple terminal windows for full operation:

**Terminal 1 - MCP Server (Required for Gmail operations):**
```bash
cd /mnt/d/AI_Employee_Hackathon_0/Gold/MCP/gmail_send_server
npm start
```

**Terminal 2 - Gmail Watcher:**
```bash
cd /mnt/d/AI_Employee_Hackathon_0/Gold/Watchers
python gmail_watcher.py
```

**Terminal 3 - File System Watcher:**
```bash
cd /mnt/d/AI_Employee_Hackathon_0/Gold/Watchers
python filesystem_watcher.py
```

**Terminal 4 - Facebook Poster:**
```bash
cd /mnt/d/AI_Employee_Hackathon_0/Gold/Watchers
python facebook_poster.py --once
```

**Terminal 5 - Instagram Poster:**
```bash
cd /mnt/d/AI_Employee_Hackathon_0/Gold/Watchers
python instagram_poster.py --once
```

**Terminal 6 - Orchestrator:**
```bash
cd /mnt/d/AI_Employee_Hackathon_0/Gold
python orchestrator.py
```

### Option 2: Run All via PM2 (Recommended for Production)

Install PM2:
```bash
npm install -g pm2
```

Start all services:
```bash
# Start MCP server
cd /mnt/d/AI_Employee_Hackathon_0/Gold/MCP/gmail_send_server
pm2 start npm start --name "gmail-mcp-server"
pm2 save

# Start Orchestrator
cd /mnt/d/AI_Employee_Hackathon_0/Gold
pm2 start orchestrator.py --name "ai-employee-orchestrator" --interpreter python3
pm2 save

# Start additional watchers (optional)
cd /mnt/d/AI_Employee_Hackathon_0/Gold/Watchers
pm2 start gmail_watcher.py --name "gmail-watcher"
pm2 start filesystem_watcher.py --name "filesystem-watcher"
pm2 save

# Configure PM2 to start on boot
pm2 startup
```

### Option 3: Run via Cron (Automated Scheduling)

Add to your crontab (`crontab -e`):
```bash
# Check for new emails every 5 minutes
*/5 * * * * cd /mnt/d/AI_Employee_Hackathon_0/Gold/Watchers && python gmail_watcher.py --iterations=1 >> /mnt/d/AI_Employee_Hackathon_0/Gold/Logs/cron.log 2>&1

# Check file system every 2 minutes
*/2 * * * * cd /mnt/d/AI_Employee_Hackathon_0/Gold/Watchers && python filesystem_watcher.py --iterations=1 >> /mnt/d/AI_Employee_Hackathon_0/Gold/Logs/cron.log 2>&1

# Process tasks every minute
* * * * * cd /mnt/d/AI_Employee_Hackathon_0/Gold && python orchestrator.py --iterations=1 >> /mnt/d/AI_Employee_Hackathon_0/Gold/Logs/cron.log 2>&1
```

## How It Works

### Gmail Monitoring Flow
```
Gmail Watcher runs
  ↓
Uses OAuth2 to authenticate
  ↓
Checks for unread important emails
  ↓
Creates task file in Needs_Action/
  ↓
Logs to Logs/YYYY-MM-DD.json
```

### File System Monitoring Flow
```
File System Watcher runs
  ↓
Monitors Drop_Folder/ for new files
  ↓
Detects new files
  ↓
Creates task file in Needs_Action/
  ↓
Logs to Logs/YYYY-MM-DD.json
```

### Facebook Posting Flow
```
Approved folder monitored
  ↓
Detects FB_*.md files
  ↓
Extracts content and image path
  ↓
Launches Playwright with persistent session
  ↓
Logs into Facebook (uses saved session or credentials)
  ↓
Navigates to Facebook page
  ↓
Finds post creation box
  ↓
Types content and uploads images
  ↓
Clicks "Post" button
  ↓
Takes screenshot for verification
  ↓
Moves file to Done/
  ↓
Logs to Logs/YYYY-MM-DD.json
```

### Instagram Posting Flow
```
Approved folder monitored
  ↓
Detects IG_*.md files
  ↓
Extracts content and image path
  ↓
Launches Playwright with persistent session
  ↓
Logs into Facebook (Instagram uses Meta Business Suite)
  ↓
Navigates to Meta Business Suite composer
  ↓
Presses Escape to close popups
  ↓
Clicks "Add photo" dropdown
  ↓
Clicks "Upload from desktop" with file chooser
  ↓
Uploads image via file chooser
  ↓
Types caption in content input
  ↓
Clicks "Publish" button
  ↓
Takes screenshot for verification
  ↓
Moves file to Done/
  ↓
Logs to Logs/YYYY-MM-DD.json
```

### Orchestrator Task Processing Flow
```
Scans Needs_Action/ folder
  ↓
Invokes text_analyzer skill
  ↓
Determines task intent and priority
  ↓
Creates PLAN_*.md in Plans/ folder
  ↓
Invokes appropriate skills based on plan
  ↓
Creates draft in Pending_Approval/
  ↓
Waits for human approval (move to Approved/ or Rejected/)
  ↓
Executes action (email, social post, etc.)
  ↓
Moves all files to Done/
  ↓
Updates Dashboard.md
  ↓
Logs to Logs/YYYY-MM-DD.json
```

## How to Test

### 1. Test Gmail Watcher
```bash
cd /mnt/d/AI_Employee_Hackathon_0/Gold/Watchers
python gmail_watcher.py
```

**Expected behavior:**
- Checks for unread important emails
- Creates `EMAIL_*.md` files in `Needs_Action/`
- Logs activities to `Logs/YYYY-MM-DD.json`

**Verify:**
- `Needs_Action/` contains new `EMAIL_*.md` file
- `Logs/YYYY-MM-DD.json` has new entry
- `Config/GmailWatcher_state.json` updated

### 2. Test File System Watcher
```bash
# Create a test file
echo "Test task for AI Employee" > /mnt/d/AI_Employee_Hackathon_0/Gold/Drop_Folder/test.txt

# Run watcher
cd /mnt/d/AI_Employee_Hackathon_0/Gold/Watchers
python filesystem_watcher.py
```

**Expected behavior:**
- Detects `test.txt` in `Drop_Folder/`
- Creates `FILE_test.md` in `Needs_Action/`

**Verify:**
- `Needs_Action/` contains `FILE_test.md`
- `Logs/YYYY-MM-DD.json` has new entry

### 3. Test Facebook Poster

**Step 1:** Create test post in `Approved/`
```bash
cat > /mnt/d/AI_Employee_Hackathon_0/Gold/Approved/FB_test_post.md << 'EOF'
---
type: facebook_post
status: pending

## Post Content
This is a test post from my AI Employee!

#AI #Automation #Testing
EOF
```

**Step 2:** Run poster
```bash
cd /mnt/d/AI_Employee_Hackathon_0/Gold/Watchers
python facebook_poster.py --once
```

**Expected behavior:**
- Logs into Facebook
- Posts content to specified page
- Takes screenshot
- Moves file to `Done/`

**Verify:**
- `Done/` contains `FB_test_post.md`
- `Config/FacebookPoster_state.json` updated
- Post appears on your Facebook page
- Screenshot in `Config/after_post.png`

### 4. Test Instagram Poster

**Step 1:** Create test post in `Approved/`
```bash
cat > /mnt/d/AI_Employee_Hackathon_0/Gold/Approved/IG_test_post.md << 'EOF'
---
type: instagram_post
status: pending

## Post Content
This is a test post from my AI Employee! 📸

#AI #Automation #Testing
EOF
```

**Step 2:** Run poster
```bash
cd /mnt/d/AI_Employee_Hackathon_0/Gold/Watchers
python instagram_poster.py --once
```

**Expected behavior:**
- Logs into Facebook/Meta
- Navigates to Meta Business Suite
- Uploads image (from `Config/ig_default_image.png`)
- Posts caption
- Takes screenshots
- Moves file to `Done/`

**Verify:**
- `Done/` contains `IG_test_post.md`
- `Config/InstagramPoster_state.json` updated
- Post appears on your Instagram account
- Screenshots in `Config/` show successful upload

### 5. Test Full Workflow

**Step 1:** Create manual task
```bash
cat > /mnt/d/AI_Employee_Hackathon_0/Gold/Needs_Action/MANUAL_test_task.md << 'EOF'
---
type: manual_task
priority: medium
status: pending

# Task
Please draft a professional email response to the client inquiry about the new pricing model. Include the following information:
- Pricing tiers overview
- Key features comparison
- Recommendation for their use case

# Notes
This is a manual test task to verify the complete workflow.
EOF
```

**Step 2:** Run orchestrator
```bash
cd /mnt/d/AI_Employee_Hackathon_0/Gold
python orchestrator.py
```

**Expected behavior:**
- Task detected in `Needs_Action/`
- Plan created in `Plans/`
- Draft email created in `Pending_Approval/`
- Dashboard updated

**Step 3:** Approve action
```bash
# Move to Approved folder
mv /mnt/d/AI_Employee_Hackathon_0/Gold/Pending_Approval/EMAIL_client_inquiry.md /mnt/d/AI_Employee_Hackathon_0/Gold/Approved/

# Run orchestrator again
python orchestrator.py
```

**Step 4:** Verify completion
- Check `Pending_Approval/` is empty
- Check `Approved/` contains `EMAIL_client_inquiry_draft.md`
- Check `Done/` contains original task and plan
- Check `Dashboard.md` updated

## Configuration

### Edit `Config/system_config.json`
```json
{
  "check_interval": 60,
  "max_iterations": 5,
  "dry_run": true
}
```

**Settings:**
- `check_interval`: Seconds between orchestrator checks (60 = 1 minute)
- `max_iterations`: Max autonomous iterations before stopping (0 = unlimited)
- `dry_run`: Safety mode - set to `false` for production

### Watcher Configuration

Each watcher maintains its own state file in `Config/`:

- `GmailWatcher_state.json` - Processed email IDs
- `FacebookPoster_state.json` - Processed Facebook posts
- `InstagramPoster_state.json` - Processed Instagram posts
- `LinkedInPoster_state.json` - Processed LinkedIn posts (Silver)

State files contain:
- `processed_files`: List of already processed items
- `last_updated`: Timestamp of last update

## Security Notes

- **DRY_RUN is true by default** - No real external actions are taken without explicit approval
- **No network requests** are made without approval
- **All actions are logged** to `Logs/` for audit trails
- **File operations are scoped** to Gold folder only
- **Approval thresholds** are enforced per `Company_Handbook.md`
- **Session persistence** reduces authentication frequency and security risk
- **Credentials stored locally** in `Config/` and `.env` (never in git)

## Agent Skills

Gold Tier includes all 12 specialized Agent Skills:
- `file_processor` - Read and write files to vault
- `text_analyzer` - Analyze content and extract intent
- `task_planner` - Create step-by-step execution plans
- `email_drafter` - Draft email responses
- `data_extractor` - Extract structured data from text
- `gmail_reader` - Read and analyze Gmail emails
- `gmail_sender` - Send emails via Gmail API
- `whatsapp_monitor` - Monitor WhatsApp for important messages
- `linkedin_poster` - Create and post LinkedIn content
- `scheduler` - Schedule tasks and reminders
- `plan_creator` - Create detailed project plans
- `approval_manager` - Handle approval workflow

See `Skills/README.md` for detailed documentation of each skill.

## Troubleshooting

### Gmail Authentication Issues
**Problem:** "Invalid credentials" or "401 error" in logs
**Solution:**
1. Delete `Config/gmail_token.json`
2. Run `gmail_watcher.py` to trigger new OAuth flow
3. Complete authentication in browser
4. New token will be saved automatically

### Facebook Login Timeout
**Problem:** "Login timeout" or "Elements not found"
**Solution:**
1. Delete `Config/facebook_session/` folder
2. Run `facebook_poster.py` with `HEADLESS=false` to see browser
3. Complete login in visible browser window
4. Session will be saved for future runs

### Instagram Image Upload Timeout
**Problem:** "Image upload failed" or "File chooser timeout"
**Solution:**
1. Check `Config/upload_debug.png` screenshot
2. Verify "Add photo" dropdown is visible
3. Check Meta Business Suite UI hasn't changed
4. Increase `BROWSER_TIMEOUT` in `.env` if needed
5. Verify `Config/ig_default_image.png` exists

### Orchestrator Not Processing Tasks
**Problem:** Tasks in `Needs_Action/` not being processed
**Solution:**
1. Check `Config/system_config.json` has `"dry_run": false`
2. Verify `VAULT_PATH` in `.env` is correct
3. Check all folders exist (`Needs_Action`, `Plans`, `Done`, etc.)
4. Check `Logs/YYYY-MM-DD.json` for error messages
5. Restart orchestrator

### Posts Not Appearing on Social Media
**Problem:** File moved to `Done/` but post not visible
**Solution:**
1. Check `Logs/YYYY-MM-DD.json` for "Post successful" confirmation
2. Verify credentials in `.env` are correct
3. Check page ID for Facebook matches your AI Employee page
4. Verify Instagram account is connected to Meta Business Suite
5. Review screenshots in `Config/` folder

### Session Persistence Not Working
**Problem:** Login required every run despite session folder existing
**Solution:**
1. Check `Config/{platform}_session/` folder exists and is writable
2. Verify session folder path in script matches `.env`
3. Check browser permissions (read/write for session folder)
4. Check for antivirus blocking session writes
5. Try running with `HEADLESS=false` first time

## Monitoring

### Dashboard
Check `Gold/Dashboard.md` for:
- Task counts by status (Needs_Action, Plans, Done)
- Recent activities
- Agent skill usage
- System health

### Logs
View daily logs:
```bash
# Today's logs
cat /mnt/d/AI_Employee_Hackathon_0/Gold/Logs/$(date +%Y-%m-%d).json | jq

# Real-time monitoring
tail -f /mnt/d/AI_Employee_Hackathon_0/Gold/Logs/$(date +%Y-%m-%d).json
```

### State Files
Monitor watcher state files:
```bash
# Gmail watcher state
cat Gold/Config/GmailWatcher_state.json

# Facebook poster state
cat Gold/Config/FacebookPoster_state.json

# Instagram poster state
cat Gold/Config/InstagramPoster_state.json
```

## What's Next - Gold Tier Completion Status

### Completed Components ✅
- ✅ **Facebook Poster** - Automated posting to AI Employee Facebook Page
- ✅ **Instagram Poster** - Automated posting via Meta Business Suite
- ✅ **Facebook Login Helper** - Session persistence for Facebook
- ✅ **Gmail Watcher** - Monitors Gmail inbox
- ✅ **File System Watcher** - Monitors Drop_Folder
- ✅ **Base Watcher** - Abstract base class
- ✅ **Orchestrator** - Main task coordinator
- ✅ **MCP Gmail Send Server** - Email sending capability
- ✅ **Facebook Session** - Persistent browser session
- ✅ **Default Instagram Image** - `Config/ig_default_image.png`
- ✅ **Environment Configuration** - `.env` for all credentials

### Pending Components ⏳
- ⏳ **Twitter/X Integration** - Automated posting to Twitter
- ⏳ **Odoo Accounting + MCP** - Self-hosted accounting integration
- ⏳ **CEO Weekly Briefing** - Automated business audit and reporting
- ⏳ **Ralph Wiggum Loop** - Autonomous multi-step task completion
- ⏳ **Error Recovery / Watchdog** - Self-healing workflows

### Next Steps for Completion

1. **Twitter/X Integration:**
   - Create `twitter_poster.py` using Playwright
   - Authenticate with Twitter credentials
   - Implement post creation and scheduling
   - Add to orchestrator workflow

2. **Odoo Accounting:**
   - Install Odoo Community locally
   - Configure JSON-RPC API access
   - Create MCP Odoo server
   - Integrate invoice creation and tracking
   - Add P&L balance sheet management

3. **CEO Weekly Briefing:**
   - Create `briefing_generator.py` skill
   - Integrate with accounting data
   - Generate weekly revenue reports
   - Track bottlenecks and optimization opportunities
   - Create briefings in `Briefings/` folder

4. **Ralph Wiggum Loop:**
   - Implement stop hook in orchestrator
   - Detect when task completes (file moves to Done/)
   - Auto-continue until success or max iterations
   - Enable autonomous multi-step workflows

5. **Error Recovery / Watchdog:**
   - Create `watchdog.py` to monitor critical processes
   - Auto-restart failed watchers and MCP server
   - Alert on repeated failures
   - Implement graceful degradation for partial outages

6. **Cloud Deployment:**
   - Deploy to Oracle Cloud Free Tier or similar
   - Configure process manager (PM2) for auto-start
   - Set up cloud-specific `.env` with cloud paths
   - Implement health monitoring with alerts
   - Enable 24/7 operation

## Migration from Silver to Gold

If you're upgrading from Silver Tier:

1. ✅ **Keep Silver folder intact** - It will continue working
2. ✅ **Copy `.env` file** - Use Silver settings as starting point
3. ✅ **Migrate processed files** - Move relevant Done/ items if needed
4. ✅ **Update MCP config** - Add Gold MCP servers (future)
5. ✅ **Install new dependencies** - Playwright for Instagram
6. ✅ **Test incrementally** - Start with one watcher, add more gradually
7. ✅ **Review LinkedIn Poster** - Ensure still working if needed

## Support

For issues or questions:
1. Check `Logs/YYYY-MM-DD.json` for detailed error messages
2. Review screenshots in `Config/` for automation failures
3. Consult `Company_Handbook.md` for business rules
4. Review `ARCHITECTURE.md` for complete system understanding
5. Check each watcher's state file in `Config/`

## License

MIT License - Part of Personal AI Employee Hackathon 0

## Summary

Gold Tier transforms your AI Employee from an **active assistant** (Silver Tier) to a **fully autonomous digital FTE** that works across multiple platforms with intelligent reasoning and comprehensive error handling.

**Key Achievements:**
- 📧 **Multi-platform social media automation** (Facebook + Instagram)
- 📧 **Robust session management** for reduced login friction
- 📧 **Advanced error handling** with screenshots for debugging
- 📧 **Comprehensive logging** for complete audit trails
- 📧 **Scalable architecture** ready for cloud deployment
- 📧 **Human oversight maintained** via approval workflows

**The result: A Digital FTE that works 24/7, handles multiple communication channels, and provides business intelligence while keeping you in control! 🚀
