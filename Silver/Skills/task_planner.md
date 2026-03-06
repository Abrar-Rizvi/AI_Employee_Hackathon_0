---
name: task-planner
description: Create structured, step-by-step execution plans as markdown files. Use this skill when a task requires multiple steps or needs to be broken down into actionable items.
license: Apache-2.0
compatibility: Requires yaml for frontmatter
metadata:
  author: AI Employee Bronze Tier
  version: "1.0"
  tier: bronze
---

# Task Planner Skill

## Purpose
Create detailed, step-by-step execution plans for complex tasks that require multiple actions. Plans are saved as markdown files in the `Plans/` folder with proper frontmatter.

## When to Use This Skill
- Task requires multiple steps to complete
- Complex workflow needs documentation
- Task involves approval workflows
- Need to track progress through a process
- Breaking down ambiguous requests into clear actions

## Input Parameters

```json
{
  "task_name": "Human-readable task name",
  "task_description": "Detailed description of what needs to be done",
  "priority": "high|medium|low",
  "intent_analysis": {
    "intent": "detected_intent",
    "category": "task_category"
  },
  "business_rules": {
    "requires_approval": true,
    "approval_threshold": "$500"
  },
  "steps": [
    "Step 1 description",
    "Step 2 description"
  ]
}
```

## Output Format

### Plan File Created in `Plans/`
```markdown
---
type: plan
created: 2026-02-24T12:00:00
priority: high
status: pending
intent: payment_request
category: finance
requires_approval: true
approval_threshold: "$500"
estimated_steps: 5
---

# Task Plan: [Task Name]

**Created:** 2026-02-24
**Priority:** High
**Status:** Pending

## Overview
[Task description]

## Steps

### Step 1: [Step Title]
**Status:** Pending
**Action:** [Description]
**Tools Required:** [List of tools/skills]

### Step 2: [Step Title]
**Status:** Pending
**Action:** [Description]
**Tools Required:** [List of tools/skills]

[... additional steps ...]

## Approval Requirements
- [ ] Review against Company_Handbook.md
- [ ] Confirm amount is within authority
- [ ] Get approval if > $500

## Notes
[Any additional notes or context]
```

### JSON Response
```json
{
  "status": "success",
  "plan_file": "Plans/task_plan_001.md",
  "plan_name": "Task Plan: Payment Processing",
  "steps_count": 5,
  "estimated_duration": "15 minutes",
  "requires_approval": true,
  "timestamp": "ISO-8601 timestamp"
}
```

## Plan Templates

### Template 1: Email Response Plan
```python
def create_email_plan(sender: str, subject: str, analysis: dict) -> dict:
    """Create a plan for drafting an email response."""

    plan_content = f"""---
type: plan
created: {datetime.now().isoformat()}
priority: {analysis.get('priority', 'medium')}
status: pending
intent: email_draft
category: communication
requires_approval: true
---

# Task Plan: Email Response to {sender}

**Created:** {datetime.now().strftime('%Y-%m-%d')}
**Priority:** {analysis.get('priority', 'medium').capitalize()}
**Status:** Pending

## Overview
Draft a formal response to the received email.

**Email Details:**
- **From:** {sender}
- **Subject:** {subject}
- **Detected:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Steps

### Step 1: Analyze Original Email
**Status:** Pending
**Action:** Read and understand the full context of the original email
**Tools Required:** file_processor, text_analyzer

### Step 2: Check Company Rules
**Status:** Pending
**Action:** Review Company_Handbook.md for communication guidelines
**Tools Required:** file_processor

### Step 3: Identify Key Points
**Status:** Pending
**Action:** Extract main questions, requests, or action items from email
**Tools Required:** text_analyzer

### Step 4: Draft Response
**Status:** Pending
**Action:** Create formal email draft following business communication rules
**Tools Required:** email_drafter

### Step 5: Review and Submit
**Status:** Pending
**Action:** Save draft to Pending_Approval/ for human review
**Tools Required:** file_processor

## Approval Requirements
- [ ] Tone is formal and professional
- [ ] All questions addressed
- [ ] No sensitive information included
- [ ] Ready for human review

## Notes
- Use formal language as per Company_Handbook.md
- Be polite and professional
- Flag any requests for approval
"""

    plan_filename = f"email_response_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    return {
        "status": "success",
        "plan_file": f"Plans/{plan_filename}",
        "plan_name": f"Email Response to {sender}",
        "steps_count": 5,
        "requires_approval": True,
        "content": plan_content
    }
```

