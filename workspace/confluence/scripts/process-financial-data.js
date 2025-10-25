#!/usr/bin/env node
import { google } from 'googleapis';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Google Sheets 데이터를 가져와서 재무제표로 정제
 */
async function main() {
  try {
    console.log('Google Sheets 데이터를 가져오는 중...\n');

    // Google Service Account 인증
    const credentialsPath = path.resolve(__dirname, '../../../config/google_api_key.json');
    const credentials = JSON.parse(fs.readFileSync(credentialsPath, 'utf8'));

    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });

    const sheets = google.sheets({ version: 'v4', auth });
    const spreadsheetId = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';

    // 1. 모든 시트 목록 가져오기
    const spreadsheet = await sheets.spreadsheets.get({
      spreadsheetId,
    });

    console.log('📋 워크시트 목록:');
    spreadsheet.data.sheets.forEach((sheet, index) => {
      console.log(`  ${index + 1}. ${sheet.properties.title} (ID: ${sheet.properties.sheetId})`);
    });

    // 2. 각 시트의 데이터 가져오기
    console.log('\n데이터를 분석하는 중...\n');

    const allData = {};
    for (const sheet of spreadsheet.data.sheets) {
      const sheetName = sheet.properties.title;

      try {
        const response = await sheets.spreadsheets.values.get({
          spreadsheetId,
          range: `${sheetName}!A1:Z1000`,
        });

        allData[sheetName] = response.data.values || [];
        console.log(`✅ ${sheetName}: ${allData[sheetName].length}행 데이터`);
      } catch (error) {
        console.log(`⚠️  ${sheetName}: 데이터 읽기 실패`);
      }
    }

    // 3. 데이터 정제 및 재무제표 형태로 변환
    console.log('\n재무제표 형태로 데이터 변환 중...\n');

    const financialData = processFinancialData(allData);

    // 4. Summary 시트에 기록
    console.log('Summary 워크시트에 데이터 작성 중...\n');

    await writeSummarySheet(sheets, spreadsheetId, financialData);

    console.log('\n✅ 재무 데이터 정제 및 Summary 시트 업데이트 완료!');
    console.log(`🔗 Google Sheets: https://docs.google.com/spreadsheets/d/${spreadsheetId}/edit`);

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
    if (error.response?.data) {
      console.error('상세 정보:', JSON.stringify(error.response.data, null, 2));
    }
    process.exit(1);
  }
}

/**
 * 원본 데이터를 재무제표 형태로 변환
 */
function processFinancialData(allData) {
  const financial = {
    assets: [],
    liabilities: [],
    equity: [],
    revenue: [],
    expenses: [],
    summary: {
      totalAssets: 0,
      totalLiabilities: 0,
      totalEquity: 0,
      totalRevenue: 0,
      totalExpenses: 0,
      netIncome: 0,
    }
  };

  // 각 시트의 데이터를 분석하여 재무제표 항목으로 분류
  for (const [sheetName, rows] of Object.entries(allData)) {
    if (rows.length === 0) continue;

    console.log(`분석 중: ${sheetName}`);

    // 첫 행을 헤더로 간주
    const headers = rows[0] || [];

    // 데이터 행들을 처리
    for (let i = 1; i < rows.length; i++) {
      const row = rows[i];
      if (!row || row.length === 0) continue;

      const item = {
        sheetName,
        rowIndex: i + 1,
        data: {},
      };

      // 각 열의 데이터를 헤더와 매칭
      headers.forEach((header, colIndex) => {
        if (row[colIndex]) {
          item.data[header] = row[colIndex];
        }
      });

      // 금액 데이터가 있는 경우 분류 (예시 로직 - 실제 데이터에 맞게 조정 필요)
      const amount = extractAmount(item.data);
      if (amount !== null) {
        // 간단한 키워드 기반 분류
        const itemName = Object.values(item.data).join(' ').toLowerCase();

        if (itemName.includes('자산') || itemName.includes('asset')) {
          financial.assets.push({ ...item.data, amount });
          financial.summary.totalAssets += amount;
        } else if (itemName.includes('부채') || itemName.includes('liability')) {
          financial.liabilities.push({ ...item.data, amount });
          financial.summary.totalLiabilities += amount;
        } else if (itemName.includes('자본') || itemName.includes('equity')) {
          financial.equity.push({ ...item.data, amount });
          financial.summary.totalEquity += amount;
        } else if (itemName.includes('수익') || itemName.includes('매출') || itemName.includes('revenue')) {
          financial.revenue.push({ ...item.data, amount });
          financial.summary.totalRevenue += amount;
        } else if (itemName.includes('비용') || itemName.includes('expense') || itemName.includes('cost')) {
          financial.expenses.push({ ...item.data, amount });
          financial.summary.totalExpenses += amount;
        }
      }
    }
  }

  // 순이익 계산
  financial.summary.netIncome = financial.summary.totalRevenue - financial.summary.totalExpenses;

  return financial;
}

