---
name: approval-manager
description: Manage human-in-the-loop approval workflow. Track pending approvals, route requests, and enforce business rules.
license: Apache-2.0
compatibility: Python built-in, no external dependencies
metadata:
  author: AI Employee Silver Tier
  version: "1.0"
  tier: silver
---

# Approval Manager Skill

## Purpose
Manage the complete human-in-the-loop approval workflow for the AI Employee. Track pending approvals, route requests to appropriate approvers, enforce business rules from Company_Handbook.md, and maintain audit trails of all approval decisions.

## When to Use This Skill
- Routing actions requiring approval
- Checking if approval is needed for an action
- Submitting approval requests
- Processing approval decisions (approve/reject)
- Listing pending approvals
- Generating approval reports
- Enforcing Company_Handbook.md rules

## Input Parameters

```json
{
  "action": "check|submit|approve|reject|list|cancel",
  "request_id": "req_001",
  "action_type": "email_send|payment_process|social_post|file_delete",
  "request_details": {
    "recipient": "new.contact@example.com",
    "amount": 750.00,
    "platform": "linkedin",
    "file": "/path/to/file.pdf"
  },
  "reason": "Payment exceeds $500 threshold",
  "requester": "ai_employee",
  "approver": "manager@company.com",
  "comment": "Approved - within budget",
  "dry_run": true
}
```

## Output Format

```json
{
  "status": "success",
  "action": "submit",
  "timestamp": "2026-02-24T12:00:00",
  "request_id": "req_001",
  "approval_required": true,
  "approval_status": "pending",
  "reason": "New contact detected - requires approval per Company_Handbook.md",
  "rules_checked": [
    "rule: email_new_contact",
    "rule: payment_threshold"
  ],
  "approver": "manager@company.com",
  "expires_at": "2026-02-24T18:00:00"
}
```

## Python Implementation

