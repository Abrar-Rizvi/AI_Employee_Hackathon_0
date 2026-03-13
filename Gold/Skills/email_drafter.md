---
name: email-drafter
description: Draft professional email responses following business communication guidelines. Use this skill when you need to create email drafts for approval.
license: Apache-2.0
compatibility: Requires file_processor for saving drafts
metadata:
  author: AI Employee Bronze Tier
  version: "1.0"
  tier: bronze
---

# Email Drafter Skill

## Purpose
Draft professional, formal email responses following the communication guidelines from `Company_Handbook.md`. All drafts are saved to `Pending_Approval/` for human review before sending.

## When to Use This Skill
- Response needed to an incoming email
- Formal communication required
- Following up on a request
- Sending business correspondence
- Any email requiring approval before sending

## Input Parameters

```json
{
  "original_email": {
    "from": "sender@example.com",
    "subject": "Original subject line",
    "body": "Full email content",
    "received_date": "2026-02-24"
  },
  "response_requirements": {
    "tone": "formal|professional|friendly",
    "include_references": true,
    "address_points": ["point1", "point2"]
  },
  "company_rules": {
    "formal_language": true,
    "approval_required": true,
    "no_sensitive_info": true
  }
}
```

## Output Format

### Email Draft File in `Pending_Approval/`
```markdown
---
type: email_draft
created: 2026-02-24T12:00:00
priority: high
status: pending_approval
original_from: sender@example.com
original_subject: Re: Original Subject
---

# Email Draft: Response to sender@example.com

**Status:** Pending Approval
**Created:** 2026-02-24
**To:** sender@example.com
**Subject:** Re: Original Subject

## Original Email
**From:** sender@example.com
**Subject:** Original Subject
**Received:** 2026-02-24

[Original email content]

## Draft Response

Dear [Sender Name],

Thank you for your email dated [date] regarding [subject].

[Response body]

Sincerely,

[Your Name]

## Review Checklist
- [ ] Tone is formal and professional
- [ ] All points addressed
- [ ] No sensitive information included
- [ ] Follows Company_Handbook.md guidelines
- [ ] Ready to send
```

### JSON Response
```json
{
  "status": "success",
  "draft_file": "Pending_Approval/email_draft_001.md",
  "to": "recipient@example.com",
  "subject": "Re: Subject",
  "word_count": 245,
  "requires_approval": true,
  "timestamp": "ISO-8601 timestamp"
}
```

## Email Templates

### Template 1: Acknowledgment of Payment/Invoice
```python
def draft_payment_acknowledgment(invoice_data: dict, original_email: dict) -> dict:
    """Draft acknowledgment for received invoice."""

    sender = original_email.get("from", "vendor@example.com")
    invoice_number = invoice_data.get("invoice_number", "UNKNOWN")
    amount = invoice_data.get("amount", 0)
    due_date = invoice_data.get("due_date", "TBD")

    draft_content = f"""---
type: email_draft
created: {datetime.now().isoformat()}
priority: { "high" if amount > 500 else "medium" }
status: pending_approval
original_from: {sender}
original_subject: {original_email.get('subject', 'Invoice Received')}
approval_required: {"true" if amount > 500 else "false"}
---

# Email Draft: Invoice Acknowledgment - {invoice_number}

**Status:** Pending Approval
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**To:** {sender}
**Subject:** Re: Invoice {invoice_number} - Acknowledgment

## Original Email
**From:** {sender}
**Subject:** {original_email.get('subject', 'Invoice Received')}
**Received:** {datetime.now().strftime('%Y-%m-%d')}

{original_email.get('body', 'Email content not available')}

## Draft Response

Dear {sender.split('@')[0].title()},

Thank you for your email and for providing invoice {invoice_number}.

We acknowledge receipt of your invoice for ${amount:.2f}, due on {due_date}.

Please be advised that we are currently reviewing the invoice details. You can expect the following:

• Payment processing will begin within 3-5 business days
• You will receive a confirmation email once payment has been initiated
• Please allow additional time for bank processing

{'IMPORTANT: As this invoice exceeds $500, it requires managerial approval before payment can be processed. We will notify you once approval has been obtained.' if amount > 500 else 'This invoice is within our standard processing limits.'}

If you have any questions or require additional information, please do not hesitate to contact us.

Thank you for your continued partnership.

Sincerely,

Finance Department

---

## Review Checklist
- [ ] Invoice details verified ({invoice_number})
- [ ] Amount confirmed (${amount:.2f})
- [ ] {'Manager approval obtained (>$500)' if amount > 500 else 'Within approval authority'}
- [ ] Tone is professional and courteous
- [ ] No sensitive information disclosed
- [ ] Ready to send

## Notes
- Invoice amount: ${amount:.2f}
- Due date: {due_date}
- {'⚠️ REQUIRES MANAGER APPROVAL' if amount > 500 else '✓ Standard processing'}
- Reference: Company_Handbook.md payment rules
"""

    # Save draft
    draft_filename = f"email_draft_{invoice_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    return {
        "status": "success",
        "draft_file": f"Pending_Approval/{draft_filename}",
        "to": sender,
        "subject": f"Re: Invoice {invoice_number} - Acknowledgment",
        "word_count": len(draft_content.split()),
        "requires_approval": amount > 500,
        "content": draft_content
    }
```

