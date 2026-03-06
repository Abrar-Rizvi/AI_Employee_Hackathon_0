#!/usr/bin/env node
/**
 * Automated Gmail Authorization with Send Permission
 * Opens browser and automatically handles OAuth flow
 */

import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs/promises';
import http from 'http';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);
const __dirname = dirname(fileURLToPath(import.meta.url));

async function setupGmailSend() {
  console.log('\n=================================');
  console.log('🔐 Gmail Send Authorization');
  console.log('=================================\n');

  try {
    const { google } = await import('googleapis');
    const { OAuth2Client } = await import('google-auth-library');

    const credentialsPath = join(__dirname, '../../Config/gmail_credentials.json');
    const tokenPath = join(__dirname, '../../Config/gmail_token.json');

    console.log('Loading credentials...');
    const credentialsContent = await fs.readFile(credentialsPath, 'utf-8');
    const credentials = JSON.parse(credentialsContent);

    // Scopes for SENDING emails (we need gmail.send)
    const SCOPES = ['https://www.googleapis.com/auth/gmail.send'];

    const oauth2Client = new OAuth2Client(
      credentials.installed.client_id,
      credentials.installed.client_secret,
      'http://localhost:3000/oauth2callback',
      SCOPES
    );

    // Create a simple HTTP server to handle the callback
    const server = http.createServer((req, res) => {
      if (req.url.startsWith('/oauth2callback')) {
        const url = new URL(req.url, 'http://localhost:3000');
        const code = url.searchParams.get('code');

        if (code) {
          res.writeHead(200, { 'Content-Type': 'text/html' });
          res.end(`
            <html>
            <head><title>Authorization Success</title></head>
            <body>
              <h1>✅ Authorization Successful!</h1>
              <p>You can close this window and return to the terminal.</p>
            </body>
            </html>
          `);

          // Exchange code for tokens
          oauth2Client.getToken(code).then(({ tokens }) => {
            console.log('\n✅ Authorization successful!');
            console.log('Saving token...');

            fs.writeFile(tokenPath, JSON.stringify(tokens, null, 2))
              .then(() => {
                console.log('✅ Token saved!');
                console.log('\nYou can now send emails via Gmail MCP Server!\n');
                server.close();
                process.exit(0);
              });
          }).catch(err => {
            console.error('\n❌ Error exchanging token:', err.message);
            server.close();
            process.exit(1);
          });
        } else {
          res.writeHead(400);
          res.end('Authorization code not found');
        }
      }
    });

    // Start server
    server.listen(3000, () => {
      console.log('Local OAuth server running on http://localhost:3000\n');
    });

    // Generate auth URL
    const authUrl = oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: SCOPES,
      prompt: 'consent'
    });

    console.log('Opening browser for authorization...\n');

    // Open browser
    try {
      const opener = process.platform === 'win32' ? 'start' :
                     process.platform === 'darwin' ? 'open' : 'xdg-open';
      await execAsync(`${opener} "${authUrl}"`);
      console.log('✅ Browser opened!');
      console.log('\nWaiting for authorization...\n');
    } catch (err) {
      console.log('\nCould not open browser automatically.');
      console.log('Please open this URL manually:\n');
      console.log(authUrl + '\n');
    }

  } catch (error) {
    console.error('\n❌ Error:', error.message);
    process.exit(1);
  }
}

setupGmailSend().catch(console.error);
