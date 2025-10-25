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

    console.log('clear 시트에서 차입금 확인 중...\n');

    const response = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: 'clear!A1:Z1000',
    });

    const rows = response.data.values || [];

    console.log('=== 차입금으로 분류된 거래 ===\n');

    for (let i = 1; i < rows.length; i++) {
      const row = rows[i];
      const accountType = row[8]; // 계정타입
      const category = row[7]; // 계정과목

      if (category && category.startsWith('차입금')) {
        const date = row[0];
        const type = row[1];
        const amount = row[2];
        const description = row[5];

        console.log(`[${type}] ${description}`);
        console.log(`   금액: ${amount}`);
        console.log(`   날짜: ${date}`);
        console.log(`   계정과목: ${category}`);
        console.log('');
      }
    }

    console.log('\n=== 송호빈 입금 내역 (모두) ===\n');

    for (let i = 1; i < rows.length; i++) {
      const row = rows[i];
      const type = row[1];
      const description = row[5];

      if (type === '입금' && description.includes('송호빈')) {
        const date = row[0];
        const amount = row[2];
        const category = row[7];

        console.log(`${description}: ${amount}원 (${date})`);
        console.log(`   계정과목: ${category}`);
        console.log('');
      }
    }

    console.log('\n=== 김선호 입금 내역 (모두) ===\n');

    for (let i = 1; i < rows.length; i++) {
      const row = rows[i];
      const type = row[1];
      const description = row[5];

      if (type === '입금' && description.includes('김선호')) {
        const date = row[0];
        const amount = row[2];
        const category = row[7];

        console.log(`${description}: ${amount}원 (${date})`);
        console.log(`   계정과목: ${category}`);
        console.log('');
      }
    }

  } catch (error) {
    console.error('오류:', error.message);
  }
}

main();
