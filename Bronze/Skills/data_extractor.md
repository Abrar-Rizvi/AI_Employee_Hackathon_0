---
name: data-extractor
description: Extract structured data from documents, emails, and forms. Use this skill when you need to pull specific information from unstructured text.
license: Apache-2.0
compatibility: Requires re for pattern matching
metadata:
  author: AI Employee Bronze Tier
  version: "1.0"
  tier: bronze
---

# Data Extractor Skill

## Purpose
Extract structured data from unstructured documents including invoices, forms, emails, and other text-based files. Output data in JSON format for downstream processing.

## When to Use This Skill
- Extracting data from invoices or receipts
- Pulling information from forms
- Parsing email content for specific fields
- Converting unstructured text to structured data
- Extracting entities from documents

## Input Parameters

```json
{
  "source_file": "path/to/document.txt",
  "content": "Full text content of the document",
  "extraction_schema": {
    "field1": "string|number|date|email|currency",
    "field2": "string|number|date|email|currency"
  },
  "options": {
    "include_confidence": true,
    "strict_mode": false,
    "handle_missing": "skip|null|default"
  }
}
```

## Output Format

```json
{
  "status": "success",
  "source_file": "document.txt",
  "extracted_at": "2026-02-24T12:00:00",
  "data": {
    "field1": "extracted value",
    "field2": "extracted value"
  },
  "confidence": {
    "field1": 0.95,
    "field2": 0.80
  },
  "missing_fields": [],
  "metadata": {
    "total_fields": 2,
    "extracted_count": 2,
    "extraction_rate": 1.0
  }
}
```

## Extraction Schemas

### Schema 1: Invoice/Receipt
```python
INVOICE_SCHEMA = {
    "invoice_number": "string",
    "invoice_date": "date",
    "due_date": "date",
    "vendor_name": "string",
    "vendor_email": "email",
    "amount": "currency",
    "tax": "currency",
    "total": "currency",
    "line_items": "list"
}

def extract_invoice_data(content: str, options: dict = None) -> dict:
    """Extract data from an invoice or receipt."""

    import re
    from datetime import datetime

    if options is None:
        options = {}

    result = {
        "invoice_number": None,
        "invoice_date": None,
        "due_date": None,
        "vendor_name": None,
        "vendor_email": None,
        "amount": None,
        "tax": None,
        "total": None,
        "line_items": []
    }

    confidence = {}

    # Extract invoice number (multiple patterns)
    patterns = [
        r'invoice\s*#?\s*:?\s*([A-Z0-9-]+)',
        r'bill\s*#?\s*:?\s*([A-Z0-9-]+)',
        r'inv\s*#?\s*:?\s*([A-Z0-9-]+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            result["invoice_number"] = match.group(1)
            confidence["invoice_number"] = 0.95
            break

    # Extract dates
    dates = re.findall(r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}', content)

    if dates:
        # First date is typically invoice date
        result["invoice_date"] = dates[0]
        confidence["invoice_date"] = 0.90

        # Second date (if exists) might be due date
        if len(dates) > 1:
            result["due_date"] = dates[1]
            confidence["due_date"] = 0.85

    # Extract vendor name (usually after "From:", "Vendor:", or at top)
    vendor_patterns = [
        r'from\s*:?\s*([^\n]+)',
        r'vendor\s*:?\s*([^\n]+)',
        r'supplier\s*:?\s*([^\n]+)'
    ]

    for pattern in vendor_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            result["vendor_name"] = match.group(1).strip()
            confidence["vendor_name"] = 0.80
            break

    # Extract email
    emails = re.findall(r'[\w\.-]+@[\w\.-]+', content)
    if emails:
        result["vendor_email"] = emails[0]
        confidence["vendor_email"] = 0.95

    # Extract currency amounts (multiple patterns)
    # Look for amounts with currency symbols
    amounts = re.findall(r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', content)

    # Clean and convert amounts
    clean_amounts = []
    for amt in amounts:
        clean_amt = float(amt.replace(',', ''))
        if 0 < clean_amt < 100000:  # Reasonable range
            clean_amounts.append(clean_amt)

    if clean_amounts:
        # Usually largest amount is total, second largest is subtotal/amount
        clean_amounts.sort(reverse=True)

        if len(clean_amounts) >= 1:
            result["total"] = clean_amounts[0]
            confidence["total"] = 0.90

        if len(clean_amounts) >= 2:
            result["amount"] = clean_amounts[1]
            confidence["amount"] = 0.85

        if len(clean_amounts) >= 3:
            result["tax"] = clean_amounts[2] - clean_amounts[1]
            confidence["tax"] = 0.70

    # Extract line items (look for table-like structures)
    line_item_pattern = r'([^\n]+?)\s+\$?(\d+(?:\.\d{2})?)\s+\$?(\d+(?:\.\d{2})?)'
    items = re.findall(line_item_pattern, content)

    for item in items:
        result["line_items"].append({
            "description": item[0].strip(),
            "quantity": 1,
            "unit_price": float(item[1]),
            "total": float(item[2])
        })

    # Calculate metadata
    extracted_count = sum(1 for v in result.values() if v is not None and v != [] and v != "")
    total_fields = len(result)

    return {
        "status": "success",
        "schema": "invoice",
        "data": result,
        "confidence": confidence,
        "missing_fields": [k for k, v in result.items() if v is None or v == []],
        "metadata": {
            "total_fields": total_fields,
            "extracted_count": extracted_count,
            "extraction_rate": extracted_count / total_fields
        },
        "timestamp": datetime.now().isoformat()
    }
```

