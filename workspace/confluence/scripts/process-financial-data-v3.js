#!/usr/bin/env node
import { google } from 'googleapis';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * 한국 재무제표 기준 계정과목 분류
 * raw_data -> clear(1차 정제) -> Summary(재무제표)
 */
async function main() {
  try {
    console.log('Google Sheets 재무 데이터 처리 시작...\n');

    const credentialsPath = path.resolve(__dirname, '../../../config/google_api_key.json');
    const credentials = JSON.parse(fs.readFileSync(credentialsPath, 'utf8'));

    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });

    const sheets = google.sheets({ version: 'v4', auth });
    const spreadsheetId = '14x_3ry6R9gNwvrmqLvnVEb8219fZ76B5h98eZrPcR64';

    // 1단계: raw_data 가져오기
    console.log('1단계: raw_data 시트 데이터 가져오는 중...');
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: 'raw_data!A1:Z1000',
    });

    const rows = response.data.values || [];
    if (rows.length === 0) {
      console.log('데이터가 없습니다.');
      return;
    }

    console.log(`   총 ${rows.length - 1}개 거래 내역 확인\n`);

    // 2단계: 거래 내역 분류 및 clear 시트 작성
    console.log('2단계: 거래 내역 분류 및 clear 시트 작성 중...');
    const categorizedData = categorizeTransactions(rows);
    await writeClearSheet(sheets, spreadsheetId, categorizedData);

    console.log(`   매출: ${categorizedData.revenue.length}건`);
    console.log(`   비용: ${categorizedData.expenses.length}건`);
    console.log(`   기타: ${categorizedData.others.length}건\n`);

    // 3단계: clear 시트 데이터 읽어오기
    console.log('3단계: clear 시트 데이터 읽어오는 중...');
    const clearResponse = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: 'clear!A1:Z1000',
    });

    const clearRows = clearResponse.data.values || [];
    console.log(`   ${clearRows.length - 1}개 정제된 데이터 확인\n`);

    // 4단계: Summary 시트에 재무제표 작성
    console.log('4단계: Summary 시트에 재무제표 작성 중...');
    await writeSummarySheet(sheets, spreadsheetId, categorizedData);

    console.log('\n✅ 재무 데이터 처리 완료!');
    console.log(`🔗 Clear 시트: https://docs.google.com/spreadsheets/d/${spreadsheetId}/edit#gid=clear`);
    console.log(`🔗 Summary 시트: https://docs.google.com/spreadsheets/d/${spreadsheetId}/edit#gid=Summary`);

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
    if (error.response?.data) {
      console.error('상세:', JSON.stringify(error.response.data, null, 2));
    }
    process.exit(1);
  }
}

/**
 * 거래 내역 분류 (한국 재무제표 기준)
 */
function categorizeTransactions(rows) {
  const headers = rows[0];
  const transactions = {
    revenue: [],    // 매출
    expenses: [],   // 비용
    others: [],     // 기타 (환불, 투자금 등)
  };

  const summary = {
    // 매출 (수익)
    totalRevenue: 0,
    categoryRevenue: {},

    // 비용
    totalExpenses: 0,
    categoryExpenses: {},

    // 기타
    totalOthers: 0,
    categoryOthers: {},

    // 기간
    startDate: null,
    endDate: null,
  };

  for (let i = 1; i < rows.length; i++) {
    const row = rows[i];
    if (!row || row.length === 0) continue;

    const transaction = {
      date: row[0] || '',          // 거래일시
      type: row[1] || '',          // 구분 (입금/출금)
      amount: parseAmount(row[2]), // 거래금액
      balance: parseAmount(row[3]), // 거래 후 잔액
      transType: row[4] || '',     // 거래구분
      description: row[5] || '',   // 내용
      memo: row[6] || '',          // 메모
    };

    // 금액이 0이면 스킵
    if (transaction.amount === 0) continue;

    // 거래 기간 업데이트 (시작일, 종료일) - 날짜만 추출 (시간 제외)
    if (transaction.date) {
      const dateOnly = transaction.date.split(' ')[0]; // "2025.09.03 10:12:08" -> "2025.09.03"
      if (!summary.startDate || dateOnly < summary.startDate) {
        summary.startDate = dateOnly;
      }
      if (!summary.endDate || dateOnly > summary.endDate) {
        summary.endDate = dateOnly;
      }
    }

    // 한국 재무제표 계정과목으로 분류
    const category = categorizeTransaction(transaction);

    // null이면 재무제표에서 제외 (AWS 테스트 거래 등)
    if (category === null) continue;

    transaction.category = category;

    // 계정과목 타입 결정
    const accountType = getAccountType(category);
    transaction.accountType = accountType;

    // 입금/출금에 따라 분류
    if (transaction.type === '입금') {
      if (accountType === '매출') {
        transactions.revenue.push(transaction);
        summary.totalRevenue += transaction.amount;

        if (!summary.categoryRevenue[category]) {
          summary.categoryRevenue[category] = 0;
        }
        summary.categoryRevenue[category] += transaction.amount;
      } else {
        transactions.others.push(transaction);
        summary.totalOthers += transaction.amount;

        if (!summary.categoryOthers[category]) {
          summary.categoryOthers[category] = 0;
        }
        summary.categoryOthers[category] += transaction.amount;
      }
    } else if (transaction.type === '출금') {
      const absAmount = Math.abs(transaction.amount);

      if (accountType === '비용') {
        transactions.expenses.push(transaction);
        summary.totalExpenses += absAmount;

        if (!summary.categoryExpenses[category]) {
          summary.categoryExpenses[category] = 0;
        }
        summary.categoryExpenses[category] += absAmount;
      } else {
        transactions.others.push(transaction);
        summary.totalOthers += absAmount;

        if (!summary.categoryOthers[category]) {
          summary.categoryOthers[category] = 0;
        }
        // 출금은 마이너스 값으로 저장 (현금흐름 계산을 위해)
        summary.categoryOthers[category] += transaction.amount; // 마이너스 값 그대로
      }
    }
  }

  transactions.summary = summary;
  return transactions;
}

