#!/usr/bin/env node
/**
 * Nofee 재무제표 생성 스크립트 v7
 * 전문 회계법인 스타일 (Big 4 Accounting Firms Style)
 *
 * Features:
 * - A~E 컬럼 활용 (넓은 전문가 레이아웃)
 * - 항목명 셀 병합 (깔끔한 구조)
 * - 전문적인 테두리 및 구분선
 * - 계층 구조 명확한 인덴트
 * - 당기/전기 비교 컬럼 (향후 확장 가능)
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

// 전문 회계법인 색상 팔레트
const COLORS = {
  HEADER_NAVY: { red: 0.129, green: 0.196, blue: 0.349 },    // 네이비 #213859
  HEADER_GRAY: { red: 0.4, green: 0.4, blue: 0.4 },          // 진한 회색
  SECTION_BLUE: { red: 0.263, green: 0.4, blue: 0.698 },     // 전문 블루 #4366B2
  SUBSECTION: { red: 0.918, green: 0.933, blue: 0.957 },     // 연한 블루그레이
  TOTAL_YELLOW: { red: 1, green: 0.925, blue: 0.698 },       // 전문 옐로우
  WHITE: { red: 1, green: 1, blue: 1 },
  LIGHT_GRAY: { red: 0.98, green: 0.98, blue: 0.98 }
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
  if (rows.length === 0) throw new Error('Clear 시트에 데이터가 없습니다');

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
    매출: {}, 비용: {}, 자본금: {}, 차입금: {}, 영업외수익: {}, 보증금: {}, 기타: {},
    기초잔액: 0, 최종잔액: 0, 총매출: 0, 총비용: 0, 총영업외수익: 0, 순손익: 0
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
      if (계정?.includes('자본금')) result.자본금[계정] = (result.자본금[계정] || 0) + 금액;
      else result.기타[계정] = (result.기타[계정] || 0) + 금액;
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
 * 전문 회계법인 스타일 재무제표 생성
 */
