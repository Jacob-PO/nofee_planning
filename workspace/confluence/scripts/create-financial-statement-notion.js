import NotionClient from '../lib/notion-client.js';
import { google } from 'googleapis';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config({ path: resolve(__dirname, '../../../config/confluence.env') });

// Google Sheets 설정
const SPREADSHEET_ID = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';
const PARENT_PAGE_ID = process.env.NOTION_PARENT_PAGE_ID || '2941d254-f808-8019-aba3-fe6126e89874';

/**
 * Google Sheets API 인증
 */
async function getGoogleSheetsClient() {
  const keyFile = resolve(__dirname, '../../../config/google_api_key.json');

  const auth = new google.auth.GoogleAuth({
    keyFile: keyFile,
    scopes: ['https://www.googleapis.com/auth/spreadsheets'],
  });

  const authClient = await auth.getClient();
  return google.sheets({ version: 'v4', auth: authClient });
}

/**
 * Summary 시트 데이터 가져오기
 */
async function getSummaryData() {
  const sheets = await getGoogleSheetsClient();

  const response = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'Summary!A1:B500',
  });

  return response.data.values || [];
}

/**
 * 전문적인 재무제표 블록 생성
 */
function createProfessionalFinancialStatement(summaryData) {
  const blocks = [];
  const notion = new NotionClient();

  // 데이터 파싱
  const parsed = parseFinancialData(summaryData);

  // 1. 문서 헤더 (회사명, 보고서 제목, 기준일)
  blocks.push({
    object: 'block',
    type: 'heading_1',
    heading_1: {
      rich_text: [{
        type: 'text',
        text: { content: '손 익 계 산 서' },
        annotations: { bold: true }
      }],
      color: 'default',
    },
  });

  blocks.push(notion.createParagraph(''));

  // 회사 정보
  blocks.push({
    object: 'block',
    type: 'paragraph',
    paragraph: {
      rich_text: [
        { type: 'text', text: { content: '회사명: ' }, annotations: { bold: true } },
        { type: 'text', text: { content: '(주)노피' } }
      ],
    },
  });

  blocks.push({
    object: 'block',
    type: 'paragraph',
    paragraph: {
      rich_text: [
        { type: 'text', text: { content: '보고기간: ' }, annotations: { bold: true } },
        { type: 'text', text: { content: `${parsed.date} 기준` } }
      ],
    },
  });

  blocks.push({
    object: 'block',
    type: 'paragraph',
    paragraph: {
      rich_text: [
        { type: 'text', text: { content: '단위: ' }, annotations: { bold: true } },
        { type: 'text', text: { content: '원' } }
      ],
    },
  });

  blocks.push(notion.createDivider());
  blocks.push(notion.createParagraph(''));

  // 2. 손익계산서 본문
  blocks.push({
    object: 'block',
    type: 'heading_2',
    heading_2: {
      rich_text: [{
        type: 'text',
        text: { content: 'I. 손익계산서' },
        annotations: { bold: true }
      }],
    },
  });

  // 매출
  if (parsed.revenue.length > 0) {
    blocks.push(...createFinancialTable('1. 매출', parsed.revenue, parsed.totalRevenue));
  }

  // 판매비와관리비
  if (parsed.expensesSummary.length > 0) {
    blocks.push(...createFinancialTable('2. 판매비와관리비', parsed.expensesSummary, parsed.totalExpenses, true));

    // 상세 내역
    if (parsed.expensesDetail.length > 0) {
      blocks.push({
        object: 'block',
        type: 'toggle',
        toggle: {
          rich_text: [{ type: 'text', text: { content: '   [판매비와관리비 상세 내역]' } }],
          children: [createDetailTable(parsed.expensesDetail)],
        },
      });
    }
  }

  // 영업손익
  blocks.push(createSummaryRow('3. 영업이익(손실)', parsed.operatingIncome));

  // 영업외손익
  if (parsed.nonOperatingIncome.length > 0) {
    blocks.push(...createFinancialTable('4. 영업외수익', parsed.nonOperatingIncome, parsed.totalNonOperatingIncome));
  }

  if (parsed.nonOperatingExpenses.length > 0) {
    blocks.push(...createFinancialTable('5. 영업외비용', parsed.nonOperatingExpenses, parsed.totalNonOperatingExpenses));
  }

  // 당기순손익 계산
  blocks.push(notion.createParagraph(''));
  blocks.push({
    object: 'block',
    type: 'heading_3',
    heading_3: {
      rich_text: [{
        type: 'text',
        text: { content: '6. 당기순손익 계산' },
        annotations: { bold: true }
      }],
    },
  });

  blocks.push(createCalculationTable([
    ['매출', parsed.totalRevenue],
    ['(-) 판매비와관리비', `-${parsed.totalExpenses}`],
    ['= 영업이익(손실)', parsed.operatingIncome],
    ['(+) 영업외수익', parsed.totalNonOperatingIncome],
    ['(-) 영업외비용', parsed.totalNonOperatingExpenses],
    ['', ''],
    ['당기순이익(손실)', parsed.netIncome],
  ]));

  // 재무비율
  blocks.push(notion.createParagraph(''));
  blocks.push({
    object: 'block',
    type: 'heading_3',
    heading_3: {
      rich_text: [{
        type: 'text',
        text: { content: '7. 재무비율 분석' },
        annotations: { bold: true }
      }],
    },
  });

  blocks.push(createRatioTable(parsed.ratios));

  // 3. 재무상태 (차입금, 자본금)
  blocks.push(notion.createParagraph(''));
  blocks.push(notion.createDivider());
  blocks.push({
    object: 'block',
    type: 'heading_2',
    heading_2: {
      rich_text: [{
        type: 'text',
        text: { content: 'II. 재무상태' },
        annotations: { bold: true }
      }],
    },
  });

  // 차입금
  if (parsed.borrowings.length > 0) {
    blocks.push(...createFinancialTable('1. 차입금 및 자산', parsed.borrowings, null));
  }

  // 자본금
  if (parsed.capital.length > 0) {
    blocks.push(...createFinancialTable('2. 자본변동', parsed.capital, parsed.totalCapital));
  }

  // 4. 현금흐름표
  blocks.push(notion.createParagraph(''));
  blocks.push(notion.createDivider());
  blocks.push({
    object: 'block',
    type: 'heading_2',
    heading_2: {
      rich_text: [{
        type: 'text',
        text: { content: 'III. 현금흐름표' },
        annotations: { bold: true }
      }],
    },
  });

  blocks.push(createCashFlowTable(parsed.cashFlow));

  // 5. 주석 및 작성자 정보
  blocks.push(notion.createParagraph(''));
  blocks.push(notion.createDivider());
  blocks.push({
    object: 'block',
    type: 'paragraph',
    paragraph: {
      rich_text: [
        { type: 'text', text: { content: '본 재무제표는 회계원칙에 따라 작성되었습니다.' }, annotations: { italic: true } }
      ],
    },
  });

  blocks.push({
    object: 'block',
    type: 'paragraph',
    paragraph: {
      rich_text: [
        { type: 'text', text: { content: `작성일: ${new Date().toLocaleDateString('ko-KR')}` }, annotations: { italic: true } }
      ],
    },
  });

  return blocks;
}