/**
 * 이름 정규화 (동일인 통합)
 */
function normalizeName(name) {
  // 정동민(딘) -> 정동민
  if (name.includes('정동민')) {
    return '정동민';
  }
  // 노피 -> 이지애 -> 김선호
  if (name.includes('노피') || name.includes('이지애')) {
    return '김선호';
  }
  return name;
}

/**
 * 한국 재무제표 계정과목 분류
 */
function categorizeTransaction(transaction) {
  const desc = transaction.description.toLowerCase();
  let originalDesc = transaction.description;
  const transType = transaction.transType;

  // AWS 100원 테스트 거래 제외 (결제 테스트용)
  if (desc.includes('amazon') && desc.includes('aws') && Math.abs(transaction.amount) === 100) {
    return null;  // 재무제표에서 제외
  }

  // 이름 정규화
  originalDesc = normalizeName(originalDesc);

  // === 입금 (매출/영업외수익/자본거래) ===
  if (transaction.type === '입금') {
    // 특정 거래: 2025.06.18 노피 500,000원 -> 정동민 자본금
    if (transaction.date.startsWith('2025.06.18') &&
        desc.includes('노피') &&
        transaction.amount === 500000) {
      return '자본금 - 정동민';
    }

    // 특정 거래: 2025.06.16 김선호 9,950,000원 -> 차입금
    if (transaction.date.startsWith('2025.06.16') &&
        desc.includes('김선호') &&
        transaction.amount === 9950000) {
      return '차입금 - 김선호';
    }

    // 매출 (영업 수익)
    if (desc.includes('주식회사 유모바일') || desc.includes('유모바일')) {
      return '매출 - 유모바일';
    }
    if (desc.includes('티아이앤이')) {
      return '매출 - 티아이앤이';
    }
    if (desc.includes('해피넷')) {
      return '매출 - 해피넷';
    }
    if (desc.includes('폰샵')) {
      return '매출 - 폰샵';
    }
    if (desc.includes('그로우플러')) {
      return '매출 - 그로우플러';
    }
    if (desc.includes('폰슐랭')) {
      return '매출 - 폰슐랭';
    }
    if (desc.includes('이노스페이스')) {
      return '매출 - 이노스페이스';
    }

    // 영업외수익
    if (transType.includes('이자') || desc.includes('이자')) {
      return '영업외수익 - 이자수익';
    }
    if (transType.includes('캐시백') || desc.includes('캐시백')) {
      return '영업외수익 - 캐시백';
    }

    // 광고비 환불
    if (desc.includes('카카오') && (transaction.amount === 144762 || transaction.amount === 90000)) {
      return '영업외수익 - 광고비환불';
    }
    // 페이스북 광고비 환불 (2,874원)
    if ((desc.includes('facebk') || desc.includes('facebook')) && transaction.amount === 2874) {
      return '영업외수익 - 광고비환불';
    }

    // 박환성은 사무실 임대료 환급 (영업외수익)
    if (desc.includes('박환성')) {
      return '영업외수익 - 임대료환급';
    }

    // 자본금/투자금 (대표자 및 투자자만, 소액은 자본금)
    const representatives = ['송호빈', '정동민', '김선호', '이지애', '노피'];
    const trimmedDesc = originalDesc.replace(/\(.*?\)/g, '').trim();
    const amount = transaction.amount;

    // 김선호, 송호빈 차입금
    // 김선호: 995만원 + 5백만원 차입금 (총 1,495만원)
    // 송호빈: 1천만원 2건 (총 2천만원)
    if ((trimmedDesc.includes('김선호') && amount === 5000000) ||
        (trimmedDesc.includes('송호빈') && amount === 10000000)) {
      return '차입금 - ' + originalDesc;
    }

    if (representatives.some(rep => trimmedDesc.includes(rep))) {
      return '자본금 - ' + originalDesc;
    }

    // 다른 사람 이름이면 기타 수익
    if (isPersonName(originalDesc)) {
      return '기타 수익';
    }

    // 기타 매출
    return '기타 매출';
  }

  // === 출금 (판매비와관리비/영업외비용/자본거래) ===
  if (transaction.type === '출금') {
    // 광고선전비 (판매비)
    if (desc.includes('카카오') && desc.includes('광고')) {
      return '광고선전비 - 카카오';
    }
    if (desc.includes('facebook') || desc.includes('fb.me/ads') ||
        desc.includes('facebk') || desc.includes('meta')) {
      return '광고선전비 - 페이스북';
    }
    if (desc.includes('구글') || desc.includes('google')) {
      return '광고선전비 - 구글';
    }
    if (desc.includes('뽐뿌') || desc.includes('바이럴')) {
      return '광고선전비 - 바이럴마케팅';
    }
    if (desc.includes('카톡채널') || desc.includes('카카오채널')) {
      return '광고선전비 - 카카오채널';
    }

    // 복리후생비 - 식비
    if (desc.includes('향원각') || desc.includes('식사') || desc.includes('식당') ||
        desc.includes('롯데몰') || desc.includes('롯데쇼핑') || desc.includes('롯데슈') ||
        desc.includes('갓텐코리아') || desc.includes('갓텐') ||
        desc.includes('세븐일레븐') || desc.includes('양평해장국') ||
        desc.includes('맥도날드') || desc.includes('브루다') ||
        desc.includes('gs25') || desc.includes('두꺼비집') ||
        desc.includes('빙츄르')) {
      return '복리후생비 - 식비';
    }
    if (desc.includes('메가엠지씨') || desc.includes('카페') || desc.includes('커피')) {
      return '복리후생비 - 커피/음료';
    }
    if (desc.includes('데이앤나잇') || desc.includes('편의점')) {
      return '복리후생비 - 편의점';
    }

    // 대교통신은 장비/비품 (통신비보다 먼저 체크)
    if (desc.includes('대교통신')) {
      return '사업 운영비 - 장비/비품';
    }

    // 통신비 (관리비)
    if (desc.includes('통신') || desc.includes('헬로비전') ||
        desc.includes('인터넷') || desc.includes('케이블')) {
      return '통신비';
    }

    // 외주비
    if (desc.includes('디자이너') || desc.includes('사례비') ||
        desc.includes('외주') || desc.includes('프리랜서')) {
      return '외주비';
    }

    // 서비스 운영비 (일반관리비)
    if (desc.includes('amazon') || desc.includes('aws')) {
      return '서비스 운영비 - AWS';
    }
    if (desc.includes('anthropic')) {
      return '서비스 운영비 - Anthropic';
    }
    if (desc.includes('webflow')) {
      return '서비스 운영비 - Webflow';
    }
    if (desc.includes('ssl') && desc.includes('결제')) {
      return '서비스 운영비 - SSL';
    }

    // 사무실 관련
    if (desc.includes('사무실') || desc.includes('월세')) {
      const amount = Math.abs(transaction.amount);
      // 사무실보증금
      if (desc.includes('보증금')) {
        return '보증금 - 사무실';
      }
      // 사무실중개수수료, 월세 등
      return '사업 운영비 - 사무실';
    }
    if (desc.includes('보증보험료') || desc.includes('보험')) {
      return '사업 운영비 - 보험료';
    }
    if (desc.includes('신분증') || desc.includes('스캐너') ||
        desc.includes('공기청정기') || desc.includes('장비') ||
        desc.includes('다이소') || desc.includes('daiso')) {
      return '사업 운영비 - 장비/비품';
    }
    if (desc.includes('인증서') || desc.includes('범용인증')) {
      return '사업 운영비 - 인증서';
    }
    if (desc.includes('보증금') && desc.includes('이자')) {
      return '사업 운영비 - 보증금이자';
    }

    // 세금과공과 (관리비)
    if (transType.includes('공과금') || desc.includes('지로') ||
        desc.includes('지방세') || desc.includes('세금') ||
        desc.includes('서울등록')) {
      return '세금과공과';
    }

    // 교통비 (관리비)
    if (desc.includes('주유') || desc.includes('택시') ||
        desc.includes('버스') || desc.includes('지하철') ||
        desc.includes('주차') || desc.includes('시설관리공단')) {
      return '여비교통비';
    }

    // 사무용품비
    if (desc.includes('문구') || desc.includes('사무용품')) {
      return '사무용품비';
    }

    // 접대비
    if (desc.includes('카카오선물') || desc.includes('선물하기')) {
      return '접대비';
    }

    // 환불 (송호빈 자본금 조정)
    if (desc.includes('환불')) {
      return '자본인출 - 환불(자본금조정)';
    }

    // 카드 결제는 내용으로 재분류 시도, 실패시 기타
    if (transType.includes('카드')) {
      return '기타 비용';
    }

    // 일반 이체
    if (transType.includes('이체')) {
      const amount = Math.abs(transaction.amount);

      // 대표 이름이면 차입금 상환 또는 자본 인출
      const representatives = ['송호빈', '정동민', '김선호', '이지애'];
      const trimmedDesc = originalDesc.replace(/\(.*?\)/g, '').trim(); // (딘) 같은 괄호 제거

      if (representatives.some(rep => trimmedDesc.includes(rep))) {
        // 2025.07.02 김선호 10,000,000원 출금 -> 차입금 상환
        if (transaction.date.startsWith('2025.07.02') &&
            trimmedDesc.includes('김선호') &&
            amount === 10000000) {
          return '차입금상환 - 김선호';
        }

        // 송호빈, 김선호 1천만원 출금은 차입금 상환
        if ((trimmedDesc.includes('송호빈') || trimmedDesc.includes('김선호')) && amount === 10000000) {
          return '차입금상환 - ' + trimmedDesc;
        }
        return '자본인출 - ' + trimmedDesc;
      }

      // 네이버페이 27,800원은 장비/비품 (사람이름 체크 전에 먼저 확인)
      if (desc.includes('네이버페이') && amount === 27800) {
        return '사업 운영비 - 장비/비품';
      }

      // 조순남, 이미숙, 박옥자, 연동현 등은 사업 운영비 - 장비/비품
      const equipmentExpenseNames = ['조순남', '이미숙', '박옥자', '연동현'];
      if (equipmentExpenseNames.some(name => trimmedDesc.includes(name))) {
        return '사업 운영비 - 장비/비품';
      }

      // 개인에게 25,000원 또는 50,000원 이체는 차입금 이자비용
      // (단, 위에서 이미 분류된 경우 제외)
      if (isPersonName(originalDesc) && (amount === 25000 || amount === 50000)) {
        return '영업외비용 - 이자비용';
      }

      // 다른 사람 이름이면 급여/복리후생비
      if (isPersonName(originalDesc)) {
        return '복리후생비 - 기타';
      }

      // 네이버페이 등은 기타 비용
      return '기타 비용';
    }

    return '기타 비용';
  }

  return '미분류';
}

