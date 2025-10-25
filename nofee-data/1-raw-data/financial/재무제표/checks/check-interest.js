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
    console.log('=== 영업외비용 - 이자비용 ===\n');
    
    for (let i = 1; i < rows.length; i++) {
      const category = rows[i][7] || '';
      if (category.includes('영업외비용') && category.includes('이자')) {
        const date = rows[i][0];
        const type = rows[i][1];
        const amount = rows[i][2];
        const desc = rows[i][5];
        console.log(`[${type}] ${desc}: ${amount}원 (${date})`);
      }
    }

  } catch (error) {
    console.error('오류:', error.message);
  }
}

main();
