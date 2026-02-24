# AI Employee Skills

This directory documents the skills that Claude uses when processing tasks in the Bronze Tier.

## Available Skills

### 1. file_processor
**Purpose:** Read and write files in the vault

**Input:**
- File path (relative or absolute)
- Operation type (read/write)

**Output:**
- File contents (for read)
- Confirmation of write (for write)

**Example Usage:**
```python
# Read a file
content = read_file("Needs_Action/task_2026-02-24.md")

# Write a file
write_file("Plans/plan_001.md", "# Task Plan\n...")
```

---

### 2. text_analyzer
**Purpose:** Analyze text content and extract intent

**Input:**
- Text content to analyze
- Analysis type (sentiment, intent, entity extraction)

**Output:**
- Structured analysis results
- Detected intent/categories

**Example Usage:**
```python
# Analyze intent from dropped file
intent = analyze_intent(file_content)
# Returns: {"intent": "email_draft", "priority": "high", "category": "communication"}
```

---

### 3. task_planner
**Purpose:** Create step-by-step plans as .md files in /Plans/

**Input:**
- Task description
- Requirements from dropped file
- Business rules from Company_Handbook.md

**Output:**
- Markdown plan file with structured steps
- Frontmatter with metadata

**Example Usage:**
```python
# Create a plan for processing email
plan = create_plan(
    title="Email Response Plan",
    steps=[
        "Analyze email content",
        "Check against Company_Handbook.md rules",
        "Draft response",
        "Flag if over $500 threshold",
        "Save to Pending_Approval"
    ]
)
# Creates: Plans/email_response_plan.md
```

---

### 4. email_drafter
**Purpose:** Draft email responses for approval

**Input:**
- Original email content
- Sender information
- Response requirements from Company_Handbook.md

**Output:**
- Draft email in formal language
- Saved to Pending_Approval folder

**Example Usage:**
```python
# Draft email response
draft = draft_email(
    to="client@example.com",
    subject="Re: Project Proposal",
    original_email=email_content,
    tone="formal"
)
# Creates: Pending_Approval/email_draft_001.md
```

---

### 5. data_extractor
**Purpose:** Extract structured data from dropped files

**Input:**
- File path or content
- Extraction schema

**Output:**
- Structured JSON data
- Key-value pairs

**Example Usage:**
```python
# Extract data from invoice
data = extract_data(
    file="invoice.pdf",
    schema={
        "invoice_number": "string",
        "amount": "number",
        "vendor": "string",
        "date": "date"
    }
)
# Returns: {"invoice_number": "INV-001", "amount": 750.00, "vendor": "Acme Corp", "date": "2026-02-24"}
```

---

## Skill invocation flow

1. **File dropped** → `file_processor` reads the file
2. **Content analyzed** → `text_analyzer` determines intent
3. **Data extracted** → `data_extractor` pulls structured info
4. **Plan created** → `task_planner` creates execution plan
5. **Action taken** → `email_drafter` or other skill executes
6. **Result saved** → File moved to appropriate folder

## Adding new skills

To add a new skill:

1. Create a Python module in this folder
2. Document it following the format above
3. Register in the orchestrator logic
4. Test with DRY_RUN=true first

## Skill configuration

Skills can be configured via environment variables or config files:

```bash
# Set default skill parameters
export SKILL_TIMEOUT=30
export SKILL_MAX_RETRIES=3
export SKILL_LOG_LEVEL=info
```