/**
 * 계정과목 타입 결정 (매출/비용/기타)
 */
function getAccountType(category) {
  if (category.startsWith('매출')) return '매출';
  if (category.startsWith('자본금') || category.startsWith('자본인출')) return '자본거래';
  if (category.startsWith('차입금')) return '차입금';
  if (category.startsWith('차입금상환')) return '차입금상환';
  if (category.startsWith('보증금')) return '보증금';
  if (category.startsWith('보증금반환')) return '보증금반환';
  if (category.startsWith('영업외수익') || (category.includes('환불') && category.startsWith('영업외'))) return '영업외수익';
  if (category.startsWith('영업외비용')) return '영업외비용';

  // 판매비와관리비
  if (category.startsWith('광고선전비') ||
      category.startsWith('복리후생비') ||
      category.startsWith('통신비') ||
      category.startsWith('외주비') ||
      category.startsWith('서비스 운영비') ||
      category.startsWith('사업 운영비') ||
      category.startsWith('세금과공과') ||
      category.startsWith('여비교통비') ||
      category.startsWith('사무용품비') ||
      category.startsWith('접대비')) {
    return '비용';
  }

  if (category.startsWith('기타 비용')) return '비용';
  if (category.startsWith('기타 매출')) return '매출';

  return '기타';
}

/**
 * 사람 이름인지 판단 (한글 2-4자)
 */
