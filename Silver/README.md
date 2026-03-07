# Silver Tier - Personal AI Employee

The Silver Tier is the advanced level of the Personal AI Employee Hackathon. It provides autonomous email monitoring, social media automation, external action capabilities via MCP servers, and human-in-the-loop approval workflows using Claude Code and Obsidian.

## What Silver Tier Does

- **Monitors Gmail inbox** for important emails using OAuth2 authentication
- **Watches the file system** for incoming documents and tasks
- **Automatically posts to LinkedIn** using Playwright browser automation
- **Sends emails via MCP server** for external communication
- **Maintains human approval workflow** for all autonomous actions
- **Runs automated tasks** via cron scheduling
- **Logs all activities** to JSON files for complete audit trails
- **Integrates with Claude Code** for intelligent task processing
- **Supports 12 specialized Agent Skills** for various operations
- **Persists LinkedIn sessions** to avoid repeated logins
- **Plans complex multi-step tasks** with reasoning and approval

## What's New in Silver Tier

Bronze Tier capabilities **PLUS**:

- ✅ **Gmail Watcher** with OAuth2 and label management
- ✅ **LinkedIn Auto-Poster** with Playwright automation
- ✅ **Gmail Send MCP Server** for external email sending
- ✅ **Enhanced approval workflow** with multiple stages
- ✅ **Cron/Task Scheduler** for automated execution
- ✅ **Session persistence** for LinkedIn and other services
- ✅ **Improved error handling** with automatic retries
- ✅ **JSON structured logging** for all activities
- ✅ **Smart login detection** to avoid repeated authentication
- ✅ **Dry-run mode** for safe testing without external actions

## Folder Structure

```
Silver/
├── Dashboard.md                 # Live dashboard with stats and activities
├── Company_Handbook.md          # Business rules and approval thresholds
├── Needs_Action/                # Incoming tasks waiting to be processed
├── Plans/                       # Step-by-step plans created by Claude
├── Approved/                    # Tasks and posts approved for execution
├── Rejected/                    # Tasks and posts rejected
├── Pending_Approval/            # Items awaiting human review
├── Done/                        # Completed tasks and sent posts
├── Logs/                        # Daily JSON logs and error logs
├── Skills/                      # Documentation of Claude's skills
├── Config/                      # System configuration and credentials
├── Watchers/                    # Autonomous monitoring scripts
│   ├── base_watcher.py         # Base class for all watchers
│   ├── gmail_watcher.py        # Monitors Gmail for important emails
│   ├── filesystem_watcher.py   # Monitors Drop_Folder for new files
│   ├── linkedin_poster.py      # Auto-posts to LinkedIn
│   └── test_linkedin_poster.py # Test helper for LinkedIn poster
├── MCP/                         # Model Context Protocol servers
│   └── gmail_send_server/      # MCP server for sending emails
│       ├── index.js            # Main MCP server
│       ├── package.json        # Dependencies
│       ├── test-email.js       # Test script
│       └── README.md           # MCP documentation
├── orchestrator.py              # Main task processor
├── .env                         # Environment configuration
└── README.md                    # This file
```

## Prerequisites

### System Requirements

- **Python 3.8+** for Python scripts
- **Node.js 18+** for MCP servers
- **Google Cloud Project** with Gmail API enabled
- **LinkedIn account** for auto-posting
- **Claude Code** CLI tool installed

### Python Dependencies

```bash
pip install watchdog python-dotenv google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### Node.js Dependencies

```bash
cd /mnt/d/AI_Employee_Hackathon_0/Silver/MCP/gmail_send_server
npm install
```

### Playwright Installation (for LinkedIn)

```bash
pip install playwright
playwright install chromium
```

## How to Setup

### 1. Gmail API Setup

1. **Create Google Cloud Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable **Gmail API**

2. **Create OAuth Credentials:**
   - Go to **APIs & Services** → **Credentials**
   - Create **OAuth 2.0 Client ID**
   - Application type: **Desktop app**
   - Download credentials JSON

3. **Save Credentials:**
   ```bash
   mv ~/Downloads/client_secret_*.json /mnt/d/AI_Employee_Hackathon_0/Silver/Config/gmail_credentials.json
   ```

4. **Generate Access Token:**
   - Run any Gmail watcher script
   - Complete the OAuth flow in your browser
   - Token will be saved automatically to `Config/gmail_token.json`

### 2. LinkedIn Setup

1. **Create LinkedIn account** (or use existing)
2. **Add credentials to .env:**
   ```bash
   LINKEDIN_EMAIL=your_email@gmail.com
   LINKEDIN_PASSWORD=your_password
   LINKEDIN_HEADLESS=true
   ```

3. **First login will be visible** - complete it once
4. **Session is saved** - subsequent runs use saved session

### 3. Environment Configuration

Create/edit `/mnt/d/AI_Employee_Hackathon_0/Silver/.env`:

```bash
# Vault Path
VAULT_PATH=/mnt/d/AI_Employee_Hackathon_0/Silver

