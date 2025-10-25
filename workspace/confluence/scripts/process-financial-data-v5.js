#!/usr/bin/env node
/**
 * Nofee 재무제표 생성 스크립트 v5
 * 세계 최고 수준의 전문 재무제표 문서
 *
 * Features:
 * - 글로벌 스탠다드 재무제표 구조
 * - 전문적인 표 디자인 (색상, 테두리, 정렬)
 * - 손익계산서 (Income Statement)
 * - 재무상태표 (Balance Sheet)
 * - 현금흐름표 (Cash Flow Statement)
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

// 색상 정의 (Google Sheets RGB format)
const COLORS = {
  HEADER_DARK: { red: 0.2, green: 0.369, blue: 0.573 },      // 진한 파란색 #335B92
  HEADER_LIGHT: { red: 0.851, green: 0.918, blue: 0.827 },   // 연한 녹색 #D9EAD3
  SECTION: { red: 0.427, green: 0.62, blue: 0.839 },         // 밝은 파란색 #6D9ED6
  SUBSECTION: { red: 0.851, green: 0.918, blue: 0.827 },     // 연한 녹색 #D9EAD3
  TOTAL: { red: 1, green: 0.949, blue: 0.8 },                // 연한 황색 #FFF2CC
  WHITE: { red: 1, green: 1, blue: 1 },
  GRAY_LIGHT: { red: 0.98, green: 0.98, blue: 0.98 }
};

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

  const transactions = [];
  for (let i = 1; i < rows.length; i++) {
    const row = rows[i];
    if (!row[0]) continue;

    transactions.push({
      일시: row[0],
      구분: row[1],
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
    매출: {},
    비용: {},
    자본금: {},
    차입금: {},
    영업외수익: {},
    보증금: {},
    기타: {},
    기초잔액: 0,
    최종잔액: 0,
    총매출: 0,
    총비용: 0,
    총영업외수익: 0,
    순손익: 0
  };

  transactions.forEach((t, idx) => {
    const 계정 = t.계정과목;
    const 타입 = t.계정타입;
    const 금액 = t.금액;

    if (idx === 0) result.기초잔액 = t.잔액 - t.금액;
    if (idx === transactions.length - 1) result.최종잔액 = t.잔액;

    if (타입 === '매출') {
      result.매출[계정] = (result.매출[계정] || 0) + 금액;
      result.총매출 += 금액;
    }
    else if (타입 === '비용') {
      result.비용[계정] = (result.비용[계정] || 0) + Math.abs(금액);
      result.총비용 += Math.abs(금액);
    }
    else if (타입 === '자본거래') {
      if (계정?.includes('자본금')) {
        result.자본금[계정] = (result.자본금[계정] || 0) + 금액;
      } else {
        result.기타[계정] = (result.기타[계정] || 0) + 금액;
      }
    }
    else if (타입 === '차입금') {
      result.차입금[계정] = (result.차입금[계정] || 0) + 금액;
    }
    else if (타입 === '영업외수익') {
      result.영업외수익[계정] = (result.영업외수익[계정] || 0) + 금액;
      result.총영업외수익 += 금액;
    }
    else if (타입 === '보증금') {
      result.보증금[계정] = (result.보증금[계정] || 0) + 금액;
    }
  });

  // 김선호 차입금 상환 처리
  const 김선호자본금 = result.자본금['자본금 - 김선호'] || 0;
  const 김선호차입금상환 = result.차입금['차입금상환 - 김선호'] || 0;
  if (김선호차입금상환 !== 0 && 김선호자본금 > 0) {
    result.자본금['자본금 - 김선호'] = 김선호자본금 + 김선호차입금상환;
  }

  result.순손익 = result.총매출 - result.총비용;

  console.log('✅ 집계 완료\n');
  return result;
}

/**
 * Summary 시트 데이터 생성 (글로벌 스탠다드)
 */
