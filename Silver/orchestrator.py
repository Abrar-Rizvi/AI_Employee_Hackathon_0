#!/usr/bin/env python3
"""
Orchestrator for Bronze Tier AI Employee
Scans for tasks, processes them using skills, and updates the dashboard.
"""

import os
import sys
import json
import time
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Configuration based on working directory
BRONZE_DIR = Path(__file__).parent
NEEDS_ACTION_FOLDER = BRONZE_DIR / "Needs_Action"
DONE_FOLDER = BRONZE_DIR / "Done"
LOGS_FOLDER = BRONZE_DIR / "Logs"
PLANS_FOLDER = BRONZE_DIR / "Plans"
PENDING_APPROVAL_FOLDER = BRONZE_DIR / "Pending_Approval"
CONFIG_FILE = BRONZE_DIR / "Config" / "system_config.json"
DASHBOARD_FILE = BRONZE_DIR / "Dashboard.md"
ERROR_LOG_FILE = LOGS_FOLDER / "errors.log"
COMPANY_HANDBOOK = BRONZE_DIR / "Company_Handbook.md"

# Default configuration
DEFAULT_CONFIG = {
    "check_interval": 60,
    "max_iterations": 5,
    "dry_run": True
}

# Global state
config = DEFAULT_CONFIG.copy()
running = True


# =============================================================================
# SKILL: TEXT ANALYZER
# =============================================================================

