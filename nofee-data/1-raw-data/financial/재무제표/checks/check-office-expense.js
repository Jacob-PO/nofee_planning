import { google } from 'googleapis';
import { resolve } from 'path';

const SPREADSHEET_ID = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';

async function checkOfficeExpense() {
  const keyFile = resolve('../../config/google_api_key.json');

  const auth = new google.auth.GoogleAuth({
    keyFile: keyFile,
    scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
  });

  const authClient = await auth.getClient();
  const sheets = google.sheets({ version: 'v4', auth: authClient });

  // clear 시트에서 사무실 관련 비용 확인
  const response = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'clear!A1:H300',
  });

  const rows = response.data.values || [];

  console.log('사무실 관련 비용 확인:\n');

  let total = 0;
  rows.forEach((row, idx) => {
    const category = row[7] || '';
    const amount = row[2] || '';

    if (category.includes('사무실')) {
      console.log(`행 ${idx + 1}: ${row.join(' | ')}`);
      const numAmount = Math.abs(parseFloat(amount.replace(/,/g, '')) || 0);
      total += numAmount;
    }
  });

  console.log('\n총 사무실 비용 (clear): ' + total.toLocaleString() + '원');
  console.log('\n개인 계약금 추가: 1,000,000원');
  console.log('예상 총합: ' + (total + 1000000).toLocaleString() + '원');
}

checkOfficeExpense().catch(console.error);