function isPersonName(str) {
  const koreanNamePattern = /^[가-힣]{2,4}$/;
  const trimmed = str.trim();

  // "정동민(딘)" 같은 경우 처리
  const nameMatch = trimmed.match(/^([가-힣]{2,4})/);
  if (nameMatch) {
    return koreanNamePattern.test(nameMatch[1]);
  }

  return koreanNamePattern.test(trimmed);
}

/**
 * 금액 파싱
 */
function parseAmount(value) {
  if (!value) return 0;
  const cleaned = String(value).replace(/[,원₩\s]/g, '');
  const number = parseFloat(cleaned);
  return isNaN(number) ? 0 : number;
}

/**
 * 숫자 포맷팅
 */
function formatNumber(num, forceSign = false) {
  const formatted = new Intl.NumberFormat('ko-KR').format(Math.abs(num));
  if (num < 0) {
    return '(' + formatted + ')';  // 음수는 괄호로 표시
  }
  if (forceSign && num > 0) {
    return '+' + formatted;
  }
  return formatted;
}

/**
 * clear 시트 작성 (1차 정제 데이터)
 */
async function writeClearSheet(sheets, spreadsheetId, transactions) {
  const { revenue, expenses, others } = transactions;

  // 모든 거래를 하나의 배열로 합치고 날짜순 정렬
  const allTransactions = [...revenue, ...expenses, ...others]
    .sort((a, b) => new Date(a.date) - new Date(b.date));

  const clearData = [
    ['거래일시', '구분', '거래금액', '거래 후 잔액', '거래구분', '내용', '메모', '계정과목', '계정타입'],
    ...allTransactions.map(t => [
      t.date,
      t.type,
      t.amount,
      t.balance,
      t.transType,
      t.description,
      t.memo,
      t.category,
      t.accountType
    ])
  ];

  // clear 시트 확인 및 생성
  try {
    const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId });
    const clearSheet = spreadsheet.data.sheets.find(
      s => s.properties.title === 'clear'
    );

    if (clearSheet) {
      await sheets.spreadsheets.values.clear({
        spreadsheetId,
        range: 'clear!A1:Z10000',
      });
    } else {
      // clear 시트 생성
      await sheets.spreadsheets.batchUpdate({
        spreadsheetId,
        resource: {
          requests: [{
            addSheet: {
              properties: {
                title: 'clear',
              },
            },
          }],
        },
      });
    }
  } catch (error) {
    console.error('clear 시트 준비 중 오류:', error.message);
  }

  // 데이터 작성
  await sheets.spreadsheets.values.update({
    spreadsheetId,
    range: 'clear!A1',
    valueInputOption: 'RAW',
    resource: {
      values: clearData,
    },
  });

  console.log('   ✅ clear 시트 업데이트 완료');
}

/**
 * Summary 시트 작성 (한국 재무제표 형식)
 */