def analyze_intent(content: str, context: dict = None) -> dict:
    """Analyze text to determine intent and extract key information."""

    results = {
        "intent": "unknown",
        "confidence": 0.0,
        "priority": "medium",
        "category": "other",
        "entities": {},
        "requires_approval": False,
        "approval_reason": None
    }

    content_lower = content.lower()

    # Detect email reply request
    if re.search(r'\b(reply|respond|draft.*email|email.*response)\b', content_lower):
        results["intent"] = "email_draft"
        results["category"] = "communication"
        results["confidence"] = 0.8
        results["requires_approval"] = True
        results["approval_reason"] = "Email reply requires approval per business rules"

        # Extract email addresses
        emails = re.findall(r'[\w\.-]+@[\w\.-]+', content)
        if emails:
            results["entities"]["sender"] = emails[0]

        # Extract subject
        subject = re.search(r'Subject:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        if subject:
            results["entities"]["subject"] = subject.group(1).strip()

    # Detect payment request
    elif re.search(r'\b(invoice|payment|pay|transfer|amount due)\b', content_lower):
        results["intent"] = "payment_request"
        results["category"] = "finance"
        results["confidence"] = 0.9

        # Extract amounts
        amounts = re.findall(r'\$?(\d+(?:\.\d{2})?)', content)
        if amounts:
            amount = float(amounts[0])
            results["entities"]["amount"] = amount

            # Check $500 threshold from Company_Handbook.md
            if amount > 500:
                results["requires_approval"] = True
                results["approval_reason"] = f"Payment of ${amount} exceeds $500 threshold"
                results["priority"] = "high"

        # Extract invoice numbers
        invoice = re.search(r'invoice\s*#?\s*([A-Z0-9-]+)', content, re.IGNORECASE)
        if invoice:
            results["entities"]["invoice_number"] = invoice.group(1)

        # Extract vendor
        vendor = re.search(r'from\s*:?\s*([^\n]+)|vendor\s*:?\s*([^\n]+)', content, re.IGNORECASE)
        if vendor:
            results["entities"]["vendor"] = vendor.group(1) or vendor.group(2)

    # Detect data extraction request
    elif re.search(r'\b(extract|parse|analyze|summarize)\b', content_lower):
        results["intent"] = "data_extraction"
        results["category"] = "admin"
        results["confidence"] = 0.7

    return results


# =============================================================================
# SKILL: FILE PROCESSOR
# =============================================================================

def read_file(file_path: Path) -> dict:
    """Read a file and return structured result."""
    try:
        if not file_path.exists():
            return {
                "status": "error",
                "error": f"File not found: {file_path}",
                "timestamp": datetime.now().isoformat()
            }

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return {
            "status": "success",
            "content": content,
            "size": file_path.stat().st_size,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def write_file(file_path: Path, content: str) -> dict:
    """Write content to a file."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if not config["dry_run"]:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        return {
            "status": "success",
            "file": str(file_path),
            "dry_run": config["dry_run"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# =============================================================================
# SKILL: EMAIL DRAFTER
# =============================================================================

def draft_email_response(original_email: dict, analysis: dict) -> dict:
    """Draft an email response based on original email and analysis."""

    sender = original_email.get("from", "unknown@example.com")
    subject = original_email.get("subject", "No Subject")
    body = original_email.get("body", "")

    intent = analysis.get("intent", "unknown")

    if intent == "payment_acknowledgment":
        invoice = analysis.get("entities", {}).get("invoice_number", "UNKNOWN")
        amount = analysis.get("entities", {}).get("amount", 0)

        draft_content = f"""---
type: email_draft
created: {datetime.now().isoformat()}
priority: {"high" if amount > 500 else "medium"}
status: pending_approval
original_from: {sender}
original_subject: {subject}
---

# Email Draft: Invoice Acknowledgment - {invoice}

**Status:** Pending Approval
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**To:** {sender}
**Subject:** Re: Invoice {invoice} - Acknowledgment

## Original Email
**From:** {sender}
**Subject:** {subject}
**Received:** {datetime.now().strftime('%Y-%m-%d')}

{body}

## Draft Response

Dear {sender.split('@')[0].title()},

Thank you for your email and for providing invoice {invoice}.

We acknowledge receipt of your invoice for ${amount:.2f}.

Please be advised that we are currently reviewing the invoice details. You can expect payment processing within 3-5 business days.

{"IMPORTANT: As this invoice exceeds $500, it requires managerial approval before payment can be processed." if amount > 500 else "This invoice is within our standard processing limits."}

Thank you for your continued partnership.

Sincerely,

Finance Department

---

## Review Checklist
- [ ] Invoice details verified ({invoice})
- [ ] Amount confirmed (${amount:.2f})
- [ ] {"Manager approval obtained (>$500)" if amount > 500 else "Within approval authority"}
- [ ] Tone is professional and courteous
- [ ] Ready to send

## Notes
- Invoice amount: ${amount:.2f}
- {"⚠️ REQUIRES MANAGER APPROVAL" if amount > 500 else "✓ Standard processing"}
- Reference: Company_Handbook.md payment rules
"""
    else:
        # Generic business response
        draft_content = f"""---
type: email_draft
created: {datetime.now().isoformat()}
priority: medium
status: pending_approval
original_from: {sender}
original_subject: {subject}
---

# Email Draft: Response to {sender}

**Status:** Pending Approval
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**To:** {sender}
**Subject:** Re: {subject}

## Original Email
**From:** {sender}
**Subject:** {subject}
**Received:** {datetime.now().strftime('%Y-%m-%d')}

{body}

## Draft Response

Dear {sender.split('@')[0].title()},

Thank you for your email regarding {subject}.

We have received your communication and appreciate you bringing this matter to our attention. We are currently reviewing the details and will provide a comprehensive response shortly.

Should you require any clarification or have additional questions in the meantime, please do not hesitate to reach out.

Sincerely,

Customer Service Team

---

## Review Checklist
- [ ] All points from original email addressed
- [ ] Tone is formal and professional
- [ ] No sensitive information included
- [ ] Follows Company_Handbook.md communication rules
- [ ] Ready to send
"""

    # Save draft
    draft_filename = f"email_draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    draft_path = PENDING_APPROVAL_FOLDER / draft_filename

    result = write_file(draft_path, draft_content)

    return {
        **result,
        "draft_file": str(draft_path),
        "to": sender,
        "subject": f"Re: {subject}",
        "requires_approval": True
    }


# =============================================================================
# SKILL: TASK PLANNER
# =============================================================================

def create_task_plan(task_name: str, description: str, analysis: dict) -> dict:
    """Create a structured task plan."""

    intent = analysis.get("intent", "unknown")
    priority = analysis.get("priority", "medium")
    requires_approval = analysis.get("requires_approval", False)

    plan_content = f"""---
type: plan
created: {datetime.now().isoformat()}
priority: {priority}
status: pending
intent: {intent}
category: {analysis.get("category", "other")}
requires_approval: {str(requires_approval).lower()}
---

# Task Plan: {task_name}

**Created:** {datetime.now().strftime('%Y-%m-%d')}
**Priority:** {priority.capitalize()}
**Status:** Pending

## Overview
{description}

## Intent Analysis
- **Detected Intent:** {intent}
- **Category:** {analysis.get("category", "other")}
- **Confidence:** {analysis.get("confidence", 0):.2f}
- **Requires Approval:** {"Yes" if requires_approval else "No"}
{f'**Approval Reason:** {analysis.get("approval_reason")}' if requires_approval else ''}

## Steps

### Step 1: Analyze Request
**Status:** Pending
**Action:** Review and understand the full context
**Tools Required:** text_analyzer

### Step 2: Check Company Rules
**Status:** Pending
**Action:** Review Company_Handbook.md for applicable rules
**Tools Required:** file_processor

### Step 3: Process Content
**Status:** Pending
**Action:** Extract and process relevant information
**Tools Required:** data_extractor

### Step 4: Execute Action
**Status:** Pending
**Action:** Complete the primary task action
**Tools Required:** {get_tool_for_intent(intent)}

### Step 5: Review and Complete
**Status:** Pending
**Action:** Verify results and document completion
**Tools Required:** file_processor

## Approval Requirements
{"- [ ] Manager approval required (exceeds threshold)" if requires_approval else "- [ ] Within approval authority"}
- [ ] Checked against Company_Handbook.md
- [ ] Result verified

## Notes
- Plan created by orchestrator at {datetime.now().isoformat()}
- Reference: Company_Handbook.md rules
"""

    plan_filename = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    plan_path = PLANS_FOLDER / plan_filename

    result = write_file(plan_path, plan_content)

    return {
        **result,
        "plan_file": str(plan_path),
        "plan_name": task_name,
        "steps_count": 5
    }


def get_tool_for_intent(intent: str) -> str:
    """Map intent to required tool."""
    tools = {
        "email_draft": "email_drafter",
        "payment_request": "email_drafter, data_extractor",
        "data_extraction": "data_extractor",
        "unknown": "task_planner"
    }
    return tools.get(intent, "file_processor")


# =============================================================================
# SKILL: DATA EXTRACTOR
# =============================================================================

def extract_data_from_content(content: str, schema_type: str = "auto") -> dict:
    """Extract structured data from content."""

    # Extract common fields
    data = {}
    confidence = {}

    # Emails
    emails = re.findall(r'[\w\.-]+@[\w\.-]+', content)
    if emails:
        data["email"] = emails[0]
        confidence["email"] = 0.95

    # Amounts/Currency
    amounts = re.findall(r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', content)
    if amounts:
        clean_amounts = [float(a.replace(',', '')) for a in amounts if 0 < float(a.replace(',', '')) < 100000]
        if clean_amounts:
            data["amounts"] = clean_amounts
            confidence["amounts"] = 0.85

    # Dates
    dates = re.findall(r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}', content)
    if dates:
        data["dates"] = dates
        confidence["dates"] = 0.90

    # Invoice numbers
    invoice = re.search(r'invoice\s*#?\s*([A-Z0-9-]+)', content, re.IGNORECASE)
    if invoice:
        data["invoice_number"] = invoice.group(1)
        confidence["invoice_number"] = 0.90

    # Phone numbers
    phone = re.search(r'\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}', content)
    if phone:
        data["phone"] = phone.group(0)
        confidence["phone"] = 0.90

    # Save to JSON log
    extraction_result = {
        "status": "success",
        "schema": schema_type,
        "data": data,
        "confidence": confidence,
        "timestamp": datetime.now().isoformat()
    }

    log_filename = f"extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_path = LOGS_FOLDER / log_filename

    if not config["dry_run"]:
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(extraction_result, f, indent=2)

    return {
        **extraction_result,
        "log_file": str(log_path),
        "dry_run": config["dry_run"]
    }


# =============================================================================
# ORCHESTRATOR FUNCTIONS
# =============================================================================

def load_config() -> Dict[str, Any]:
    """Load configuration from config file or use defaults."""
    global config
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                config.update(loaded_config)
        except Exception as e:
            log_error(f"Error loading config: {e}")
    return config


def log_error(message: str):
    """Log error to errors.log file."""
    ERROR_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    log_entry = f"{timestamp} - ERROR - {message}\n"
    try:
        with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Failed to write error log: {e}")


def log_activity(action: str, file: str, status: str, details: Dict = None):
    """Log activity to daily log file."""
    LOGS_FOLDER.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = LOGS_FOLDER / f"{today}.json"

    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "action": action,
        "file": file,
        "status": status
    }
    if details:
        log_entry.update(details)

    try:
        # Read existing logs or create new list
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logs = []

        logs.append(log_entry)

        # Write back
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2)

    except Exception as e:
        log_error(f"Failed to write activity log: {e}")


def ensure_folders_exist():
    """Ensure all required folders exist."""
    folders = [
        NEEDS_ACTION_FOLDER,
        DONE_FOLDER,
        LOGS_FOLDER,
        PLANS_FOLDER,
        BRONZE_DIR / "Approved",
        BRONZE_DIR / "Rejected",
        PENDING_APPROVAL_FOLDER
    ]

    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)


def get_folder_count(folder: Path) -> int:
    """Get count of .md files in a folder."""
    if not folder.exists():
        return 0
    return len(list(folder.glob("*.md")))


def get_recent_activities(limit: int = 5) -> List[Dict]:
    """Get recent log entries from today's log."""
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = LOGS_FOLDER / f"{today}.json"

    if not log_file.exists():
        return []

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        return logs[-limit:] if logs else []
    except Exception:
        return []


def update_dashboard():
    """Update the Dashboard.md with current stats."""
    try:
        needs_action_count = get_folder_count(NEEDS_ACTION_FOLDER)
        pending_count = get_folder_count(PENDING_APPROVAL_FOLDER)
        done_count = get_folder_count(DONE_FOLDER)
        plans_count = get_folder_count(PLANS_FOLDER)

        recent_activities = get_recent_activities(5)
        activities_text = ""
        if recent_activities:
            for activity in recent_activities:
                timestamp = activity.get("timestamp", "")[:19]
                action = activity.get("action", "")
                status = activity.get("status", "")
                activities_text += f"- [{timestamp}] {action} - {status}\n"
        else:
            activities_text = "- No activities yet\n"

        dashboard_content = f"""---
type: dashboard
last_updated: {datetime.now().strftime("%Y-%m-%d")}
status: active
---

# AI Employee Dashboard (Bronze Tier)

## System Status
- Claude Code: Running
- Obsidian Vault: Active
- File Watcher: Monitoring
- Orchestrator: Active

## Task Summary
- Needs Action: {needs_action_count}
- Pending Approval: {pending_count}
- Active Plans: {plans_count}
- Completed Tasks: {done_count}

## Recent Activities
{activities_text}
"""

        if not config["dry_run"]:
            with open(DASHBOARD_FILE, 'w', encoding='utf-8') as f:
                f.write(dashboard_content)

        log_activity(
            "dashboard_update",
            str(DASHBOARD_FILE),
            "updated",
            {"needs_action": needs_action_count, "pending": pending_count, "done": done_count, "plans": plans_count}
        )

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Dashboard updated - Needs: {needs_action_count}, Pending: {pending_count}, Plans: {plans_count}, Done: {done_count}")

    except Exception as e:
        log_error(f"Failed to update dashboard: {e}")
        print(f"Error updating dashboard: {e}")


def process_task_file(task_file: Path):
    """Process a single task file using skills."""

    print(f"\n{'=' * 60}")
    print(f"Processing Task: {task_file.name}")
    print('=' * 60)

    try:
        # Step 1: Read task file (file_processor skill)
        print("[1/6] Reading task file...")
        task_result = read_file(task_file)

        if task_result["status"] != "success":
            log_error(f"Failed to read task file: {task_result.get('error')}")
            return

        task_content = task_result["content"]

        # Extract metadata from task frontmatter
        original_name = re.search(r'original_name:\s*(.+)', task_content)
        source_path = re.search(r'source_path:\s*(.+)', task_content)

        task_name = original_name.group(1).strip() if original_name else task_file.stem
        source_file = source_path.group(1).strip() if source_path else None

        print(f"  ✓ Task name: {task_name}")
        print(f"  ✓ Source: {source_file or 'Not specified'}")

        # Step 2: Find and read the actual dropped file
        source_content = ""
        if source_file:
            # Try to find the file in Needs_Action folder
            possible_files = list(NEEDS_ACTION_FOLDER.glob(task_name))
            if possible_files:
                source_result = read_file(possible_files[0])
                if source_result["status"] == "success":
                    source_content = source_result["content"]
                    print(f"[2/6] Read source file: {possible_files[0].name} ({source_result['size']} bytes)")

        # Combine task and source content for analysis
        analysis_content = task_content + "\n" + source_content

        # Step 3: Analyze intent (text_analyzer skill)
        print("[3/6] Analyzing intent...")
        analysis = analyze_intent(analysis_content)
        print(f"  ✓ Intent: {analysis['intent']}")
        print(f"  ✓ Category: {analysis['category']}")
        print(f"  ✓ Confidence: {analysis['confidence']:.2f}")
        print(f"  ✓ Requires Approval: {analysis['requires_approval']}")

        log_activity(
            "intent_analyzed",
            str(task_file),
            analysis['intent'],
            analysis
        )

        # Step 4: Route to appropriate skill based on intent
        print("[4/6] Executing skill...")

        if analysis['intent'] == 'email_draft':
            # Extract email info from source content
            email_info = {
                "from": analysis.get("entities", {}).get("sender", "unknown@example.com"),
                "subject": analysis.get("entities", {}).get("subject", "No Subject"),
                "body": source_content[:500] if source_content else task_content[:500]
            }

            result = draft_email_response(email_info, {**analysis, "intent": "payment_acknowledgment" if "invoice" in analysis_content.lower() else "general"})
            print(f"  ✓ Email draft created: {Path(result.get('draft_file', '')).name}")

        elif analysis['intent'] == 'payment_request':
            # Create plan and draft acknowledgment email
            plan_result = create_task_plan(
                f"Payment Processing - {analysis.get('entities', {}).get('invoice_number', 'Unknown')}",
                f"Process payment of ${analysis.get('entities', {}).get('amount', 0):.2f} from {analysis.get('entities', {}).get('vendor', 'Unknown')}",
                analysis
            )
            print(f"  ✓ Plan created: {Path(plan_result.get('plan_file', '')).name}")

            # Also create email draft
            email_info = {
                "from": analysis.get("entities", {}).get("vendor", "vendor@example.com"),
                "subject": f"Invoice {analysis.get('entities', {}).get('invoice_number', 'Unknown')}",
                "body": source_content[:500] if source_content else "Invoice received"
            }

            email_result = draft_email_response(email_info, {**analysis, "intent": "payment_acknowledgment"})
            print(f"  ✓ Email draft created: {Path(email_result.get('draft_file', '')).name}")

        elif analysis['intent'] == 'data_extraction':
            # Extract data
            extract_result = extract_data_from_content(source_content or analysis_content)
            print(f"  ✓ Data extracted: {len(extract_result.get('data', {}))} fields")
            print(f"    Fields: {', '.join(extract_result.get('data', {}).keys())}")

            # Create plan
            plan_result = create_task_plan(
                f"Data Extraction - {task_name}",
                f"Extract structured data from {task_name}",
                analysis
            )
            print(f"  ✓ Plan created: {Path(plan_result.get('plan_file', '')).name}")

        else:
            # Unknown intent - create generic plan
            plan_result = create_task_plan(
                task_name,
                f"Process task: {task_name}",
                analysis
            )
            print(f"  ✓ Generic plan created: {Path(plan_result.get('plan_file', '')).name}")

        # Step 5: Log completion
        print("[5/6] Logging activity...")
        log_activity(
            "task_processed",
            str(task_file),
            "completed",
            {
                "intent": analysis['intent'],
                "requires_approval": analysis['requires_approval']
            }
        )

        # Step 6: Move task to Done
        print("[6/6] Archiving task...")
        if not config["dry_run"]:
            dest_path = DONE_FOLDER / task_file.name
            shutil.move(str(task_file), str(dest_path))

            # Also move source file if it exists
            if source_file:
                possible_files = list(NEEDS_ACTION_FOLDER.glob(task_name))
                for pf in possible_files:
                    if pf != task_file:  # Don't move the task file itself
                        shutil.move(str(pf), str(DONE_FOLDER / pf.name))

            log_activity(
                "task_archived",
                str(task_file),
                "moved_to_done",
                {"destination": str(dest_path)}
            )

        print(f"  ✓ Task moved to Done/")
        print(f"\n✓ Task processing complete!\n")

    except Exception as e:
        log_error(f"Error processing task file {task_file}: {e}")
        print(f"✗ Error processing task: {e}")
        import traceback
        traceback.print_exc()


def scan_and_process():
    """Scan Needs_Action folder and process all task files."""
    ensure_folders_exist()

    task_files = list(NEEDS_ACTION_FOLDER.glob("*.md"))

    if not task_files:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] No tasks found in Needs_Action")
        return

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Found {len(task_files)} task(s) to process")

    for task_file in task_files:
        process_task_file(task_file)

    # Update dashboard after processing
    update_dashboard()


def main():
    """Main entry point for the orchestrator."""
    global running

    print("=" * 60)
    print("Bronze Tier - Orchestrator Starting")
    print("=" * 60)

    # Load configuration
    load_config()
    print(f"\nConfiguration loaded:")
    print(f"  Check interval: {config['check_interval']} seconds")
    print(f"  Max iterations: {config['max_iterations']}")
    print(f"  Dry run: {config['dry_run']}")
    print("")

    ensure_folders_exist()
    update_dashboard()

    print("Orchestrator ready. Monitoring for tasks...")
    print("")

    iteration = 0
    try:
        while running and iteration < config['max_iterations']:
            scan_and_process()
            iteration += 1

            if iteration < config['max_iterations']:
                print(f"Waiting {config['check_interval']} seconds...")
                time.sleep(config['check_interval'])

    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")

    update_dashboard()
    print("\nOrchestrator stopped.")


if __name__ == "__main__":
    main()