### Template 2: Payment Processing Plan
```python
def create_payment_plan(invoice_number: str, amount: float, vendor: str, analysis: dict) -> dict:
    """Create a plan for processing a payment request."""

    requires_approval = amount > 500
    priority = "high" if requires_approval else "medium"

    plan_content = f"""---
type: plan
created: {datetime.now().isoformat()}
priority: {priority}
status: pending
intent: payment_request
category: finance
requires_approval: {str(requires_approval).lower()}
amount: {amount}
invoice: {invoice_number}
---

# Task Plan: Payment Processing - {invoice_number}

**Created:** {datetime.now().strftime('%Y-%m-%d')}
**Priority:** {priority.capitalize()}
**Status:** Pending

## Overview
Process payment request for vendor invoice.

**Payment Details:**
- **Invoice Number:** {invoice_number}
- **Amount:** ${amount:.2f}
- **Vendor:** {vendor}
- **Requires Approval:** {'Yes' if requires_approval else 'No'}

## Steps

### Step 1: Verify Invoice Details
**Status:** Pending
**Action:** Confirm invoice number, amount, and vendor information
**Tools Required:** data_extractor

### Step 2: Check Approval Threshold
**Status:** Pending
**Action:** Verify if amount exceeds $500 approval threshold
**Tools Required:** text_analyzer

### Step 3: Validate Against Budget
**Status:** Pending
**Action:** Check if funds are available and within budget
**Tools Required:** file_processor (budget records)

### Step 4: Prepare Payment
**Status:** Pending
**Action:** Create payment request documentation
**Tools Required:** file_processor

### Step 5: { 'Get Approval' if requires_approval else 'Process Payment' }
**Status:** Pending
**Action:** {'Save to Pending_Approval/ for authorization' if requires_approval else 'Initiate payment transfer'}
**Tools Required:** file_processor

## Approval Requirements
- [ ] Invoice verified and accurate
- [ ] Amount matches quoted price
- [ ] { 'Manager approval required (>$500)' if requires_approval else 'Within approval authority' }
- [ ] Payment details confirmed

## Notes
- Payment amount: ${amount:.2f}
- {'⚠️ EXCEEDS $500 THRESHOLD - APPROVAL REQUIRED' if requires_approval else '✓ Within approval limit'}
- Reference: Company_Handbook.md approval rules
"""

    plan_filename = f"payment_plan_{invoice_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    return {
        "status": "success",
        "plan_file": f"Plans/{plan_filename}",
        "plan_name": f"Payment Processing - {invoice_number}",
        "steps_count": 5,
        "requires_approval": requires_approval,
        "content": plan_content
    }
```

### Template 3: Data Extraction Plan
```python
def create_extraction_plan(file_name: str, data_type: str) -> dict:
    """Create a plan for extracting structured data from a document."""

    plan_content = f"""---
type: plan
created: {datetime.now().isoformat()}
priority: medium
status: pending
intent: data_extraction
category: admin
requires_approval: false
---

# Task Plan: Data Extraction from {file_name}

**Created:** {datetime.now().strftime('%Y-%m-%d')}
**Priority:** Medium
**Status:** Pending

## Overview
Extract structured data from the provided document.

**Source File:** {file_name}
**Data Type:** {data_type}

## Steps

### Step 1: Read Source Document
**Status:** Pending
**Action:** Load the document content using file_processor
**Tools Required:** file_processor

### Step 2: Analyze Document Structure
**Status:** Pending
**Action:** Identify data fields, patterns, and format
**Tools Required:** text_analyzer

### Step 3: Extract Data Fields
**Status:** Pending
**Action:** Pull out all relevant data points
**Tools Required:** data_extractor

### Step 4: Validate Extracted Data
**Status:** Pending
**Action:** Check for completeness and accuracy
**Tools Required:** text_analyzer

### Step 5: Save Results
**Status:** Pending
**Action:** Write extracted data to structured format
**Tools Required:** file_processor

## Output Format
The extracted data will be saved in JSON format with the following structure:
```json
{{
  "source_file": "{file_name}",
  "extracted_at": "{datetime.now().isoformat()}",
  "data": {{}}
}}
```

## Notes
- Preserve original data format where possible
- Flag any missing or ambiguous data
- Include confidence scores for uncertain fields
"""

    plan_filename = f"extraction_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    return {
        "status": "success",
        "plan_file": f"Plans/{plan_filename}",
        "plan_name": f"Data Extraction from {file_name}",
        "steps_count": 5,
        "requires_approval": False,
        "content": plan_content
    }
```

