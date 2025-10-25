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
      range: 'raw_data!A:G'
    });

    const rows = response.data.values;

    console.log('Raw_data 70번 행 확인 (김선호 995만원)');
    console.log('='.repeat(80));
    console.log('');

    console.log('[헤더]');
    console.log(rows[0].join(' | '));
    console.log('');

    console.log('[70번 행]');
    const row70 = rows[70];
    if (row70) {
      rows[0].forEach((header, idx) => {
        console.log(`  ${header}: ${row70[idx] || ''}`);
      });
    } else {
      console.log('70번 행이 없습니다.');
    }

  } catch (error) {
    console.error('오류:', error.message);
  }
})();
