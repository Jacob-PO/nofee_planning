#!/usr/bin/env node
import { google } from 'googleapis';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const SPREADSHEET_ID = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';
const CREDENTIALS_PATH = path.resolve(__dirname, '../../../config/google_api_key.json');

async function main() {
  const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));
  const auth = new google.auth.GoogleAuth({
    credentials,
    scopes: ['https://www.googleapis.com/auth/spreadsheets']
  });

  const sheets = google.sheets({ version: 'v4', auth });

  const result = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'clear!A:I'
  });

  const rows = result.data.values || [];

  console.log('=== 보증금 거래 찾기 ===\n');
  for (let i = 1; i < rows.length; i++) {
    const row = rows[i];
    const 계정 = row[7];
    const 타입 = row[8];

    if (계정?.includes('보증금') || 타입?.includes('보증금')) {
      console.log(`[${i}] ${row[0]} | ${row[2]?.padStart(12)} | ${row[5]} | ${계정} | ${타입}`);
    }
  }

  console.log('\n=== 영업외수익 거래 찾기 ===\n');
  for (let i = 1; i < rows.length; i++) {
    const row = rows[i];
    const 타입 = row[8];

    if (타입?.includes('영업외')) {
      console.log(`[${i}] ${row[0]} | ${row[2]?.padStart(12)} | ${row[5]} | ${row[7]} | ${타입}`);
    }
  }
}

main();
