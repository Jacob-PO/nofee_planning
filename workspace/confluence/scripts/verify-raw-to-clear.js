#!/usr/bin/env node
/**
 * raw_data → clear 변환 100% 검증
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
  console.log('🔍 raw_data → clear 변환 검증 시작\n');
  console.log('='.repeat(80));
  console.log();

  const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));
  const auth = new google.auth.GoogleAuth({
    credentials,
    scopes: ['https://www.googleapis.com/auth/spreadsheets']
  });

  const sheets = google.sheets({ version: 'v4', auth });

  // raw_data 읽기
  console.log('📊 raw_data 시트 읽는 중...');
  const rawResult = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'raw_data!A:G'
  });
  const rawRows = rawResult.data.values || [];
  const rawData = rawRows.slice(1).filter(row => row[0]);
  console.log(`   총 ${rawData.length}개 거래\n`);

  // clear 읽기
  console.log('📊 clear 시트 읽는 중...');
  const clearResult = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'clear!A:I'
  });
  const clearRows = clearResult.data.values || [];
  const clearData = clearRows.slice(1).filter(row => row[0]);
  console.log(`   총 ${clearData.length}개 거래\n`);

  console.log('='.repeat(80));
  console.log();

  // ========================================
  // 1. 행 수 비교
  // ========================================
  console.log('[ 1. 행 수 비교 ]');
  console.log(`  raw_data:  ${rawData.length}개`);
  console.log(`  clear:     ${clearData.length}개`);
  console.log(`  차이:      ${clearData.length - rawData.length}개`);

  if (rawData.length === clearData.length) {
    console.log('  ✅ 행 수 일치\n');
  } else {
    console.log('  ⚠️  행 수 불일치 - 추가/삭제된 거래 확인 필요\n');
  }

  // ========================================
  // 2. 기초/최종 잔액 비교
  // ========================================
  console.log('[ 2. 잔액 비교 ]');

  const raw기초잔액 = parseFloat(rawRows[1][3]?.replace(/,/g, '') || 0) - parseFloat(rawRows[1][2]?.replace(/,/g, '') || 0);
  const raw최종잔액 = parseFloat(rawData[rawData.length - 1][3]?.replace(/,/g, '') || 0);

  const clear기초잔액 = parseFloat(clearRows[1][3]?.replace(/,/g, '') || 0) - parseFloat(clearRows[1][2]?.replace(/,/g, '') || 0);
  const clear최종잔액 = parseFloat(clearData[clearData.length - 1][3]?.replace(/,/g, '') || 0);

  console.log('  기초 잔액:');
  console.log(`    raw_data:  ${raw기초잔액.toLocaleString().padStart(12)}`);
  console.log(`    clear:     ${clear기초잔액.toLocaleString().padStart(12)}`);
  console.log(`    차이:      ${(clear기초잔액 - raw기초잔액).toLocaleString().padStart(12)}`);
  if (raw기초잔액 === clear기초잔액) console.log('    ✅ 일치');
  else console.log('    ❌ 불일치');
  console.log();

  console.log('  최종 잔액:');
  console.log(`    raw_data:  ${raw최종잔액.toLocaleString().padStart(12)}`);
  console.log(`    clear:     ${clear최종잔액.toLocaleString().padStart(12)}`);
  console.log(`    차이:      ${(clear최종잔액 - raw최종잔액).toLocaleString().padStart(12)}`);
  if (raw최종잔액 === clear최종잔액) console.log('    ✅ 일치');
  else console.log('    ❌ 불일치');
  console.log();

  // ========================================
  // 3. 전체 금액 합계 비교
  // ========================================
  console.log('[ 3. 전체 금액 합계 ]');

  let raw입금합 = 0;
  let raw출금합 = 0;
  let clear입금합 = 0;
  let clear출금합 = 0;

  rawData.forEach(row => {
    const 금액 = parseFloat(row[2]?.replace(/,/g, '') || 0);
    if (금액 > 0) raw입금합 += 금액;
    else raw출금합 += 금액;
  });

  clearData.forEach(row => {
    const 금액 = parseFloat(row[2]?.replace(/,/g, '') || 0);
    if (금액 > 0) clear입금합 += 금액;
    else clear출금합 += 금액;
  });

  console.log('  입금 합계:');
  console.log(`    raw_data:  ${raw입금합.toLocaleString().padStart(12)}`);
  console.log(`    clear:     ${clear입금합.toLocaleString().padStart(12)}`);
  console.log(`    차이:      ${(clear입금합 - raw입금합).toLocaleString().padStart(12)}`);
  if (raw입금합 === clear입금합) console.log('    ✅ 일치');
  else console.log('    ❌ 불일치');
  console.log();

  console.log('  출금 합계:');
  console.log(`    raw_data:  ${raw출금합.toLocaleString().padStart(12)}`);
  console.log(`    clear:     ${clear출금합.toLocaleString().padStart(12)}`);
  console.log(`    차이:      ${(clear출금합 - raw출금합).toLocaleString().padStart(12)}`);
  if (raw출금합 === clear출금합) console.log('    ✅ 일치');
  else console.log('    ❌ 불일치');
  console.log();

  // ========================================
  // 4. 거래 1:1 매칭 검증
  // ========================================
  console.log('[ 4. 거래 1:1 매칭 검증 ]');
  console.log('  (raw_data와 clear의 각 행을 비교)\n');

  let 불일치건수 = 0;
  const 불일치목록 = [];

  for (let i = 0; i < Math.min(rawData.length, clearData.length); i++) {
    const raw = rawData[i];
    const clear = clearData[i];

    const raw일시 = raw[0];
    const raw금액 = parseFloat(raw[2]?.replace(/,/g, '') || 0);
    const raw잔액 = parseFloat(raw[3]?.replace(/,/g, '') || 0);

    const clear일시 = clear[0];
    const clear금액 = parseFloat(clear[2]?.replace(/,/g, '') || 0);
    const clear잔액 = parseFloat(clear[3]?.replace(/,/g, '') || 0);

    if (raw일시 !== clear일시 || raw금액 !== clear금액 || raw잔액 !== clear잔액) {
      불일치건수++;
      if (불일치건수 <= 10) {
        불일치목록.push({
          행: i + 2,
          raw일시,
          clear일시,
          raw금액,
          clear금액,
          raw잔액,
          clear잔액
        });
      }
    }
  }

  if (불일치건수 === 0) {
    console.log('  ✅ 모든 거래가 완벽하게 일치합니다!\n');
  } else {
    console.log(`  ❌ 불일치 거래: ${불일치건수}건\n`);
    console.log('  [ 불일치 상세 (최대 10건) ]\n');
    불일치목록.forEach(item => {
      console.log(`  행 ${item.행}:`);
      if (item.raw일시 !== item.clear일시) {
        console.log(`    일시: raw="${item.raw일시}" vs clear="${item.clear일시}"`);
      }
      if (item.raw금액 !== item.clear금액) {
        console.log(`    금액: raw=${item.raw금액.toLocaleString()} vs clear=${item.clear금액.toLocaleString()}`);
      }
      if (item.raw잔액 !== item.clear잔액) {
        console.log(`    잔액: raw=${item.raw잔액.toLocaleString()} vs clear=${item.clear잔액.toLocaleString()}`);
      }
      console.log();
    });
  }

  // ========================================
  // 5. 잔액 연속성 검증
  // ========================================
  console.log('[ 5. 잔액 연속성 검증 ]');
  console.log('  (각 거래 후 잔액이 올바른지 확인)\n');

  let 잔액오류건수 = 0;
  const 잔액오류목록 = [];

  for (let i = 1; i < clearData.length; i++) {
    const 이전행 = clearData[i - 1];
    const 현재행 = clearData[i];

    const 이전잔액 = parseFloat(이전행[3]?.replace(/,/g, '') || 0);
    const 현재금액 = parseFloat(현재행[2]?.replace(/,/g, '') || 0);
    const 현재잔액 = parseFloat(현재행[3]?.replace(/,/g, '') || 0);

    const 계산잔액 = 이전잔액 + 현재금액;

    if (Math.abs(계산잔액 - 현재잔액) > 0.01) {
      잔액오류건수++;
      if (잔액오류건수 <= 10) {
        잔액오류목록.push({
          행: i + 2,
          일시: 현재행[0],
          이전잔액,
          현재금액,
          계산잔액,
          현재잔액,
          차이: 현재잔액 - 계산잔액
        });
      }
    }
  }

  if (잔액오류건수 === 0) {
    console.log('  ✅ 모든 잔액이 연속적으로 올바릅니다!\n');
  } else {
    console.log(`  ❌ 잔액 오류: ${잔액오류건수}건\n`);
    console.log('  [ 잔액 오류 상세 (최대 10건) ]\n');
    잔액오류목록.forEach(item => {
      console.log(`  행 ${item.행} (${item.일시}):`);
      console.log(`    이전 잔액:  ${item.이전잔액.toLocaleString().padStart(12)}`);
      console.log(`    현재 금액:  ${item.현재금액.toLocaleString().padStart(12)}`);
      console.log(`    계산 잔액:  ${item.계산잔액.toLocaleString().padStart(12)}`);
      console.log(`    실제 잔액:  ${item.현재잔액.toLocaleString().padStart(12)}`);
      console.log(`    차이:      ${item.차이.toLocaleString().padStart(12)}`);
      console.log();
    });
  }

  // ========================================
  // 6. 계정과목 분류 검증
  // ========================================
  console.log('[ 6. 계정과목 분류 현황 ]');
  console.log('  (clear 시트의 계정과목이 올바르게 분류되었는지 확인)\n');

  const 미분류 = [];
  const 계정통계 = {};

  clearData.forEach((row, idx) => {
    const 계정과목 = row[7];
    const 계정타입 = row[8];

    if (!계정과목 || 계정과목.trim() === '') {
      미분류.push({
        행: idx + 2,
        일시: row[0],
        금액: row[2],
        내용: row[5]
      });
    }

    const key = 계정타입 || '미분류';
    계정통계[key] = (계정통계[key] || 0) + 1;
  });

  console.log('  계정타입별 거래 건수:');
  Object.entries(계정통계).sort().forEach(([타입, 건수]) => {
    console.log(`    ${타입.padEnd(15)} ${건수.toString().padStart(4)}건`);
  });
  console.log();

  if (미분류.length === 0) {
    console.log('  ✅ 모든 거래가 계정과목으로 분류되었습니다!\n');
  } else {
    console.log(`  ⚠️  미분류 거래: ${미분류.length}건\n`);
    console.log('  [ 미분류 거래 목록 (최대 10건) ]\n');
    미분류.slice(0, 10).forEach(item => {
      console.log(`  행 ${item.행}: ${item.일시} | ${item.금액} | ${item.내용}`);
    });
    console.log();
  }

  // ========================================
  // 최종 요약
  // ========================================
  console.log('='.repeat(80));
  console.log('[ 최종 검증 결과 ]');
  console.log('='.repeat(80));

  const 모든검증통과 = (
    rawData.length === clearData.length &&
    raw기초잔액 === clear기초잔액 &&
    raw최종잔액 === clear최종잔액 &&
    raw입금합 === clear입금합 &&
    raw출금합 === clear출금합 &&
    불일치건수 === 0 &&
    잔액오류건수 === 0 &&
    미분류.length === 0
  );

  console.log(`  행 수 일치:           ${rawData.length === clearData.length ? '✅' : '❌'}`);
  console.log(`  기초잔액 일치:         ${raw기초잔액 === clear기초잔액 ? '✅' : '❌'}`);
  console.log(`  최종잔액 일치:         ${raw최종잔액 === clear최종잔액 ? '✅' : '❌'}`);
  console.log(`  입금합계 일치:         ${raw입금합 === clear입금합 ? '✅' : '❌'}`);
  console.log(`  출금합계 일치:         ${raw출금합 === clear출금합 ? '✅' : '❌'}`);
  console.log(`  거래 1:1 매칭:        ${불일치건수 === 0 ? '✅' : '❌'}`);
  console.log(`  잔액 연속성:          ${잔액오류건수 === 0 ? '✅' : '❌'}`);
  console.log(`  계정과목 분류:         ${미분류.length === 0 ? '✅' : '❌'}`);
  console.log();

  if (모든검증통과) {
    console.log('🎉 완벽! raw_data → clear 변환이 100% 정확합니다!\n');
  } else {
    console.log('⚠️  일부 항목에서 문제가 발견되었습니다. 위 내용을 확인하세요.\n');
  }

  console.log('='.repeat(80));
}

main();
