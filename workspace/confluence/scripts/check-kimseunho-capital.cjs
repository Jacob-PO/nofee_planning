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

    console.log('김선호 자본금 거래 확인');
    console.log('='.repeat(80));
    console.log('');

    let total = 0;

    rows.forEach((row, idx) => {
      if (idx === 0) return;

      const 계정과목 = row[7] || '';
      const 금액 = parseInt(row[2]?.replace(/,/g, '') || 0);

      if (계정과목.includes('자본금') && 계정과목.includes('김선호')) {
        console.log(`[${idx}] ${row[0]} | ${row[2]} | ${계정과목} | ${row[5]}`);
        total += 금액;
      }
    });

    console.log('');
    console.log('='.repeat(80));
    console.log(`김선호 자본금 합계: ${total.toLocaleString()}원`);

  } catch (error) {
    console.error('오류:', error.message);
  }
})();
