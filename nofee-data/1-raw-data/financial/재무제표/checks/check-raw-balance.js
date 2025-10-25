import { google } from 'googleapis';
import { resolve } from 'path';

const SPREADSHEET_ID = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';

async function checkRawBalance() {
  const keyFile = resolve('../../config/google_api_key.json');

  const auth = new google.auth.GoogleAuth({
    keyFile: keyFile,
    scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
  });

  const authClient = await auth.getClient();
  const sheets = google.sheets({ version: 'v4', auth: authClient });

  const response = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'raw_data!A1:G300',
  });

  const rows = response.data.values || [];

  console.log('raw_data 최종 10개 거래:\n');

  const lastRows = rows.slice(-11);
  lastRows.forEach((row, idx) => {
    console.log(`행 ${rows.length - 11 + idx + 1}: ${row.join(' | ')}`);
  });

  // 최종 잔액 찾기
  let lastBalance = 0;
  let lastDate = '';
  for (let i = rows.length - 1; i >= 0; i--) {
    const balance = rows[i][3];
    if (balance && !isNaN(parseFloat(balance.replace(/,/g, '')))) {
      lastBalance = parseFloat(balance.replace(/,/g, ''));
      lastDate = rows[i][0];
      console.log('\n최종 거래일: ' + lastDate);
      console.log('최종 잔액: ' + lastBalance.toLocaleString() + '원');
      break;
    }
  }
}

checkRawBalance().catch(console.error);
