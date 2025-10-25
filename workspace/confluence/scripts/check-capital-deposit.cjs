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

    console.log('Clear 시트 58번 행 확인');
    console.log('='.repeat(80));
    console.log('');

    // 헤더
    console.log('[헤더]');
    console.log(rows[0].join(' | '));
    console.log('');

    // 58번 행 (인덱스 58)
    console.log('[58번 행]');
    const row58 = rows[58];
    if (row58) {
      rows[0].forEach((header, idx) => {
        console.log(`  ${header}: ${row58[idx] || ''}`);
      });
    } else {
      console.log('58번 행이 없습니다.');
    }

  } catch (error) {
    console.error('오류:', error.message);
  }
})();