/**
 * 재무 데이터 파싱
 */
function parseFinancialData(data) {
  const result = {
    date: '',
    revenue: [],
    totalRevenue: '0',
    expensesSummary: [],
    expensesDetail: [],
    totalExpenses: '0',
    operatingIncome: '0',
    nonOperatingIncome: [],
    totalNonOperatingIncome: '0',
    nonOperatingExpenses: [],
    totalNonOperatingExpenses: '0',
    netIncome: '0',
    ratios: [],
    borrowings: [],
    capital: [],
    totalCapital: '0',
    cashFlow: [],
  };

  let section = null;
  let isDetailSection = false;

  for (let i = 0; i < data.length; i++) {
    const [col1, col2] = data[i] || [];

    if (!col1) continue;

    // 날짜 추출
    if (i === 1 && col1 === '작성일자') {
      result.date = col2;
      continue;
    }

    // 섹션 구분
    if (col1.includes('=== I. 매출 ===')) {
      section = 'revenue';
      continue;
    } else if (col1.includes('=== II. 판매비와관리비 ===')) {
      section = 'expenses';
      isDetailSection = false;
      continue;
    } else if (col1.includes('[판매비와관리비 상세]')) {
      isDetailSection = true;
      continue;
    } else if (col1.includes('=== III. 영업손익 ===')) {
      section = 'operating';
      continue;
    } else if (col1.includes('=== IV. 당기순손익 계산 ===')) {
      section = 'netincome';
      continue;
    } else if (col1.includes('[영업외수익 상세]')) {
      section = 'nonopincome';
      continue;
    } else if (col1.includes('[영업외비용 상세]')) {
      section = 'nonopexpense';
      continue;
    } else if (col1.includes('=== V. 재무비율 분석 ===')) {
      section = 'ratios';
      continue;
    } else if (col1.includes('=== VI. 차입금')) {
      section = 'borrowings';
      continue;
    } else if (col1.includes('=== VII. 자본변동')) {
      section = 'capital';
      continue;
    } else if (col1.includes('=== VIII. 현금 흐름')) {
      section = 'cashflow';
      continue;
    }

    // 데이터 수집
    if (section === 'revenue') {
      if (col1.startsWith('매출 - ')) {
        result.revenue.push([col1.replace('매출 - ', ''), col2]);
      } else if (col1 === '매출 합계') {
        result.totalRevenue = col2;
      }
    } else if (section === 'expenses') {
      if (col1 === '계정과목' || col1 === '금액 (원)') continue;

      if (isDetailSection) {
        if (!col1.startsWith('[') && col1 !== '판매비와관리비 합계') {
          result.expensesDetail.push([col1, col2]);
        }
      } else {
        if (col1 === '판매비와관리비 합계') {
          result.totalExpenses = col2;
        } else {
          result.expensesSummary.push([col1, col2]);
        }
      }
    } else if (section === 'operating') {
      if (col1 === '영업이익(손실)') {
        result.operatingIncome = col2;
      }
    } else if (section === 'netincome') {
      if (col1 === '당기순이익(손실)') {
        result.netIncome = col2;
      }
    } else if (section === 'nonopincome') {
      result.nonOperatingIncome.push([col1, col2]);
      if (col1.includes('합계')) {
        result.totalNonOperatingIncome = col2;
      }
    } else if (section === 'nonopexpense') {
      result.nonOperatingExpenses.push([col1, col2]);
      if (col1.includes('합계')) {
        result.totalNonOperatingExpenses = col2;
      }
    } else if (section === 'ratios') {
      if (col1 && col2) {
        result.ratios.push([col1, col2]);
      }
    } else if (section === 'borrowings') {
      if (!col1.startsWith('[') && !col1.startsWith('===') && col1 !== '계정과목') {
        result.borrowings.push([col1, col2]);
      }
    } else if (section === 'capital') {
      if (col1 === '구분' || col1 === '금액 (원)') continue;
      if (col1 === '순자본변동') {
        result.totalCapital = col2;
      } else {
        result.capital.push([col1, col2]);
      }
    } else if (section === 'cashflow') {
      if (!col1.startsWith('[') && col1 !== '항목' && col1 !== '금액 (원)') {
        result.cashFlow.push([col1, col2]);
      }
    }
  }

  return result;
}

