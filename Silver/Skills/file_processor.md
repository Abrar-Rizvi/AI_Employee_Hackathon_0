---
name: file-processor
description: Read and write files in the Obsidian vault. Use this skill when you need to read file contents, create new files, or update existing files in the Bronze folder structure.
license: Apache-2.0
compatibility: Requires pathlib for file operations
metadata:
  author: AI Employee Bronze Tier
  version: "1.0"
  tier: bronze
---

# File Processor Skill

## Purpose
Read, create, and update files within the Bronze folder structure of the Obsidian vault.

## When to Use This Skill
- Reading task files from `Needs_Action/`
- Reading configuration files from `Config/`
- Creating plan files in `Plans/`
- Creating email drafts in `Pending_Approval/`
- Updating the `Dashboard.md`
- Reading business rules from `Company_Handbook.md`

## Input Parameters

### For Reading Files
```json
{
  "file_path": "relative/path/from/bronze/folder",
  "operation": "read"
}
```

### For Writing Files
```json
{
  "file_path": "relative/path/from/bronze/folder",
  "operation": "write",
  "content": "file content here",
  "create_directories": true
}
```

## Output Format

### Success Response
```json
{
  "status": "success",
  "operation": "read|write",
  "file_path": "path/to/file",
  "content": "file contents (for read operations)",
  "timestamp": "ISO-8601 timestamp"
}
```

### Error Response
```json
{
  "status": "error",
  "error": "error message",
  "file_path": "path/to/file",
  "timestamp": "ISO-8601 timestamp"
}
```

## Example Usage

### Example 1: Read a Task File
**User Request:** "Read the task file that was just dropped"

**Execution:**
```python
from pathlib import Path

def read_file(file_path: str) -> dict:
    """Read a file from the Bronze folder."""
    full_path = Path(__file__).parent.parent / file_path

    if not full_path.exists():
        return {
            "status": "error",
            "error": f"File not found: {file_path}",
            "file_path": file_path,
            "timestamp": datetime.now().isoformat()
        }

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return {
            "status": "success",
            "operation": "read",
            "file_path": file_path,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "file_path": file_path,
            "timestamp": datetime.now().isoformat()
        }
```

### Example 2: Write a Plan File
**User Request:** "Create a plan for processing the email"

**Execution:**
```python
def write_file(file_path: str, content: str) -> dict:
    """Write a file to the Bronze folder."""
    full_path = Path(__file__).parent.parent / file_path

    try:
        # Create parent directories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return {
            "status": "success",
            "operation": "write",
            "file_path": file_path,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "file_path": file_path,
            "timestamp": datetime.now().isoformat()
        }

# Usage
plan_content = """---
type: plan
created: 2026-02-24
status: pending
---

# Email Processing Plan

## Steps
1. Read the dropped email file
2. Check Company_Handbook.md for approval rules
3. Extract key information (sender, subject, request)
4. Draft formal response
5. Save to Pending_Approval/
"""

write_file("Plans/email_processing_plan.md", plan_content)
```

## Important Notes

1. **Always use relative paths** from the Bronze folder
2. **Never use absolute paths** - breaks portability
3. **Check DRY_RUN flag** before writing files
4. **Handle exceptions gracefully** and return structured error responses
5. **Use UTF-8 encoding** for all file operations
6. **Create parent directories** when needed

## Integration Points

This skill integrates with:
- **text_analyzer**: After reading files, pass content to text analyzer
- **task_planner**: Write generated plans to Plans/ folder
- **email_drafter**: Write drafted emails to Pending_Approval/
- **orchestrator**: Called by orchestrator when processing tasks

## Error Handling

Common errors to handle:
- `FileNotFoundError`: File doesn't exist
- `PermissionError`: No write access
- `UnicodeDecodeError`: File encoding issues
- `OSError`: General file system errors

Always return structured error responses that include:
- Error type
- Error message
- File path
- Timestamp