### Schema 2: Contact Information
```python
CONTACT_SCHEMA = {
    "name": "string",
    "email": "email",
    "phone": "phone",
    "company": "string",
    "address": "string"
}

def extract_contact_data(content: str, options: dict = None) -> dict:
    """Extract contact information from text."""

    import re
    from datetime import datetime

    result = {
        "name": None,
        "email": None,
        "phone": None,
        "company": None,
        "address": None
    }

    confidence = {}

    # Extract email
    emails = re.findall(r'[\w\.-]+@[\w\.-]+', content)
    if emails:
        result["email"] = emails[0]
        confidence["email"] = 0.98

    # Extract phone (multiple formats)
    phone_patterns = [
        r'\(\d{3}\)\s*\d{3}-\d{4}',
        r'\d{3}-\d{3}-\d{4}',
        r'\d{3}\.\d{3}\.\d{4}',
        r'\d{10}',
        r'\+\d{1,3}[\s-]?\d{3}[\s-]?\d{3}[\s-]?\d{4}'
    ]

    for pattern in phone_patterns:
        match = re.search(pattern, content)
        if match:
            result["phone"] = match.group(0)
            confidence["phone"] = 0.90
            break

    # Extract company name
    company_patterns = [
        r'company\s*:?\s*([^\n]+)',
        r'organization\s*:?\s*([^\n]+)',
        r'firm\s*:?\s*([^\n]+)'
    ]

    for pattern in company_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            result["company"] = match.group(1).strip()
            confidence["company"] = 0.85
            break

    # Extract address
    address_pattern = r'(?:address|location|addr)\s*:?\s*([^\n]+(?:\n[^\n]+){0,2})'
    match = re.search(address_pattern, content, re.IGNORECASE)
    if match:
        result["address"] = match.group(1).strip()
        confidence["address"] = 0.80

    # Extract name (often at beginning or before email)
    # Look for patterns like "Name: value" or "John Doe <email>"
    name_patterns = [
        r'name\s*:?\s*([^\n<]+)',
        r'from\s*:?\s*([^\n<]+)',
        r'^([A-Z][a-z]+\s+[A-Z][a-z]+)\s*<'
    ]

    for pattern in name_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
        if match:
            result["name"] = match.group(1).strip()
            confidence["name"] = 0.75
            break

    extracted_count = sum(1 for v in result.values() if v is not None)

    return {
        "status": "success",
        "schema": "contact",
        "data": result,
        "confidence": confidence,
        "missing_fields": [k for k, v in result.items() if v is None],
        "metadata": {
            "total_fields": len(result),
            "extracted_count": extracted_count,
            "extraction_rate": extracted_count / len(result)
        },
        "timestamp": datetime.now().isoformat()
    }
```

### Schema 3: Email Metadata
```python
EMAIL_SCHEMA = {
    "from": "email",
    "to": "email_list",
    "cc": "email_list",
    "subject": "string",
    "date": "date",
    "message_id": "string",
    "priority": "string"
}

def extract_email_metadata(content: str, options: dict = None) -> dict:
    """Extract metadata from email headers."""

    import re
    from datetime import datetime

    result = {
        "from": None,
        "to": [],
        "cc": [],
        "subject": None,
        "date": None,
        "message_id": None,
        "priority": None
    }

    confidence = {}

    # Extract from
    from_match = re.search(r'from\s*:?\s*([^\n]+)', content, re.IGNORECASE)
    if from_match:
        result["from"] = from_match.group(1).strip()
        confidence["from"] = 0.95

    # Extract to
    to_match = re.search(r'to\s*:?\s*([^\n]+)', content, re.IGNORECASE)
    if to_match:
        to_emails = re.findall(r'[\w\.-]+@[\w\.-]+', to_match.group(1))
        result["to"] = to_emails
        confidence["to"] = 0.95

    # Extract cc
    cc_match = re.search(r'cc\s*:?\s*([^\n]+)', content, re.IGNORECASE)
    if cc_match:
        cc_emails = re.findall(r'[\w\.-]+@[\w\.-]+', cc_match.group(1))
        result["cc"] = cc_emails
        confidence["cc"] = 0.95

    # Extract subject
    subject_match = re.search(r'subject\s*:?\s*([^\n]+)', content, re.IGNORECASE)
    if subject_match:
        result["subject"] = subject_match.group(1).strip()
        confidence["subject"] = 0.98

    # Extract date
    date_match = re.search(r'date\s*:?\s*([^\n]+)', content, re.IGNORECASE)
    if date_match:
        result["date"] = date_match.group(1).strip()
        confidence["date"] = 0.90

    # Extract priority
    priority_match = re.search(r'priority\s*:?\s*([^\n]+)', content, re.IGNORECASE)
    if priority_match:
        result["priority"] = priority_match.group(1).strip().lower()
        confidence["priority"] = 0.90

    # Extract message ID
    message_id_match = re.search(r'message-id\s*:?\s*([^\n]+)', content, re.IGNORECASE)
    if message_id_match:
        result["message_id"] = message_id_match.group(1).strip()
        confidence["message_id"] = 0.95

    extracted_count = sum(1 for v in result.values() if v is not None and v != [])

    return {
        "status": "success",
        "schema": "email",
        "data": result,
        "confidence": confidence,
        "missing_fields": [],
        "metadata": {
            "total_fields": len(result),
            "extracted_count": extracted_count,
            "extraction_rate": extracted_count / len(result)
        },
        "timestamp": datetime.now().isoformat()
    }
```

