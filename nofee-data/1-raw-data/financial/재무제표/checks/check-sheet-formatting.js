import { google } from 'googleapis';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config({ path: resolve(__dirname, '../../../config/confluence.env') });

const SPREADSHEET_ID = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';

async function checkFormatting() {
  const keyFile = resolve(__dirname, '../../../config/google_api_key.json');

  const auth = new google.auth.GoogleAuth({
    keyFile: keyFile,
    scopes: ['https://www.googleapis.com/auth/spreadsheets'],
  });

  const authClient = await auth.getClient();
  const sheets = google.sheets({ version: 'v4', auth: authClient });

  // Summary 시트 정보 가져오기
  const spreadsheet = await sheets.spreadsheets.get({
    spreadsheetId: SPREADSHEET_ID,
    ranges: ['Summary!A1:B10'],
    includeGridData: true,
  });

  console.log('Summary 시트 포맷팅 확인:\n');

  const summarySheet = spreadsheet.data.sheets.find(
    s => s.properties.title === 'Summary'
  );

  if (!summarySheet) {
    console.log('Summary 시트를 찾을 수 없습니다.');
    return;
  }

  console.log(`시트 ID: ${summarySheet.properties.sheetId}`);
  console.log(`Grid 속성:`, summarySheet.properties.gridProperties);

  if (summarySheet.data && summarySheet.data[0]) {
    const rows = summarySheet.data[0].rowData;
    console.log(`\n첫 10행 포맷팅:\n`);

    rows.forEach((row, idx) => {
      if (row.values && row.values[0]) {
        const cell = row.values[0];
        console.log(`행 ${idx + 1}:`);
        console.log(`  값: ${cell.formattedValue || '(비어있음)'}`);
        if (cell.userEnteredFormat) {
          console.log(`  배경색:`, cell.userEnteredFormat.backgroundColor);
          console.log(`  텍스트:`, cell.userEnteredFormat.textFormat);
        } else {
          console.log(`  포맷팅 없음`);
        }
      }
    });
  }
}

checkFormatting().catch(console.error);
