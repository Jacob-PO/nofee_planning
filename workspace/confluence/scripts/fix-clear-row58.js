#!/usr/bin/env node
/**
 * Clear 시트 58번 행 직접 수정: 자본금 → 차입금
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
    console.log('🔧 Clear 시트 58번 행 수정: 자본금 → 차입금\n');
    console.log('='.repeat(60));

    const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));
    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: ['https://www.googleapis.com/auth/spreadsheets']
    });

    const sheets = google.sheets({ version: 'v4', auth: await auth.getClient() });

    console.log('\n📝 수정 중...');
    console.log('   H58: 자본금 - 김선호 → 차입금 - 김선호');
    console.log('   I58: 자본거래 → 차입금\n');

    await sheets.spreadsheets.values.update({
      spreadsheetId: SPREADSHEET_ID,
      range: 'clear!H58:I58',
      valueInputOption: 'RAW',
      resource: {
        values: [['차입금 - 김선호', '차입금']]
      }
    });

    console.log('✅ 수정 완료!\n');
    console.log('='.repeat(60));

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
    process.exit(1);
  }
}

main();
