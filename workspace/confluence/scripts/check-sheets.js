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

  const response = await sheets.spreadsheets.get({
    spreadsheetId: SPREADSHEET_ID
  });

  console.log('=== 스프레드시트 정보 ===\n');
  console.log('제목:', response.data.properties.title);
  console.log();

  console.log('=== 시트 목록 ===\n');
  response.data.sheets.forEach(sheet => {
    console.log(`이름: ${sheet.properties.title}`);
    console.log(`ID: ${sheet.properties.sheetId}`);
    console.log(`색인: ${sheet.properties.index}`);
    console.log();
  });
}

main();