### Template 2: General Business Response
```python
def draft_business_response(email_data: dict, original_email: dict) -> dict:
    """Draft a general business email response."""

    sender = original_email.get("from", "contact@example.com")
    subject = original_email.get("subject", "Your Inquiry")
    original_body = original_email.get("body", "")

    # Extract key points from original email
    key_points = email_data.get("address_points", ["your inquiry"])

    draft_content = f"""---
type: email_draft
created: {datetime.now().isoformat()}
priority: medium
status: pending_approval
original_from: {sender}
original_subject: {subject}
approval_required: true
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

{original_body}

## Draft Response

Dear {sender.split('@')[0].title()},

Thank you for your email regarding {subject}.

We have received your communication and appreciate you bringing this matter to our attention.

"""

    # Add responses to key points
    for i, point in enumerate(key_points, 1):
        draft_content += f"\nRegarding {point}, "
        draft_content += "we are currently reviewing the details and will provide a comprehensive response shortly.\n"

    draft_content += f"""
Should you require any clarification or have additional questions in the meantime, please do not hesitate to reach out.

We value your correspondence and aim to respond to all inquiries within 24-48 hours.

Sincerely,

Customer Service Team

---

## Review Checklist
- [ ] All points from original email addressed
- [ ] Tone is formal and professional
- [ ] Response timeframe appropriate
- [ ] No sensitive information included
- [ ] Follows Company_Handbook.md communication rules
- [ ] Ready to send

## Notes
- Response follows formal business communication guidelines
- All inquiries will be addressed within 24-48 hours
- Reference: Company_Handbook.md communication rules
"""

    draft_filename = f"email_draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    return {
        "status": "success",
        "draft_file": f"Pending_Approval/{draft_filename}",
        "to": sender,
        "subject": f"Re: {subject}",
        "word_count": len(draft_content.split()),
        "requires_approval": True,
        "content": draft_content
    }
```