function generateSummaryData(data) {
  console.log('📝 재무제표 생성 중...\n');

  const rows = [];
  const 생성일 = new Date().toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  // ========================================
  // 회사 정보 헤더
  // ========================================
  rows.push(['주식회사 노피']);
  rows.push(['재무제표']);
  rows.push([`${생성일} 기준`]);
  rows.push([]);

  // ========================================
  // 1. 손익계산서
  // ========================================
  rows.push(['손익계산서']);
  rows.push([]);
  rows.push(['항목', '금액 (원)']);

  // 매출
  rows.push(['I. 매출']);
  Object.entries(data.매출).forEach(([계정, 금액]) => {
    const name = 계정.replace('매출 - ', '');
    rows.push([`  ${name}`, 금액]);
  });
  rows.push(['매출 합계', data.총매출]);
  rows.push([]);

  // 판매비와관리비
  rows.push(['II. 판매비와관리비']);

  // 비용을 카테고리별로 그룹화
  const 비용그룹 = {
    '광고선전비': [],
    '복리후생비': [],
    '서비스 운영비': [],
    '사업 운영비': [],
    '기타': []
  };

  Object.entries(data.비용).forEach(([계정, 금액]) => {
    if (계정.includes('광고선전비')) {
      비용그룹['광고선전비'].push([계정, 금액]);
    } else if (계정.includes('복리후생비')) {
      비용그룹['복리후생비'].push([계정, 금액]);
    } else if (계정.includes('서비스 운영비')) {
      비용그룹['서비스 운영비'].push([계정, 금액]);
    } else if (계정.includes('사업 운영비')) {
      비용그룹['사업 운영비'].push([계정, 금액]);
    } else {
      비용그룹['기타'].push([계정, 금액]);
    }
  });

  // 그룹별로 출력
  Object.entries(비용그룹).forEach(([그룹명, 항목들]) => {
    if (항목들.length > 0) {
      rows.push([`  ${그룹명}`, '']);
      항목들.forEach(([계정, 금액]) => {
        const name = 계정.replace(/.*? - /, '');
        rows.push([`    ${name}`, 금액]);
      });
    }
  });

  rows.push(['판매비와관리비 합계', data.총비용]);
  rows.push([]);

  // 영업이익
  const 영업이익 = data.총매출 - data.총비용;
  rows.push(['영업이익', 영업이익]);
  rows.push([]);

  // 영업외수익
  if (Object.keys(data.영업외수익).length > 0) {
    rows.push(['III. 영업외수익']);
    Object.entries(data.영업외수익).forEach(([계정, 금액]) => {
      const name = 계정.replace('영업외수익 - ', '');
      rows.push([`  ${name}`, 금액]);
    });
    rows.push(['영업외수익 합계', data.총영업외수익]);
    rows.push([]);
  }

  // 당기순이익
  const 당기순이익 = 영업이익 + data.총영업외수익;
  rows.push(['당기순이익', 당기순이익]);
  rows.push([]);
  rows.push([]);

  // ========================================
  // 2. 재무상태표
  // ========================================
  rows.push(['재무상태표']);
  rows.push([]);
  rows.push(['항목', '금액 (원)']);

  // 자산
  rows.push(['[ 자산 ]']);
  rows.push([]);

  // 유동자산
  rows.push(['I. 유동자산']);
  rows.push(['  현금및현금성자산', data.최종잔액]);
  const 유동자산합계 = data.최종잔액;
  rows.push(['유동자산 합계', 유동자산합계]);
  rows.push([]);

  // 비유동자산
  if (Object.keys(data.보증금).length > 0) {
    rows.push(['II. 비유동자산']);
    Object.entries(data.보증금).forEach(([계정, 금액]) => {
      const name = 계정.replace('보증금 - ', '');
      rows.push([`  ${name} 보증금`, Math.abs(금액)]);
    });
    const 보증금합계 = Object.values(data.보증금).reduce((sum, v) => sum + Math.abs(v), 0);
    rows.push(['비유동자산 합계', 보증금합계]);
    rows.push([]);

    rows.push(['자산총계', 유동자산합계 + 보증금합계]);
  } else {
    rows.push(['자산총계', 유동자산합계]);
  }
  rows.push([]);

  // 부채 및 자본
  rows.push(['[ 부채 및 자본 ]']);
  rows.push([]);

  // 부채
  const 차입금합계 = Object.values(data.차입금).reduce((sum, v) => sum + v, 0);
  if (차입금합계 > 0) {
    rows.push(['I. 부채']);
    rows.push(['  차입금']);
    Object.entries(data.차입금).forEach(([계정, 금액]) => {
      const name = 계정.replace(/차입금상환 - |차입금 - /, '');
      rows.push([`    ${name}`, 금액]);
    });
    rows.push(['부채총계', 차입금합계]);
    rows.push([]);
  }

  // 자본
  rows.push(['II. 자본']);
  rows.push(['  자본금']);

  const 자본금상세 = [];
  Object.entries(data.자본금).forEach(([계정, 금액]) => {
    자본금상세.push([계정, 금액]);
  });

  자본금상세.sort((a, b) => a[0].localeCompare(b[0]));
  자본금상세.forEach(([계정, 금액]) => {
    const name = 계정.replace(/자본금 - |자본인출 - /, '');
    rows.push([`    ${name}`, 금액]);
  });

  const 자본금합계 = Object.values(data.자본금).reduce((sum, v) => sum + v, 0);
  rows.push(['  이익잉여금', 당기순이익]);
  rows.push(['자본총계', 자본금합계 + 당기순이익]);
  rows.push([]);

  rows.push(['부채 및 자본 총계', 차입금합계 + 자본금합계 + 당기순이익]);
  rows.push([]);
  rows.push([]);

  // ========================================
  // 3. 현금흐름표
  // ========================================
  rows.push(['현금흐름표']);
  rows.push([]);
  rows.push(['항목', '금액 (원)']);
  rows.push(['기초 현금', data.기초잔액]);
  rows.push(['  영업활동 현금흐름', 영업이익]);
  rows.push(['  영업외활동 현금흐름', data.총영업외수익]);
  rows.push(['  재무활동 현금흐름', 자본금합계 + 차입금합계]);
  const 보증금지급 = Object.values(data.보증금).reduce((sum, v) => sum + v, 0);
  rows.push(['  투자활동 현금흐름', 보증금지급]);
  rows.push(['기말 현금', data.최종잔액]);
  rows.push([]);

  // 검증
  const 계산잔액 = data.기초잔액 + data.총매출 - data.총비용 + data.총영업외수익 +
                  자본금합계 + 차입금합계 + 보증금지급;
  rows.push(['계산된 잔액', 계산잔액]);
  rows.push(['차이', data.최종잔액 - 계산잔액]);

  console.log('✅ 재무제표 생성 완료\n');
  return rows;
}