async function writeSummarySheet(sheets, spreadsheetId, transactions) {
  const { summary } = transactions;

  // 매출 계정과목별 정렬
  const revenueSummary = Object.entries(summary.categoryRevenue)
    .sort((a, b) => b[1] - a[1])
    .map(([category, amount]) => [category, formatNumber(amount)]);

  // 김선호 개인 지출 1,000,000원은 2025.10.22에 회사 통장에서 정산 완료
  // 따라서 별도로 비용에 추가하지 않음

  // 비용 계정과목별 정렬 (대분류로 그룹화)
  const expensesByCategory = {};
  Object.entries(summary.categoryExpenses).forEach(([category, amount]) => {
    const mainCategory = category.split(' - ')[0]; // 대분류 추출
    if (!expensesByCategory[mainCategory]) {
      expensesByCategory[mainCategory] = [];
    }
    expensesByCategory[mainCategory].push([category, amount]);
  });

  // 비용 대분류별 합계 및 상세
  const expenseSummary = [];
  const expenseDetails = [];

  Object.entries(expensesByCategory).forEach(([mainCat, items]) => {
    const total = items.reduce((sum, [_, amt]) => sum + amt, 0);
    expenseSummary.push([mainCat, formatNumber(total)]);

    // 상세 내역
    items.sort((a, b) => b[1] - a[1]);
    items.forEach(([cat, amt]) => {
      expenseDetails.push(['  ' + cat, formatNumber(amt)]);
    });
  });

  expenseSummary.sort((a, b) => {
    const aNum = parseFloat(a[1].replace(/,/g, ''));
    const bNum = parseFloat(b[1].replace(/,/g, ''));
    return bNum - aNum;
  });

  // 영업외수익, 영업외비용, 차입금, 차입금상환, 보증금, 보증금반환, 자본거래 분리
  const nonOperatingIncome = {};
  const nonOperatingExpenses = {};
  const borrowings = {};
  const borrowingRepayments = {};
  const deposits = {};
  const depositReturns = {};
  const capitalTransactions = {};

  Object.entries(summary.categoryOthers).forEach(([category, amount]) => {
    if (category.startsWith('영업외수익')) {
      nonOperatingIncome[category] = amount;
    } else if (category.startsWith('영업외비용')) {
      nonOperatingExpenses[category] = amount;
    } else if (category.startsWith('차입금상환')) {
      borrowingRepayments[category] = amount;
    } else if (category.startsWith('차입금')) {
      borrowings[category] = amount;
    } else if (category.startsWith('보증금반환')) {
      depositReturns[category] = amount;
    } else if (category.startsWith('보증금')) {
      deposits[category] = amount;
    } else if (category.startsWith('자본금') || category.startsWith('자본인출')) {
      capitalTransactions[category] = amount;
    } else {
      nonOperatingIncome[category] = amount; // 기타는 영업외수익으로
    }
  });

  const nonOperatingIncomeSummary = Object.entries(nonOperatingIncome)
    .sort((a, b) => b[1] - a[1])
    .map(([category, amount]) => [category, formatNumber(amount)]);

  const nonOperatingExpensesSummary = Object.entries(nonOperatingExpenses)
    .sort((a, b) => b[1] - a[1])
    .map(([category, amount]) => [category, formatNumber(amount)]);

  const borrowingsSummary = Object.entries(borrowings)
    .sort((a, b) => b[1] - a[1])
    .map(([category, amount]) => [category, formatNumber(amount)]);

  const borrowingRepaymentsSummary = Object.entries(borrowingRepayments)
    .sort((a, b) => b[1] - a[1])
    .map(([category, amount]) => [category, formatNumber(Math.abs(amount))]);

  const depositsSummary = Object.entries(deposits)
    .sort((a, b) => b[1] - a[1])
    .map(([category, amount]) => [category, formatNumber(amount)]);

  const depositReturnsSummary = Object.entries(depositReturns)
    .sort((a, b) => b[1] - a[1])
    .map(([category, amount]) => [category, formatNumber(Math.abs(amount))]);

  // 환불을 송호빈 자본금에 반영
  const refundAmount = capitalTransactions['자본인출 - 환불(자본금조정)'] || 0;
  if (refundAmount !== 0 && capitalTransactions['자본금 - 송호빈']) {
    // 송호빈 자본금에서 환불 금액 차감 (refundAmount는 이미 음수)
    capitalTransactions['자본금 - 송호빈'] += refundAmount;
    // 환불 항목 제거
    delete capitalTransactions['자본인출 - 환불(자본금조정)'];
  }

  // 통장 잔액 계산용: 실제 통장에 들어온 자본금 (조정 전)
  const actualCapitalInForCash = Object.entries(capitalTransactions)
    .filter(([cat, _]) => cat.startsWith('자본금'))
    .reduce((sum, [_, amt]) => sum + amt, 0);

  // 김선호 자본금 조정 (Summary 표시용):
  // Clear 시트에서 집계된 김선호 자본금: 1,750,000원
  // 실제 자본금: 1,700,000원 (차입금 이득 5만원 제외)
  // 차입금 이득: 995만원 빌려줬는데 1,000만원 상환 받음 = 5만원 이득
  if (capitalTransactions['자본금 - 김선호']) {
    capitalTransactions['자본금 - 김선호'] = 1700000; // 170만원으로 고정
  }

  const capitalTransactionsSummary = Object.entries(capitalTransactions)
    .sort((a, b) => a[0].localeCompare(b[0], 'ko'))  // 가나다 순 정렬
    .map(([category, amount]) => [category, formatNumber(amount)]);

  // 영업외수익/비용 합계
  const totalNonOperatingIncome = Object.values(nonOperatingIncome).reduce((sum, amt) => sum + amt, 0);
  const totalNonOperatingExpenses = Object.values(nonOperatingExpenses).reduce((sum, amt) => sum + amt, 0);

  // 영업이익 계산 (김선호 개인 계약금 1,000,000원은 이미 summary.totalExpenses에 포함됨)
  const operatingIncome = summary.totalRevenue - summary.totalExpenses;
  // nonOperatingExpenses는 이미 음수이므로 더하기 (이중 부정)
  const netIncome = operatingIncome + totalNonOperatingIncome + totalNonOperatingExpenses;

  const summaryData = [
    ['Nofee 재무제표 (손익계산서)'],
    ['회계기간', `${summary.startDate || '시작일 미상'} ~ ${summary.endDate || '종료일 미상'}`],
    ['작성일자', new Date().toLocaleDateString('ko-KR')],
    [],
    ['=== I. 매출 ==='],
    ['계정과목', '금액 (원)'],
    ...revenueSummary,
    ['매출 합계', formatNumber(summary.totalRevenue)],
    [],
    ['=== II. 판매비와관리비 ==='],
    ['계정과목', '금액 (원)'],
    ...expenseSummary,
    [],
    ['[판매비와관리비 상세]'],
    ...expenseDetails,
    [],
    ['판매비와관리비 합계', formatNumber(summary.totalExpenses)],
    [],
    ['=== III. 영업손익 ==='],
    ['영업이익(손실)', formatNumber(operatingIncome)],
  ];

  summaryData.push(
    [],
    ['=== IV. 당기순손익 계산 ==='],
    ['계정', '금액 (원)'],
    ['매출', formatNumber(summary.totalRevenue)],
    ['(-) 판매비와관리비', formatNumber(summary.totalExpenses)],
    ['= 영업이익(손실)', formatNumber(operatingIncome)],
    ['(+) 영업외수익', formatNumber(totalNonOperatingIncome)],
    ['(-) 영업외비용', formatNumber(totalNonOperatingExpenses)],
    [],
    ['당기순이익(손실)', formatNumber(netIncome)]
  );

  // 영업외수익 상세가 있으면 추가
  if (nonOperatingIncomeSummary.length > 0) {
    summaryData.push(
      [],
      ['[영업외수익 상세]'],
      ...nonOperatingIncomeSummary
    );
  }

  // 영업외비용 상세가 있으면 추가
  if (nonOperatingExpensesSummary.length > 0) {
    summaryData.push(
      [],
      ['[영업외비용 상세]'],
      ...nonOperatingExpensesSummary
    );
  }

  summaryData.push(
    [],
    ['=== V. 재무비율 분석 ==='],
    ['비용/매출 비율', summary.totalRevenue > 0 ? `${((summary.totalExpenses / summary.totalRevenue) * 100).toFixed(2)}%` : 'N/A'],
    ['영업이익률', summary.totalRevenue > 0 ? `${((operatingIncome / summary.totalRevenue) * 100).toFixed(2)}%` : 'N/A'],
    ['당기순이익률', summary.totalRevenue > 0 ? `${((netIncome / summary.totalRevenue) * 100).toFixed(2)}%` : 'N/A']
  );

  // 차입금/보증금 섹션 (손익계산서 외)
  if (borrowingsSummary.length > 0 || borrowingRepaymentsSummary.length > 0 || depositsSummary.length > 0) {
    summaryData.push(
      [],
      ['=== VI. 차입금 및 자산 (손익계산서 외) ===']
    );

    if (borrowingsSummary.length > 0 || borrowingRepaymentsSummary.length > 0) {
      const totalBorrowings = Object.values(borrowings).reduce((sum, amt) => sum + amt, 0);
      const totalRepayments = Object.values(borrowingRepayments).reduce((sum, amt) => sum + Math.abs(amt), 0);
      const netBorrowings = totalBorrowings - totalRepayments;

      summaryData.push(
        ['[차입금]'],
        ...borrowingsSummary,
        ['차입금 합계', formatNumber(totalBorrowings)],
        []
      );

      if (borrowingRepaymentsSummary.length > 0) {
        summaryData.push(
          ['[차입금 상환]'],
          ...borrowingRepaymentsSummary,
          ['상환 합계', formatNumber(totalRepayments)],
          []
        );
      }

      summaryData.push(
        ['순차입금 (차입금 - 상환)', formatNumber(netBorrowings)],
        []
      );
    }

    if (depositsSummary.length > 0 || depositReturnsSummary.length > 0) {
      const totalDeposits = Object.values(deposits).reduce((sum, amt) => sum + Math.abs(amt), 0);
      const totalDepositReturns = Object.values(depositReturns).reduce((sum, amt) => sum + Math.abs(amt), 0);

      if (depositsSummary.length > 0) {
        summaryData.push(
          ['[보증금]'],
          ...depositsSummary,
          ['보증금 합계', formatNumber(totalDeposits)],
          []
        );
      }

      if (depositReturnsSummary.length > 0) {
        summaryData.push(
          ['[보증금 반환 (임시대여)]'],
          ...depositReturnsSummary,
          ['반환 합계', formatNumber(totalDepositReturns)]
        );
      }
    }
  }

  // 자본거래가 있으면 별도 섹션으로 추가
  if (capitalTransactionsSummary.length > 0) {
    const totalCapitalIn = Object.entries(capitalTransactions)
      .filter(([cat, _]) => cat.startsWith('자본금'))
      .reduce((sum, [_, amt]) => sum + amt, 0);

    const totalCapitalOut = Object.entries(capitalTransactions)
      .filter(([cat, _]) => cat.startsWith('자본인출'))
      .reduce((sum, [_, amt]) => sum + amt, 0);

    summaryData.push(
      [],
      ['=== VII. 자본변동 (손익계산서 외) ==='],
      ['구분', '금액 (원)'],
      ...capitalTransactionsSummary,
      [],
      ['자본금 입금 합계', formatNumber(totalCapitalIn)],
      ['자본인출 합계', formatNumber(Math.abs(totalCapitalOut))],
      ['순자본변동', formatNumber(totalCapitalIn - Math.abs(totalCapitalOut))]
    );
  }

  // 현금 흐름 요약 (통장 잔고 계산)
  const totalBorrowings = Object.values(borrowings).reduce((sum, amt) => sum + amt, 0);
  const totalRepayments = Object.values(borrowingRepayments).reduce((sum, amt) => sum + Math.abs(amt), 0);
  const totalDeposits = Object.values(deposits).reduce((sum, amt) => sum + Math.abs(amt), 0);
  const totalDepositReturns = Object.values(depositReturns).reduce((sum, amt) => sum + Math.abs(amt), 0);
  const totalCapitalIn = Object.entries(capitalTransactions)
    .filter(([cat, _]) => cat.startsWith('자본금'))
    .reduce((sum, [_, amt]) => sum + amt, 0);
  const totalCapitalOut = Object.entries(capitalTransactions)
    .filter(([cat, _]) => cat.startsWith('자본인출'))
    .reduce((sum, [_, amt]) => sum + Math.abs(amt), 0);

  // 보증금반환(+) - 보증금납부(-) = 순보증금 지출
  const netDeposits = totalDeposits - totalDepositReturns;

  // 통장 잔액 계산: 실제 통장에 들어온 자본금 사용
  const actualCashIncome = summary.totalRevenue - summary.totalExpenses + totalNonOperatingIncome + totalNonOperatingExpenses;

  const cashBalance = actualCapitalInForCash - totalCapitalOut + (totalBorrowings - totalRepayments) - netDeposits + actualCashIncome;

  summaryData.push(
    [],
    ['=== VIII. 현금 흐름 요약 ==='],
    ['항목', '금액 (원)'],
    [],
    ['[투자 및 차입]'],
    ['  자본금 투자', formatNumber(actualCapitalInForCash)],
    ['  차입금 (빌린 돈)', formatNumber(totalBorrowings)],
    ['  차입금 상환', formatNumber(-totalRepayments)],
    ['  자본인출', formatNumber(-totalCapitalOut)],
    [],
    ['[자산 증감]'],
    ['  보증금 지출 (자산 증가)', formatNumber(-netDeposits)],
    [],
    ['[영업 활동]'],
    ['  매출', formatNumber(summary.totalRevenue)],
    ['  비용 지출 (통장)', formatNumber(-summary.totalExpenses)],
    ['  영업외수익', formatNumber(totalNonOperatingIncome)],
    ['  = 통장 순손익', formatNumber(actualCashIncome)],
    [],
    ['[통장 잔액 계산]'],
    ['  기초 잔액', '0'],
    ['  순투자 (투자 - 인출)', formatNumber(totalCapitalIn - totalCapitalOut)],
    ['  순차입 (차입 - 상환)', formatNumber(totalBorrowings - totalRepayments)],
    ['  보증금 지출', formatNumber(-netDeposits)],
    ['  통장 순손익', formatNumber(actualCashIncome)],
    ['  차입금 이득 조정', formatNumber(actualCapitalInForCash - totalCapitalIn)],
    [],
    ['= 현재 통장 잔액', formatNumber(cashBalance)]
  );

  // summary 시트 확인 및 생성
  const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId });
  const summarySheet = spreadsheet.data.sheets.find(
    s => s.properties.title === 'summary'
  );

  if (!summarySheet) {
    // summary 시트 생성
    try {
      await sheets.spreadsheets.batchUpdate({
        spreadsheetId,
        resource: {
          requests: [{
            addSheet: {
              properties: {
                title: 'summary',
              },
            },
          }],
        },
      });
      console.log('   summary 시트 생성됨');
    } catch (error) {
      // 이미 존재하면 무시
      if (!error.message.includes('already exists')) {
        throw error;
      }
    }
  }

  // 기존 내용 완전히 삭제
  await sheets.spreadsheets.values.clear({
    spreadsheetId,
    range: 'summary!A:Z',
  });
  console.log('   Summary 시트 기존 내용 삭제됨');

  // 새로운 데이터 작성
  await sheets.spreadsheets.values.update({
    spreadsheetId,
    range: 'summary!A1',
    valueInputOption: 'RAW',
    resource: {
      values: summaryData,
    },
  });

  console.log('   ✅ Summary 시트 업데이트 완료');
}

