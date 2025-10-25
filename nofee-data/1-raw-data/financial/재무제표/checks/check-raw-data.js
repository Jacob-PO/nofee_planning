import { google } from 'googleapis';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config({ path: resolve(__dirname, '../../../config/confluence.env') });

const SPREADSHEET_ID = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';

async function checkRawData() {
  const keyFile = resolve(__dirname, '../../../config/google_api_key.json');

  const auth = new google.auth.GoogleAuth({
    keyFile: keyFile,
    scopes: ['https://www.googleapis.com/auth/spreadsheets'],
  });

  const authClient = await auth.getClient();
  const sheets = google.sheets({ version: 'v4', auth: authClient });

  const response = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'raw_data!A1:D10',
  });

  const data = response.data.values || [];

  console.log('raw_data 시트 데이터 (처음 10행):');
  console.log(`총 ${data.length}개 행\n`);

  data.forEach((row, idx) => {
    console.log(`${idx + 1}: ${row.join(' | ')}`);
  });
}

checkRawData().catch(console.error);
