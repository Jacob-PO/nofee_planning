#!/usr/bin/env node
/**
 * 9,950,000원 김선호 거래를 찾아서 자본금 → 차입금으로 수정
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
    console.log('🔍 9,950,000원 김선호 거래 찾아서 수정\n');
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

    // 9,950,000원 김선호 거래 찾기
    let foundIndex = -1;
    for (let i = 1; i < rows.length; i++) {
      const 금액 = rows[i][2] || '';
      const 내용 = rows[i][5] || '';

      if ((금액.includes('9950000') || 금액.includes('9,950,000')) && 내용.includes('김선호')) {
        foundIndex = i;
        console.log(`\n✅ ${i}번 행에서 찾음!`);
        console.log(`   날짜: ${rows[i][0]}`);
        console.log(`   금액: ${rows[i][2]}`);
        console.log(`   내용: ${rows[i][5]}`);
        console.log(`   현재 계정과목: ${rows[i][7]}`);
        console.log(`   현재 계정타입: ${rows[i][8]}`);
        break;
      }
    }

    if (foundIndex === -1) {
      console.log('\n❌ 해당 거래를 찾을 수 없습니다.');
      return;
    }

    // 수정
    console.log('\n✏️  수정 중...');
    rows[foundIndex][7] = '차입금 - 김선호';
    rows[foundIndex][8] = '차입금';

    console.log(`   수정 후 계정과목: ${rows[foundIndex][7]}`);
    console.log(`   수정 후 계정타입: ${rows[foundIndex][8]}`);

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
