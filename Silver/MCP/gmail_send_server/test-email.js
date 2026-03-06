#!/usr/bin/env node
/**
 * Direct test of email sending
 */

import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs/promises';

const __dirname = dirname(fileURLToPath(import.meta.url));

const CONFIG = {
  credentialsPath: join(__dirname, '../../Config/gmail_credentials.json'),
  tokenPath: join(__dirname, '../../Config/gmail_token.json'),
  dryRun: process.env.DRY_RUN !== 'false',
};

async function sendDirectEmail(to, subject, body) {
  console.log('\n=================================');
  console.log('📧 Sending Email via MCP Server');
  console.log('=================================\n');
  console.log(`To: ${to}`);
  console.log(`Subject: ${subject}`);
  console.log(`Body: ${body}`);
  console.log(`Mode: ${CONFIG.dryRun ? 'DRY RUN' : 'LIVE'}`);
  console.log('');

  if (CONFIG.dryRun) {
    console.log('✅ DRY RUN MODE - Email would be sent');
    console.log('   To send real emails, set DRY_RUN=false in MCP config or .env\n');
    return { success: true, dryRun: true };
  }

  try {
    const { google } = await import('googleapis');
    const { OAuth2Client } = await import('google-auth-library');

    // Load credentials
    const credentialsContent = await fs.readFile(CONFIG.credentialsPath, 'utf-8');
    const credentials = JSON.parse(credentialsContent);

    // Load token
    const tokenContent = await fs.readFile(CONFIG.tokenPath, 'utf-8');
    const token = JSON.parse(tokenContent);

    // Create OAuth2 client
    const oauth2Client = new OAuth2Client(
      credentials.installed.client_id,
      credentials.installed.client_secret
    );

    oauth2Client.setCredentials({
      access_token: token.access_token,
      refresh_token: token.refresh_token,
      expiry_date: token.expiry_date
    });

    // Initialize Gmail
    const gmail = google.gmail({ version: 'v1', auth: oauth2Client });

    // Create email
    const emailLines = [];
    emailLines.push(`To: ${to}`);
    emailLines.push(`Subject: ${subject}`);
    emailLines.push('');
    emailLines.push(body);

    const emailMessage = emailLines.join('\r\n');
    const encodedMessage = Buffer.from(emailMessage)
      .toString('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '');

    // Send
    console.log('Sending...');
    const response = await gmail.users.messages.send({
      userId: 'me',
      requestBody: { raw: encodedMessage }
    });

    console.log(`✅ SUCCESS! Email sent!`);
    console.log(`   Message ID: ${response.data.id}\n`);

    // Log to activity log
    const logsPath = join(__dirname, '../../Logs');
    await fs.mkdir(logsPath, { recursive: true });

    const today = new Date().toISOString().split('T')[0];
    const logFile = join(logsPath, `${today}.json`);

    let logs = [];
    try {
      const existingLogs = await fs.readFile(logFile, 'utf-8');
      logs = JSON.parse(existingLogs);
    } catch {}

    logs.push({
      timestamp: new Date().toISOString(),
      server: 'gmail_send_mcp',
      action: 'email_sent',
      dry_run: false,
      message_id: response.data.id,
      to,
      subject
    });

    await fs.writeFile(logFile, JSON.stringify(logs, null, 2));

    return { success: true, messageId: response.data.id };

  } catch (error) {
    console.log(`❌ ERROR: ${error.message}\n`);
    return { success: false, error: error.message };
  }
}

// Run test
const to = 'abrarrizvi1999@gmail.com';
const subject = 'MCP Test - Silver Tier Complete';
const body = 'This email was sent automatically by AI Employee MCP Server!';

sendDirectEmail(to, subject, body)
  .then(result => {
    if (result.success) {
      console.log('=================================');
      console.log('Test Complete!');
      console.log('=================================\n');
    }
    process.exit(result.success ? 0 : 1);
  })
  .catch(error => {
    console.error(error);
    process.exit(1);
  });