# Dry Run Mode (set to 'false' for actual operations)
DRY_RUN=true

# Log Level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Gmail Configuration
GMAIL_CREDENTIALS=/mnt/d/AI_Employee_Hackathon_0/Silver/Config/gmail_credentials.json
GMAIL_TOKEN=/mnt/d/AI_Employee_Hackathon_0/Silver/Config/gmail_token.json
GMAIL_CHECK_INTERVAL=30

# LinkedIn Configuration
LINKEDIN_EMAIL=your_email@gmail.com
LINKEDIN_PASSWORD=your_password
LINKEDIN_HEADLESS=true

# Max Iterations (0 = unlimited)
MAX_ITERATIONS=0
```

### 4. MCP Server Registration

The Gmail Send MCP server is already registered in Claude Code config at:
`~/.config/claude-code/mcp.json`

To use it, restart Claude Code after installation.

## How to Run

### Option 1: Run All Watchers Individually

You need **multiple terminal windows**:

**Terminal 1 - Gmail Watcher:**
```bash
cd /mnt/d/AI_Employee_Hackathon_0/Silver/Watchers
python gmail_watcher.py
```

**Terminal 2 - File System Watcher:**
```bash
cd /mnt/d/AI_Employee_Hackathon_0/Silver/Watchers
python filesystem_watcher.py
```

**Terminal 3 - LinkedIn Poster:**
```bash
cd /mnt/d/AI_Employee_Hackathon_0/Silver/Watchers
python linkedin_poster.py --continuous --interval=300
```

**Terminal 4 - Orchestrator:**
```bash
cd /mnt/d/AI_Employee_Hackathon_0/Silver
python orchestrator.py
```

### Option 2: Run with Cron (Automated)

Add to crontab (`crontab -e`):

```bash
# Check for new emails every 5 minutes
*/5 * * * * cd /mnt/d/AI_Employee_Hackathon_0/Silver/Watchers && python gmail_watcher.py --iterations=1 >> /mnt/d/AI_Employee_Hackathon_0/Silver/Logs/cron.log 2>&1

# Check file system every 2 minutes
*/2 * * * * cd /mnt/d/AI_Employee_Hackathon_0/Silver/Watchers && python filesystem_watcher.py --iterations=1 >> /mnt/d/AI_Employee_Hackathon_0/Silver/Logs/cron.log 2>&1

# Post LinkedIn content every 30 minutes
*/30 * * * * cd /mnt/d/AI_Employee_Hackathon_0/Silver/Watchers && python linkedin_poster.py --iterations=1 >> /mnt/d/AI_Employee_Hackathon_0/Silver/Logs/cron.log 2>&1

# Run orchestrator every minute
* * * * * cd /mnt/d/AI_Employee_Hackathon_0/Silver && python orchestrator.py --iterations=1 >> /mnt/d/AI_Employee_Hackathon_0/Silver/Logs/cron.log 2>&1
```

### Option 3: Task Scheduler (Windows)

Create tasks in Windows Task Scheduler to run the scripts on your preferred schedule.

## How to Test

### 1. Test Gmail Watcher

```bash
cd /mnt/d/AI_Employee_Hackathon_0/Silver/Watchers
python gmail_watcher.py
```

**Expected behavior:**
- Checks for unread important emails
- Creates task files in `Needs_Action/`
- Logs all activities to `Logs/YYYY-MM-DD.json`

### 2. Test File System Watcher

```bash
cd /mnt/d/AI_Employee_Hackathon_0/Silver/Watchers
python filesystem_watcher.py
```

**Expected behavior:**
- Monitors `Silver/Drop_Folder/` for new files
- Creates task files for detected files
- Processes files through the orchestrator

### 3. Test LinkedIn Poster

**Step 1:** Create a test post in `Pending_Approval/`:

```markdown
---
type: linkedin_post
status: pending
---

This is a test post from my AI Employee! 🚀

