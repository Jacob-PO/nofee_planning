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
    range: 'summary!A1:F30'
  });

  const rows = result.data.values || [];
  console.log('=== Summary 시트 현재 상태 (처음 30줄) ===\n');
  rows.forEach((row, idx) => {
    const line = `[${(idx+1).toString().padStart(2)}] `;
    const cols = [];
    for (let i = 0; i < 6; i++) {
      const val = (row[i] || '').toString().substring(0, 15);
      cols.push(val.padEnd(15));
    }
    console.log(line + cols.join(' | '));
  });
}

main();
