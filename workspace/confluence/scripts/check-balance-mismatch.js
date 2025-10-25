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

  // 1. Clear 시트 최종 잔액
  console.log('=== Clear 시트 최종 잔액 ===\n');
  const clearResult = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'clear!A:D'
  });

  const clearRows = clearResult.data.values || [];
  const lastClear = clearRows[clearRows.length - 1];
  const clear최종잔액 = parseFloat(lastClear[3]?.replace(/,/g, '') || 0);

  console.log(`마지막 거래: ${lastClear[0]}`);
  console.log(`거래 후 잔액: ${clear최종잔액.toLocaleString()}원\n`);

  // 2. Summary 시트 잔액
  console.log('=== Summary 시트 잔액 ===\n');
  const summaryResult = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'summary!A:B'
  });

  const summaryRows = summaryResult.data.values || [];

  let 현금및현금성자산 = 0;
  let 기말현금 = 0;

  summaryRows.forEach((row, idx) => {
    if (row[0]?.includes('현금및현금성자산')) {
      현금및현금성자산 = parseFloat(row[1]?.replace(/,/g, '') || 0);
      console.log(`현금및현금성자산 (재무상태표): ${현금및현금성자산.toLocaleString()}원`);
    }
    if (row[0]?.includes('기말 현금') || row[0]?.includes('기말현금')) {
      기말현금 = parseFloat(row[1]?.replace(/,/g, '') || 0);
      console.log(`기말 현금 (현금흐름표): ${기말현금.toLocaleString()}원`);
    }
  });

  console.log();
  console.log('=== 검증 ===\n');
  console.log(`Clear 최종잔액:        ${clear최종잔액.toLocaleString()}원`);
  console.log(`Summary 현금자산:      ${현금및현금성자산.toLocaleString()}원`);
  console.log(`Summary 기말현금:      ${기말현금.toLocaleString()}원`);
  console.log();

  if (clear최종잔액 === 현금및현금성자산 && 현금및현금성자산 === 기말현금) {
    console.log('✅ 모든 잔액이 일치합니다!');
  } else {
    console.log('❌ 잔액 불일치!');
    if (clear최종잔액 !== 현금및현금성자산) {
      console.log(`   Clear vs 재무상태표 차이: ${(clear최종잔액 - 현금및현금성자산).toLocaleString()}원`);
    }
    if (clear최종잔액 !== 기말현금) {
      console.log(`   Clear vs 현금흐름표 차이: ${(clear최종잔액 - 기말현금).toLocaleString()}원`);
    }
  }
}

main();
