#!/usr/bin/env node
/**
 * 노피 GA 데이터 수집 스크립트
 * Google Analytics Data API를 사용하여 상세한 성과 데이터 수집
 */

import { BetaAnalyticsDataClient } from '@google-analytics/data';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 설정
const PROPERTY_ID = '474694872'; // 노피 GA4 속성 ID
const CREDENTIALS_PATH = path.resolve(__dirname, '../../config/google_api_key.json');
const OUTPUT_DIR = path.resolve(__dirname, '../nofee-data');

// 날짜 포맷 함수
function formatDate(date) {
  return date.toISOString().split('T')[0];
}

// 전체 데이터 수집을 위한 날짜 범위 설정
const today = new Date();
const startDate = new Date('2020-01-01'); // GA4 시작 가능 최소 날짜부터 전체 데이터 수집

async function collectGAData() {
  try {
    console.log('🚀 노피 GA 데이터 수집 시작\n');
    console.log('='.repeat(70));

    // Google Analytics Data API 클라이언트 초기화
    const analyticsDataClient = new BetaAnalyticsDataClient({
      keyFilename: CREDENTIALS_PATH,
    });

    const allData = {
      collectedAt: new Date().toISOString(),
      period: {
        start: formatDate(startDate),
        end: formatDate(today),
      },
      data: {}
    };

    // 1. 전체 사용자 및 세션 데이터
    console.log('\n📊 1. 전체 사용자 및 세션 데이터 수집 중...');
    const [overviewResponse] = await analyticsDataClient.runReport({
      property: `properties/${PROPERTY_ID}`,
      dateRanges: [
        {
          startDate: formatDate(startDate),
          endDate: formatDate(today),
        },
      ],
      dimensions: [
        { name: 'date' },
      ],
      metrics: [
        { name: 'activeUsers' },
        { name: 'newUsers' },
        { name: 'sessions' },
        { name: 'sessionsPerUser' },
        { name: 'screenPageViews' },
        { name: 'averageSessionDuration' },
        { name: 'bounceRate' },
      ],
    });

    allData.data.dailyOverview = overviewResponse.rows.map(row => ({
      date: row.dimensionValues[0].value,
      activeUsers: parseInt(row.metricValues[0].value),
      newUsers: parseInt(row.metricValues[1].value),
      sessions: parseInt(row.metricValues[2].value),
      sessionsPerUser: parseFloat(row.metricValues[3].value),
      pageViews: parseInt(row.metricValues[4].value),
      avgSessionDuration: parseFloat(row.metricValues[5].value),
      bounceRate: parseFloat(row.metricValues[6].value),
    }));

    console.log(`   ✅ ${allData.data.dailyOverview.length}일치 데이터 수집 완료`);

    // 2. 페이지별 조회수
    console.log('\n📄 2. 페이지별 조회수 수집 중...');
    const [pageViewsResponse] = await analyticsDataClient.runReport({
      property: `properties/${PROPERTY_ID}`,
      dateRanges: [
        {
          startDate: formatDate(startDate),
          endDate: formatDate(today),
        },
      ],
      dimensions: [
        { name: 'pagePath' },
        { name: 'pageTitle' },
      ],
      metrics: [
        { name: 'screenPageViews' },
        { name: 'averageSessionDuration' },
        { name: 'bounceRate' },
      ],
      orderBys: [
        {
          metric: { metricName: 'screenPageViews' },
          desc: true,
        },
      ],
      limit: 100,
    });

    allData.data.topPages = pageViewsResponse.rows.map(row => ({
      path: row.dimensionValues[0].value,
      title: row.dimensionValues[1].value,
      pageViews: parseInt(row.metricValues[0].value),
      avgSessionDuration: parseFloat(row.metricValues[1].value),
      bounceRate: parseFloat(row.metricValues[2].value),
    }));

    console.log(`   ✅ ${allData.data.topPages.length}개 페이지 데이터 수집 완료`);

    // 3. 트래픽 소스
    console.log('\n🔗 3. 트래픽 소스 수집 중...');
    const [trafficSourceResponse] = await analyticsDataClient.runReport({
      property: `properties/${PROPERTY_ID}`,
      dateRanges: [
        {
          startDate: formatDate(startDate),
          endDate: formatDate(today),
        },
      ],
      dimensions: [
        { name: 'sessionSource' },
        { name: 'sessionMedium' },
      ],
      metrics: [
        { name: 'sessions' },
        { name: 'activeUsers' },
        { name: 'newUsers' },
      ],
      orderBys: [
        {
          metric: { metricName: 'sessions' },
          desc: true,
        },
      ],
    });

    allData.data.trafficSources = trafficSourceResponse.rows.map(row => ({
      source: row.dimensionValues[0].value,
      medium: row.dimensionValues[1].value,
      sessions: parseInt(row.metricValues[0].value),
      activeUsers: parseInt(row.metricValues[1].value),
      newUsers: parseInt(row.metricValues[2].value),
    }));

    console.log(`   ✅ ${allData.data.trafficSources.length}개 소스 데이터 수집 완료`);

    // 4. 디바이스 정보
    console.log('\n📱 4. 디바이스별 데이터 수집 중...');
    const [deviceResponse] = await analyticsDataClient.runReport({
      property: `properties/${PROPERTY_ID}`,
      dateRanges: [
        {
          startDate: formatDate(startDate),
          endDate: formatDate(today),
        },
      ],
      dimensions: [
        { name: 'deviceCategory' },
      ],
      metrics: [
        { name: 'activeUsers' },
        { name: 'sessions' },
        { name: 'screenPageViews' },
      ],
    });

    allData.data.devices = deviceResponse.rows.map(row => ({
      category: row.dimensionValues[0].value,
      activeUsers: parseInt(row.metricValues[0].value),
      sessions: parseInt(row.metricValues[1].value),
      pageViews: parseInt(row.metricValues[2].value),
    }));

    console.log(`   ✅ ${allData.data.devices.length}개 디바이스 카테고리 수집 완료`);

    // 5. 이벤트 데이터
    console.log('\n🎯 5. 이벤트 데이터 수집 중...');
    const [eventsResponse] = await analyticsDataClient.runReport({
      property: `properties/${PROPERTY_ID}`,
      dateRanges: [
        {
          startDate: formatDate(startDate),
          endDate: formatDate(today),
        },
      ],
      dimensions: [
        { name: 'eventName' },
      ],
      metrics: [
        { name: 'eventCount' },
        { name: 'eventCountPerUser' },
      ],
      orderBys: [
        {
          metric: { metricName: 'eventCount' },
          desc: true,
        },
      ],
      limit: 50,
    });

    allData.data.events = eventsResponse.rows.map(row => ({
      name: row.dimensionValues[0].value,
      count: parseInt(row.metricValues[0].value),
      countPerUser: parseFloat(row.metricValues[1].value),
    }));

    console.log(`   ✅ ${allData.data.events.length}개 이벤트 수집 완료`);

    // 6. 지역 정보
    console.log('\n🌏 6. 지역별 데이터 수집 중...');
    const [locationResponse] = await analyticsDataClient.runReport({
      property: `properties/${PROPERTY_ID}`,
      dateRanges: [
        {
          startDate: formatDate(startDate),
          endDate: formatDate(today),
        },
      ],
      dimensions: [
        { name: 'city' },
        { name: 'country' },
      ],
      metrics: [
        { name: 'activeUsers' },
        { name: 'sessions' },
      ],
      orderBys: [
        {
          metric: { metricName: 'activeUsers' },
          desc: true,
        },
      ],
      limit: 50,
    });

    allData.data.locations = locationResponse.rows.map(row => ({
      city: row.dimensionValues[0].value,
      country: row.dimensionValues[1].value,
      activeUsers: parseInt(row.metricValues[0].value),
      sessions: parseInt(row.metricValues[1].value),
    }));

    console.log(`   ✅ ${allData.data.locations.length}개 지역 데이터 수집 완료`);

    // 7. 요약 통계
    console.log('\n📈 7. 요약 통계 계산 중...');
    allData.summary = {
      totalActiveUsers: allData.data.dailyOverview.reduce((sum, day) => sum + day.activeUsers, 0),
      totalSessions: allData.data.dailyOverview.reduce((sum, day) => sum + day.sessions, 0),
      totalPageViews: allData.data.dailyOverview.reduce((sum, day) => sum + day.pageViews, 0),
      avgDailyUsers: Math.round(allData.data.dailyOverview.reduce((sum, day) => sum + day.activeUsers, 0) / allData.data.dailyOverview.length),
      avgSessionDuration: allData.data.dailyOverview.reduce((sum, day) => sum + day.avgSessionDuration, 0) / allData.data.dailyOverview.length,
      avgBounceRate: allData.data.dailyOverview.reduce((sum, day) => sum + day.bounceRate, 0) / allData.data.dailyOverview.length,
    };

    console.log('   ✅ 요약 통계 계산 완료');

    // 데이터 저장
    console.log('\n💾 데이터 저장 중...');
    if (!fs.existsSync(OUTPUT_DIR)) {
      fs.mkdirSync(OUTPUT_DIR, { recursive: true });
    }

    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `ga-data-${timestamp}.json`;
    const filepath = path.join(OUTPUT_DIR, filename);

    fs.writeFileSync(filepath, JSON.stringify(allData, null, 2), 'utf8');

    console.log(`   ✅ 파일 저장 완료: ${filename}`);

    // 최신 데이터로 심볼릭 링크 생성
    const latestPath = path.join(OUTPUT_DIR, 'ga-data-latest.json');
    if (fs.existsSync(latestPath)) {
      fs.unlinkSync(latestPath);
    }
    fs.symlinkSync(filename, latestPath);

    console.log('\n='.repeat(70));
    console.log('✨ GA 데이터 수집 완료!');
    console.log('='.repeat(70));
    console.log('\n📊 수집된 데이터 요약:');
    console.log(`   - 기간: ${allData.period.start} ~ ${allData.period.end}`);
    console.log(`   - 총 활성 사용자: ${allData.summary.totalActiveUsers.toLocaleString()}명`);
    console.log(`   - 총 세션: ${allData.summary.totalSessions.toLocaleString()}회`);
    console.log(`   - 총 페이지뷰: ${allData.summary.totalPageViews.toLocaleString()}회`);
    console.log(`   - 일평균 사용자: ${allData.summary.avgDailyUsers.toLocaleString()}명`);
    console.log(`   - 평균 세션 시간: ${Math.round(allData.summary.avgSessionDuration)}초`);
    console.log(`   - 평균 이탈률: ${(allData.summary.avgBounceRate * 100).toFixed(2)}%`);
    console.log('');
    console.log(`📁 저장 위치: ${filepath}`);

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
    if (error.message.includes('PROPERTY_ID')) {
      console.error('\n💡 GA4 Property ID를 스크립트에 설정해주세요.');
      console.error('   GA4 관리 > 속성 설정에서 확인 가능합니다.');
    }
    process.exit(1);
  }
}

// 실행
collectGAData();
