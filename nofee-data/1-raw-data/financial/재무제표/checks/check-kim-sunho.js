import { google } from 'googleapis';
import { resolve } from 'path';

const SPREADSHEET_ID = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';

async function checkKimSunho() {
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

  console.log('김선호 관련 거래 내역:\n');

  let capitalIn = 0;
  let capitalOut = 0;
  let borrowingIn = 0;
  let borrowingOut = 0;

  rows.forEach((row, idx) => {
    const desc = row[6] || '';
    const category = row[7] || '';

    if (desc.includes('김선호') || category.includes('김선호') ||
        desc.includes('노피') || desc.includes('이지애')) {
      console.log(`행 ${idx + 1}: ${row.join(' | ')}`);

      const amount = parseFloat((row[2] || '0').replace(/,/g, ''));
      if (category.includes('자본금')) {
        if (amount > 0) capitalIn += amount;
        else capitalOut += amount;
      } else if (category.includes('차입금상환')) {
        borrowingOut += Math.abs(amount);
      } else if (category.includes('차입금')) {
        borrowingIn += amount;
      }
    }
  });

  console.log('\n=== 김선호 거래 요약 ===');
  console.log(`자본금 입금: ${capitalIn.toLocaleString()}원`);
  console.log(`자본금 출금: ${capitalOut.toLocaleString()}원`);
  console.log(`차입금 입금: ${borrowingIn.toLocaleString()}원`);
  console.log(`차입금 상환: ${borrowingOut.toLocaleString()}원`);
  console.log(`순 차입금: ${(borrowingIn - borrowingOut).toLocaleString()}원`);
}

checkKimSunho().catch(console.error);
