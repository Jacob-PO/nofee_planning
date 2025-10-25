#!/usr/bin/env node
/**
 * Nofee 재무제표 생성 스크립트 v6
 * 세계 최고 수준의 전문 재무제표 문서 (와이드 레이아웃)
 *
 * Features:
 * - 셀 병합을 활용한 전문적 레이아웃
 * - A~F 컬럼 활용 (넓은 레이아웃)
 * - 손익계산서와 재무상태표 좌우 배치
 * - 구분선, 테두리, 색상 코딩
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

// 색상 정의
const COLORS = {
  HEADER_DARK: { red: 0.2, green: 0.369, blue: 0.573 },      // 진한 파란색
  HEADER_LIGHT: { red: 0.851, green: 0.918, blue: 0.827 },   // 연한 녹색
  SECTION: { red: 0.427, green: 0.62, blue: 0.839 },         // 밝은 파란색
  SUBSECTION: { red: 0.851, green: 0.918, blue: 0.827 },     // 연한 녹색
  TOTAL: { red: 1, green: 0.949, blue: 0.8 },                // 연한 황색
  WHITE: { red: 1, green: 1, blue: 1 },
  GRAY_LIGHT: { red: 0.95, green: 0.95, blue: 0.95 }
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
 * Summary 시트 데이터 생성 (와이드 레이아웃)
 */