/**
 * 데이터에서 금액 추출
 */
function extractAmount(data) {
  // 다양한 형태의 금액 데이터 추출 시도
  for (const value of Object.values(data)) {
    if (typeof value === 'string') {
      // 숫자 + 원, 콤마 제거
      const cleaned = value.replace(/[,원₩\s]/g, '');
      const number = parseFloat(cleaned);
      if (!isNaN(number) && number !== 0) {
        return number;
      }
    } else if (typeof value === 'number') {
      return value;
    }
  }
  return null;
}

/**
 * Summary 시트에 재무제표 작성
 */
async function writeSummarySheet(sheets, spreadsheetId, financialData) {
  const summaryData = [
    ['NoFee 재무제표 요약'],
    ['생성일시', new Date().toLocaleString('ko-KR')],
    [],
    ['구분', '항목', '금액 (원)'],
    [],
    ['자산'],
    ...financialData.assets.map(item => ['', getItemName(item), formatNumber(item.amount)]),
    ['', '자산 합계', formatNumber(financialData.summary.totalAssets)],
    [],
    ['부채'],
    ...financialData.liabilities.map(item => ['', getItemName(item), formatNumber(item.amount)]),
    ['', '부채 합계', formatNumber(financialData.summary.totalLiabilities)],
    [],
    ['자본'],
    ...financialData.equity.map(item => ['', getItemName(item), formatNumber(item.amount)]),
    ['', '자본 합계', formatNumber(financialData.summary.totalEquity)],
    [],
    ['수익'],
    ...financialData.revenue.map(item => ['', getItemName(item), formatNumber(item.amount)]),
    ['', '수익 합계', formatNumber(financialData.summary.totalRevenue)],
    [],
    ['비용'],
    ...financialData.expenses.map(item => ['', getItemName(item), formatNumber(item.amount)]),
    ['', '비용 합계', formatNumber(financialData.summary.totalExpenses)],
    [],
    ['순이익', '', formatNumber(financialData.summary.netIncome)],
    [],
    ['요약'],
    ['총 자산', formatNumber(financialData.summary.totalAssets)],
    ['총 부채', formatNumber(financialData.summary.totalLiabilities)],
    ['총 자본', formatNumber(financialData.summary.totalEquity)],
    ['총 수익', formatNumber(financialData.summary.totalRevenue)],
    ['총 비용', formatNumber(financialData.summary.totalExpenses)],
    ['순이익', formatNumber(financialData.summary.netIncome)],
  ];

  // Summary 시트 확인 및 생성
  try {
    await sheets.spreadsheets.values.clear({
      spreadsheetId,
      range: 'Summary!A1:Z1000',
    });
  } catch (error) {
    // Summary 시트가 없으면 생성
    await sheets.spreadsheets.batchUpdate({
      spreadsheetId,
      resource: {
        requests: [
          {
            addSheet: {
              properties: {
                title: 'Summary',
              },
            },
          },
        ],
      },
    });
  }

  // 데이터 작성
  await sheets.spreadsheets.values.update({
    spreadsheetId,
    range: 'Summary!A1',
    valueInputOption: 'RAW',
    resource: {
      values: summaryData,
    },
  });

  console.log('✅ Summary 시트 업데이트 완료');
}

/**
 * 항목 이름 추출
 */
function getItemName(item) {
  // 첫 번째 의미있는 값을 항목명으로 사용
  for (const [key, value] of Object.entries(item)) {
    if (key !== 'amount' && value && typeof value === 'string') {
      return value;
    }
  }
  return '기타';
}

/**
 * 숫자 포맷팅
 */
function formatNumber(num) {
  return new Intl.NumberFormat('ko-KR').format(num);
}

main();
