#!/usr/bin/env node
/**
 * GA 데이터 분석 및 인사이트 생성 스크립트
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const DATA_DIR = path.resolve(__dirname, '../nofee-data');
const LATEST_DATA = path.join(DATA_DIR, 'ga-data-latest.json');

function analyzeGAData() {
  console.log('📊 노피 GA 데이터 분석 시작\n');
  console.log('='.repeat(80));

  // 데이터 로드
  const rawData = fs.readFileSync(LATEST_DATA, 'utf8');
  const gaData = JSON.parse(rawData);

  const analysis = {
    generatedAt: new Date().toISOString(),
    period: gaData.period,
    summary: gaData.summary,
    insights: {},
    recommendations: []
  };

  // 1. 일별 트렌드 분석
  console.log('\n📈 1. 일별 트렌드 분석');
  console.log('-'.repeat(80));

  const dailyData = gaData.data.dailyOverview;
  const sortedByUsers = [...dailyData].sort((a, b) => b.activeUsers - a.activeUsers);

  analysis.insights.dailyTrends = {
    peakDay: sortedByUsers[0],
    lowestDay: sortedByUsers[sortedByUsers.length - 1],
    averages: {
      dailyUsers: Math.round(dailyData.reduce((sum, d) => sum + d.activeUsers, 0) / dailyData.length),
      dailySessions: Math.round(dailyData.reduce((sum, d) => sum + d.sessions, 0) / dailyData.length),
      dailyPageViews: Math.round(dailyData.reduce((sum, d) => sum + d.pageViews, 0) / dailyData.length)
    }
  };

  console.log(`   최고 활성 사용자 날짜: ${sortedByUsers[0].date} (${sortedByUsers[0].activeUsers}명)`);
  console.log(`   최저 활성 사용자 날짜: ${sortedByUsers[sortedByUsers.length - 1].date} (${sortedByUsers[sortedByUsers.length - 1].activeUsers}명)`);
  console.log(`   일평균 사용자: ${analysis.insights.dailyTrends.averages.dailyUsers}명`);
  console.log(`   일평균 세션: ${analysis.insights.dailyTrends.averages.dailySessions}회`);
  console.log(`   일평균 페이지뷰: ${analysis.insights.dailyTrends.averages.dailyPageViews}회`);

  // 2. 페이지 성과 분석
  console.log('\n📄 2. 상위 페이지 성과');
  console.log('-'.repeat(80));

  const topPages = gaData.data.topPages.slice(0, 10);
  analysis.insights.topPages = topPages.map((page, idx) => ({
    rank: idx + 1,
    path: page.path,
    pageViews: page.pageViews,
    avgSessionDuration: Math.round(page.avgSessionDuration),
    bounceRate: (page.bounceRate * 100).toFixed(2) + '%'
  }));

  topPages.forEach((page, idx) => {
    console.log(`   ${idx + 1}. ${page.path}`);
    console.log(`      조회수: ${page.pageViews.toLocaleString()}회 | 평균 시간: ${Math.round(page.avgSessionDuration)}초 | 이탈률: ${(page.bounceRate * 100).toFixed(2)}%`);
  });

  // 3. 트래픽 소스 분석
  console.log('\n🔗 3. 트래픽 소스 분석');
  console.log('-'.repeat(80));

  const topSources = gaData.data.trafficSources
    .sort((a, b) => b.sessions - a.sessions)
    .slice(0, 10);

  analysis.insights.trafficSources = topSources.map((source, idx) => ({
    rank: idx + 1,
    source: source.source,
    medium: source.medium,
    sessions: source.sessions,
    activeUsers: source.activeUsers,
    percentage: ((source.sessions / gaData.summary.totalSessions) * 100).toFixed(2) + '%'
  }));

  topSources.forEach((source, idx) => {
    const percentage = ((source.sessions / gaData.summary.totalSessions) * 100).toFixed(2);
    console.log(`   ${idx + 1}. ${source.source} (${source.medium})`);
    console.log(`      세션: ${source.sessions.toLocaleString()}회 (${percentage}%) | 사용자: ${source.activeUsers.toLocaleString()}명`);
  });

  // 4. 디바이스 분석
  console.log('\n📱 4. 디바이스별 사용 현황');
  console.log('-'.repeat(80));

  analysis.insights.devices = gaData.data.devices.map(device => ({
    category: device.category,
    activeUsers: device.activeUsers,
    sessions: device.sessions,
    pageViews: device.pageViews,
    percentage: ((device.sessions / gaData.summary.totalSessions) * 100).toFixed(2) + '%'
  }));

  gaData.data.devices.forEach(device => {
    const percentage = ((device.sessions / gaData.summary.totalSessions) * 100).toFixed(2);
    console.log(`   ${device.category}:`);
    console.log(`      사용자: ${device.activeUsers.toLocaleString()}명 | 세션: ${device.sessions.toLocaleString()}회 (${percentage}%)`);
  });

  // 5. 주요 이벤트 분석
  console.log('\n🎯 5. 주요 이벤트');
  console.log('-'.repeat(80));

  analysis.insights.topEvents = gaData.data.events.slice(0, 10).map((event, idx) => ({
    rank: idx + 1,
    name: event.name,
    count: event.count,
    countPerUser: event.countPerUser.toFixed(2)
  }));

  gaData.data.events.slice(0, 10).forEach((event, idx) => {
    console.log(`   ${idx + 1}. ${event.name}`);
    console.log(`      발생 횟수: ${event.count.toLocaleString()}회 | 사용자당: ${event.countPerUser.toFixed(2)}회`);
  });

  // 6. 지역별 분석
  console.log('\n🌏 6. 상위 지역 (Top 10)');
  console.log('-'.repeat(80));

  const topLocations = gaData.data.locations.slice(0, 10);
  analysis.insights.topLocations = topLocations.map((loc, idx) => ({
    rank: idx + 1,
    city: loc.city,
    country: loc.country,
    activeUsers: loc.activeUsers,
    sessions: loc.sessions
  }));

  topLocations.forEach((loc, idx) => {
    console.log(`   ${idx + 1}. ${loc.city}, ${loc.country}`);
    console.log(`      사용자: ${loc.activeUsers.toLocaleString()}명 | 세션: ${loc.sessions.toLocaleString()}회`);
  });

  // 7. 인사이트 및 추천사항
  console.log('\n💡 7. 주요 인사이트');
  console.log('-'.repeat(80));

  // 사용자 참여도 분석
  const avgPagesPerSession = gaData.summary.totalPageViews / gaData.summary.totalSessions;
  analysis.insights.engagement = {
    pagesPerSession: avgPagesPerSession.toFixed(2),
    avgSessionDuration: Math.round(gaData.summary.avgSessionDuration),
    bounceRate: (gaData.summary.avgBounceRate * 100).toFixed(2) + '%'
  };

  console.log(`   평균 세션당 페이지뷰: ${avgPagesPerSession.toFixed(2)}페이지`);
  console.log(`   평균 세션 시간: ${Math.round(gaData.summary.avgSessionDuration)}초 (${Math.round(gaData.summary.avgSessionDuration / 60)}분)`);
  console.log(`   평균 이탈률: ${(gaData.summary.avgBounceRate * 100).toFixed(2)}%`);

  // 추천사항 생성
  console.log('\n🎯 8. 개선 추천사항');
  console.log('-'.repeat(80));

  if (avgPagesPerSession > 5) {
    analysis.recommendations.push('✅ 사용자 참여도가 매우 높습니다. 현재 콘텐츠 전략을 유지하세요.');
    console.log('   ✅ 사용자 참여도가 매우 높습니다. 현재 콘텐츠 전략을 유지하세요.');
  } else if (avgPagesPerSession < 3) {
    analysis.recommendations.push('⚠️ 세션당 페이지뷰가 낮습니다. 내부 링크 및 관련 콘텐츠 추천을 강화하세요.');
    console.log('   ⚠️ 세션당 페이지뷰가 낮습니다. 내부 링크 및 관련 콘텐츠 추천을 강화하세요.');
  }

  if (gaData.summary.avgBounceRate < 0.3) {
    analysis.recommendations.push('✅ 이탈률이 낮아 사용자 경험이 우수합니다.');
    console.log('   ✅ 이탈률이 낮아 사용자 경험이 우수합니다.');
  }

  const mobilePercentage = gaData.data.devices.find(d => d.category === 'mobile')?.sessions / gaData.summary.totalSessions;
  if (mobilePercentage > 0.6) {
    analysis.recommendations.push(`📱 모바일 사용자가 ${(mobilePercentage * 100).toFixed(0)}%입니다. 모바일 최적화에 집중하세요.`);
    console.log(`   📱 모바일 사용자가 ${(mobilePercentage * 100).toFixed(0)}%입니다. 모바일 최적화에 집중하세요.`);
  }

  // 성장 잠재력 분석
  const newUserRate = dailyData.reduce((sum, d) => sum + d.newUsers, 0) / gaData.summary.totalActiveUsers;
  analysis.insights.growth = {
    newUserRate: (newUserRate * 100).toFixed(2) + '%',
    returningUserRate: ((1 - newUserRate) * 100).toFixed(2) + '%'
  };

  console.log(`\n   신규 사용자 비율: ${(newUserRate * 100).toFixed(2)}%`);
  console.log(`   재방문 사용자 비율: ${((1 - newUserRate) * 100).toFixed(2)}%`);

  if (newUserRate > 0.7) {
    analysis.recommendations.push('📈 신규 사용자 비율이 높습니다. 재방문을 유도하는 전략(뉴스레터, 푸시 알림 등)을 고려하세요.');
    console.log('   📈 신규 사용자 비율이 높습니다. 재방문을 유도하는 전략(뉴스레터, 푸시 알림 등)을 고려하세요.');
  }

  // 분석 결과 저장
  console.log('\n💾 분석 결과 저장 중...');
  const timestamp = new Date().toISOString().split('T')[0];
  const analysisFilename = `ga-analysis-${timestamp}.json`;
  const analysisPath = path.join(DATA_DIR, analysisFilename);

  fs.writeFileSync(analysisPath, JSON.stringify(analysis, null, 2), 'utf8');
  console.log(`   ✅ 파일 저장 완료: ${analysisFilename}`);

  // 최신 분석 심볼릭 링크
  const latestAnalysisPath = path.join(DATA_DIR, 'ga-analysis-latest.json');
  if (fs.existsSync(latestAnalysisPath)) {
    fs.unlinkSync(latestAnalysisPath);
  }
  fs.symlinkSync(analysisFilename, latestAnalysisPath);

  console.log('\n='.repeat(80));
  console.log('✨ 분석 완료!');
  console.log('='.repeat(80));
  console.log(`📁 저장 위치: ${analysisPath}\n`);
}

analyzeGAData();