#AI #Automation #Testing
```

**Step 2:** Move it to `Approved/`

**Step 3:** Run the poster:
```bash
cd /mnt/d/AI_Employee_Hackathon_0/Silver/Watchers
python linkedin_poster.py
```

**Step 4:** Check the result:
- Post should appear on your LinkedIn profile
- File moved to `Done/`
- Entry in `Logs/YYYY-MM-DD.json`

### 4. Test MCP Server (Gmail Send)

```bash
cd /mnt/d/AI_Employee_Hackathon_0/Silver/MCP/gmail_send_server
node test-email.js
```

**Expected behavior:**
- In DRY_RUN mode: Shows email would be sent
- In LIVE mode: Actually sends email
- Logs to `Logs/YYYY-MM-DD.json`

**To send real email:**
```bash
DRY_RUN=false node test-email.js
```

## How It Works

### Gmail Monitoring Flow

```
1. Gmail Watcher runs
   ↓
2. Uses OAuth2 to authenticate with Gmail
   ↓
3. Checks for unread important emails
   ↓
4. Creates task file in Needs_Action/
   ↓
5. Orchestrator processes the task
   ↓
6. Claude analyzes and responds
   ↓
7. Response drafted in Pending_Approval/
   ↓
8. Human approves by moving to Approved/
   ↓
9. MCP server sends the email
   ↓
10. Task moved to Done/
```

### LinkedIn Auto-Post Flow

```
1. Create post in Pending_Approval/
   ↓
2. Review and edit content
   ↓
3. Move to Approved/
   ↓
4. LinkedIn Poster detects approved post
   ↓
5. Opens LinkedIn with Playwright
   ↓
6. Logs in (first time) or uses saved session
   ↓
7. Navigates to feed
   ↓
8. Clicks "Start a post"
   ↓
9. Types content
   ↓
10. Clicks "Post"
   ↓
11. Confirms success
   ↓
12. Moves file to Done/
```

### Human Approval Workflow

```
                          ┌─────────────┐
                          │  New Task   │
                          └──────┬──────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │  Pending_Approval/    │
                    │  (Human Review)       │
                    └───────────┬────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
             ┌─────────────┐         ┌─────────────┐
             │  Approved/  │         │  Rejected/  │
             └──────┬──────┘         └─────────────┘
                    │
                    ▼
             ┌─────────────┐
             │  Executed   │
             │  (MCP/Script)│
             └──────┬──────┘
                    │
                    ▼
             ┌─────────────┐
             │    Done/    │
             └─────────────┘
```

## Agent Skills

Silver Tier includes **12 specialized Agent Skills**:

| Skill | Description |
|-------|-------------|
| **file_processor** | Read and write files to the vault |
| **text_analyzer** | Analyze content and extract intent |
| **data_extractor** | Extract structured data from text |
| **email_drafter** | Draft email responses |
| **task_planner** | Create step-by-step execution plans |
| **linkedin_poster** | Create and post LinkedIn content |
| **gmail_reader** | Read and analyze Gmail emails |
| **gmail_sender** | Send emails via Gmail API |
| **whatsapp_monitor** | Monitor WhatsApp for important messages |
| **scheduler** | Schedule tasks and reminders |
| **plan_creator** | Create detailed project plans |
| **summary_generator** | Generate concise summaries |

See `Skills/README.md` for detailed documentation of each skill.

## Configuration

### Watcher Configuration

Each watcher has its own configuration in `Config/`:

**Gmail Watcher (`Config/GmailWatcher_state.json`):**
- Processed email IDs
- Last check timestamp
- Label filters

**LinkedIn Poster (`Config/LinkedInPoster_state.json`):**
- Processed post file names
- Last update timestamp

### System Configuration

Edit `.env` file for global settings:

```bash
# Safety Mode
DRY_RUN=true              # Set to false for real actions

# Logging
LOG_LEVEL=INFO            # DEBUG, INFO, WARNING, ERROR