function generateProfessionalStatement(data) {
  console.log('📝 전문 재무제표 생성 중...\n');

  const rows = [];
  const 생성일 = new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' });

  const 영업이익 = data.총매출 - data.총비용;
  const 당기순이익 = 영업이익 + data.총영업외수익;
  const 자본금합계 = Object.values(data.자본금).reduce((sum, v) => sum + v, 0);
  const 차입금합계 = Object.values(data.차입금).reduce((sum, v) => sum + v, 0);
  const 유동자산합계 = data.최종잔액;
  const 보증금합계 = Object.values(data.보증금).reduce((sum, v) => sum + Math.abs(v), 0);

  // ========================================
  // 회사 헤더
  // ========================================
  rows.push(['주식회사 노피', '', '', '', '']);
  rows.push(['재무제표', '', '', '', '']);
  rows.push([`제 1 기: ${생성일} 현재`, '', '', '', '']);
  rows.push(['', '', '', '', '']);

  // ========================================
  // 손익계산서
  // ========================================
  rows.push(['손익계산서', '', '', '', '']);
  rows.push(['', '', '', '', '']);
  rows.push(['과목', '', '주석', '당기', '']);

  // I. 매출액
  rows.push(['I. 매출액', '', '', '', '']);
  Object.entries(data.매출).forEach(([계정, 금액]) => {
    const name = 계정.replace('매출 - ', '');
    rows.push([`    ${name}`, '', '', 금액, '']);
  });
  rows.push(['', '', '', '', '']);
  rows.push(['매출액 합계', '', '', data.총매출, '']);
  rows.push(['', '', '', '', '']);

  // II. 매출원가 (현재 0)
  rows.push(['II. 매출원가', '', '', 0, '']);
  rows.push(['', '', '', '', '']);
  rows.push(['매출총이익', '', '', data.총매출, '']);
  rows.push(['', '', '', '', '']);

  // III. 판매비와관리비
  rows.push(['III. 판매비와관리비', '', '', '', '']);

  // 비용 그룹화
  const 비용그룹 = {
    '광고선전비': [],
    '복리후생비': [],
    '서비스운영비': [],
    '사업운영비': [],
    '기타': []
  };

  Object.entries(data.비용).forEach(([계정, 금액]) => {
    if (계정.includes('광고선전비')) 비용그룹['광고선전비'].push([계정, 금액]);
    else if (계정.includes('복리후생비')) 비용그룹['복리후생비'].push([계정, 금액]);
    else if (계정.includes('서비스 운영비')) 비용그룹['서비스운영비'].push([계정, 금액]);
    else if (계정.includes('사업 운영비')) 비용그룹['사업운영비'].push([계정, 금액]);
    else 비용그룹['기타'].push([계정, 금액]);
  });

  // 광고선전비
  if (비용그룹['광고선전비'].length > 0) {
    const 광고비합계 = 비용그룹['광고선전비'].reduce((sum, [, v]) => sum + v, 0);
    rows.push(['    광고선전비', '', '1', 광고비합계, '']);
  }

  // 복리후생비
  if (비용그룹['복리후생비'].length > 0) {
    const 복리후생비합계 = 비용그룹['복리후생비'].reduce((sum, [, v]) => sum + v, 0);
    rows.push(['    복리후생비', '', '', 복리후생비합계, '']);
  }

  // 서비스운영비
  if (비용그룹['서비스운영비'].length > 0) {
    const 서비스운영비합계 = 비용그룹['서비스운영비'].reduce((sum, [, v]) => sum + v, 0);
    rows.push(['    서비스운영비', '', '2', 서비스운영비합계, '']);
  }

  // 사업운영비
  if (비용그룹['사업운영비'].length > 0) {
    const 사업운영비합계 = 비용그룹['사업운영비'].reduce((sum, [, v]) => sum + v, 0);
    rows.push(['    사업운영비', '', '', 사업운영비합계, '']);
  }

  // 기타
  비용그룹['기타'].forEach(([계정, 금액]) => {
    rows.push([`    ${계정}`, '', '', 금액, '']);
  });

  rows.push(['', '', '', '', '']);
  rows.push(['판매비와관리비 합계', '', '', data.총비용, '']);
  rows.push(['', '', '', '', '']);
  rows.push(['영업이익', '', '', 영업이익, '']);
  rows.push(['', '', '', '', '']);

  // IV. 영업외수익
  if (Object.keys(data.영업외수익).length > 0) {
    rows.push(['IV. 영업외수익', '', '', '', '']);
    Object.entries(data.영업외수익).forEach(([계정, 금액]) => {
      const name = 계정.replace('영업외수익 - ', '');
      rows.push([`    ${name}`, '', '', 금액, '']);
    });
    rows.push(['', '', '', '', '']);
    rows.push(['영업외수익 합계', '', '', data.총영업외수익, '']);
    rows.push(['', '', '', '', '']);
  }

  rows.push(['당기순이익', '', '', 당기순이익, '']);
  rows.push(['', '', '', '', '']);
  rows.push(['', '', '', '', '']);

  // ========================================
  // 재무상태표
  // ========================================
  rows.push(['재무상태표', '', '', '', '']);
  rows.push(['', '', '', '', '']);
  rows.push(['과목', '', '주석', '당기', '']);

  // 자산
  rows.push(['자  산', '', '', '', '']);
  rows.push(['', '', '', '', '']);
  rows.push(['I. 유동자산', '', '', '', '']);
  rows.push(['    현금및현금성자산', '', '3', data.최종잔액, '']);
  rows.push(['', '', '', '', '']);
  rows.push(['유동자산 합계', '', '', 유동자산합계, '']);
  rows.push(['', '', '', '', '']);

  if (보증금합계 > 0) {
    rows.push(['II. 비유동자산', '', '', '', '']);
    rows.push(['    보증금', '', '', 보증금합계, '']);
    rows.push(['', '', '', '', '']);
    rows.push(['비유동자산 합계', '', '', 보증금합계, '']);
    rows.push(['', '', '', '', '']);
  }

  rows.push(['자산총계', '', '', 유동자산합계 + 보증금합계, '']);
  rows.push(['', '', '', '', '']);
  rows.push(['', '', '', '', '']);

  // 부채
  rows.push(['부  채', '', '', '', '']);
  rows.push(['', '', '', '', '']);
  if (차입금합계 > 0) {
    rows.push(['I. 유동부채', '', '', '', '']);
    rows.push(['    차입금', '', '4', 차입금합계, '']);
    rows.push(['', '', '', '', '']);
    rows.push(['부채총계', '', '', 차입금합계, '']);
    rows.push(['', '', '', '', '']);
  }

  // 자본
  rows.push(['자  본', '', '', '', '']);
  rows.push(['', '', '', '', '']);
  rows.push(['I. 자본금', '', '5', 자본금합계, '']);
  rows.push(['II. 이익잉여금', '', '', 당기순이익, '']);
  rows.push(['', '', '', '', '']);
  rows.push(['자본총계', '', '', 자본금합계 + 당기순이익, '']);
  rows.push(['', '', '', '', '']);
  rows.push(['부채 및 자본 총계', '', '', 차입금합계 + 자본금합계 + 당기순이익, '']);
  rows.push(['', '', '', '', '']);
  rows.push(['', '', '', '', '']);

  // ========================================
  // 주석 (간단 버전)
  // ========================================
  rows.push(['주석', '', '', '', '']);
  rows.push(['', '', '', '', '']);
  rows.push(['1. 광고선전비', '', '', '', '']);
  비용그룹['광고선전비'].forEach(([계정, 금액]) => {
    const name = 계정.replace('광고선전비 - ', '');
    rows.push([`   - ${name}`, '', '', 금액, '']);
  });
  rows.push(['', '', '', '', '']);

  rows.push(['2. 서비스운영비', '', '', '', '']);
  비용그룹['서비스운영비'].forEach(([계정, 금액]) => {
    const name = 계정.replace('서비스 운영비 - ', '');
    rows.push([`   - ${name}`, '', '', 금액, '']);
  });
  rows.push(['', '', '', '', '']);

  rows.push(['3. 현금및현금성자산', '', '', '', '']);
  rows.push(['   - 기업은행 보통예금', '', '', data.최종잔액, '']);
  rows.push(['', '', '', '', '']);

  rows.push(['4. 차입금', '', '', '', '']);
  Object.entries(data.차입금).forEach(([계정, 금액]) => {
    const name = 계정.replace(/차입금상환 - |차입금 - /, '');
    rows.push([`   - ${name}`, '', '', 금액, '']);
  });
  rows.push(['', '', '', '', '']);

  rows.push(['5. 자본금', '', '', '', '']);
  Object.entries(data.자본금).sort((a, b) => a[0].localeCompare(b[0])).forEach(([계정, 금액]) => {
    const name = 계정.replace(/자본금 - |자본인출 - /, '');
    rows.push([`   - ${name}`, '', '', 금액, '']);
  });

  console.log('✅ 재무제표 생성 완료\n');
  return rows;
}