function generateSummaryData(data) {
  console.log('📝 재무제표 생성 중 (와이드 레이아웃)...\n');

  const rows = [];
  const 생성일 = new Date().toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  const 영업이익 = data.총매출 - data.총비용;
  const 당기순이익 = 영업이익 + data.총영업외수익;
  const 자본금합계 = Object.values(data.자본금).reduce((sum, v) => sum + v, 0);
  const 차입금합계 = Object.values(data.차입금).reduce((sum, v) => sum + v, 0);
  const 유동자산합계 = data.최종잔액;
  const 보증금합계 = Object.values(data.보증금).reduce((sum, v) => sum + Math.abs(v), 0);

  // ========================================
  // 회사 정보 헤더 (A1:F3) - 병합
  // ========================================
  rows.push(['주식회사 노피', '', '', '', '', '']);
  rows.push(['재무제표', '', '', '', '', '']);
  rows.push([`${생성일} 기준`, '', '', '', '', '']);
  rows.push(['', '', '', '', '', '']);

  // ========================================
  // 손익계산서 (왼쪽) + 재무상태표 (오른쪽)
  // ========================================

  // 컬럼 헤더
  rows.push(['손익계산서', '', '', '재무상태표', '', '']);
  rows.push(['', '', '', '', '', '']);

  // 테이블 헤더
  rows.push(['항목', '금액 (원)', '', '항목', '금액 (원)', '']);

  // 매출 vs 자산
  rows.push(['I. 매출', '', '', '[ 자산 ]', '', '']);

  // 매출 상세 vs 유동자산
  const 매출항목 = Object.entries(data.매출);
  rows.push(['  이노스페이스', 매출항목.find(([k]) => k.includes('이노스페이스'))?.[1] || 0, '', 'I. 유동자산', '', '']);
  rows.push(['  유모바일', 매출항목.find(([k]) => k.includes('유모바일'))?.[1] || 0, '', '  현금및현금성자산', data.최종잔액, '']);
  rows.push(['  티아이앤이', 매출항목.find(([k]) => k.includes('티아이앤이'))?.[1] || 0, '', '유동자산 합계', 유동자산합계, '']);
  rows.push(['  해피넷', 매출항목.find(([k]) => k.includes('해피넷'))?.[1] || 0, '', '', '', '']);
  rows.push(['  그로우플러', 매출항목.find(([k]) => k.includes('그로우플러'))?.[1] || 0, '', 'II. 비유동자산', '', '']);
  rows.push(['  폰슐랭', 매출항목.find(([k]) => k.includes('폰슐랭'))?.[1] || 0, '', '  사무실 보증금', 보증금합계, '']);
  rows.push(['  폰샵', 매출항목.find(([k]) => k.includes('폰샵'))?.[1] || 0, '', '비유동자산 합계', 보증금합계, '']);
  rows.push(['매출 합계', data.총매출, '', '', '', '']);
  rows.push(['', '', '', '자산총계', 유동자산합계 + 보증금합계, '']);
  rows.push(['', '', '', '', '', '']);

  // 판매비와관리비 vs 부채 및 자본
  rows.push(['II. 판매비와관리비', '', '', '[ 부채 및 자본 ]', '', '']);
  rows.push(['  광고선전비', '', '', '', '', '']);

  // 광고선전비 상세 vs 부채
  const 광고비 = Object.entries(data.비용).filter(([k]) => k.includes('광고선전비'));
  let rowIdx = 0;
  광고비.forEach(([계정, 금액], idx) => {
    const name = 계정.replace('광고선전비 - ', '');
    if (idx === 0) {
      rows.push([`    ${name}`, 금액, '', 'I. 부채', '', '']);
    } else if (idx === 1) {
      rows.push([`    ${name}`, 금액, '', '  차입금', '', '']);
    } else {
      rows.push([`    ${name}`, 금액, '', '', '', '']);
    }
  });

  // 차입금 상세
  const 차입금항목 = Object.entries(data.차입금);
  차입금항목.forEach(([계정, 금액], idx) => {
    const name = 계정.replace(/차입금상환 - |차입금 - /, '');
    if (idx + 광고비.length < 15) {
      rows.push(['', '', '', `    ${name}`, 금액, '']);
    }
  });
  rows.push(['', '', '', '부채총계', 차입금합계, '']);
  rows.push(['', '', '', '', '', '']);

  // 복리후생비 vs 자본
  rows.push(['  복리후생비', '', '', 'II. 자본', '', '']);
  const 복리후생비 = Object.entries(data.비용).filter(([k]) => k.includes('복리후생비'));
  복리후생비.forEach(([계정, 금액], idx) => {
    const name = 계정.replace('복리후생비 - ', '');
    if (idx === 0) {
      rows.push([`    ${name}`, 금액, '', '  자본금', '', '']);
    } else {
      rows.push([`    ${name}`, 금액, '', '', '', '']);
    }
  });

  // 자본금 상세
  const 자본금항목 = Object.entries(data.자본금).sort((a, b) => a[0].localeCompare(b[0]));
  자본금항목.forEach(([계정, 금액]) => {
    const name = 계정.replace(/자본금 - |자본인출 - /, '');
    rows.push(['', '', '', `    ${name}`, 금액, '']);
  });

  // 서비스 운영비
  rows.push(['  서비스 운영비', '', '', '  이익잉여금', 당기순이익, '']);
  const 서비스운영비 = Object.entries(data.비용).filter(([k]) => k.includes('서비스 운영비'));
  서비스운영비.forEach(([계정, 금액], idx) => {
    const name = 계정.replace('서비스 운영비 - ', '');
    if (idx === 0) {
      rows.push([`    ${name}`, 금액, '', '자본총계', 자본금합계 + 당기순이익, '']);
    } else {
      rows.push([`    ${name}`, 금액, '', '', '', '']);
    }
  });
  rows.push(['', '', '', '', '', '']);

  // 사업 운영비 vs 부채자본총계
  rows.push(['  사업 운영비', '', '', '부채 및 자본 총계', 차입금합계 + 자본금합계 + 당기순이익, '']);
  const 사업운영비 = Object.entries(data.비용).filter(([k]) => k.includes('사업 운영비'));
  사업운영비.forEach(([계정, 금액]) => {
    const name = 계정.replace('사업 운영비 - ', '');
    rows.push([`    ${name}`, 금액, '', '', '', '']);
  });

  // 기타 비용
  rows.push(['  기타 비용', '', '', '', '', '']);
  const 기타비용 = Object.entries(data.비용).filter(([k]) =>
    !k.includes('광고선전비') &&
    !k.includes('복리후생비') &&
    !k.includes('서비스 운영비') &&
    !k.includes('사업 운영비')
  );
  기타비용.forEach(([계정, 금액]) => {
    rows.push([`    ${계정}`, 금액, '', '', '', '']);
  });

  rows.push(['판매비와관리비 합계', data.총비용, '', '', '', '']);
  rows.push(['', '', '', '', '', '']);
  rows.push(['영업이익', 영업이익, '', '', '', '']);
  rows.push(['', '', '', '', '', '']);

  // 영업외수익
  if (Object.keys(data.영업외수익).length > 0) {
    rows.push(['III. 영업외수익', '', '', '', '', '']);
    Object.entries(data.영업외수익).forEach(([계정, 금액]) => {
      const name = 계정.replace('영업외수익 - ', '');
      rows.push([`  ${name}`, 금액, '', '', '', '']);
    });
    rows.push(['영업외수익 합계', data.총영업외수익, '', '', '', '']);
    rows.push(['', '', '', '', '', '']);
  }

  rows.push(['당기순이익', 당기순이익, '', '', '', '']);
  rows.push(['', '', '', '', '', '']);
  rows.push(['', '', '', '', '', '']);

  // ========================================
  // 현금흐름표 (전체 너비)
  // ========================================
  rows.push(['현금흐름표', '', '', '', '', '']);
  rows.push(['', '', '', '', '', '']);
  rows.push(['항목', '금액 (원)', '', '', '', '']);
  rows.push(['기초 현금', data.기초잔액, '', '', '', '']);
  rows.push(['  영업활동 현금흐름', 영업이익, '', '', '', '']);
  rows.push(['  영업외활동 현금흐름', data.총영업외수익, '', '', '', '']);
  rows.push(['  재무활동 현금흐름', 자본금합계 + 차입금합계, '', '', '', '']);
  const 보증금지급 = Object.values(data.보증금).reduce((sum, v) => sum + v, 0);
  rows.push(['  투자활동 현금흐름', 보증금지급, '', '', '', '']);
  rows.push(['기말 현금', data.최종잔액, '', '', '', '']);

  console.log('✅ 재무제표 생성 완료\n');
  return rows;
}

