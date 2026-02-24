---
name: text-analyzer
description: Analyze text content to extract intent, sentiment, entities, and categorize information. Use this skill after reading file contents to understand what action is needed.
license: Apache-2.0
compatibility: Requires re for pattern matching
metadata:
  author: AI Employee Bronze Tier
  version: "1.0"
  tier: bronze
---

# Text Analyzer Skill

## Purpose
Analyze text content from dropped files to determine intent, extract key information, and categorize the request for appropriate processing.

## When to Use This Skill
- After reading a file from `Needs_Action/`
- When determining what type of task was dropped
- To extract structured data from unstructured text
- To check for approval requirements against business rules

## Input Parameters

```json
{
  "content": "text content to analyze",
  "analysis_type": "intent|sentiment|entities|all",
  "context": {
    "source_file": "filename.txt",
    "company_rules": "reference to Company_Handbook.md"
  }
}
```

## Output Format

```json
{
  "status": "success",
  "analysis_type": "intent",
  "results": {
    "intent": "email_draft|payment_request|data_extraction|unknown",
    "confidence": 0.95,
    "priority": "high|medium|low",
    "category": "communication|finance|admin|other",
    "entities": {
      "sender": "email@example.com",
      "amount": 750.00,
      "request_type": "invoice_payment"
    },
    "requires_approval": true,
    "approval_reason": "Payment over $500 threshold",
    "extracted_data": {}
  },
  "timestamp": "ISO-8601 timestamp"
}
```

## Intent Detection Patterns

### Email Draft Request
**Indicators:**
- Keywords: "reply", "respond", "email", "draft", "response"
- Pattern: email addresses, subject lines
- Example: "Please draft a response to client@company.com"

### Payment Request
**Indicators:**
- Keywords: "pay", "invoice", "payment", "transfer", "approve"
- Pattern: currency amounts ($), invoice numbers
- Example: "Process payment of $750 for invoice INV-001"

### Data Extraction Request
**Indicators:**
- Keywords: "extract", "parse", "analyze", "summarize"
- Pattern: structured documents, forms
- Example: "Extract customer data from this form"

### Task/Plan Request
**Indicators:**
- Keywords: "plan", "steps", "how to", "process"
- Pattern: action items, sequences
- Example: "Create a plan for the project launch"

## Example Usage

### Example 1: Analyze Email for Intent
**Input Content:**
```
From: vendor@supplier.com
Subject: Invoice #INV-2024-001 for $750

Dear Team,

Please find attached invoice for services rendered.
Amount due: $750
Due date: 2026-03-01

Please process payment at your earliest convenience.

Best regards,
ABC Supplier
```

**Analysis:**
```python
import re
from datetime import datetime

def analyze_intent(content: str, context: dict = None) -> dict:
    """Analyze text to determine intent and extract key information."""

    results = {
        "intent": "unknown",
        "confidence": 0.0,
        "priority": "medium",
        "category": "other",
        "entities": {},
        "requires_approval": False,
        "approval_reason": None,
        "extracted_data": {}
    }

    content_lower = content.lower()

    # Detect email reply request
    if re.search(r'\b(reply|respond|draft.*email|email.*response)\b', content_lower):
        results["intent"] = "email_draft"
        results["category"] = "communication"
        results["confidence"] = 0.8
        results["requires_approval"] = True
        results["approval_reason"] = "Email reply to new contact"

        # Extract email addresses
        emails = re.findall(r'[\w\.-]+@[\w\.-]+', content)
        if emails:
            results["entities"]["sender"] = emails[0]

    # Detect payment request
    if re.search(r'\b(invoice|payment|pay|transfer|amount due)\b', content_lower):
        results["intent"] = "payment_request"
        results["category"] = "finance"
        results["confidence"] = 0.9

        # Extract amounts
        amounts = re.findall(r'\$?(\d+(?:\.\d{2})?)', content)
        if amounts:
            amount = float(amounts[0])
            results["entities"]["amount"] = amount

            # Check $500 threshold
            if amount > 500:
                results["requires_approval"] = True
                results["approval_reason"] = f"Payment of ${amount} exceeds $500 threshold"
                results["priority"] = "high"

        # Extract invoice numbers
        invoice = re.search(r'invoice\s*#?\s*([A-Z0-9-]+)', content, re.IGNORECASE)
        if invoice:
            results["entities"]["invoice_number"] = invoice.group(1)

    # Extract subject lines (for emails)
    subject = re.search(r'Subject:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
    if subject:
        results["entities"]["subject"] = subject.group(1).strip()

    # Extract dates
    dates = re.findall(r'\d{4}-\d{2}-\d{2}', content)
    if dates:
        results["entities"]["dates"] = dates

    return {
        "status": "success",
        "analysis_type": "intent",
        "results": results,
        "timestamp": datetime.now().isoformat()
    }
```

