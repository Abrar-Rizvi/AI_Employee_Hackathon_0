#!/usr/bin/env node
/**
 * Gmail Authorization Script
 * Generates a token with send permission for the MCP server
 */

import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs/promises';
import readline from 'readline';
import { stdin as input, stdout as output } from 'process';

const __dirname = dirname(fileURLToPath(import.meta.url));

async function prompt(query) {
  const rl = readline.createInterface({ input, output });
  return new Promise(resolve => rl.question(query, ans => {
    rl.close();
    resolve(ans);
  }));
}

async function authorizeGmail() {
  console.log('\n=================================');
  console.log('🔐 Gmail Authorization for Email Sending');
  console.log('=================================\n');

  try {
    const { google } = await import('googleapis');
    const { OAuth2Client } = await import('google-auth-library');

    // Load credentials
    const credentialsPath = join(__dirname, '../../Config/gmail_credentials.json');
    const tokenPath = join(__dirname, '../../Config/gmail_token.json');

    console.log('Loading credentials from:', credentialsPath);
    const credentialsContent = await fs.readFile(credentialsPath, 'utf-8');
    const credentials = JSON.parse(credentialsContent);

    // Create OAuth2 client with scopes for SENDING emails
    const SCOPES = [
      'https://www.googleapis.com/auth/gmail.send'
    ];

    const oauth2Client = new OAuth2Client(
      credentials.installed.client_id,
      credentials.installed.client_secret,
      'urn:ietf:wg:oauth:2.0:oob',
      SCOPES
    );

    // Generate authorization URL
    const authUrl = oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: SCOPES,
      prompt: 'consent'
    });

    console.log('\n📋 Steps to authorize:\n');
    console.log('1. Copy this URL and open it in your browser:');
    console.log('\n' + authUrl + '\n');

    console.log('2. Sign in to your Google Account');
    console.log('3. Allow the permissions (Gmail API - Send emails)');
    console.log('4. Copy the authorization code\n');

    const code = await prompt('Enter the authorization code: ');

    if (!code) {
      console.log('\n❌ No code provided. Authorization cancelled.');
      process.exit(1);
    }

    console.log('\nExchanging authorization code for tokens...');

    const { tokens } = await oauth2Client.getToken(code);

    console.log('✅ Authorization successful!');
    console.log('\nToken details:');
    console.log(`  Access Token: ${tokens.access_token.substring(0, 20)}...`);
    console.log(`  Refresh Token: ${tokens.refresh_token ? tokens.refresh_token.substring(0, 20) + '...' : '(not provided)'}`);

    // Save token
    await fs.writeFile(tokenPath, JSON.stringify(tokens, null, 2));
    console.log('\n✅ Token saved to:', tokenPath);

    console.log('\n✅ You can now send emails via Gmail MCP Server!');
    console.log('\n=================================\n');

  } catch (error) {
    console.error('\n❌ Authorization failed:', error.message);
    console.error('\nMake sure gmail_credentials.json exists and is valid.\n');
    process.exit(1);
  }
}

authorizeGmail().catch(console.error);