```python
#!/usr/bin/env python3
"""
Approval Manager Skill for Silver Tier AI Employee
Manage human-in-the-loop approval workflow.
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Configuration
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'
BRONZE_DIR = Path(__file__).parent.parent.parent / "Bronze"
APPROVAL_FILE = BRONZE_DIR / "Config" / "approvals.json"
COMPANY_HANDBOOK = BRONZE_DIR / "Company_Handbook.md"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ApprovalRule:
    """Represents an approval rule from Company_Handbook.md."""

    def __init__(
        self,
        rule_id: str,
        name: str,
        condition: str,
        threshold: Any = None,
        approver: str = "manager",
        description: str = ""
    ):
        self.rule_id = rule_id
        self.name = name
        self.condition = condition
        self.threshold = threshold
        self.approver = approver
        self.description = description

    def evaluate(self, context: Dict) -> bool:
        """Evaluate if this rule applies to the given context."""
        if self.condition == "payment_amount":
            amount = context.get('amount', 0)
            return amount > self.threshold if self.threshold else False

        elif self.condition == "new_contact":
            # Check if recipient is in known contacts
            known_contacts = self._load_known_contacts()
            recipient = context.get('recipient', '')
            return recipient not in known_contacts

        elif self.condition == "social_media_post":
            return True  # All social posts require approval

        elif self.condition == "file_deletion":
            return True  # All file deletions require approval

        elif self.condition == "payment_any":
            return context.get('is_payment', False)

        return False

    def _load_known_contacts(self) -> set:
        """Load known contacts from file."""
        contacts_file = BRONZE_DIR / "Config" / "known_contacts.json"

        if contacts_file.exists():
            try:
                with open(contacts_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('contacts', []))
            except:
                pass

        return set()


class ApprovalRequest:
    """Represents an approval request."""

    def __init__(
        self,
        request_id: str,
        action_type: str,
        request_details: Dict,
        reason: str,
        approver: str = "manager",
        timeout_hours: int = 6
    ):
        self.request_id = request_id
        self.action_type = action_type
        self.request_details = request_details
        self.reason = reason
        self.approver = approver
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(hours=timeout_hours)
        self.status = "pending"  # pending, approved, rejected, expired, cancelled
        self.approver_comment = None
        self.reviewed_at = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "action_type": self.action_type,
            "request_details": self.request_details,
            "reason": self.reason,
            "approver": self.approver,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "status": self.status,
            "approver_comment": self.approver_comment,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None
        }

    def is_expired(self) -> bool:
        """Check if request has expired."""
        return datetime.now() > self.expires_at


class ApprovalManager:
    """Manages approval workflow."""

    def __init__(self):
        self.rules = self._load_rules()
        self.requests = self._load_requests()
        self.handbook_rules = self._load_company_handbook()

    def _load_rules(self) -> List[ApprovalRule]:
        """Load approval rules from configuration."""
        return [
            ApprovalRule(
                rule_id="payment_500",
                name="Payment over $500",
                condition="payment_amount",
                threshold=500,
                approver="manager",
                description="Payments over $500 require managerial approval"
            ),
            ApprovalRule(
                rule_id="email_new_contact",
                name="Email to new contact",
                condition="new_contact",
                approver="manager",
                description="Email replies to new contacts require approval"
            ),
            ApprovalRule(
                rule_id="social_post",
                name="Social media post",
                condition="social_media_post",
                approver="manager",
                description="All social media posts require approval"
            ),
            ApprovalRule(
                rule_id="file_delete",
                name="File deletion",
                condition="file_deletion",
                approver="manager",
                description="All file deletions require approval"
            ),
            ApprovalRule(
                rule_id="payment_any",
                name="Any payment",
                condition="payment_any",
                approver="finance",
                description="All payments require finance approval"
            )
        ]

    def _load_requests(self) -> Dict[str, ApprovalRequest]:
        """Load existing approval requests."""
        requests = {}

        if APPROVAL_FILE.exists():
            try:
                with open(APPROVAL_FILE, 'r') as f:
                    data = json.load(f)

                for req_data in data:
                    request = ApprovalRequest(
                        request_id=req_data['request_id'],
                        action_type=req_data['action_type'],
                        request_details=req_data['request_details'],
                        reason=req_data['reason'],
                        approver=req_data.get('approver', 'manager'),
                        timeout_hours=6
                    )

                    # Restore status
                    request.status = req_data['status']
                    request.approver_comment = req_data.get('approver_comment')
                    if req_data.get('reviewed_at'):
                        request.reviewed_at = datetime.fromisoformat(req_data['reviewed_at'])

                    requests[request.request_id] = request

            except Exception as e:
                logger.error(f"Failed to load requests: {e}")

        return requests

    def _save_requests(self):
        """Save approval requests to file."""
        try:
            APPROVAL_FILE.parent.mkdir(parents=True, exist_ok=True)

            data = [req.to_dict() for req in self.requests.values()]

            with open(APPROVAL_FILE, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save requests: {e}")

    def _load_company_handbook(self) -> Dict:
        """Load rules from Company_Handbook.md."""
        rules = {
            "payment_threshold": 500,
            "email_new_contact": True,
            "social_media_posts": True,
            "file_deletions": True,
            "business_hours": "9 AM - 6 PM"
        }

        if COMPANY_HANDBOOK.exists():
            try:
                with open(COMPANY_HANDBOOK, 'r') as f:
                    content = f.read()

                # Parse payment threshold
                import re
                payment_match = re.search(r'Payments?:\s*>\s*\$(\d+)', content)
                if payment_match:
                    rules["payment_threshold"] = int(payment_match.group(1))

            except Exception as e:
                logger.warning(f"Could not parse Company_Handbook.md: {e}")

        return rules

    def check_approval_required(self, action_type: str, context: Dict) -> Dict[str, Any]:
        """Check if an action requires approval."""

        triggered_rules = []
        reasons = []

        # Check each rule
        for rule in self.rules:
            if rule.evaluate(context):
                triggered_rules.append(rule)
                reasons.append(rule.description)

        # Also check handbook rules
        if action_type == "email_send":
            if self.handbook_rules.get("email_new_contact") and context.get("is_new_contact"):
                reasons.append("Email to new contact requires approval")

        approval_required = len(triggered_rules) > 0 or len(reasons) > 0

        # Determine approver
        approver = "manager"
        for rule in triggered_rules:
            if rule.approver == "finance":
                approver = "finance"
                break

        return {
            "status": "success",
            "action": "check",
            "timestamp": datetime.now().isoformat(),
            "approval_required": approval_required,
            "reason": "; ".join(reasons) if reasons else "No approval required",
            "rules_checked": [r.rule_id for r in triggered_rules],
            "approver": approver,
            "handbook_rules_applied": len(reasons) > 0
        }

    def submit_approval_request(
        self,
        action_type: str,
        request_details: Dict,
        reason: str,
        approver: str = "manager"
    ) -> Dict[str, Any]:
        """Submit a new approval request."""

        # First check if approval is needed
        check_result = self.check_approval_required(action_type, request_details)

        if not check_result['approval_required']:
            return {
                "status": "success",
                "action": "submit",
                "timestamp": datetime.now().isoformat(),
                "message": "No approval required for this action",
                "approval_required": False
            }

        # Create approval request
        request_id = f"req_{uuid.uuid4().hex[:8]}"

        request = ApprovalRequest(
            request_id=request_id,
            action_type=action_type,
            request_details=request_details,
            reason=reason,
            approver=approver
        )

        self.requests[request_id] = request
        self._save_requests()

        # Log activity
        self._log_activity('approval_requested', {
            'request_id': request_id,
            'action_type': action_type,
            'approver': approver
        })

        return {
            "status": "success",
            "action": "submit",
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "approval_required": True,
            "approval_status": "pending",
            "reason": reason,
            "approver": approver,
            "expires_at": request.expires_at.isoformat(),
            "message": f"Approval request submitted. Request ID: {request_id}"
        }

    def approve_request(
        self,
        request_id: str,
        comment: str = None,
        approver: str = "manager"
    ) -> Dict[str, Any]:
        """Approve an approval request."""

        if request_id not in self.requests:
            return {
                "status": "error",
                "error": f"Request not found: {request_id}",
                "timestamp": datetime.now().isoformat()
            }

        request = self.requests[request_id]

        if request.status != "pending":
            return {
                "status": "error",
                "error": f"Request is not pending (current status: {request.status})",
                "timestamp": datetime.now().isoformat()
            }

        if request.is_expired():
            request.status = "expired"
            self._save_requests()

            return {
                "status": "error",
                "error": "Request has expired",
                "timestamp": datetime.now().isoformat()
            }

        # Approve request
        request.status = "approved"
        request.approver_comment = comment
        request.reviewed_at = datetime.now()

        self._save_requests()

        # Log activity
        self._log_activity('approval_granted', {
            'request_id': request_id,
            'approver': approver,
            'comment': comment
        })

        return {
            "status": "success",
            "action": "approve",
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "approval_status": "approved",
            "comment": comment,
            "action_allowed": True,
            "message": f"Request {request_id} approved. Action may proceed."
        }

    def reject_request(
        self,
        request_id: str,
        comment: str = None,
        approver: str = "manager"
    ) -> Dict[str, Any]:
        """Reject an approval request."""

        if request_id not in self.requests:
            return {
                "status": "error",
                "error": f"Request not found: {request_id}",
                "timestamp": datetime.now().isoformat()
            }

        request = self.requests[request_id]

        if request.status != "pending":
            return {
                "status": "error",
                "error": f"Request is not pending (current status: {request.status})",
                "timestamp": datetime.now().isoformat()
            }

        # Reject request
        request.status = "rejected"
        request.approver_comment = comment
        request.reviewed_at = datetime.now()

        self._save_requests()

        # Log activity
        self._log_activity('approval_rejected', {
            'request_id': request_id,
            'approver': approver,
            'comment': comment
        })

        return {
            "status": "success",
            "action": "reject",
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "approval_status": "rejected",
            "comment": comment,
            "action_allowed": False,
            "message": f"Request {request_id} rejected. Action cannot proceed."
        }

    def list_requests(self, status: str = None) -> Dict[str, Any]:
        """List approval requests, optionally filtered by status."""

        requests = list(self.requests.values())

        if status:
            requests = [r for r in requests if r.status == status]

        # Check for expired requests
        for request in requests:
            if request.status == "pending" and request.is_expired():
                request.status = "expired"

        self._save_requests()

        return {
            "status": "success",
            "action": "list",
            "timestamp": datetime.now().isoformat(),
            "requests": [r.to_dict() for r in requests],
            "count": len(requests),
            "filter": status
        }

    def cancel_request(self, request_id: str) -> Dict[str, Any]:
        """Cancel a pending approval request."""

        if request_id not in self.requests:
            return {
                "status": "error",
                "error": f"Request not found: {request_id}",
                "timestamp": datetime.now().isoformat()
            }

        request = self.requests[request_id]

        if request.status != "pending":
            return {
                "status": "error",
                "error": f"Cannot cancel request with status: {request.status}",
                "timestamp": datetime.now().isoformat()
            }

        request.status = "cancelled"
        self._save_requests()

        # Log activity
        self._log_activity('approval_cancelled', {
            'request_id': request_id
        })

        return {
            "status": "success",
            "action": "cancel",
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "approval_status": "cancelled",
            "message": f"Request {request_id} cancelled"
        }

    def cleanup_expired_requests(self) -> Dict[str, Any]:
        """Mark expired requests and remove old completed ones."""

        expired_count = 0
        removed_count = 0

        to_remove = []

        for request_id, request in self.requests.items():
            if request.status == "pending" and request.is_expired():
                request.status = "expired"
                expired_count += 1

            # Remove completed/rejected/expired requests older than 30 days
            if request.status in ["completed", "rejected", "expired", "cancelled"]:
                age = datetime.now() - request.reviewed_at if request.reviewed_at else datetime.now() - request.created_at
                if age.days > 30:
                    to_remove.append(request_id)

        for request_id in to_remove:
            del self.requests[request_id]
            removed_count += 1

        if expired_count > 0 or removed_count > 0:
            self._save_requests()

        return {
            "status": "success",
            "action": "cleanup",
            "timestamp": datetime.now().isoformat(),
            "expired_marked": expired_count,
            "old_removed": removed_count
        }

    def _log_activity(self, action: str, details: Dict = None):
        """Log activity to JSON file."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "skill": "approval_manager",
            "dry_run": DRY_RUN
        }

        if details:
            log_entry.update(details)

        # Save to logs folder
        log_dir = BRONZE_DIR / "Logs"
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


def approval_manager_handler(input_params: Dict) -> Dict[str, Any]:
    """Main handler function for Approval Manager skill."""
    action = input_params.get('action', 'check')

    manager = ApprovalManager()

    try:
        if action == 'check':
            return manager.check_approval_required(
                action_type=input_params.get('action_type'),
                context=input_params.get('request_details', {})
            )

        elif action == 'submit':
            return manager.submit_approval_request(
                action_type=input_params['action_type'],
                request_details=input_params.get('request_details', {}),
                reason=input_params.get('reason', ''),
                approver=input_params.get('approver', 'manager')
            )

        elif action == 'approve':
            return manager.approve_request(
                request_id=input_params['request_id'],
                comment=input_params.get('comment'),
                approver=input_params.get('approver', 'manager')
            )

        elif action == 'reject':
            return manager.reject_request(
                request_id=input_params['request_id'],
                comment=input_params.get('comment'),
                approver=input_params.get('approver', 'manager')
            )

        elif action == 'list':
            return manager.list_requests(
                status=input_params.get('status')
            )

        elif action == 'cancel':
            return manager.cancel_request(
                request_id=input_params['request_id']
            )

        elif action == 'cleanup':
            return manager.cleanup_expired_requests()

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
    # Example: Check if payment requires approval
    params = {
        "action": "check",
        "action_type": "payment_process",
        "request_details": {
            "amount": 750.00,
            "vendor": "acme-corp"
        }
    }

    result = approval_manager_handler(params)
    print(json.dumps(result, indent=2))
```