/**
 * 재무 테이블 생성 (제목 포함)
 */
function createFinancialTable(title, data, total = null, showDetail = false) {
  const blocks = [];

  // 제목 추가
  blocks.push({
    object: 'block',
    type: 'heading_3',
    heading_3: {
      rich_text: [{
        type: 'text',
        text: { content: title },
        annotations: { bold: true }
      }],
    },
  });

  const rows = [['계정과목', '금액 (원)']];

  data.forEach(([label, value]) => {
    rows.push([label, value || '']);
  });

  if (total) {
    rows.push(['합계', total]);
  }

  blocks.push({
    object: 'block',
    type: 'table',
    table: {
      table_width: 2,
      has_column_header: true,
      has_row_header: false,
      children: rows.map((row, idx) => ({
        type: 'table_row',
        table_row: {
          cells: row.map(cell => [{
            type: 'text',
            text: { content: cell },
            annotations: idx === 0 || idx === rows.length - 1 ? { bold: true } : { bold: false }
          }])
        }
      }))
    }
  });

  return blocks;
}

/**
 * 상세 테이블 생성
 */
function createDetailTable(data) {
  const rows = data.map(([label, value]) => [label, value]);

  return {
    object: 'block',
    type: 'table',
    table: {
      table_width: 2,
      has_column_header: false,
      has_row_header: false,
      children: rows.map(row => ({
        type: 'table_row',
        table_row: {
          cells: row.map(cell => [{
            type: 'text',
            text: { content: cell || '' }
          }])
        }
      }))
    }
  };
}

