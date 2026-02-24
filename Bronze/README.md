# Bronze Tier - Personal AI Employee

The Bronze Tier is the foundational level of the Personal AI Employee Hackathon. It provides automated file monitoring, task processing, and dashboard tracking using Claude Code and Obsidian.

## What Bronze Tier Does

- **Monitors a Drop Folder** for incoming files (.txt, .pdf, .doc, .docx, .md)
- **Creates tasks** automatically when files are dropped
- **Processes tasks** on a 60-second interval
- **Updates a dashboard** with real-time statistics
- **Logs all activities** to JSON files for audit trails
- **Follows company rules** from `Company_Handbook.md`

## Folder Structure

```
Bronze/
├── Dashboard.md              # Live dashboard with stats and activities
├── Company_Handbook.md       # Business rules and approval thresholds
├── Needs_Action/             # Incoming tasks waiting to be processed
├── Plans/                    # Step-by-step plans created by Claude
├── Approved/                 # Tasks that have been approved
├── Rejected/                 # Tasks that have been rejected
├── Pending_Approval/         # Items awaiting human review
├── Done/                     # Completed tasks
├── Logs/                     # Daily JSON logs and error logs
├── Skills/                   # Documentation of Claude's skills
├── Config/                   # System configuration files
├── Drop_Folder/              # Drop files here for processing
├── filesystem_watcher.py     # Monitors Drop_Folder for new files
├── orchestrator.py           # Processes tasks and updates dashboard
└── README.md                 # This file
```

## How to Run

### Prerequisites

Install required Python dependencies:

```bash
pip install watchdog python-dotenv
```

### Starting the System

You need two terminal windows:

**Terminal 1 - File Watcher:**
```bash
cd Bronze
python filesystem_watcher.py
```

**Terminal 2 - Orchestrator:**
```bash
cd Bronze
python orchestrator.py
```

### Environment Variables

- `DRY_RUN` - Set to `false` to enable actual file operations (default: `true`)
  ```bash
  export DRY_RUN=false
  python orchestrator.py
  ```

## How to Test

1. **Start both scripts** in separate terminals
2. **Drop a test file** into `Bronze/Drop_Folder/`
   - Supports: .txt, .pdf, .doc, .docx, .md
3. **Watch the output** - you should see:
   - File watcher detects the file
   - Task created in `Needs_Action/`
   - Orchestrator processes the task
   - Dashboard updates with new counts
4. **Check the results:**
   - `Needs_Action/` - Should be empty (task processed)
   - `Done/` - Should contain the processed task
   - `Dashboard.md` - Updated with latest stats
   - `Logs/YYYY-MM-DD.json` - Activity log for today

### Example Test

Create a simple test file:
```bash
echo "Test task for AI Employee" > Bronze/Drop_Folder/test.txt
```

Within 60 seconds, the system will:
1. Detect `test.txt`
2. Create a task file in `Needs_Action/`
3. Process the task
4. Move it to `Done/`
5. Update the dashboard

## Configuration

Edit `Config/system_config.json` to adjust:

```json
{
  "check_interval": 60,        // Seconds between scans
  "max_iterations": 5,         // Max loops before auto-exit
  "dry_run": true              // Safety mode - set false for real actions
}
```

## Security Notes

- **DRY_RUN is true by default** - No real external actions are taken
- **No network requests** are made without approval
- **All actions are logged** to `Logs/` for audit trails
- **File operations are scoped** to the Bronze folder only
- **Approval thresholds** are enforced per Company_Handbook.md

## Skills Documentation

See `Skills/README.md` for detailed documentation of all available skills:

- **file_processor** - Read and write files
- **text_analyzer** - Analyze content and extract intent
- **task_planner** - Create step-by-step plans
- **email_drafter** - Draft email responses
- **data_extractor** - Extract structured data

## Troubleshooting

### Watcher not detecting files
- Check that the file has a supported extension (.txt, .pdf, .doc, .docx, .md)
- Ensure both scripts are running
- Check console for error messages

### Dashboard not updating
- Verify `Config/system_config.json` has `"dry_run": false` to write changes
- Check `Logs/errors.log` for error messages
- Ensure all folders exist

### Tasks not processing
- Check that task files have `.md` extension
- Verify `Needs_Action/` folder exists
- Review `Logs/` for processing errors

## Next Steps

After Bronze Tier is working:

1. **Test with real files** - Drop actual documents you want processed
2. **Customize Company_Handbook.md** - Add your business rules
3. **Enable dry_run=false** - When ready for real actions
4. **Build Silver Tier** - Add Claude Code CLI integration
5. **Build Gold Tier** - Add autonomous execution