# Intervals
GMAIL_CHECK_INTERVAL=30   # Seconds between Gmail checks
MAX_ITERATIONS=0          # 0 = unlimited, N = stop after N iterations
```

## Security Notes

- **DRY_RUN is true by default** - No real external actions are taken
- **Credentials stored locally** in `Config/` folder
- **OAuth2 used** for Gmail (no passwords in code)
- **Session persistence** reduces authentication frequency
- **All actions logged** to `Logs/` for audit trails
- **Human approval required** for sensitive actions
- **.gitignore configured** to exclude sensitive files from git

## Troubleshooting

### Gmail Authentication Issues

**Problem:** "Invalid credentials" or "401 error"

**Solution:**
1. Delete `Config/gmail_token.json`
2. Run any Gmail watcher script
3. Complete OAuth flow in browser
4. New token will be saved automatically

### LinkedIn Login Issues

**Problem:** "Login timeout" or "Elements not found"

**Solution:**
1. Delete `Config/linkedin_session/` folder
2. Run `python test_linkedin_poster.py --test login`
3. Complete login in the browser window
4. New session will be saved automatically
5. Check `Logs/login_debug.png` for debugging

### MCP Server Not Working

**Problem:** "Unknown tool: send_email" in Claude Code

**Solution:**
1. Install dependencies: `npm install` in MCP folder
2. Check MCP config: `cat ~/.config/claude-code/mcp.json`
3. Restart Claude Code completely
4. Try the tool again

### Posts Not Appearing on LinkedIn

**Problem:** File not moved to Done/ or no post on LinkedIn

**Solution:**
1. Check file has `type: linkedin_post` in frontmatter
2. Check file is in `Approved/` not `Pending_Approval/`
3. Check `Logs/YYYY-MM-DD.json` for errors
4. Verify LinkedIn credentials in `.env`
5. Check `LINKEDIN_HEADLESS=false` for first login

### Cron Jobs Not Running

**Problem:** Scheduled tasks not executing

**Solution:**
1. Check cron log: `tail -f Silver/Logs/cron.log`
2. Verify crontab: `crontab -l`
3. Ensure scripts have execute permissions: `chmod +x Watchers/*.py`
4. Check Python path in cron: Use full path to python

## Performance

| Component | CPU Usage | Memory | Frequency |
|-----------|-----------|---------|-----------|
| Gmail Watcher | Low | ~50MB | Every 30s (configurable) |
| File Watcher | Low | ~30MB | Continuous |
| LinkedIn Poster | Medium | ~150MB | Every 5min (configurable) |
| Orchestrator | Low | ~40MB | Every 60s |
| MCP Server | Low | ~60MB | On demand |

## Monitoring

### Dashboard

Check `Silver/Dashboard.md` for:
- Task counts by status
- Recent activities
- Agent skill usage
- System health

### Logs

All activities logged to `Logs/YYYY-MM-DD.json`:

```json
{
  "timestamp": "2026-03-04T10:30:00.000Z",
  "watcher": "gmail_watcher",
  "action": "email_found",
  "dry_run": false,
  "email_id": "1234567890abcdef",
  "subject": "Important Update"
}
```

View logs:
```bash
# Today's logs
cat /mnt/d/AI_Employee_Hackathon_0/Silver/Logs/$(date +%Y-%m-%d).json | jq

# Real-time monitoring
tail -f /mnt/d/AI_Employee_Hackathon_0/Silver/Logs/watcher.log
```

## What's Next - Gold Tier Preview

After Silver Tier is mastered, **Gold Tier** adds:

- ✅ **Odoo Accounting Integration** - Automated bookkeeping
- ✅ **Multi-Platform Social Media** - Facebook, Instagram, Twitter
- ✅ **CEO Briefing System** - Weekly automated business audits
- ✅ **Advanced Error Recovery** - Self-healing workflows
- ✅ **24/7 Cloud Deployment** - Cloud hosting with Watchdog process
- ✅ **Local Executive Delegation** - Manage other AI agents locally
- ✅ **Financial Reporting** - P&L, balance sheets, cash flow
- ✅ **Invoice Processing** - Automatic invoice creation and sending

## Migration from Bronze to Silver

If you're upgrading from Bronze Tier:

1. ✅ **Keep Bronze folder intact** - It will continue working
2. ✅ **Copy .env file** - Use Bronze settings as starting point
3. ✅ **Migrate processed files** - Move Done/ items if needed
4. ✅ **Update MCP config** - Add new MCP server credentials
5. ✅ **Install new dependencies** - Python packages and Node.js
6. ✅ **Test incrementally** - Start with one watcher, add more gradually

## Support

For issues or questions:

1. Check `Logs/` for error messages
2. Review relevant README files in subdirectories
3. Check `Skills/README.md` for skill documentation
4. Review `project_details.md` for complete system overview

## License

MIT License - Part of Personal AI Employee Hackathon 0

## Summary

Silver Tier transforms your AI Employee from a **passive file processor** to an **active digital assistant** that can:

- 📧 **Monitor and respond to emails**
- 📱 **Post to social media automatically**
- 📁 **Watch file system for tasks**
- ✉️ **Send emails via MCP protocol**
- 👤 **Maintain human oversight** via approval workflow
- ⏰ **Run scheduled tasks** via cron
- 🧠 **Use 12 specialized skills** for various operations

**The result: A Digital FTE that works 24/7/365 while keeping you in the loop!** 🚀
