#!/usr/bin/env node
import { google } from 'googleapis';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * raw_data 시트 구조 분석
 */
async function main() {
  try {
    console.log('raw_data 시트 구조 분석 중...\n');

    // Google Service Account 인증
    const credentialsPath = path.resolve(__dirname, '../../../config/google_api_key.json');
    const credentials = JSON.parse(fs.readFileSync(credentialsPath, 'utf8'));

    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });

    const sheets = google.sheets({ version: 'v4', auth });
    const spreadsheetId = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';

    // raw_data 시트 데이터 가져오기
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: 'raw_data!A1:Z1000',
    });

    const rows = response.data.values || [];

    if (rows.length === 0) {
      console.log('데이터가 없습니다.');
      return;
    }

    // 헤더 분석
    console.log('='.repeat(80));
    console.log('헤더 (첫 번째 행):');
    console.log('='.repeat(80));
    const headers = rows[0];
    headers.forEach((header, index) => {
      console.log(`  [${index}] ${header}`);
    });

    // 샘플 데이터 출력 (처음 10개 행)
    console.log('\n' + '='.repeat(80));
    console.log('샘플 데이터 (처음 10개 거래):');
    console.log('='.repeat(80));

    for (let i = 1; i <= Math.min(10, rows.length - 1); i++) {
      const row = rows[i];
      console.log(`\n--- 행 ${i} ---`);
      headers.forEach((header, colIndex) => {
        if (row[colIndex]) {
          console.log(`  ${header}: ${row[colIndex]}`);
        }
      });
    }

    // 데이터 통계
    console.log('\n' + '='.repeat(80));
    console.log('데이터 통계:');
    console.log('='.repeat(80));
    console.log(`  총 행 수: ${rows.length - 1}개 (헤더 제외)`);

    // 고유값 분석 (거래 유형, 카테고리 등)
    const uniqueValues = {};
    headers.forEach((header, colIndex) => {
      const values = new Set();
      for (let i = 1; i < rows.length; i++) {
        if (rows[i][colIndex]) {
          values.add(rows[i][colIndex]);
        }
      }
      if (values.size > 0 && values.size < 50) { // 고유값이 50개 미만인 경우만 출력
        uniqueValues[header] = Array.from(values);
      }
    });

    console.log('\n고유값이 적은 컬럼 (카테고리성 데이터):');
    Object.entries(uniqueValues).forEach(([header, values]) => {
      console.log(`\n  ${header}: ${values.length}개`);
      values.slice(0, 10).forEach(value => {
        console.log(`    - ${value}`);
      });
      if (values.length > 10) {
        console.log(`    ... (외 ${values.length - 10}개)`);
      }
    });

    console.log('\n' + '='.repeat(80));

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
    process.exit(1);
  }
}

main();
