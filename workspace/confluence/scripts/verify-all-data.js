#!/usr/bin/env node
/**
 * 전체 데이터 100% 검증 스크립트
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
  console.log('🔍 100% 데이터 검증 시작\n');
  console.log('='.repeat(70));
  console.log();

  const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));
  const auth = new google.auth.GoogleAuth({
    credentials,
    scopes: ['https://www.googleapis.com/auth/spreadsheets']
  });

  const sheets = google.sheets({ version: 'v4', auth });

  const result = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'clear!A:I'
  });

  const rows = result.data.values || [];
  console.log(`📊 Clear 시트: 총 ${rows.length - 1}개 거래\n`);

  const 집계 = {
    매출: {},
    비용: {},
    자본거래: {},
    차입금: {},
    기타: {}
  };

  let 첫잔액 = 0;
  let 마지막잔액 = 0;

  for (let i = 1; i < rows.length; i++) {
    const row = rows[i];
    if (!row[0]) continue;

    const 금액 = parseFloat(row[2]?.replace(/,/g, '') || 0);
    const 잔액 = parseFloat(row[3]?.replace(/,/g, '') || 0);
    const 계정 = row[7];
    const 타입 = row[8];

    if (i === 1) {
      첫잔액 = 잔액 - 금액;
    }
    마지막잔액 = 잔액;

    if (타입 === '매출') {
      집계.매출[계정] = (집계.매출[계정] || 0) + 금액;
    } else if (타입 === '비용') {
      집계.비용[계정] = (집계.비용[계정] || 0) + Math.abs(금액);
    } else if (타입 === '자본거래') {
      집계.자본거래[계정] = (집계.자본거래[계정] || 0) + 금액;
    } else if (타입 === '차입금') {
      집계.차입금[계정] = (집계.차입금[계정] || 0) + 금액;
    } else {
      집계.기타[타입 || '미분류'] = (집계.기타[타입 || '미분류'] || 0) + 금액;
    }
  }

  // 매출
  console.log('[ 1. 매출 상세 ]');
  let 총매출 = 0;
  Object.entries(집계.매출).sort().forEach(([k, v]) => {
    console.log(`  ${k.padEnd(35)} ${v.toLocaleString().padStart(12)}`);
    총매출 += v;
  });
  console.log(`  ${'합계'.padEnd(35)} ${총매출.toLocaleString().padStart(12)}`);
  console.log();

  // 비용
  console.log('[ 2. 비용 상세 ]');
  let 총비용 = 0;
  Object.entries(집계.비용).sort().forEach(([k, v]) => {
    console.log(`  ${k.padEnd(35)} ${v.toLocaleString().padStart(12)}`);
    총비용 += v;
  });
  console.log(`  ${'합계'.padEnd(35)} ${총비용.toLocaleString().padStart(12)}`);
  console.log();

  // 자본거래
  console.log('[ 3. 자본거래 상세 ]');
  let 총자본 = 0;
  Object.entries(집계.자본거래).sort().forEach(([k, v]) => {
    console.log(`  ${k.padEnd(35)} ${v.toLocaleString().padStart(12)}`);
    총자본 += v;
  });
  console.log(`  ${'합계'.padEnd(35)} ${총자본.toLocaleString().padStart(12)}`);
  console.log();

  // 차입금
  console.log('[ 4. 차입금 상세 ]');
  let 총차입 = 0;
  Object.entries(집계.차입금).sort().forEach(([k, v]) => {
    console.log(`  ${k.padEnd(35)} ${v.toLocaleString().padStart(12)}`);
    총차입 += v;
  });
  console.log(`  ${'합계'.padEnd(35)} ${총차입.toLocaleString().padStart(12)}`);
  console.log();

  // 기타
  if (Object.keys(집계.기타).length > 0) {
    console.log('[ 5. 기타 ]');
    Object.entries(집계.기타).forEach(([k, v]) => {
      console.log(`  ${k.padEnd(35)} ${v.toLocaleString().padStart(12)}`);
    });
    console.log();
  }

  // 통장 잔액 검증
  console.log('='.repeat(70));
  console.log('[ 통장 잔액 검증 ]');
  console.log('='.repeat(70));
  console.log(`  기초 잔액:                          ${첫잔액.toLocaleString().padStart(12)}`);
  console.log(`  + 매출:                             ${총매출.toLocaleString().padStart(12)}`);
  console.log(`  - 비용:                             ${(-총비용).toLocaleString().padStart(12)}`);
  console.log(`  + 자본거래:                          ${총자본.toLocaleString().padStart(12)}`);
  console.log(`  + 차입금:                            ${총차입.toLocaleString().padStart(12)}`);
  console.log('  ' + '-'.repeat(50));
  const 계산잔액 = 첫잔액 + 총매출 - 총비용 + 총자본 + 총차입;
  console.log(`  = 계산 잔액:                         ${계산잔액.toLocaleString().padStart(12)}`);
  console.log(`  실제 잔액:                           ${마지막잔액.toLocaleString().padStart(12)}`);
  console.log('  ' + '-'.repeat(50));
  const 차이 = 마지막잔액 - 계산잔액;
  console.log(`  차이:                               ${차이.toLocaleString().padStart(12)}`);
  console.log();

  if (차이 === 0) {
    console.log('✅ 완벽! 잔액이 정확히 일치합니다.\n');
  } else {
    console.log('⚠️  잔액 차이가 있습니다.');
    console.log('   → 개인 지출이나 장부 밖 거래가 있을 수 있습니다.\n');
  }

  // 자본금 개인별 분석
  console.log('='.repeat(70));
  console.log('[ 자본금 개인별 분석 ]');
  console.log('='.repeat(70));

  const 송호빈 = (집계.자본거래['자본금 - 송호빈'] || 0) + (집계.자본거래['자본인출 - 환불(자본금조정)'] || 0);
  const 정동민 = 집계.자본거래['자본금 - 정동민'] || 0;
  const 김선호_원본 = 집계.자본거래['자본금 - 김선호'] || 0;
  const 김선호_차입금상환 = 집계.차입금['차입금상환 - 김선호'] || 0;
  const 김선호 = 김선호_원본 + 김선호_차입금상환;

  console.log(`  송호빈:`);
  console.log(`    자본금:                           ${(집계.자본거래['자본금 - 송호빈'] || 0).toLocaleString().padStart(12)}`);
  console.log(`    환불(자본금조정):                   ${(집계.자본거래['자본인출 - 환불(자본금조정)'] || 0).toLocaleString().padStart(12)}`);
  console.log(`    합계:                             ${송호빈.toLocaleString().padStart(12)}`);
  console.log();

  console.log(`  정동민:`);
  console.log(`    자본금:                           ${정동민.toLocaleString().padStart(12)}`);
  console.log();

  console.log(`  김선호:`);
  console.log(`    자본금(원본):                      ${김선호_원본.toLocaleString().padStart(12)}`);
  console.log(`    차입금상환:                        ${김선호_차입금상환.toLocaleString().padStart(12)}`);
  console.log(`    합계(장부상):                      ${김선호.toLocaleString().padStart(12)}`);
  console.log(`    ※ 개인 지출(장부 밖):              1,000,000`);
  console.log(`    실질 자본금:                       ${(김선호 + 1000000).toLocaleString().padStart(12)}`);
  console.log();

  console.log('  ' + '-'.repeat(50));
  console.log(`  장부상 자본금 합계:                   ${(송호빈 + 정동민 + 김선호).toLocaleString().padStart(12)}`);
  console.log(`  실질 자본금 합계:                     ${(송호빈 + 정동민 + 김선호 + 1000000).toLocaleString().padStart(12)}`);
  console.log();

  // 차입금 분석
  console.log('='.repeat(70));
  console.log('[ 차입금 분석 ]');
  console.log('='.repeat(70));

  const 송호빈차입 = (집계.차입금['차입금 - 송호빈'] || 0);
  const 송호빈상환 = (집계.차입금['차입금상환 - 송호빈'] || 0);
  const 김선호차입 = (집계.차입금['차입금 - 김선호'] || 0);

  console.log(`  송호빈:`);
  console.log(`    차입금:                           ${송호빈차입.toLocaleString().padStart(12)}`);
  console.log(`    상환:                             ${송호빈상환.toLocaleString().padStart(12)}`);
  console.log(`    잔액:                             ${(송호빈차입 + 송호빈상환).toLocaleString().padStart(12)}`);
  console.log();

  console.log(`  김선호:`);
  console.log(`    차입금:                           ${김선호차입.toLocaleString().padStart(12)}`);
  console.log(`    상환:                             ${김선호_차입금상환.toLocaleString().padStart(12)}`);
  console.log(`    잔액:                             ${(김선호차입 + 김선호_차입금상환).toLocaleString().padStart(12)}`);
  console.log();

  console.log('  ' + '-'.repeat(50));
  console.log(`  총 차입금 잔액:                       ${총차입.toLocaleString().padStart(12)}`);
  console.log();

  // 최종 요약
  console.log('='.repeat(70));
  console.log('[ 최종 요약 ]');
  console.log('='.repeat(70));
  console.log(`  매출:                               ${총매출.toLocaleString().padStart(12)}`);
  console.log(`  비용:                               ${총비용.toLocaleString().padStart(12)}`);
  console.log(`  영업손익:                            ${(총매출 - 총비용).toLocaleString().padStart(12)}`);
  console.log();
  console.log(`  자본금(장부상):                       ${(송호빈 + 정동민 + 김선호).toLocaleString().padStart(12)}`);
  console.log(`  자본금(실질):                         ${(송호빈 + 정동민 + 김선호 + 1000000).toLocaleString().padStart(12)}`);
  console.log(`  차입금:                              ${총차입.toLocaleString().padStart(12)}`);
  console.log();
  console.log(`  통장 잔액:                           ${마지막잔액.toLocaleString().padStart(12)}`);
  console.log();

  console.log('='.repeat(70));
  console.log('✨ 검증 완료\n');
}

main();
