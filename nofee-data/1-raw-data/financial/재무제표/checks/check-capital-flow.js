import { google } from 'googleapis';
import { resolve } from 'path';

const SPREADSHEET_ID = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';

async function checkCapitalFlow() {
  const keyFile = resolve('../../config/google_api_key.json');

  const auth = new google.auth.GoogleAuth({
    keyFile: keyFile,
    scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
  });

  const authClient = await auth.getClient();
  const sheets = google.sheets({ version: 'v4', auth: authClient });

  const response = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'clear!A1:H300',
  });

  const rows = response.data.values || [];

  console.log('2025.06.16 ~ 2025.07.02 사이 거래:\n');

  rows.forEach((row, idx) => {
    const date = row[0] || '';

    if (date >= '2025.06.16' && date <= '2025.07.05') {
      console.log(`행 ${idx + 1}: ${row.join(' | ')}`);
    }
  });

  console.log('\n\n9,000,000원 또는 544,500원 거래:\n');
  rows.forEach((row, idx) => {
    const amount = row[2] || '';

    if (amount.includes('9000000') || amount.includes('-9000000') ||
        amount.includes('544500') || amount.includes('-544500')) {
      console.log(`행 ${idx + 1}: ${row.join(' | ')}`);
    }
  });
}

checkCapitalFlow().catch(console.error);