## Integration Points

This skill integrates with:
- **gmail_sender** - Check approval for new contact emails
- **linkedin_poster** - Get approval before posting
- **scheduler** - Check approval before scheduling tasks
- **file_processor** - Get approval before file deletion
- **Company_Handbook.md** - Enforce business rules
- All Silver skills requiring approval

## Approval Rules

Default rules loaded from Company_Handbook.md:

| Rule | Threshold | Approver | Description |
|------|-----------|----------|-------------|
| payment_500 | $500 | manager | Payments over $500 |
| email_new_contact | any | manager | Emails to new contacts |
| social_post | any | manager | Social media posts |
| file_delete | any | manager | File deletions |
| payment_any | any | finance | All payments |

## Workflow

1. **Check** - Action is checked against rules
2. **Submit** - Request created if approval needed
3. **Notify** - Approver notified (email/message)
4. **Approve/Reject** - Approver makes decision
5. **Proceed** - Action executes if approved
6. **Audit** - Decision logged

## Error Handling

1. **Request Not Found** - Return error with available IDs
2. **Invalid Status** - Reject state transitions
3. **Expired Request** - Mark as expired, reject action
4. **Unauthorized Approver** - Verify approver role
5. **File Corruption** - Recreate from defaults

## Testing

```bash
# Check if approval required
python approval_manager.md --action check \
  --action_type email_send \
  --request_details '{"recipient": "new@example.com"}'

# Submit approval request
python approval_manager.md --action submit \
  --action_type payment_process \
  --request_details '{"amount": 750}' \
  --reason "Payment exceeds $500 threshold"

# Approve request
python approval_manager.md --action approve \
  --request_id req_abc123 \
  --comment "Approved - within budget"

# List pending requests
python approval_manager.md --action list --status pending
```

## Persistence

Approval requests saved to: `Bronze/Config/approvals.json`

Includes:
- All requests (pending and historical)
- Status changes with timestamps
- Approver comments
- Request details and metadata