## Main Extraction Function

```python
from pathlib import Path
from datetime import datetime
import json

def extract_data(source_file: str, content: str, schema: dict, options: dict = None) -> dict:
    """Main entry point for data extraction."""

    if options is None:
        options = {
            "include_confidence": True,
            "strict_mode": False,
            "handle_missing": "skip"
        }

    # Determine schema type
    schema_type = options.get("schema_type", "auto")

    if schema_type == "invoice" or "invoice_number" in schema:
        result = extract_invoice_data(content, options)
    elif schema_type == "contact" or "email" in schema.values():
        result = extract_contact_data(content, options)
    elif schema_type == "email" or "subject" in schema:
        result = extract_email_metadata(content, options)
    else:
        # Generic extraction
        result = extract_generic_data(content, schema, options)

    # Save results to JSON file
    bronze_dir = Path(__file__).parent.parent
    logs_dir = bronze_dir / "Logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    output_file = logs_dir / f"extracted_{Path(source_file).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    dry_run = options.get("dry_run", True)

    if not dry_run:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
    else:
        print(f"[DRY RUN] Would save extraction to: {output_file}")

    return {
        **result,
        "output_file": str(output_file),
        "dry_run": dry_run
    }


def extract_generic_data(content: str, schema: dict, options: dict) -> dict:
    """Generic extraction based on provided schema."""

    import re
    result = {}
    confidence = {}

    for field, field_type in schema.items():
        value = None
        conf = 0.0

        if field_type == "email":
            match = re.search(r'[\w\.-]+@[\w\.-]+', content)
            if match:
                value = match.group(0)
                conf = 0.95

        elif field_type == "phone":
            match = re.search(r'\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}', content)
            if match:
                value = match.group(0)
                conf = 0.90

        elif field_type == "date":
            match = re.search(r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}', content)
            if match:
                value = match.group(0)
                conf = 0.90

        elif field_type == "currency":
            match = re.search(r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', content)
            if match:
                value = float(match.group(1).replace(',', ''))
                conf = 0.90

        elif field_type == "string":
            # Look for field name pattern
            pattern = rf'{field}\s*:?\s*([^\n]+)'
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                conf = 0.75

        elif field_type == "number":
            # Look for field name with numeric value
            pattern = rf'{field}\s*:?\s*(\d+(?:\.\d+)?)'
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                conf = 0.85

        result[field] = value
        if options.get("include_confidence", True):
            confidence[field] = conf

    extracted_count = sum(1 for v in result.values() if v is not None)

    return {
        "status": "success",
        "schema": "custom",
        "data": result,
        "confidence": confidence if options.get("include_confidence") else None,
        "missing_fields": [k for k, v in result.items() if v is None],
        "metadata": {
            "total_fields": len(schema),
            "extracted_count": extracted_count,
            "extraction_rate": extracted_count / len(schema)
        },
        "timestamp": datetime.now().isoformat()
    }
```

## Important Notes

1. **Always return structured JSON** for programmatic use
2. **Include confidence scores** for extracted fields
3. **Handle missing data** gracefully based on options
4. **Support multiple schemas** for different document types
5. **Save results to Logs/** for audit trail
6. **Use regex patterns** tailored to specific formats
7. **Check DRY_RUN flag** before writing output files
8. **Validate extracted data** when possible

## Integration Points

This skill integrates with:
- **file_processor**: Reads source files, saves extraction results
- **text_analyzer**: Determines document type and appropriate schema
- **task_planner**: Creates plans for complex extraction workflows
- **orchestrator**: Called when data extraction intent is detected

## Error Handling

```python
def safe_extract_data(source_file: str, content: str, schema: dict, options: dict = None) -> dict:
    """Extract data with comprehensive error handling."""

    try:
        if not content or not content.strip():
            return {
                "status": "error",
                "error": "Empty content provided",
                "source_file": source_file,
                "timestamp": datetime.now().isoformat()
            }

        if not schema:
            return {
                "status": "error",
                "error": "Extraction schema is required",
                "source_file": source_file,
                "timestamp": datetime.now().isoformat()
            }

        return extract_data(source_file, content, schema, options)

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "source_file": source_file,
            "timestamp": datetime.now().isoformat()
        }
```