/**
 * Summary 시트에 쓰고 포맷팅 적용
 */
async function writeSummarySheet(sheets, rows) {
  console.log('💾 Summary 시트 업데이트 중...\n');

  // 기존 데이터 클리어
  await sheets.spreadsheets.values.clear({
    spreadsheetId: SPREADSHEET_ID,
    range: 'summary!A:Z'
  });

  // 데이터 쓰기
  await sheets.spreadsheets.values.update({
    spreadsheetId: SPREADSHEET_ID,
    range: 'summary!A1',
    valueInputOption: 'USER_ENTERED',
    resource: { values: rows }
  });

  console.log('🎨 포맷팅 적용 중...\n');

  // Sheet ID 미리 가져오기
  const sheetId = await getSheetId(sheets, 'summary');

  // 포맷팅 요청 생성
  const requests = [];

  // 1. 전체 시트 기본 설정
  requests.push({
    repeatCell: {
      range: {
        sheetId: sheetId,
        startRowIndex: 0,
        endRowIndex: rows.length
      },
      cell: {
        userEnteredFormat: {
          textFormat: { fontFamily: 'Arial', fontSize: 10 },
          verticalAlignment: 'MIDDLE'
        }
      },
      fields: 'userEnteredFormat(textFormat,verticalAlignment)'
    }
  });

  // 2. 회사명 헤더 (1-3행)
  requests.push({
    repeatCell: {
      range: { sheetId: sheetId, startRowIndex: 0, endRowIndex: 1 },
      cell: {
        userEnteredFormat: {
          backgroundColor: COLORS.HEADER_DARK,
          textFormat: {
            foregroundColor: COLORS.WHITE,
            fontSize: 18,
            bold: true
          },
          horizontalAlignment: 'CENTER'
        }
      },
      fields: 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
    }
  });

  requests.push({
    repeatCell: {
      range: { sheetId: sheetId, startRowIndex: 1, endRowIndex: 3 },
      cell: {
        userEnteredFormat: {
          backgroundColor: COLORS.HEADER_LIGHT,
          textFormat: { fontSize: 12, bold: true },
          horizontalAlignment: 'CENTER'
        }
      },
      fields: 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
    }
  });

  // 3. 섹션 헤더 찾아서 포맷팅
  rows.forEach((row, idx) => {
    const text = row[0] || '';

    // 주요 섹션 (손익계산서, 재무상태표 등)
    if (text === '손익계산서' ||
        text === '재무상태표' ||
        text === '현금흐름표') {
      requests.push({
        repeatCell: {
          range: {
            sheetId: sheetId,
            startRowIndex: idx,
            endRowIndex: idx + 1
          },
          cell: {
            userEnteredFormat: {
              backgroundColor: COLORS.SECTION,
              textFormat: {
                foregroundColor: COLORS.WHITE,
                fontSize: 14,
                bold: true
              },
              horizontalAlignment: 'LEFT'
            }
          },
          fields: 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
        }
      });
    }

    // 소계/합계 행 (영업이익, 당기순이익 포함)
    else if (text.includes('합계') || text.includes('총계') ||
             text === '영업이익' || text === '당기순이익') {
      requests.push({
        repeatCell: {
          range: {
            sheetId: sheetId,
            startRowIndex: idx,
            endRowIndex: idx + 1
          },
          cell: {
            userEnteredFormat: {
              backgroundColor: COLORS.TOTAL,
              textFormat: { bold: true },
              borders: {
                top: { style: 'SOLID', width: 1 },
                bottom: { style: 'DOUBLE', width: 2 }
              }
            }
          },
          fields: 'userEnteredFormat(backgroundColor,textFormat,borders)'
        }
      });
    }

    // 중간 섹션 (매출, 판매비와관리비 등)
    else if (text.startsWith('I. ') || text.startsWith('II. ') || text.startsWith('III. ') ||
             text.startsWith('[ ')) {
      requests.push({
        repeatCell: {
          range: {
            sheetId: sheetId,
            startRowIndex: idx,
            endRowIndex: idx + 1
          },
          cell: {
            userEnteredFormat: {
              backgroundColor: COLORS.SUBSECTION,
              textFormat: { bold: true, fontSize: 11 }
            }
          },
          fields: 'userEnteredFormat(backgroundColor,textFormat)'
        }
      });
    }
  });

  // 4. 컬럼 너비 조정
  requests.push({
    updateDimensionProperties: {
      range: {
        sheetId: sheetId,
        dimension: 'COLUMNS',
        startIndex: 0,
        endIndex: 1
      },
      properties: { pixelSize: 350 },
      fields: 'pixelSize'
    }
  });

  requests.push({
    updateDimensionProperties: {
      range: {
        sheetId: sheetId,
        dimension: 'COLUMNS',
        startIndex: 1,
        endIndex: 2
      },
      properties: { pixelSize: 150 },
      fields: 'pixelSize'
    }
  });

  // 5. 금액 컬럼 (B열) 숫자 포맷팅 및 오른쪽 정렬
  requests.push({
    repeatCell: {
      range: {
        sheetId: sheetId,
        startColumnIndex: 1,
        endColumnIndex: 2
      },
      cell: {
        userEnteredFormat: {
          numberFormat: { type: 'NUMBER', pattern: '#,##0' },
          horizontalAlignment: 'RIGHT'
        }
      },
      fields: 'userEnteredFormat(numberFormat,horizontalAlignment)'
    }
  });

  // 포맷팅 일괄 적용
  if (requests.length > 0) {
    await sheets.spreadsheets.batchUpdate({
      spreadsheetId: SPREADSHEET_ID,
      resource: { requests }
    });
  }

  console.log('✅ Summary 시트 업데이트 완료!\n');
}

/**
 * Sheet ID 가져오기
 */
async function getSheetId(sheets, sheetName) {
  const response = await sheets.spreadsheets.get({
    spreadsheetId: SPREADSHEET_ID
  });

  const sheet = response.data.sheets.find(s => s.properties.title === sheetName);
  return sheet ? sheet.properties.sheetId : 0;
}

/**
 * 메인 함수
 */
async function main() {
  try {
    console.log('🚀 Nofee 재무제표 생성 시작 (v5 - Professional Edition)\n');
    console.log('='.repeat(70));
    console.log();

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
    const summaryRows = generateSummaryData(aggregatedData);

    // 4. Summary 시트 쓰기 및 포맷팅
    await writeSummarySheet(sheets, summaryRows);

    console.log('='.repeat(70));
    console.log('✨ 완료! 전문가 수준의 재무제표가 생성되었습니다.\n');
    console.log(`🔗 https://docs.google.com/spreadsheets/d/${SPREADSHEET_ID}/edit#gid=0`);
    console.log();

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

main();
