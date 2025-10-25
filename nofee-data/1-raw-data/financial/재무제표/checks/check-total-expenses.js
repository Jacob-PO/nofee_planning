import { google } from 'googleapis';
import { resolve } from 'path';

const SPREADSHEET_ID = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';

async function check() {
  const keyFile = resolve('../../config/google_api_key.json');
  const auth = new google.auth.GoogleAuth({
    keyFile: keyFile,
    scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
  });

  const authClient = await auth.getClient();
  const sheets = google.sheets({ version: 'v4', auth: authClient });

  const clear = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'clear!A1:H300',
  });

  const rows = clear.data.values.slice(1);

  // summary 객체 재현
  const summary = {
    totalExpenses: 0,
    categoryExpenses: {},
  };

  rows.forEach((row) => {
    const type = row[1] || '';
    const amount = parseFloat((row[2] || '0').replace(/,/g, ''));
    const category = row[7] || '';

    if (type === '출금' && category && !category.startsWith('매출') &&
        !category.startsWith('영업외') && !category.startsWith('차입금') &&
        !category.startsWith('보증금') && !category.startsWith('자본')) {

      const absAmount = Math.abs(amount);
      summary.totalExpenses += absAmount;

      if (!summary.categoryExpenses[category]) {
        summary.categoryExpenses[category] = 0;
      }
      summary.categoryExpenses[category] += absAmount;
    }
  });

  console.log('clear 시트에서 계산한 totalExpenses: ' + summary.totalExpenses.toLocaleString() + '원');

  // 개인 계약금 추가
  summary.categoryExpenses['사업 운영비 - 사무실'] = (summary.categoryExpenses['사업 운영비 - 사무실'] || 0) + 1000000;
  summary.totalExpenses += 1000000;

  console.log('개인 계약금 추가 후: ' + summary.totalExpenses.toLocaleString() + '원');

  // Summary에서 가져온 값과 비교
  const summaryResp = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'Summary!A1:B200',
  });

  let summaryTotal = 0;
  summaryResp.data.values.forEach((row) => {
    if (row[0] === '판매비와관리비 합계') {
      summaryTotal = parseFloat((row[1] || '0').replace(/,/g, ''));
    }
  });

  console.log('Summary 시트 판관비 합계: ' + summaryTotal.toLocaleString() + '원');
  console.log('차이: ' + (summaryTotal - summary.totalExpenses).toLocaleString() + '원');
}

check().catch(console.error);
