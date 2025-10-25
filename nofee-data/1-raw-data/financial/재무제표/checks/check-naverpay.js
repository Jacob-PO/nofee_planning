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
      range: 'clear!A1:Z1000',
    });

    const rows = response.data.values || [];
    console.log('=== 네이버페이 거래 ===\n');
    
    for (let i = 1; i < rows.length; i++) {
      const desc = rows[i][5] || '';
      if (desc.includes('네이버페이')) {
        const date = rows[i][0];
        const amount = rows[i][2];
        const category = rows[i][7];
        console.log(`날짜: ${date}`);
        console.log(`금액: ${amount}원`);
        console.log(`설명: ${desc}`);
        console.log(`분류: ${category}\n`);
      }
    }

  } catch (error) {
    console.error('오류:', error.message);
  }
}

main();
