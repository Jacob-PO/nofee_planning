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

    console.log('=== 1천만원 출금 거래 ===\n');
    for (let i = 1; i < rows.length; i++) {
      const amount = parseFloat(rows[i][2]);
      if (rows[i][1] === '출금' && Math.abs(amount) === 10000000) {
        console.log(`날짜: ${rows[i][0]}`);
        console.log(`내용: ${rows[i][5]}`);
        console.log(`금액: ${amount.toLocaleString()}원`);
        console.log(`계정과목: ${rows[i][7]}`);
        console.log('');
      }
    }

  } catch (error) {
    console.error('오류:', error.message);
  }
}

main();
