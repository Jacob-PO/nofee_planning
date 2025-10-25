import { google } from 'googleapis';
import { resolve } from 'path';

const SPREADSHEET_ID = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';

async function checkExpenses() {
  const keyFile = resolve('../../config/google_api_key.json');
  const auth = new google.auth.GoogleAuth({
    keyFile: keyFile,
    scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
  });

  const authClient = await auth.getClient();
  const sheets = google.sheets({ version: 'v4', auth: authClient });

  // clear 시트에서 비용 데이터 가져오기
  const clearResp = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'clear!A1:H300',
  });

  const clearRows = clearResp.data.values || [];
  const header = clearRows[0];

  console.log('=== clear 시트 판매비와관리비 분석 ===\n');

  const expenses = {};
  let totalFromClear = 0;

  clearRows.slice(1).forEach((row, idx) => {
    const type = row[1] || ''; // 입금/출금
    const amount = parseFloat((row[2] || '0').replace(/,/g, ''));
    const category = row[7] || '';

    if (type === '출금' && category && !category.startsWith('매출') &&
        !category.startsWith('영업외') && !category.startsWith('차입금') &&
        !category.startsWith('보증금') && !category.startsWith('자본')) {

      if (!expenses[category]) {
        expenses[category] = { count: 0, total: 0, rows: [] };
      }
      expenses[category].count++;
      expenses[category].total += Math.abs(amount);
      expenses[category].rows.push(idx + 2);
      totalFromClear += Math.abs(amount);
    }
  });

  // 카테고리별 출력
  const sortedCategories = Object.entries(expenses).sort((a, b) => b[1].total - a[1].total);

  sortedCategories.forEach(([category, data]) => {
    console.log(`${category}: ${data.total.toLocaleString()}원 (${data.count}건)`);
  });

  console.log('\n=== clear 시트 판관비 합계 ===');
  console.log(`총 ${totalFromClear.toLocaleString()}원`);

  // Summary 시트에서 판관비 합계 가져오기
  const summaryResp = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'Summary!A1:B200',
  });

  const summaryRows = summaryResp.data.values || [];
  let summaryExpense = 0;

  summaryRows.forEach((row) => {
    if (row[0] === '판매비와관리비 합계') {
      summaryExpense = parseFloat((row[1] || '0').replace(/,/g, ''));
    }
  });

  console.log('\n=== Summary 시트 판관비 합계 ===');
  console.log(`${summaryExpense.toLocaleString()}원`);

  console.log('\n=== 차이 분석 ===');
  const diff = summaryExpense - totalFromClear;
  console.log(`Summary - clear = ${diff.toLocaleString()}원`);
  console.log(`김선호 개인 계약금 추가분: 1,000,000원`);

  if (diff === 1000000) {
    console.log('✅ 정확합니다! (개인 계약금 100만원만 추가됨)');
  } else {
    console.log('⚠️  차이가 100만원이 아닙니다!');
  }

  // Summary 상세 내역 확인
  console.log('\n=== Summary 판관비 상세 비교 ===');
  let inExpenseDetail = false;
  const summaryDetails = {};

  summaryRows.forEach((row) => {
    const label = row[0] || '';

    if (label === '[판매비와관리비 상세]') {
      inExpenseDetail = true;
      return;
    }

    if (inExpenseDetail) {
      if (label === '') {
        inExpenseDetail = false;
        return;
      }

      if (label.startsWith('  ')) {
        const category = label.trim();
        const amount = parseFloat((row[1] || '0').replace(/,/g, ''));
        summaryDetails[category] = amount;
      }
    }
  });

  console.log('\nSummary 상세 항목:');
  Object.entries(summaryDetails).sort((a, b) => b[1] - a[1]).forEach(([cat, amt]) => {
    const clearAmount = expenses[cat]?.total || 0;
    const match = Math.abs(clearAmount - amt) < 1;
    console.log(`${cat}: ${amt.toLocaleString()}원 ${match ? '✅' : '⚠️ clear=' + clearAmount.toLocaleString()}`);
  });
}

checkExpenses().catch(console.error);
