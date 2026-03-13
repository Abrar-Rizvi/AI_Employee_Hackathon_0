#!/usr/bin/env node
/**
 * Gmail Send MCP Server
 *
 * Model Context Protocol server for sending emails via Gmail API.
 * Part of the Silver Tier AI Employee project.
 */

import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs/promises';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Create logs directory if it doesn't exist
const logsDir = join(__dirname, '../../Logs');

// Configuration
const CONFIG = {
  credentialsPath: join(__dirname, '../../Config/gmail_credentials.json'),
  tokenPath: join(__dirname, '../../Config/gmail_token.json'),
  logsPath: logsDir,
  dryRun: process.env.DRY_RUN !== 'false', // Default to true
};

// Logging utility
async function logAction(action, details) {
  try {
    await fs.mkdir(logsDir, { recursive: true });

    const today = new Date().toISOString().split('T')[0];
    const logFile = join(logsDir, `${today}.json`);

    let logs = [];
    try {
      const existingLogs = await fs.readFile(logFile, 'utf-8');
      logs = JSON.parse(existingLogs);
    } catch {
      // File doesn't exist or is empty, start with empty array
    }

    const logEntry = {
      timestamp: new Date().toISOString(),
      server: 'gmail_send_mcp',
      action,
      dry_run: CONFIG.dryRun,
      ...details
    };

    logs.push(logEntry);
    await fs.writeFile(logFile, JSON.stringify(logs, null, 2));

    console.error(`[LOG] ${action}: ${JSON.stringify(details)}`);
  } catch (error) {
    console.error(`[ERROR] Failed to log action: ${error.message}`);
  }
}

// Gmail API using googleapis
let gmail;
let credentials;
let token;

async function initializeGmail() {
  try {
    // Dynamic import for googleapis
    const { google } = await import('googleapis');
    const { OAuth2Client } = await import('google-auth-library');

    // Load credentials
    const credentialsContent = await fs.readFile(CONFIG.credentialsPath, 'utf-8');
    credentials = JSON.parse(credentialsContent);

    // Load token
    const tokenContent = await fs.readFile(CONFIG.tokenPath, 'utf-8');
    token = JSON.parse(tokenContent);

    // Create OAuth2 client
    const oauth2Client = new OAuth2Client(
      credentials.installed.client_id,
      credentials.installed.client_secret
    );

    // Set credentials
    oauth2Client.setCredentials({
      access_token: token.access_token,
      refresh_token: token.refresh_token,
      expiry_date: token.expiry_date
    });

    // Initialize Gmail
    gmail = google.gmail({ version: 'v1', auth: oauth2Client });

    console.error('[INFO] Gmail API initialized successfully');
    await logAction('gmail_initialized', { success: true });

    return oauth2Client;
  } catch (error) {
    console.error(`[ERROR] Failed to initialize Gmail: ${error.message}`);
    await logAction('gmail_init_error', { error: error.message });
    throw error;
  }
}

async function refreshAccessToken(oauth2Client) {
  try {
    const { credentials } = await import('google-auth-library');

    await oauth2Client.refreshAccessToken();
    const newTokens = oauth2Client.credentials;

    // Save updated token
    await fs.writeFile(
      CONFIG.tokenPath,
      JSON.stringify(newTokens, null, 2)
    );

    await logAction('token_refreshed', { success: true });
    return true;
  } catch (error) {
    console.error(`[ERROR] Failed to refresh token: ${error.message}`);
    await logAction('token_refresh_error', { error: error.message });
    return false;
  }
}

