#!/usr/bin/env node
/**
 * Nofee 재무제표 생성 스크립트 v4
 * clear 시트 → Summary 시트 (손익계산서)
 *
 * 완전히 새롭게 작성된 버전
 * - 명확한 데이터 구조
 * - 깔끔한 계정과목 분류
 * - 한국 회계 기준 적용
 */

import { google } from 'googleapis';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 설정
const SPREADSHEET_ID = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';
const CREDENTIALS_PATH = path.resolve(__dirname, '../../../config/google_api_key.json');

/**
 * Clear 시트 데이터 읽기
 */
async function readClearSheet(sheets) {
  console.log('📊 Clear 시트 데이터 읽는 중...\n');

  const response = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'clear!A:I'
  });

  const rows = response.data.values || [];
  if (rows.length === 0) {
    throw new Error('Clear 시트에 데이터가 없습니다');
  }

  // 헤더 확인
  const headers = rows[0];
  console.log('헤더:', headers.join(' | '));

  // 데이터 파싱
  const transactions = [];
  for (let i = 1; i < rows.length; i++) {
    const row = rows[i];
    if (!row[0]) continue; // 빈 행 스킵

    transactions.push({
      일시: row[0],
      구분: row[1],           // 입금/출금
      금액: parseFloat(row[2]?.replace(/,/g, '') || 0),
      잔액: parseFloat(row[3]?.replace(/,/g, '') || 0),
      거래구분: row[4],
      내용: row[5],
      메모: row[6],
      계정과목: row[7],
      계정타입: row[8]
    });
  }

  console.log(`✅ 총 ${transactions.length}개 거래 로드 완료\n`);
  return transactions;
}

/**
 * 거래 데이터 집계
 */
function aggregateData(transactions) {
  console.log('🔢 데이터 집계 중...\n');

  const result = {
    // 매출
    매출: {},

    // 비용
    비용: {},

    // 자본거래
    자본금: {},
    차입금: {},
    기타자본: {},

    // 통장
    기초잔액: 0,
    최종잔액: 0,

    // 통계
    총매출: 0,
    총비용: 0,
    순손익: 0
  };

  transactions.forEach((t, idx) => {
    const 계정 = t.계정과목;
    const 타입 = t.계정타입;
    const 금액 = t.금액;

    // 기초잔액 (첫 거래의 잔액 - 첫 거래 금액)
    if (idx === 0) {
      result.기초잔액 = t.잔액 - t.금액;
    }

    // 최종잔액
    if (idx === transactions.length - 1) {
      result.최종잔액 = t.잔액;
    }

    // 계정타입별 분류
    if (타입 === '매출') {
      result.매출[계정] = (result.매출[계정] || 0) + 금액;
      result.총매출 += 금액;
    }
    else if (타입 === '비용') {
      result.비용[계정] = (result.비용[계정] || 0) + Math.abs(금액);
      result.총비용 += Math.abs(금액);
    }
    else if (타입 === '자본거래' || 타입 === '차입금') {
      if (계정?.includes('자본금')) {
        result.자본금[계정] = (result.자본금[계정] || 0) + 금액;
      } else if (계정?.includes('차입금')) {
        result.차입금[계정] = (result.차입금[계정] || 0) + 금액;
      } else {
        result.기타자본[계정] = (result.기타자본[계정] || 0) + 금액;
      }
    }
  });

  // 순손익 계산
  result.순손익 = result.총매출 - result.총비용;

  // 특수 처리: 김선호 차입금 상환
  // 김선호가 9,950,000원 입금 → 10,000,000원 차입금 상환
  // 이는 자본금이 아니라 차입금 처리
  const 김선호자본금 = result.자본금['자본금 - 김선호'] || 0;
  const 김선호차입금상환 = result.차입금['차입금상환 - 김선호'] || 0;

  if (김선호차입금상환 !== 0 && 김선호자본금 > 0) {
    // 9,950,000원을 자본금에서 차입금으로 이동
    result.자본금['자본금 - 김선호'] = 김선호자본금 + 김선호차입금상환;
    // 차입금상환은 그대로 유지 (이미 음수로 들어있음)
  }

  console.log('✅ 집계 완료');
  console.log(`   매출: ${result.총매출.toLocaleString()}원`);
  console.log(`   비용: ${result.총비용.toLocaleString()}원`);
  console.log(`   순손익: ${result.순손익.toLocaleString()}원\n`);

  return result;
}

/**
 * Summary 시트 데이터 생성
 */