### Example 2: Check Against Company Rules
```python
def check_approval_requirements(analysis: dict, handbook_rules: dict) -> dict:
    """Check if action requires approval based on Company_Handbook.md rules."""

    approval_rules = {
        "payment_threshold": 500,
        "new_contact_email": True,
        "file_deletion": True,
        "social_media": True
    }

    results = analysis["results"]

    # Check payment threshold
    if results.get("intent") == "payment_request":
        amount = results["entities"].get("amount", 0)
        if amount > approval_rules["payment_threshold"]:
            results["requires_approval"] = True
            results["approval_reason"] = f"Payment of ${amount} exceeds ${approval_rules['payment_threshold']} threshold"

    # Check email to new contacts
    if results.get("intent") == "email_draft":
        if approval_rules["new_contact_email"]:
            results["requires_approval"] = True
            results["approval_reason"] = "Email reply requires approval per business rules"

    return analysis
```

## Sentiment Analysis

```python
def analyze_sentiment(content: str) -> dict:
    """Basic sentiment analysis using keyword matching."""

    positive_words = ["thank", "appreciate", "great", "excellent", "please"]
    negative_words = ["urgent", "immediately", "problem", "error", "issue", "complaint"]
    urgent_words = ["urgent", "asap", "immediately", "deadline", "critical"]

    content_lower = content.lower()

    score = 0
    if any(word in content_lower for word in positive_words):
        score += 1
    if any(word in content_lower for word in negative_words):
        score -= 1

    if any(word in content_lower for word in urgent_words):
        priority = "high"
    elif score < 0:
        priority = "medium"
    else:
        priority = "low"

    return {
        "sentiment": "positive" if score > 0 else "neutral" if score == 0 else "negative",
        "score": score,
        "priority": priority
    }
```

## Entity Extraction Patterns

```python
# Email addresses
r'[\w\.-]+@[\w\.-]+'

# Phone numbers
r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'

# Currency amounts
r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)'

# Dates (YYYY-MM-DD)
r'\d{4}-\d{2}-\d{2}'

# Invoice numbers
r'invoice\s*#?\s*([A-Z0-9-]+)'

# URLs
r'https?://[^\s]+'
```

## Important Notes

1. **Always return structured JSON** for programmatic consumption
2. **Include confidence scores** for intent detection
3. **Extract all relevant entities** for downstream processing
4. **Check against Company_Handbook.md** rules
5. **Flag approval requirements** explicitly
6. **Handle edge cases** like ambiguous intent gracefully

## Integration Points

This skill integrates with:
- **file_processor**: Receives content from file reading
- **task_planner**: Provides analysis for plan creation
- **email_drafter**: Extracts email-specific entities
- **data_extractor**: Handles complex data extraction cases
- **orchestrator**: Determines which skill to call next

## Error Handling

```python
def analyze_text(content: str, analysis_type: str = "all") -> dict:
    """Main entry point with error handling."""

    if not content or not content.strip():
        return {
            "status": "error",
            "error": "Empty content provided",
            "timestamp": datetime.now().isoformat()
        }

    try:
        if analysis_type == "intent":
            return analyze_intent(content)
        elif analysis_type == "sentiment":
            return analyze_sentiment(content)
        elif analysis_type == "all":
            intent_result = analyze_intent(content)
            sentiment_result = analyze_sentiment(content)
            return {**intent_result, "sentiment": sentiment_result}
        else:
            return {
                "status": "error",
                "error": f"Unknown analysis type: {analysis_type}",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
```
