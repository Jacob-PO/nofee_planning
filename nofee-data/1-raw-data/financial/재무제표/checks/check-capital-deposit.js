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

    console.log('=== 자본금 입금 ===\n');
    let totalCapitalIn = 0;
    for (let i = 1; i < rows.length; i++) {
      const category = rows[i][7];
      if (category && category.startsWith('자본금')) {
        const amount = parseFloat(rows[i][2]);
        totalCapitalIn += amount;
        console.log(`${rows[i][5]}: ${amount.toLocaleString()}원`);
      }
    }
    console.log(`\n자본금 입금 합계: ${totalCapitalIn.toLocaleString()}원\n`);

    console.log('=== 자본인출 ===\n');
    let totalCapitalOut = 0;
    for (let i = 1; i < rows.length; i++) {
      const category = rows[i][7];
      if (category && category.startsWith('자본인출')) {
        const amount = parseFloat(rows[i][2]);
        totalCapitalOut += Math.abs(amount);
        console.log(`${rows[i][5]}: ${amount.toLocaleString()}원`);
      }
    }
    console.log(`\n자본인출 합계: ${totalCapitalOut.toLocaleString()}원\n`);

    console.log(`순자본금: ${(totalCapitalIn - totalCapitalOut).toLocaleString()}원\n`);

    console.log('=== 보증금 ===\n');
    let totalDeposit = 0;
    for (let i = 1; i < rows.length; i++) {
      const category = rows[i][7];
      if (category && category.startsWith('보증금 -')) {
        const amount = parseFloat(rows[i][2]);
        totalDeposit += Math.abs(amount);
        console.log(`${rows[i][5]}: ${amount.toLocaleString()}원`);
      }
    }
    console.log(`\n보증금 합계: ${totalDeposit.toLocaleString()}원\n`);

    console.log('=== 보증금반환 ===\n');
    let totalDepositReturn = 0;
    for (let i = 1; i < rows.length; i++) {
      const category = rows[i][7];
      if (category && category.startsWith('보증금반환')) {
        const amount = parseFloat(rows[i][2]);
        totalDepositReturn += Math.abs(amount);
        console.log(`${rows[i][5]}: ${amount.toLocaleString()}원`);
      }
    }
    console.log(`\n보증금반환 합계: ${totalDepositReturn.toLocaleString()}원\n`);

  } catch (error) {
    console.error('오류:', error.message);
  }
}

main();