/**
 * 계산 테이블 생성
 */
function createCalculationTable(data) {
  return {
    object: 'block',
    type: 'table',
    table: {
      table_width: 2,
      has_column_header: false,
      has_row_header: false,
      children: data.map((row, idx) => ({
        type: 'table_row',
        table_row: {
          cells: row.map((cell, cellIdx) => {
            const annotations = {
              bold: row[0] === '당기순이익(손실)' || row[0].startsWith('=')
            };

            // code annotation은 boolean이어야 함
            if (cellIdx === 1 && cell && cell.includes('(')) {
              annotations.code = true;
            }

            return [{
              type: 'text',
              text: { content: cell || '' },
              annotations
            }];
          })
        }
      }))
    }
  };
}

/**
 * 비율 테이블 생성
 */
function createRatioTable(ratios) {
  const rows = [['지표', '비율']];
  ratios.forEach(([label, value]) => {
    rows.push([label, value]);
  });

  return {
    object: 'block',
    type: 'table',
    table: {
      table_width: 2,
      has_column_header: true,
      has_row_header: false,
      children: rows.map((row, idx) => ({
        type: 'table_row',
        table_row: {
          cells: row.map(cell => [{
            type: 'text',
            text: { content: cell },
            annotations: { bold: idx === 0 }
          }])
        }
      }))
    }
  };
}

/**
 * 현금흐름 테이블 생성
 */
function createCashFlowTable(data) {
  return {
    object: 'block',
    type: 'table',
    table: {
      table_width: 2,
      has_column_header: false,
      has_row_header: false,
      children: data.map((row) => ({
        type: 'table_row',
        table_row: {
          cells: row.map((cell, idx) => [{
            type: 'text',
            text: { content: cell || '' },
            annotations: {
              bold: cell.startsWith('=') || cell.includes('현재 통장') || cell.includes('활동]') || cell.includes('증감]') || cell.includes('차입]')
            }
          }])
        }
      }))
    }
  };
}

/**
 * 요약 행 생성
 */
function createSummaryRow(label, value) {
  const valueAnnotations = { bold: false };
  if (value && value.includes('(')) {
    valueAnnotations.code = true;
  }

  return {
    object: 'block',
    type: 'paragraph',
    paragraph: {
      rich_text: [
        { type: 'text', text: { content: label + ': ' }, annotations: { bold: true } },
        { type: 'text', text: { content: value || '' }, annotations: valueAnnotations }
      ],
    },
  };
}

/**
 * Notion에 재무제표 페이지 생성
 */
async function createFinancialStatementPage() {
  console.log('NoFee 재무제표 Notion 페이지 생성 시작...\n');

  try {
    console.log('1. Google Sheets에서 Summary 데이터 가져오는 중...');
    const summaryData = await getSummaryData();
    console.log(`   ${summaryData.length}개 행 데이터 로드 완료\n`);

    console.log('2. Notion API 연결 중...');
    const notion = new NotionClient();
    console.log('   Notion API 연결 완료\n');

    console.log('3. 재무제표 블록 생성 중...');
    const blocks = createProfessionalFinancialStatement(summaryData);
    console.log(`   ${blocks.length}개 블록 생성 완료\n`);

    console.log('4. Notion 페이지 생성 중...');
    const today = new Date().toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });

    const page = await notion.client.pages.create({
      parent: {
        type: 'page_id',
        page_id: PARENT_PAGE_ID,
      },
      properties: {
        title: [
          {
            type: 'text',
            text: {
              content: `재무제표(손익계산서)_${today.replace(/\. /g, '.')}`,
            },
          },
        ],
      },
      children: blocks,
    });

    console.log('   Notion 페이지 생성 완료\n');
    console.log('재무제표 Notion 페이지 생성 완료!');
    console.log(`페이지 URL: https://notion.so/${page.id.replace(/-/g, '')}`);

    return page;
  } catch (error) {
    console.error('오류 발생:', error.message);
    if (error.body) {
      console.error('상세 오류:', JSON.stringify(error.body, null, 2));
    }
    throw error;
  }
}

// 스크립트 실행
createFinancialStatementPage().catch(console.error);