/**
 * 전문 포맷팅 적용
 */
async function writeProfessionalSheet(sheets, rows) {
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

  console.log('🎨 전문 포맷팅 적용 중...\n');

  const requests = [];

  // 1. 회사 헤더 병합 및 포맷팅
  requests.push({ mergeCells: { range: { sheetId, startRowIndex: 0, endRowIndex: 1, startColumnIndex: 0, endColumnIndex: 4 }, mergeType: 'MERGE_ALL' }});
  requests.push({ mergeCells: { range: { sheetId, startRowIndex: 1, endRowIndex: 2, startColumnIndex: 0, endColumnIndex: 4 }, mergeType: 'MERGE_ALL' }});
  requests.push({ mergeCells: { range: { sheetId, startRowIndex: 2, endRowIndex: 3, startColumnIndex: 0, endColumnIndex: 4 }, mergeType: 'MERGE_ALL' }});

  requests.push({
    repeatCell: {
      range: { sheetId, startRowIndex: 0, endRowIndex: 1 },
      cell: {
        userEnteredFormat: {
          backgroundColor: COLORS.HEADER_NAVY,
          textFormat: { foregroundColor: COLORS.WHITE, fontSize: 18, bold: true, fontFamily: 'Noto Sans KR' },
          horizontalAlignment: 'CENTER',
          verticalAlignment: 'MIDDLE'
        }
      },
      fields: 'userEnteredFormat'
    }
  });

  requests.push({
    repeatCell: {
      range: { sheetId, startRowIndex: 1, endRowIndex: 3 },
      cell: {
        userEnteredFormat: {
          backgroundColor: COLORS.SUBSECTION,
          textFormat: { fontSize: 12, bold: true, fontFamily: 'Noto Sans KR' },
          horizontalAlignment: 'CENTER'
        }
      },
      fields: 'userEnteredFormat'
    }
  });

  // 2. 컬럼 너비
  requests.push({ updateDimensionProperties: { range: { sheetId, dimension: 'COLUMNS', startIndex: 0, endIndex: 1 }, properties: { pixelSize: 300 }, fields: 'pixelSize' }});
  requests.push({ updateDimensionProperties: { range: { sheetId, dimension: 'COLUMNS', startIndex: 1, endIndex: 2 }, properties: { pixelSize: 80 }, fields: 'pixelSize' }});
  requests.push({ updateDimensionProperties: { range: { sheetId, dimension: 'COLUMNS', startIndex: 2, endIndex: 3 }, properties: { pixelSize: 60 }, fields: 'pixelSize' }});
  requests.push({ updateDimensionProperties: { range: { sheetId, dimension: 'COLUMNS', startIndex: 3, endIndex: 4 }, properties: { pixelSize: 150 }, fields: 'pixelSize' }});

  // 3. 행별 포맷팅
  rows.forEach((row, idx) => {
    const text = row[0] || '';

    // 주요 섹션 (손익계산서, 재무상태표)
    if (text === '손익계산서' || text === '재무상태표' || text === '주석') {
      requests.push({ mergeCells: { range: { sheetId, startRowIndex: idx, endRowIndex: idx + 1, startColumnIndex: 0, endColumnIndex: 4 }, mergeType: 'MERGE_ALL' }});
      requests.push({
        repeatCell: {
          range: { sheetId, startRowIndex: idx, endRowIndex: idx + 1 },
          cell: {
            userEnteredFormat: {
              backgroundColor: COLORS.SECTION_BLUE,
              textFormat: { foregroundColor: COLORS.WHITE, fontSize: 14, bold: true },
              horizontalAlignment: 'CENTER'
            }
          },
          fields: 'userEnteredFormat'
        }
      });
    }

    // 테이블 헤더 (과목, 주석, 당기)
    else if (text === '과목') {
      requests.push({
        repeatCell: {
          range: { sheetId, startRowIndex: idx, endRowIndex: idx + 1 },
          cell: {
            userEnteredFormat: {
              backgroundColor: COLORS.HEADER_GRAY,
              textFormat: { foregroundColor: COLORS.WHITE, bold: true },
              horizontalAlignment: 'CENTER',
              borders: {
                top: { style: 'SOLID_MEDIUM', width: 2 },
                bottom: { style: 'SOLID_MEDIUM', width: 2 }
              }
            }
          },
          fields: 'userEnteredFormat'
        }
      });
    }

    // 합계/총계 행
    else if (text.includes('합계') || text.includes('총계') || text === '영업이익' || text === '당기순이익' || text === '매출총이익') {
      requests.push({
        repeatCell: {
          range: { sheetId, startRowIndex: idx, endRowIndex: idx + 1 },
          cell: {
            userEnteredFormat: {
              backgroundColor: COLORS.TOTAL_YELLOW,
              textFormat: { bold: true },
              borders: {
                top: { style: 'SOLID', width: 1 },
                bottom: { style: 'DOUBLE', width: 3 }
              }
            }
          },
          fields: 'userEnteredFormat'
        }
      });
    }

    // 대분류 (I., II., III., 자산, 부채, 자본)
    else if (text.match(/^I\.|^II\.|^III\.|^자\s\s산|^부\s\s채|^자\s\s본/)) {
      requests.push({
        repeatCell: {
          range: { sheetId, startRowIndex: idx, endRowIndex: idx + 1 },
          cell: {
            userEnteredFormat: {
              backgroundColor: COLORS.SUBSECTION,
              textFormat: { bold: true, fontSize: 11 }
            }
          },
          fields: 'userEnteredFormat'
        }
      });
    }
  });

  // 4. 금액 컬럼 포맷팅 (D열)
  requests.push({
    repeatCell: {
      range: { sheetId, startColumnIndex: 3, endColumnIndex: 4 },
      cell: {
        userEnteredFormat: {
          numberFormat: { type: 'NUMBER', pattern: '#,##0' },
          horizontalAlignment: 'RIGHT'
        }
      },
      fields: 'userEnteredFormat(numberFormat,horizontalAlignment)'
    }
  });

  // 5. 주석 컬럼 중앙정렬
  requests.push({
    repeatCell: {
      range: { sheetId, startColumnIndex: 2, endColumnIndex: 3 },
      cell: {
        userEnteredFormat: {
          horizontalAlignment: 'CENTER',
          textFormat: { foregroundColor: COLORS.SECTION_BLUE, bold: true }
        }
      },
      fields: 'userEnteredFormat'
    }
  });

  // 포맷팅 적용
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
  const response = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
  const sheet = response.data.sheets.find(s => s.properties.title === sheetName);
  return sheet ? sheet.properties.sheetId : 0;
}

/**
 * 메인 함수
 */
async function main() {
  try {
    console.log('🚀 Nofee 재무제표 생성 시작 (v7 - Big 4 Accounting Firm Style)\n');
    console.log('='.repeat(70));
    console.log();

    const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));
    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: ['https://www.googleapis.com/auth/spreadsheets']
    });
    const sheets = google.sheets({ version: 'v4', auth });

    const transactions = await readClearSheet(sheets);
    const aggregatedData = aggregateData(transactions);
    const summaryRows = generateProfessionalStatement(aggregatedData);
    await writeProfessionalSheet(sheets, summaryRows);

    console.log('='.repeat(70));
    console.log('✨ 완료! 전문 회계법인 스타일 재무제표가 생성되었습니다.\n');
    console.log(`🔗 https://docs.google.com/spreadsheets/d/${SPREADSHEET_ID}/edit#gid=0`);
    console.log();

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

main();