// Send email function
async function sendEmail(params) {
  const { to, subject, body, cc } = params;

  const emailData = {
    to,
    subject,
    body,
    cc: cc || '',
    timestamp: new Date().toISOString()
  };

  console.error(`[INFO] Sending email to: ${to}`);

  try {
    if (CONFIG.dryRun) {
      console.error(`[DRY RUN] Would send email:`);
      console.error(`[DRY RUN]   To: ${to}`);
      console.error(`[DRY RUN]   Subject: ${subject}`);
      console.error(`[DRY RUN]   CC: ${cc || '(none)'}`);
      console.error(`[DRY RUN]   Body: ${body.substring(0, 100)}...`);

      await logAction('email_send_dry_run', emailData);

      return {
        success: true,
        dry_run: true,
        message: 'DRY RUN: Email would be sent',
        data: emailData
      };
    }

    // Initialize Gmail if not already done
    if (!gmail) {
      const oauth2Client = await initializeGmail();
      gmail.oauth2Client = oauth2Client;
    }

    // Create email message
    const emailLines = [];
    emailLines.push(`To: ${to}`);
    if (cc) {
      emailLines.push(`Cc: ${cc}`);
    }
    emailLines.push(`Subject: ${subject}`);
    emailLines.push(''); // Blank line between headers and body
    emailLines.push(body);

    const emailMessage = emailLines.join('\r\n');

    // Encode to base64url
    const encodedMessage = Buffer.from(emailMessage)
      .toString('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '');

    // Send email
    const response = await gmail.users.messages.send({
      userId: 'me',
      requestBody: {
        raw: encodedMessage
      }
    });

    console.error(`[INFO] Email sent successfully. ID: ${response.data.id}`);
    await logAction('email_sent', {
      success: true,
      message_id: response.data.id,
      to,
      subject
    });

    return {
      success: true,
      message_id: response.data.id,
      data: emailData
    };

  } catch (error) {
    console.error(`[ERROR] Failed to send email: ${error.message}`);

    // Try to refresh token if it's an auth error
    if (error.message.includes('invalid') || error.message.includes('401') || error.message.includes('auth')) {
      console.error('[INFO] Attempting to refresh access token...');
      if (gmail.oauth2Client) {
        const refreshed = await refreshAccessToken(gmail.oauth2Client);
        if (refreshed) {
          // Retry sending email
          try {
            const emailLines = [];
            emailLines.push(`To: ${to}`);
            if (cc) {
              emailLines.push(`Cc: ${cc}`);
            }
            emailLines.push(`Subject: ${subject}`);
            emailLines.push('');
            emailLines.push(body);

            const emailMessage = emailLines.join('\r\n');
            const encodedMessage = Buffer.from(emailMessage)
              .toString('base64')
              .replace(/\+/g, '-')
              .replace(/\//g, '_')
              .replace(/=+$/, '');

            const response = await gmail.users.messages.send({
              userId: 'me',
              requestBody: {
                raw: encodedMessage
              }
            });

            console.error(`[INFO] Email sent successfully after token refresh. ID: ${response.data.id}`);
            await logAction('email_sent_after_refresh', {
              success: true,
              message_id: response.data.id,
              to,
              subject
            });

            return {
              success: true,
              message_id: response.data.id,
              data: emailData
            };
          } catch (retryError) {
            console.error(`[ERROR] Retry also failed: ${retryError.message}`);
            await logAction('email_send_error', {
              error: retryError.message,
              to,
              subject
            });
            return {
              success: false,
              error: retryError.message,
              data: emailData
            };
          }
        }
      }
    }

    await logAction('email_send_error', {
      error: error.message,
      to,
      subject
    });

    return {
      success: false,
      error: error.message,
      data: emailData
    };
  }
}

// MCP Server setup
async function main() {
  console.error('[INFO] Starting Gmail Send MCP Server...');

  // Check if DRY_RUN is set
  if (CONFIG.dryRun) {
    console.error('[INFO] DRY_RUN mode enabled - no emails will be sent');
  }

  try {
    // Import MCP SDK dynamically
    const { Server } = await import('@modelcontextprotocol/sdk/server/index.js');
    const { StdioServerTransport } = await import('@modelcontextprotocol/sdk/server/stdio.js');
    const {
      CallToolRequestSchema,
      ListToolsRequestSchema,
    } = await import('@modelcontextprotocol/sdk/types.js');

    // Create MCP server
    const server = new Server(
      {
        name: 'gmail-send-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    // List available tools
    server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'send_email',
            description: 'Send an email using Gmail API',
            inputSchema: {
              type: 'object',
              properties: {
                to: {
                  type: 'string',
                  description: 'Recipient email address'
                },
                subject: {
                  type: 'string',
                  description: 'Email subject line'
                },
                body: {
                  type: 'string',
                  description: 'Email body content (plain text or HTML)'
                },
                cc: {
                  type: 'string',
                  description: 'Optional CC recipients (comma-separated)'
                }
              },
              required: ['to', 'subject', 'body']
            }
          }
        ]
      };
    });

    // Handle tool calls
    server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      if (name === 'send_email') {
        const result = await sendEmail(args);

        if (result.success) {
          return {
            content: [
              {
                type: 'text',
                text: result.dry_run
                  ? `DRY RUN: Email would be sent to ${args.to}\n\nSubject: ${args.subject}\n\n${args.body.substring(0, 200)}...`
                  : `Email sent successfully!\n\nMessage ID: ${result.message_id}\nTo: ${args.to}\nSubject: ${args.subject}`
              }
            ]
          };
        } else {
          return {
            content: [
              {
                type: 'text',
                text: `Failed to send email: ${result.error}`
              }
            ],
            isError: true
          };
        }
      }

      return {
        content: [
          {
            type: 'text',
            text: `Unknown tool: ${name}`
          }
        ],
        isError: true
      };
    });

    // Start server
    const transport = new StdioServerTransport();
    console.error('[INFO] Gmail Send MCP Server running on stdio');
    await server.connect(transport);

  } catch (error) {
    console.error(`[FATAL] Failed to start server: ${error.message}`);
    console.error(error);
    process.exit(1);
  }
}

// Start the server
main().catch((error) => {
  console.error(`[FATAL] Unhandled error: ${error}`);
  process.exit(1);
});
