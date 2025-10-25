#!/usr/bin/env node
/**
 * Clear 시트 전체를 읽어서 58번 행만 수정 후 다시 쓰기
 */

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
  try {
    console.log('🔧 Clear 시트 58번 행 수정 (전체 읽기/쓰기)\n');
    console.log('='.repeat(60));

    const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));
    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: ['https://www.googleapis.com/auth/spreadsheets']
    });

    const sheets = google.sheets({ version: 'v4', auth: await auth.getClient() });

    console.log('\n📖 Clear 시트 전체 읽기...');
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: SPREADSHEET_ID,
      range: 'clear!A:I'
    });

    const rows = response.data.values;
    console.log(`   총 ${rows.length}개 행 읽음`);

    // 58번 행 수정 (인덱스 58)
    console.log('\n✏️  58번 행 수정...');
    console.log(`   수정 전: ${rows[58][7]} | ${rows[58][8]}`);

    rows[58][7] = '차입금 - 김선호';  // H열: 계정과목
    rows[58][8] = '차입금';           // I열: 계정타입

    console.log(`   수정 후: ${rows[58][7]} | ${rows[58][8]}`);

    console.log('\n💾 Clear 시트 전체 쓰기...');
    await sheets.spreadsheets.values.update({
      spreadsheetId: SPREADSHEET_ID,
      range: 'clear!A:I',
      valueInputOption: 'RAW',
      resource: {
        values: rows
      }
    });

    console.log('\n✅ 수정 완료!\n');
    console.log('='.repeat(60));

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
    process.exit(1);
  }
}

main();
