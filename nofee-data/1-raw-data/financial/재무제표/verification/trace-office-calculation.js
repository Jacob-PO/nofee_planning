#!/usr/bin/env node
import { google } from 'googleapis';
import fs from 'fs';
import path from 'path';

/**
 * 사업 운영비 - 사무실 계산 과정 추적
 */
async function main() {
  console.log('=== 사업 운영비 - 사무실 계산 과정 추적 ===\n');

  const credentialsPath = path.resolve(process.cwd(), '../../config/google_api_key.json');
  const credentials = JSON.parse(fs.readFileSync(credentialsPath, 'utf8'));

  const auth = new google.auth.GoogleAuth({
    credentials,
    scopes: ['https://www.googleapis.com/auth/spreadsheets'],
  });

  const sheets = google.sheets({ version: 'v4', auth });
  const spreadsheetId = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';

  // raw_data에서 사무실 관련 거래 가져오기
  const response = await sheets.spreadsheets.values.get({
    spreadsheetId,
    range: 'raw_data!A1:Z1000',
  });

  const rows = response.data.values || [];

  console.log('📋 Step 1: raw_data에서 사무실 관련 출금 찾기\n');

  let officeExpenses = [];

  for (let i = 1; i < rows.length; i++) {
    const row = rows[i];
    if (!row || row.length === 0) continue;

    const date = row[0] || '';
    const type = row[1] || '';
    const amount = parseFloat(String(row[2] || '0').replace(/[,원₩\s]/g, ''));
    const desc = row[5] || '';

    if (type === '출금' && (desc.includes('사무실') || desc.includes('월세')) && !desc.includes('보증금')) {
      officeExpenses.push({ date, desc, amount: Math.abs(amount) });
      console.log(`✓ ${desc}: ${Math.abs(amount).toLocaleString('ko-KR')}원 (${date})`);
    }
  }

  const totalFromRawData = officeExpenses.reduce((sum, item) => sum + item.amount, 0);

  console.log(`\n📊 raw_data 통장 지출 소계: ${totalFromRawData.toLocaleString('ko-KR')}원\n`);

  // clear 데이터에서 확인
  console.log('📋 Step 2: clear 시트에서 "사업 운영비 - 사무실" 확인\n');

  const clearResponse = await sheets.spreadsheets.values.get({
    spreadsheetId,
    range: 'clear!A1:I1000',
  });

  const clearRows = clearResponse.data.values || [];
  let clearOfficeTotal = 0;

  for (let i = 1; i < clearRows.length; i++) {
    const row = clearRows[i];
    if (!row || row.length === 0) continue;

    const category = row[7];
    if (category && category === '사업 운영비 - 사무실') {
      const amount = parseFloat(String(row[2] || '0').replace(/[,원₩\s]/g, ''));
      const desc = row[5];
      clearOfficeTotal += Math.abs(amount);
      console.log(`✓ ${desc}: ${Math.abs(amount).toLocaleString('ko-KR')}원`);
    }
  }

  console.log(`\n📊 clear 시트 "사업 운영비 - 사무실" 합계: ${clearOfficeTotal.toLocaleString('ko-KR')}원\n`);

  // 코드에서 추가되는 김선호 개인 계약금
  console.log('📋 Step 3: 코드에서 추가되는 금액 (650-657번 줄)\n');
  console.log('✓ 김선호 개인통장 사무실 계약금: 1,000,000원');
  console.log('  (장부 밖 거래 - 노피 통장에서 나가지 않음)\n');

  const personalDeposit = 1000000;
  const finalTotal = clearOfficeTotal + personalDeposit;

  console.log('📊 Step 4: 최종 계산\n');
  console.log(`summary.categoryExpenses['사업 운영비 - 사무실'] = ${clearOfficeTotal.toLocaleString('ko-KR')}원 (clear 데이터)`);
  console.log(`summary.categoryExpenses['사업 운영비 - 사무실'] += ${personalDeposit.toLocaleString('ko-KR')}원 (개인 계약금)`);
  console.log(`summary.totalExpenses += ${personalDeposit.toLocaleString('ko-KR')}원\n`);

  console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
  console.log(`최종 "사업 운영비 - 사무실": ${finalTotal.toLocaleString('ko-KR')}원`);
  console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`);

  // Summary 시트에서 실제 값 확인
  console.log('📋 Step 5: Summary 시트 실제 값 확인\n');

  const summaryResponse = await sheets.spreadsheets.values.get({
    spreadsheetId,
    range: 'summary!A1:B200',
  });

  const summaryRows = summaryResponse.data.values || [];

  for (let i = 0; i < summaryRows.length; i++) {
    const row = summaryRows[i];
    if (row && row[0] && row[0].includes('사업 운영비 - 사무실')) {
      console.log(`Summary 시트 표시: ${row[0]} = ${row[1]}`);

      const summaryValue = parseFloat(String(row[1] || '0').replace(/[,원₩\s()]/g, ''));

      if (summaryValue === finalTotal) {
        console.log(`\n✅ 일치! 계산이 정확합니다.`);
      } else {
        console.log(`\n❌ 불일치! 예상: ${finalTotal.toLocaleString('ko-KR')}원, 실제: ${summaryValue.toLocaleString('ko-KR')}원`);
      }
      break;
    }
  }

  console.log('\n=== 계산 과정 추적 완료 ===');
}

main().catch(console.error);
