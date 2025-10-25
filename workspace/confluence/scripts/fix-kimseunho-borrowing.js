#!/usr/bin/env node
/**
 * 김선호 995만원 자본금 → 차입금으로 수정
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
    console.log('🔧 김선호 995만원 자본금 → 차입금 수정\n');
    console.log('='.repeat(60));

    const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));
    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: ['https://www.googleapis.com/auth/spreadsheets']
    });

    const sheets = google.sheets({ version: 'v4', auth: await auth.getClient() });

    // clear 시트 58번 행(H58, I58) 수정
    // H58: 계정과목
    // I58: 계정타입

    console.log('\n📝 Clear 시트 58번 행 수정 중...');
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
    console.log('\n이제 v3와 v4를 다시 실행해주세요:');
    console.log('  1. node scripts/process-financial-data-v3.js');
    console.log('  2. node scripts/process-financial-data-v4.js');

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
    process.exit(1);
  }
}

main();
