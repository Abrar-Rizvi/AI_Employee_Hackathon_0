#!/usr/bin/env node
/**
 * Test script for Gmail Send MCP Server
 * Tests the send_email function directly
 */

import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs/promises';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Configuration
const CONFIG = {
  credentialsPath: join(__dirname, '../../Config/gmail_credentials.json'),
  tokenPath: join(__dirname, '../../Config/gmail_token.json'),
  logsPath: join(__dirname, '../../Logs'),
  dryRun: process.env.DRY_RUN !== 'false',
};

// Logging utility
async function logAction(action, details) {
  try {
    await fs.mkdir(CONFIG.logsPath, { recursive: true });

    const today = new Date().toISOString().split('T')[0];
    const logFile = join(CONFIG.logsPath, `${today}.json`);

    let logs = [];
    try {
      const existingLogs = await fs.readFile(logFile, 'utf-8');
      logs = JSON.parse(existingLogs);
    } catch {
      // File doesn't exist or is empty
    }

    const logEntry = {
      timestamp: new Date().toISOString(),
      server: 'gmail_send_mcp_test',
      action,
      dry_run: CONFIG.dryRun,
      ...details
    };

    logs.push(logEntry);
    await fs.writeFile(logFile, JSON.stringify(logs, null, 2));
  } catch (error) {
    console.error(`[ERROR] Failed to log: ${error.message}`);
  }
}

// Gmail API function
async function sendEmail(params) {
  const { to, subject, body, cc } = params;

  console.log('\n=================================');
  console.log('Gmail Send MCP Server - Test');
  console.log('=================================\n');

  console.log(`Mode: ${CONFIG.dryRun ? 'DRY RUN' : 'LIVE'}`);
  console.log(`To: ${to}`);
  console.log(`Subject: ${subject}`);
  console.log(`CC: ${cc || '(none)'}`);
  console.log(`Body: ${body.substring(0, 100)}...`);
  console.log('');

  const emailData = {
    to,
    subject,
    body,
    cc: cc || '',
    timestamp: new Date().toISOString()
  };

  if (CONFIG.dryRun) {
    console.log('✅ DRY RUN SUCCESS - Email would be sent\n');
    await logAction('test_email_dry_run', emailData);
    return { success: true, dry_run: true };
  }

  try {
    // Import googleapis
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

    // Set credentials
    oauth2Client.setCredentials({
      access_token: token.access_token,
      refresh_token: token.refresh_token,
      expiry_date: token.expiry_date
    });

    // Initialize Gmail
    const gmail = google.gmail({ version: 'v1', auth: oauth2Client });

    // Create email message
    const emailLines = [];
    emailLines.push(`To: ${to}`);
    if (cc) {
      emailLines.push(`Cc: ${cc}`);
    }
    emailLines.push(`Subject: ${subject}`);
    emailLines.push('');
    emailLines.push(body);

    const emailMessage = emailLines.join('\r\n');

    // Encode to base64url
    const encodedMessage = Buffer.from(emailMessage)
      .toString('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '');

    // Send email
    console.log('Sending email...');
    const response = await gmail.users.messages.send({
      userId: 'me',
      requestBody: {
        raw: encodedMessage
      }
    });

    console.log(`✅ SUCCESS - Email sent!`);
    console.log(`   Message ID: ${response.data.id}\n`);

    await logAction('test_email_sent', {
      success: true,
      message_id: response.data.id,
      to,
      subject
    });

    return { success: true, message_id: response.data.id };

  } catch (error) {
    console.log(`❌ ERROR - ${error.message}\n`);
    await logAction('test_email_error', {
      error: error.message,
      to,
      subject
    });
    return { success: false, error: error.message };
  }
}

// Run tests
async function runTests() {
  console.log('\n📧 Gmail Send MCP Server - Test Suite\n');

  // Test 1: Dry run test
  console.log('Test 1: Dry Run Email');
  console.log('-------------------------');
  const test1 = await sendEmail({
    to: 'test@example.com',
    subject: 'Test Email - DRY RUN',
    body: 'This is a test email in DRY RUN mode.\n\nNo email will be sent.',
    cc: 'cc@example.com'
  });

  // Test 2: Check credentials
  console.log('Test 2: Verify Credentials');
  console.log('-------------------------');
  try {
    await fs.access(CONFIG.credentialsPath);
    console.log('✅ Credentials file exists');
  } catch {
    console.log('❌ Credentials file missing');
  }

  try {
    await fs.access(CONFIG.tokenPath);
    console.log('✅ Token file exists');
  } catch {
    console.log('❌ Token file missing');
  }

  // Test 3: Logs directory
  console.log('\nTest 3: Verify Logs Directory');
  console.log('-------------------------');
  try {
    await fs.mkdir(CONFIG.logsPath, { recursive: true });
    console.log(`✅ Logs directory ready: ${CONFIG.logsPath}`);
  } catch {
    console.log('❌ Failed to create logs directory');
  }

  console.log('\n=================================');
  console.log('Tests Complete!');
  console.log('=================================\n');

  // Instructions
  console.log('📝 Next Steps:');
  console.log('   1. Install dependencies: cd /mnt/d/AI_Employee_Hackathon_0/Silver/MCP/gmail_send_server && npm install');
  console.log('   2. Test with DRY_RUN=false for real emails');
  console.log('   3. Restart Claude Code to load MCP server');
  console.log('   4. Use in Claude Code: "Send an email to..."');
  console.log('');
}

// Run tests
runTests().catch(console.error);
