#!/usr/bin/env python3
"""
NOFEE 프로젝트 성과 분석 스크립트
"""

import json
from datetime import datetime
from pathlib import Path

def load_metrics():
    """메트릭스 JSON 파일 로드"""
    with open('metrics/overall-metrics.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_development_progress(metrics):
    """개발 진행 상황 분석"""
    print("=" * 80)
    print("📊 NOFEE 프로젝트 성과 분석 리포트")
    print("=" * 80)
    print()

    # 프로젝트 기본 정보
    project = metrics['project']
    print(f"🚀 프로젝트: {project['name']}")
    print(f"📝 설명: {project['description']}")
    print(f"📅 시작일: {project['start_date']}")
    print(f"⏱️  개발 기간: {project['duration_days']}일")
    print()

    # 전체 통계
    stats = metrics['overall_statistics']
    print("=" * 80)
    print("📈 전체 개발 통계")
    print("=" * 80)
    print(f"  • 총 저장소 수: {stats['total_repositories']}개")
    print(f"  • 총 커밋 수: {stats['total_commits']:,}개")
    print(f"  • 총 파일 수: {stats['total_files']:,}개")
    print(f"  • 총 코드 라인: {stats['total_lines_of_code']:,}줄")
    print(f"  • 개발자 수: {stats['total_contributors']}명")
    print(f"  • 일평균 커밋: {stats['average_commits_per_day']:.2f}개")
    print()

    # 저장소별 상세
    print("=" * 80)
    print("💻 저장소별 상세 통계")
    print("=" * 80)

    repos = metrics['repositories']
    for repo_name, repo_data in repos.items():
        if 'codebase' not in repo_data:
            continue

        print(f"\n📦 {repo_data['name']}")
        print(f"   타입: {repo_data['type']}")
        print(f"   설명: {repo_data['description']}")
        print(f"   기술 스택: {', '.join(repo_data['tech_stack'])}")
        print(f"\n   코드베이스:")
        print(f"     - 파일 수: {repo_data['codebase']['total_files']:,}개")
        print(f"     - 코드 라인: {repo_data['codebase']['total_lines']:,}줄")
        print(f"\n   Git 통계:")
        print(f"     - 총 커밋: {repo_data['git_stats']['total_commits']:,}개")
        print(f"     - 기여자: {repo_data['git_stats']['unique_contributors']}명")
        print(f"     - 시작일: {repo_data['git_stats']['first_commit_date']}")

    print()

    # 주요 기능
    print("=" * 80)
    print("✨ 주요 기능")
    print("=" * 80)

    features = metrics['key_features']
    print("\n사용자 기능:")
    for i, feature in enumerate(features['user_features'], 1):
        print(f"  {i}. {feature}")

    print("\n판매점 기능:")
    for i, feature in enumerate(features['agency_features'], 1):
        print(f"  {i}. {feature}")

    print("\n자동화 시스템:")
    for i, feature in enumerate(features['automation'], 1):
        print(f"  {i}. {feature}")

    print()

    # 비즈니스 성과
    print("=" * 80)
    print("🎯 비즈니스 성과")
    print("=" * 80)

    perf = metrics['performance_data']
    user_metrics = perf['user_metrics']
    business_metrics = perf['business_metrics']

    print("\n사용자 지표:")
    print(f"  • 누적 방문자: {user_metrics['total_visitors']}")
    print(f"  • 견적 신청: {user_metrics['total_quote_requests']}")
    print(f"  • 평균 평점: {user_metrics['average_rating']}")
    print(f"  • 입점 매장: {user_metrics['registered_stores']}")

    print("\n비즈니스 지표:")
    print(f"  • DB 수집률: {business_metrics['db_collection_rate']}")
    print(f"  • 비용 절감: {business_metrics['cost_reduction']}")
    print(f"  • 전환율 개선: {business_metrics['conversion_optimization']}")

    print()

    # 마일스톤
    print("=" * 80)
    print("🏆 완료된 마일스톤")
    print("=" * 80)
    print()

    milestones = metrics['milestones']['completed']
    for milestone in milestones:
        print(f"📅 {milestone['date']}")
        print(f"   {milestone['title']}")
        print(f"   → {milestone['description']}")
        print()

    # 진행 중인 작업
    if metrics['milestones']['in_progress']:
        print("=" * 80)
        print("🚧 진행 중인 작업")
        print("=" * 80)
        print()
        for item in metrics['milestones']['in_progress']:
            print(f"• {item['title']}")
            print(f"  상태: {item['status']}")
            print(f"  우선순위: {item['priority']}")
            print()

def generate_summary():
    """핵심 성과 요약"""
    metrics = load_metrics()

    print("=" * 80)
    print("🌟 핵심 성과 요약")
    print("=" * 80)
    print()

    stats = metrics['overall_statistics']
    perf = metrics['performance_data']

    print("【 개발 속도 】")
    print(f"  158일 동안 564개 커밋 (일평균 3.57개)")
    print(f"  51,041줄의 코드 작성")
    print()

    print("【 사용자 성장 】")
    print(f"  50,000+ 누적 방문자")
    print(f"  20,000+ 견적 신청")
    print(f"  100+ 입점 매장")
    print(f"  4.9점 평균 평점")
    print()

    print("【 비즈니스 효율 】")
    print(f"  DB 수집률 90% 달성 (9배 향상)")
    print(f"  알림톡 비용 50% 절감")
    print()

    print("【 기술 스택 】")
    print("  Frontend: Next.js, TypeScript, React, Tailwind CSS")
    print("  Backend: Spring Boot, Java, JPA, MySQL")
    print("  Infrastructure: GitHub Actions, AWS")
    print()

if __name__ == "__main__":
    metrics = load_metrics()
    analyze_development_progress(metrics)
    print("\n" * 2)
    generate_summary()

    print("=" * 80)
    print("분석 완료!")
    print("=" * 80)
