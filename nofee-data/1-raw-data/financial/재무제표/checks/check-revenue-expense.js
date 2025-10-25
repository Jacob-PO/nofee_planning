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

    let totalRevenue = 0;
    let totalExpenses = 0;

    for (let i = 1; i < rows.length; i++) {
      const accountType = rows[i][8]; // 계정타입
      const amount = parseFloat(rows[i][2]);

      if (accountType === '매출') {
        totalRevenue += amount;
      } else if (accountType === '비용') {
        totalExpenses += Math.abs(amount);
      }
    }

    console.log('총 매출:', totalRevenue.toLocaleString());
    console.log('총 비용:', totalExpenses.toLocaleString());
    console.log('영업이익:', (totalRevenue - totalExpenses).toLocaleString());

  } catch (error) {
    console.error('오류:', error.message);
  }
}

main();
