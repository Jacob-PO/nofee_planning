#!/usr/bin/env node
import { google } from 'googleapis';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function main() {
  try {
    const credentialsPath = path.resolve(__dirname, '../../../config/google_api_key.json');
    const credentials = JSON.parse(fs.readFileSync(credentialsPath, 'utf8'));

    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });

    const sheets = google.sheets({ version: 'v4', auth });
    const spreadsheetId = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';

    const response = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: 'raw_data!A1:Z1000',
    });

    const rows = response.data.values || [];
    console.log('=== 사무실/계약금 관련 거래 ===\n');
    
    for (let i = 1; i < rows.length; i++) {
      const desc = rows[i][5] || '';
      if (desc.includes('사무실') || desc.includes('계약금')) {
        console.log(`[${rows[i][1]}] ${rows[i][2]} - ${desc} (${rows[i][0]})`);
      }
    }

  } catch (error) {
    console.error('오류:', error.message);
  }
}

main();
