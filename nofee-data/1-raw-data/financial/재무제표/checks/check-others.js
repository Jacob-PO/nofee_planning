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

    console.log('clear 시트에서 "기타" 계정타입 거래 확인 중...\n');

    const response = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: 'clear!A1:Z1000',
    });

    const rows = response.data.values || [];
    const headers = rows[0];

    console.log('헤더:', headers.join(' | '));
    console.log('\n=== 기타로 분류된 거래들 ===\n');

    let count = 0;
    for (let i = 1; i < rows.length; i++) {
      const row = rows[i];
      const accountType = row[8]; // 계정타입 열

      if (accountType && accountType !== '매출' && accountType !== '비용') {
        count++;
        const date = row[0];
        const type = row[1];
        const amount = row[2];
        const description = row[5];
        const category = row[7];

        console.log(`${count}. [${type}] ${description}`);
        console.log(`   금액: ${amount}, 날짜: ${date}`);
        console.log(`   계정과목: ${category}`);
        console.log(`   계정타입: ${accountType}`);
        console.log('');
      }
    }

    console.log(`\n총 ${count}건의 기타 거래 확인됨`);

  } catch (error) {
    console.error('오류:', error.message);
  }
}

main();