/**
 * Summary 시트에 전문적인 포맷팅 적용 (비활성화됨)
 */
async function applyProfessionalFormatting_DISABLED(sheets, spreadsheetId, data) {
  const requests = [];
  const summarySheetId = await getSheetId(sheets, spreadsheetId, 'Summary');

  // 1. 전체 시트 기본 설정
  requests.push({
    updateSheetProperties: {
      properties: {
        sheetId: summarySheetId,
        gridProperties: {
          frozenRowCount: 0,
        },
      },
      fields: 'gridProperties.frozenRowCount',
    },
  });

  // 2. 열 너비 설정 (A열: 400px, B열: 150px)
  requests.push(
    {
      updateDimensionProperties: {
        range: {
          sheetId: summarySheetId,
          dimension: 'COLUMNS',
          startIndex: 0,
          endIndex: 1,
        },
        properties: {
          pixelSize: 400,
        },
        fields: 'pixelSize',
      },
    },
    {
      updateDimensionProperties: {
        range: {
          sheetId: summarySheetId,
          dimension: 'COLUMNS',
          startIndex: 1,
          endIndex: 2,
        },
        properties: {
          pixelSize: 150,
        },
        fields: 'pixelSize',
      },
    }
  );

  // 3. 문서 제목 포맷팅 (첫 줄) - 공식 문서 스타일
  requests.push({
    repeatCell: {
      range: {
        sheetId: summarySheetId,
        startRowIndex: 0,
        endRowIndex: 1,
        startColumnIndex: 0,
        endColumnIndex: 2,
      },
      cell: {
        userEnteredFormat: {
          backgroundColor: { red: 0.95, green: 0.95, blue: 0.95 },
          textFormat: {
            foregroundColor: { red: 0, green: 0, blue: 0 },
            fontSize: 16,
            bold: true,
          },
          horizontalAlignment: 'CENTER',
          verticalAlignment: 'MIDDLE',
          borders: {
            top: { style: 'SOLID_THICK', width: 3, color: { red: 0, green: 0, blue: 0 } },
            bottom: { style: 'SOLID_THICK', width: 3, color: { red: 0, green: 0, blue: 0 } },
            left: { style: 'SOLID', width: 1, color: { red: 0, green: 0, blue: 0 } },
            right: { style: 'SOLID', width: 1, color: { red: 0, green: 0, blue: 0 } },
          },
        },
      },
      fields: 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,borders)',
    },
  });

  // 4. 첫 줄 병합
  requests.push({
    mergeCells: {
      range: {
        sheetId: summarySheetId,
        startRowIndex: 0,
        endRowIndex: 1,
        startColumnIndex: 0,
        endColumnIndex: 2,
      },
      mergeType: 'MERGE_ALL',
    },
  });

  // 5. 작성일자 및 기준 데이터 행 (1-2행) 포맷팅
  requests.push({
    repeatCell: {
      range: {
        sheetId: summarySheetId,
        startRowIndex: 1,
        endRowIndex: 3,
        startColumnIndex: 0,
        endColumnIndex: 2,
      },
      cell: {
        userEnteredFormat: {
          backgroundColor: { red: 1, green: 1, blue: 1 },
          textFormat: {
            fontSize: 9,
            italic: true,
          },
          horizontalAlignment: 'LEFT',
          borders: {
            bottom: { style: 'SOLID', width: 1, color: { red: 0.7, green: 0.7, blue: 0.7 } },
          },
        },
      },
      fields: 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,borders)',
    },
  });

  // 6. 섹션 헤더 및 테이블 헤더 찾아서 포맷팅
  let currentRow = 0;
  for (let i = 0; i < data.length; i++) {
    const row = data[i];
    if (!row || !row[0]) {
      currentRow++;
      continue;
    }

    const cellValue = row[0];

    // 섹션 헤더 (===로 시작)
    if (cellValue.startsWith('===')) {
      // 섹션 헤더 - 공식 문서 스타일 (검정 텍스트, 흰색 배경, 테두리)
      requests.push({
        repeatCell: {
          range: {
            sheetId: summarySheetId,
            startRowIndex: currentRow,
            endRowIndex: currentRow + 1,
            startColumnIndex: 0,
            endColumnIndex: 2,
          },
          cell: {
            userEnteredFormat: {
              backgroundColor: { red: 0.9, green: 0.9, blue: 0.9 },
              textFormat: {
                foregroundColor: { red: 0, green: 0, blue: 0 },
                fontSize: 11,
                bold: true,
              },
              horizontalAlignment: 'LEFT',
              verticalAlignment: 'MIDDLE',
              borders: {
                top: { style: 'SOLID_MEDIUM', width: 2, color: { red: 0, green: 0, blue: 0 } },
                bottom: { style: 'SOLID', width: 1, color: { red: 0, green: 0, blue: 0 } },
                left: { style: 'SOLID', width: 1, color: { red: 0, green: 0, blue: 0 } },
                right: { style: 'SOLID', width: 1, color: { red: 0, green: 0, blue: 0 } },
              },
            },
          },
          fields: 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,borders)',
        },
      });

      // 병합
      requests.push({
        mergeCells: {
          range: {
            sheetId: summarySheetId,
            startRowIndex: currentRow,
            endRowIndex: currentRow + 1,
            startColumnIndex: 0,
            endColumnIndex: 2,
          },
          mergeType: 'MERGE_ALL',
        },
      });
    }
    // 서브섹션 헤더 ([로 시작)
    else if (cellValue.startsWith('[') && cellValue.endsWith(']')) {
      requests.push({
        repeatCell: {
          range: {
            sheetId: summarySheetId,
            startRowIndex: currentRow,
            endRowIndex: currentRow + 1,
            startColumnIndex: 0,
            endColumnIndex: 2,
          },
          cell: {
            userEnteredFormat: {
              backgroundColor: { red: 0.97, green: 0.97, blue: 0.97 },
              textFormat: {
                fontSize: 10,
                bold: true,
                italic: true,
              },
              horizontalAlignment: 'LEFT',
              borders: {
                top: { style: 'SOLID', width: 1, color: { red: 0.6, green: 0.6, blue: 0.6 } },
                bottom: { style: 'SOLID', width: 1, color: { red: 0.6, green: 0.6, blue: 0.6 } },
                left: { style: 'SOLID', width: 1, color: { red: 0.6, green: 0.6, blue: 0.6 } },
                right: { style: 'SOLID', width: 1, color: { red: 0.6, green: 0.6, blue: 0.6 } },
              },
            },
          },
          fields: 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,borders)',
        },
      });

      requests.push({
        mergeCells: {
          range: {
            sheetId: summarySheetId,
            startRowIndex: currentRow,
            endRowIndex: currentRow + 1,
            startColumnIndex: 0,
            endColumnIndex: 2,
          },
          mergeType: 'MERGE_ALL',
        },
      });
    }
    // 테이블 헤더
    else if (cellValue === '계정과목' || cellValue === '항목' || cellValue === '구분' || cellValue === '계정') {
      requests.push({
        repeatCell: {
          range: {
            sheetId: summarySheetId,
            startRowIndex: currentRow,
            endRowIndex: currentRow + 1,
            startColumnIndex: 0,
            endColumnIndex: 2,
          },
          cell: {
            userEnteredFormat: {
              backgroundColor: { red: 0.85, green: 0.85, blue: 0.85 },
              textFormat: {
                bold: true,
                fontSize: 9,
              },
              horizontalAlignment: 'CENTER',
              borders: {
                top: { style: 'SOLID', width: 1, color: { red: 0, green: 0, blue: 0 } },
                bottom: { style: 'SOLID_MEDIUM', width: 2, color: { red: 0, green: 0, blue: 0 } },
                left: { style: 'SOLID', width: 1, color: { red: 0, green: 0, blue: 0 } },
                right: { style: 'SOLID', width: 1, color: { red: 0, green: 0, blue: 0 } },
              },
            },
          },
          fields: 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,borders)',
        },
      });
    }
    // 합계 행
    else if (cellValue.includes('합계') || cellValue.includes('통장 잔액') || cellValue.startsWith('=')) {
      requests.push({
        repeatCell: {
          range: {
            sheetId: summarySheetId,
            startRowIndex: currentRow,
            endRowIndex: currentRow + 1,
            startColumnIndex: 0,
            endColumnIndex: 2,
          },
          cell: {
            userEnteredFormat: {
              backgroundColor: { red: 0.95, green: 0.95, blue: 0.95 },
              textFormat: {
                bold: true,
                fontSize: 10,
              },
              borders: {
                top: { style: 'DOUBLE', width: 3, color: { red: 0, green: 0, blue: 0 } },
                bottom: { style: 'DOUBLE', width: 3, color: { red: 0, green: 0, blue: 0 } },
                left: { style: 'SOLID', width: 1, color: { red: 0, green: 0, blue: 0 } },
                right: { style: 'SOLID', width: 1, color: { red: 0, green: 0, blue: 0 } },
              },
            },
          },
          fields: 'userEnteredFormat(backgroundColor,textFormat,borders)',
        },
      });
    }
    // 일반 데이터 행 (테이블 안)
    else if (i > 0 && data[i - 1] && (data[i - 1][0] === '계정과목' || data[i - 1][0] === '항목' || data[i - 1][0] === '구분' || data[i - 1][0] === '계정')) {
      // 테이블 데이터에 테두리 추가
      requests.push({
        repeatCell: {
          range: {
            sheetId: summarySheetId,
            startRowIndex: currentRow,
            endRowIndex: currentRow + 1,
            startColumnIndex: 0,
            endColumnIndex: 2,
          },
          cell: {
            userEnteredFormat: {
              borders: {
                left: { style: 'SOLID', width: 1 },
                right: { style: 'SOLID', width: 1 },
                bottom: { style: 'SOLID', width: 1 },
              },
            },
          },
          fields: 'userEnteredFormat.borders',
        },
      });

      // B열(금액) 오른쪽 정렬
      requests.push({
        repeatCell: {
          range: {
            sheetId: summarySheetId,
            startRowIndex: currentRow,
            endRowIndex: currentRow + 1,
            startColumnIndex: 1,
            endColumnIndex: 2,
          },
          cell: {
            userEnteredFormat: {
              horizontalAlignment: 'RIGHT',
            },
          },
          fields: 'userEnteredFormat.horizontalAlignment',
        },
      });
    }

    currentRow++;
  }

  // 7. 전체 시트 행 높이 조정
  requests.push({
    updateDimensionProperties: {
      range: {
        sheetId: summarySheetId,
        dimension: 'ROWS',
        startIndex: 0,
        endIndex: data.length,
      },
      properties: {
        pixelSize: 25,
      },
      fields: 'pixelSize',
    },
  });

  // 8. 제목 행 높이 크게
  requests.push({
    updateDimensionProperties: {
      range: {
        sheetId: summarySheetId,
        dimension: 'ROWS',
        startIndex: 0,
        endIndex: 1,
      },
      properties: {
        pixelSize: 50,
      },
      fields: 'pixelSize',
    },
  });

  // 포맷팅 일괄 적용
  await sheets.spreadsheets.batchUpdate({
    spreadsheetId,
    resource: { requests },
  });
}

/**
 * 시트 ID 가져오기
 */
async function getSheetId(sheets, spreadsheetId, sheetName) {
  const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId });
  const sheet = spreadsheet.data.sheets.find(
    s => s.properties.title.toLowerCase() === sheetName.toLowerCase()
  );
  return sheet ? sheet.properties.sheetId : 0;
}

main();
