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

    console.log('김선호 9,950,000원 거래 찾기');
    console.log('='.repeat(80));
    console.log('');

    rows.forEach((row, idx) => {
      if (idx === 0) return;

      const 금액 = row[2] || '';
      const 내용 = row[5] || '';

      if (금액.includes('9950000') || 금액.includes('9,950,000')) {
        console.log(`[${idx}번 행]`);
        rows[0].forEach((header, i) => {
          console.log(`  ${header}: ${row[i] || ''}`);
        });
        console.log('');
      }
    });

  } catch (error) {
    console.error('오류:', error.message);
  }
})();