### Template 3: Request for Information
```python
def draft_information_request(request_data: dict, original_email: dict) -> dict:
    """Draft an email requesting additional information."""

    sender = original_email.get("from", "contact@example.com")
    subject = original_email.get("subject", "Information Request")

    missing_info = request_data.get("missing_information", [])
    context = request_data.get("context", "your recent inquiry")

    draft_content = f"""---
type: email_draft
created: {datetime.now().isoformat()}
priority: medium
status: pending_approval
original_from: {sender}
original_subject: {subject}
approval_required: true
---

# Email Draft: Information Request

**Status:** Pending Approval
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**To:** {sender}
**Subject:** Re: {subject} - Additional Information Required

## Original Email
**From:** {sender}
**Subject:** {subject}
**Received:** {datetime.now().strftime('%Y-%m-%d')}

{original_email.get('body', '')}

## Draft Response

Dear {sender.split('@')[0].title()},

Thank you for your email regarding {context}.

In order to proceed with your request, we require some additional information. Could you please provide the following details:

"""

    for i, item in enumerate(missing_info, 1):
        draft_content += f"{i}. **{item}**\n"

    draft_content += f"""
Once we receive this information, we will be able to assist you more effectively.

Please feel free to contact us if you have any questions about the information requested.

Sincerely,

Customer Service Team

---

## Review Checklist
- [ ] Information request is clear and specific
- [ ] Tone is professional and polite
- [ ] All required items listed
- [ ] Ready to send

## Notes
- Awaiting additional information before proceeding
- Reference: Company_Handbook.md communication rules
"""

    draft_filename = f"email_request_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    return {
        "status": "success",
        "draft_file": f"Pending_Approval/{draft_filename}",
        "to": sender,
        "subject": f"Re: {subject} - Additional Information Required",
        "word_count": len(draft_content.split()),
        "requires_approval": True,
        "content": draft_content
    }
```

## Main Drafting Function

```python
from pathlib import Path
from datetime import datetime
import re

def draft_email(email_data: dict, original_email: dict) -> dict:
    """Main entry point for drafting email responses."""

    # Determine email type
    intent = email_data.get("intent", "general")

    if intent == "payment_acknowledgment":
        draft = draft_payment_acknowledgment(email_data, original_email)

    elif intent == "information_request":
        draft = draft_information_request(email_data, original_email)

    else:
        # Default to business response
        draft = draft_business_response(email_data, original_email)

    # Write draft to file
    bronze_dir = Path(__file__).parent.parent
    approval_folder = bronze_dir / "Pending_Approval"
    approval_folder.mkdir(parents=True, exist_ok=True)

    draft_file = approval_folder / draft["draft_file"].split("/")[-1]

    dry_run = email_data.get("dry_run", True)

    if not dry_run:
        with open(draft_file, 'w', encoding='utf-8') as f:
            f.write(draft["content"])
    else:
        print(f"[DRY RUN] Would create email draft: {draft_file}")

    return {
        **draft,
        "dry_run": dry_run,
        "timestamp": datetime.now().isoformat()
    }
```

## Email Analysis Helper

```python
def analyze_email_content(content: str) -> dict:
    """Analyze email content to determine appropriate response type."""

    content_lower = content.lower()

    # Detect invoice/payment context
    if re.search(r'(invoice|payment|pay.*amount)', content_lower):
        return {"intent": "payment_acknowledgment"}

    # Detect missing information
    if re.search(r'(incomplete|missing|require.*information|please provide)', content_lower):
        return {"intent": "information_request"}

    # Default to general response
    return {"intent": "general"}
```

## Important Notes

1. **Always use formal language** as per Company_Handbook.md
2. **Save to Pending_Approval/** - never send directly
3. **Include original email** for reference
4. **Address all points** from original email
5. **Check approval requirements** before sending
6. **Use professional tone** - no slang or abbreviations
7. **Proofread** for grammar and clarity
8. **Check DRY_RUN flag** before writing files

## Company Rules Integration

Always reference `Company_Handbook.md` rules:

- ✅ Be polite and professional
- ✅ Use formal language for business emails
- ⚠️ Flag payments > $500 for approval
- ❌ Never share sensitive information without approval
- ✅ Proofread before sending

## Integration Points

This skill integrates with:
- **file_processor**: Reads original emails, writes draft responses
- **text_analyzer**: Analyzes email content to determine response type
- **task_planner**: Creates execution plan for email workflows
- **orchestrator**: Called when email_draft intent is detected

## Error Handling

```python
def safe_draft_email(email_data: dict, original_email: dict) -> dict:
    """Draft email with comprehensive error handling."""

    try:
        if not original_email.get("from"):
            return {
                "status": "error",
                "error": "Original email sender is required",
                "timestamp": datetime.now().isoformat()
            }

        return draft_email(email_data, original_email)

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "email_data": email_data,
            "timestamp": datetime.now().isoformat()
        }
```
