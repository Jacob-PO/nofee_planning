const { google } = require('googleapis');
const path = require('path');
const fs = require('fs');

const CREDENTIALS_PATH = path.resolve(__dirname, '../../../config/google_api_key.json');
const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));

const auth = new google.auth.GoogleAuth({
  credentials,
  scopes: ['https://www.googleapis.com/auth/spreadsheets']
});

const SPREADSHEET_ID = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';

(async () => {
  try {
    const sheets = google.sheets({ version: 'v4', auth: await auth.getClient() });

    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: SPREADSHEET_ID,
      range: 'clear!A:I'
    });

    const rows = response.data.values;

    console.log('김선호 출금 거래 찾기 (정산 가능성)');
    console.log('='.repeat(80));
    console.log('');

    rows.forEach((row, idx) => {
      if (idx === 0) return;

      const 구분 = row[1] || '';
      const 금액 = row[2] || '';
      const 내용 = row[5] || '';
      const 계정과목 = row[7] || '';

      // 출금이고 김선호 관련
      if (구분 === '출금' && 내용.includes('김선호')) {
        console.log(`[${idx}] ${row[0]} | ${금액} | ${내용} | ${계정과목}`);
      }
    });

  } catch (error) {
    console.error('오류:', error.message);
  }
})();