/**
 * Summary 시트에 쓰고 포맷팅 적용
 */
async function writeSummarySheet(sheets, rows) {
  console.log('💾 Summary 시트 업데이트 중...\n');

  const sheetId = await getSheetId(sheets, 'summary');

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

  const requests = [];

  // 1. 회사명 헤더 병합 (A1:F1)
  requests.push({
    mergeCells: {
      range: { sheetId, startRowIndex: 0, endRowIndex: 1, startColumnIndex: 0, endColumnIndex: 6 },
      mergeType: 'MERGE_ALL'
    }
  });
  requests.push({
    mergeCells: {
      range: { sheetId, startRowIndex: 1, endRowIndex: 2, startColumnIndex: 0, endColumnIndex: 6 },
      mergeType: 'MERGE_ALL'
    }
  });
  requests.push({
    mergeCells: {
      range: { sheetId, startRowIndex: 2, endRowIndex: 3, startColumnIndex: 0, endColumnIndex: 6 },
      mergeType: 'MERGE_ALL'
    }
  });

  // 2. 회사명 헤더 포맷팅
  requests.push({
    repeatCell: {
      range: { sheetId, startRowIndex: 0, endRowIndex: 1, startColumnIndex: 0, endColumnIndex: 6 },
      cell: {
        userEnteredFormat: {
          backgroundColor: COLORS.HEADER_DARK,
          textFormat: { foregroundColor: COLORS.WHITE, fontSize: 20, bold: true },
          horizontalAlignment: 'CENTER',
          verticalAlignment: 'MIDDLE'
        }
      },
      fields: 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)'
    }
  });

  requests.push({
    repeatCell: {
      range: { sheetId, startRowIndex: 1, endRowIndex: 3, startColumnIndex: 0, endColumnIndex: 6 },
      cell: {
        userEnteredFormat: {
          backgroundColor: COLORS.HEADER_LIGHT,
          textFormat: { fontSize: 13, bold: true },
          horizontalAlignment: 'CENTER',
          verticalAlignment: 'MIDDLE'
        }
      },
      fields: 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)'
    }
  });

  // 3. 행 높이 조정
  requests.push({
    updateDimensionProperties: {
      range: { sheetId, dimension: 'ROWS', startIndex: 0, endIndex: 1 },
      properties: { pixelSize: 50 },
      fields: 'pixelSize'
    }
  });

  // 4. 컬럼 너비 조정
  requests.push({
    updateDimensionProperties: {
      range: { sheetId, dimension: 'COLUMNS', startIndex: 0, endIndex: 1 },
      properties: { pixelSize: 250 },
      fields: 'pixelSize'
    }
  });
  requests.push({
    updateDimensionProperties: {
      range: { sheetId, dimension: 'COLUMNS', startIndex: 1, endIndex: 2 },
      properties: { pixelSize: 130 },
      fields: 'pixelSize'
    }
  });
  requests.push({
    updateDimensionProperties: {
      range: { sheetId, dimension: 'COLUMNS', startIndex: 2, endIndex: 3 },
      properties: { pixelSize: 30 },
      fields: 'pixelSize'
    }
  });
  requests.push({
    updateDimensionProperties: {
      range: { sheetId, dimension: 'COLUMNS', startIndex: 3, endIndex: 4 },
      properties: { pixelSize: 250 },
      fields: 'pixelSize'
    }
  });
  requests.push({
    updateDimensionProperties: {
      range: { sheetId, dimension: 'COLUMNS', startIndex: 4, endIndex: 5 },
      properties: { pixelSize: 130 },
      fields: 'pixelSize'
    }
  });

  // 5. 섹션별 포맷팅
  rows.forEach((row, idx) => {
    const text = row[0] || '';

    // 주요 섹션
    if (text === '손익계산서' || text === '재무상태표' || text === '현금흐름표') {
      // 병합
      const endCol = text === '손익계산서' ? 3 : (text === '재무상태표' ? 6 : 6);
      const startCol = text === '재무상태표' ? 3 : 0;

      if (text !== '현금흐름표') {
        requests.push({
          mergeCells: {
            range: { sheetId, startRowIndex: idx, endRowIndex: idx + 1, startColumnIndex: startCol, endColumnIndex: endCol },
            mergeType: 'MERGE_ALL'
          }
        });
      } else {
        requests.push({
          mergeCells: {
            range: { sheetId, startRowIndex: idx, endRowIndex: idx + 1, startColumnIndex: 0, endColumnIndex: 6 },
            mergeType: 'MERGE_ALL'
          }
        });
      }

      // 포맷팅
      requests.push({
        repeatCell: {
          range: { sheetId, startRowIndex: idx, endRowIndex: idx + 1 },
          cell: {
            userEnteredFormat: {
              backgroundColor: COLORS.SECTION,
              textFormat: { foregroundColor: COLORS.WHITE, fontSize: 14, bold: true },
              horizontalAlignment: 'CENTER'
            }
          },
          fields: 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
        }
      });
    }

    // 합계 행
    else if (text.includes('합계') || text.includes('총계') || text === '영업이익' || text === '당기순이익') {
      requests.push({
        repeatCell: {
          range: { sheetId, startRowIndex: idx, endRowIndex: idx + 1 },
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

    // 중간 섹션
    else if (text.startsWith('I. ') || text.startsWith('II. ') || text.startsWith('III. ') || text.startsWith('[ ')) {
      requests.push({
        repeatCell: {
          range: { sheetId, startRowIndex: idx, endRowIndex: idx + 1 },
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

  // 6. 금액 컬럼 포맷팅 (B, E열)
  requests.push({
    repeatCell: {
      range: { sheetId, startColumnIndex: 1, endColumnIndex: 2 },
      cell: {
        userEnteredFormat: {
          numberFormat: { type: 'NUMBER', pattern: '#,##0' },
          horizontalAlignment: 'RIGHT'
        }
      },
      fields: 'userEnteredFormat(numberFormat,horizontalAlignment)'
    }
  });
  requests.push({
    repeatCell: {
      range: { sheetId, startColumnIndex: 4, endColumnIndex: 5 },
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
    console.log('🚀 Nofee 재무제표 생성 시작 (v6 - Wide Layout Edition)\n');
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
    console.log('✨ 완료! 와이드 레이아웃 재무제표가 생성되었습니다.\n');
    console.log(`🔗 https://docs.google.com/spreadsheets/d/${SPREADSHEET_ID}/edit#gid=0`);
    console.log();

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

main();