## Main Planning Function

```python
from pathlib import Path
from datetime import datetime
import json

def create_plan(task_data: dict) -> dict:
    """Main entry point for creating task plans."""

    intent = task_data.get("intent_analysis", {}).get("intent", "unknown")
    task_name = task_data.get("task_name", "Unnamed Task")

    # Route to appropriate plan template
    if intent == "email_draft":
        sender = task_data.get("entities", {}).get("sender", "unknown")
        subject = task_data.get("entities", {}).get("subject", "No subject")
        plan = create_email_plan(sender, subject, task_data)

    elif intent == "payment_request":
        invoice = task_data.get("entities", {}).get("invoice_number", "UNKNOWN")
        amount = task_data.get("entities", {}).get("amount", 0)
        vendor = task_data.get("entities", {}).get("vendor", "Unknown Vendor")
        plan = create_payment_plan(invoice, amount, vendor, task_data)

    elif intent == "data_extraction":
        file_name = task_data.get("source_file", "unknown")
        data_type = task_data.get("data_type", "general")
        plan = create_extraction_plan(file_name, data_type)

    else:
        # Generic plan template
        plan = create_generic_plan(task_data)

    # Write plan to file
    bronze_dir = Path(__file__).parent.parent
    plans_dir = bronze_dir / "Plans"
    plans_dir.mkdir(parents=True, exist_ok=True)

    plan_file = plans_dir / plan["plan_file"].split("/")[-1]

    # Check DRY_RUN
    dry_run = task_data.get("dry_run", True)

    if not dry_run:
        with open(plan_file, 'w', encoding='utf-8') as f:
            f.write(plan["content"])
    else:
        print(f"[DRY RUN] Would create plan: {plan_file}")

    return {
        **plan,
        "dry_run": dry_run,
        "timestamp": datetime.now().isoformat()
    }


def create_generic_plan(task_data: dict) -> dict:
    """Create a generic plan for unknown task types."""

    plan_content = f"""---
type: plan
created: {datetime.now().isoformat()}
priority: {task_data.get('priority', 'medium')}
status: pending
intent: {task_data.get('intent_analysis', {}).get('intent', 'unknown')}
---

# Task Plan: {task_data.get('task_name', 'Generic Task')}

**Created:** {datetime.now().strftime('%Y-%m-%d')}
**Priority:** {task_data.get('priority', 'medium').capitalize()}
**Status:** Pending

## Overview
{task_data.get('task_description', 'No description provided')}

## Steps

### Step 1: Analyze Task Requirements
**Status:** Pending
**Action:** Understand what needs to be done
**Tools Required:** text_analyzer

### Step 2: Determine Execution Approach
**Status:** Pending
**Action:** Decide on the best way to complete this task
**Tools Required:** task_planner

### Step 3: Execute Task
**Status:** Pending
**Action:** Perform the required actions
**Tools Required:** [To be determined]

### Step 4: Verify Results
**Status:** Pending
**Action:** Confirm task was completed correctly
**Tools Required:** text_analyzer

### Step 5: Document Completion
**Status:** Pending
**Action:** Save results and move to Done/
**Tools Required:** file_processor
"""

    plan_filename = f"generic_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    return {
        "status": "success",
        "plan_file": f"Plans/{plan_filename}",
        "plan_name": task_data.get("task_name", "Generic Task"),
        "steps_count": 5,
        "requires_approval": False,
        "content": plan_content
    }
```

## Important Notes

1. **Always include frontmatter** with metadata for Obsidian
2. **Use step-by-step format** for clear execution
3. **Specify tools required** for each step
4. **Check DRY_RUN flag** before writing files
5. **Route to appropriate template** based on intent
6. **Include approval requirements** in the plan
7. **Make plans actionable** and unambiguous

## Integration Points

This skill integrates with:
- **text_analyzer**: Uses intent analysis to select plan template
- **file_processor**: Writes plan files to Plans/ folder
- **orchestrator**: Called when complex tasks are detected
- **email_drafter**: Provides steps for email workflows
- **data_extractor**: Provides steps for data extraction workflows

## Error Handling

```python
def safe_create_plan(task_data: dict) -> dict:
    """Create plan with comprehensive error handling."""

    try:
        if not task_data.get("task_name"):
            return {
                "status": "error",
                "error": "task_name is required",
                "timestamp": datetime.now().isoformat()
            }

        return create_plan(task_data)

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "task_data": task_data,
            "timestamp": datetime.now().isoformat()
        }
```