function generateSummarySheet(data) {
  console.log('📝 Summary 시트 생성 중...\n');

  const rows = [];

  // 제목
  rows.push(['=== Nofee 재무제표 ===']);
  rows.push(['생성일시', new Date().toLocaleString('ko-KR')]);
  rows.push([]);

  // ========================================
  // 1. 손익계산서
  // ========================================
  rows.push(['[ 손익계산서 ]']);
  rows.push([]);

  // 매출
  rows.push(['I. 매출']);
  Object.entries(data.매출).forEach(([계정, 금액]) => {
    rows.push([`  ${계정}`,금액.toLocaleString()]);
  });
  rows.push(['매출 합계', data.총매출.toLocaleString()]);
  rows.push([]);

  // 판매비와관리비
  rows.push(['II. 판매비와관리비']);
  Object.entries(data.비용).forEach(([계정, 금액]) => {
    rows.push([`  ${계정}`,금액.toLocaleString()]);
  });
  rows.push(['판매비와관리비 합계', data.총비용.toLocaleString()]);
  rows.push([]);

  // 영업손익
  rows.push(['영업손익', data.순손익.toLocaleString()]);
  rows.push([]);

  // ========================================
  // 2. 자본 내역
  // ========================================
  rows.push(['[ 자본 내역 ]']);
  rows.push([]);

  // 자본금
  if (Object.keys(data.자본금).length > 0) {
    rows.push(['자본금']);
    Object.entries(data.자본금).forEach(([계정, 금액]) => {
      rows.push([`  ${계정}`, 금액.toLocaleString()]);
    });
    const 자본금합계 = Object.values(data.자본금).reduce((sum, v) => sum + v, 0);
    rows.push(['자본금 합계', 자본금합계.toLocaleString()]);
    rows.push([]);
  }

  // 차입금
  if (Object.keys(data.차입금).length > 0) {
    rows.push(['차입금']);
    Object.entries(data.차입금).forEach(([계정, 금액]) => {
      rows.push([`  ${계정}`, 금액.toLocaleString()]);
    });
    const 차입금합계 = Object.values(data.차입금).reduce((sum, v) => sum + v, 0);
    rows.push(['차입금 합계', 차입금합계.toLocaleString()]);
    rows.push([]);
  }

  // 기타 자본거래
  if (Object.keys(data.기타자본).length > 0) {
    rows.push(['기타 자본거래']);
    Object.entries(data.기타자본).forEach(([계정, 금액]) => {
      rows.push([`  ${계정}`, 금액.toLocaleString()]);
    });
    rows.push([]);
  }

  // ========================================
  // 3. 통장 잔액
  // ========================================
  rows.push(['[ 통장 잔액 ]']);
  rows.push([]);
  rows.push(['기초 잔액', data.기초잔액.toLocaleString()]);
  rows.push(['최종 잔액', data.최종잔액.toLocaleString()]);
  rows.push([]);

  // 잔액 검증
  const 계산잔액 = data.기초잔액 + data.총매출 - data.총비용 +
                  Object.values(data.자본금).reduce((s,v) => s+v, 0) +
                  Object.values(data.차입금).reduce((s,v) => s+v, 0) +
                  Object.values(data.기타자본).reduce((s,v) => s+v, 0);

  rows.push(['계산된 잔액', 계산잔액.toLocaleString()]);
  rows.push(['잔액 차이', (data.최종잔액 - 계산잔액).toLocaleString()]);

  console.log('✅ Summary 시트 데이터 생성 완료\n');
  return rows;
}

/**
 * Summary 시트에 쓰기
 */
async function writeSummarySheet(sheets, rows) {
  console.log('💾 Summary 시트에 쓰는 중...\n');

  // 기존 데이터 클리어
  await sheets.spreadsheets.values.clear({
    spreadsheetId: SPREADSHEET_ID,
    range: 'Summary!A:Z'
  });

  // 새 데이터 쓰기
  await sheets.spreadsheets.values.update({
    spreadsheetId: SPREADSHEET_ID,
    range: 'Summary!A1',
    valueInputOption: 'RAW',
    resource: { values: rows }
  });

  console.log('✅ Summary 시트 업데이트 완료!\n');
}

/**
 * 메인 함수
 */
async function main() {
  try {
    console.log('🚀 Nofee 재무제표 생성 시작 (v4)\n');
    console.log('='.repeat(60));
    console.log();

    // Google Sheets API 인증
    const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));
    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: ['https://www.googleapis.com/auth/spreadsheets']
    });
    const sheets = google.sheets({ version: 'v4', auth });

    // 1. Clear 시트 읽기
    const transactions = await readClearSheet(sheets);

    // 2. 데이터 집계
    const aggregatedData = aggregateData(transactions);

    // 3. Summary 시트 생성
    const summaryRows = generateSummarySheet(aggregatedData);

    // 4. Summary 시트 쓰기
    await writeSummarySheet(sheets, summaryRows);

    console.log('='.repeat(60));
    console.log('✨ 완료! Summary 시트를 확인하세요.\n');

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

// 실행
main();
