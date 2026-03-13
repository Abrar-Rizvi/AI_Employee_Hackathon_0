# Gmail Send MCP Server

Model Context Protocol (MCP) server for sending emails via Gmail API. Part of the Silver Tier AI Employee project.

## Features

- ✅ Send emails via Gmail API using MCP protocol
- ✅ Integrates with Claude Code for AI-driven email sending
- ✅ Dry-run mode for testing without sending
- ✅ Automatic token refresh on authentication errors
- ✅ JSON logging to Silver tier Logs folder
- ✅ Human-in-the-loop support (via DRY_RUN mode)

## Installation

### 1. Install Dependencies

```bash
cd /mnt/d/AI_Employee_Hackathon_0/Silver/MCP/gmail_send_server
npm install
```

### 2. Verify Gmail Credentials

Ensure your Gmail credentials exist:

```bash
ls -la /mnt/d/AI_Employee_Hackathon_0/Silver/Config/gmail_credentials.json
ls -la /mnt/d/AI_Employee_Hackathon_0/Silver/Config/gmail_token.json
```

If not, follow the Gmail API setup instructions.

## Configuration

### Environment Variables

Set in `/mnt/d/AI_Employee_Hackathon_0/Silver/.env`:

```bash
# Dry Run Mode (set to 'false' for actual email sending)
DRY_RUN=true
```

## Usage

### With Claude Code

The MCP server is registered in Claude Code's config and can be used directly:

```
Send an email to john@example.com with subject "Project Update" and body "The project is progressing well."
```

### Standalone Testing

```bash
# Start the server (listens on stdio)
npm start

# Run with dry-run mode
DRY_RUN=true npm start
```

## MCP Tool

### `send_email`

Send an email using Gmail API.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `to` | string | Yes | Recipient email address |
| `subject` | string | Yes | Email subject line |
| `body` | string | Yes | Email body content |
| `cc` | string | No | CC recipients (comma-separated) |

**Returns:**

- **Success**: Message ID and confirmation
- **Dry Run**: Confirmation with `(DRY RUN)` prefix
- **Error**: Error message

**Example Usage in Claude Code:**

```
Send an email to client@example.com
Subject: Invoice #1234
Body: Dear Client,

Please find attached invoice #1234 for $1,500.

Payment is due within 15 days.

Best regards
```

## Logging

All actions are logged to `/mnt/d/AI_Employee_Hackathon_0/Silver/Logs/YYYY-MM-DD.json`:

```json
{
  "timestamp": "2026-03-04T10:30:00.000Z",
  "server": "gmail_send_mcp",
  "action": "email_sent",
  "dry_run": false,
  "message_id": "1234567890abcdef",
  "to": "client@example.com",
  "subject": "Invoice #1234"
}
```

## Gmail API Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API

### 2. Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Create **OAuth 2.0 Client ID**
3. Application type: **Desktop app**
4. Download credentials JSON

### 3. Save Credentials

```bash
# Save to config directory
mv ~/Downloads/client_secret_*.json /mnt/d/AI_Employee_Hackathon_0/Silver/Config/gmail_credentials.json
```

### 4. Generate Access Token

The first time you use a Gmail watcher, it will prompt you to authorize. Save the token to:
`/mnt/d/AI_Employee_Hackathon_0/Silver/Config/gmail_token.json`

## Security

- ✅ Credentials stored locally in Config folder
- ✅ Tokens auto-refresh on expiry
- ✅ Dry-run mode for safe testing
- ✅ All actions logged for audit
- ✅ No credentials in source code

## Troubleshooting

### "Credentials not found"

Ensure both files exist:
- `/mnt/d/AI_Employee_Hackathon_0/Silver/Config/gmail_credentials.json`
- `/mnt/d/AI_Employee_Hackathon_0/Silver/Config/gmail_token.json`

### "401 Invalid Credentials"

The access token has expired. The server will automatically attempt to refresh it.

### "DRY_RUN mode blocking sends"

Set `DRY_RUN=false` in `.env`:
```bash
echo "DRY_RUN=false" >> /mnt/d/AI_Employee_Hackathon_0/Silver/.env
```

### "Email not sending"

Check the logs:
```bash
tail -f /mnt/d/AI_Employee_Hackathon_0/Silver/Logs/$(date +%Y-%m-%d).json
```

## Architecture

```
Claude Code
    ↓
MCP Server (stdio)
    ↓
Gmail API (googleapis)
    ↓
Gmail Service
```

## Dependencies

- `@modelcontextprotocol/sdk` - MCP protocol implementation
- `google-auth-library` - OAuth2 authentication
- `googleapis` - Gmail API client

## Version

1.0.0 - Initial release for Silver Tier AI Employee

## License

MIT

## Support

For issues or questions, check the Silver Tier documentation or project README.
