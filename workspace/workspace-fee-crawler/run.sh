#!/bin/bash

# Workspace Fee Crawler - 통합 실행 스크립트
# 모든 주요 기능을 쉽게 실행할 수 있습니다

set -e  # 에러 발생 시 중단

# 색상 코드
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 프로젝트 루트로 이동
cd "$(dirname "$0")"

# 가상환경 활성화 함수
activate_venv() {
    if [ -d "venv" ]; then
        echo -e "${GREEN}✅ 가상환경 활성화${NC}"
        source venv/bin/activate
    else
        echo -e "${RED}❌ 가상환경이 없습니다. setup.sh를 먼저 실행하세요${NC}"
        exit 1
    fi
}

# 메인 메뉴
show_menu() {
    echo -e "${BLUE}"
    echo "=================================================="
    echo " Workspace Fee Crawler - 통합 실행 메뉴"
    echo "=================================================="
    echo -e "${NC}"
    echo "1) 🔍 크롤러 실행 (KT/SK/LG)"
    echo "2) 🔍 전체 데이터 업데이트 크롤러"
    echo "3) 📊 OCR 실행 (Batch Table)"
    echo "4) 🔀 머지 & 업로드 (All)"
    echo "5) 📋 Summary 생성"
    echo "6) 🧹 공시지원금 데이터 정제"
    echo ""
    echo "7) 🚀 전체 파이프라인 (크롤러 → 머지 → Summary)"
    echo ""
    echo "8) 📁 폴더 구조 보기"
    echo "9) 🔧 설정 보기"
    echo "0) 종료"
    echo ""
}

# 1) 크롤러 실행
run_crawlers() {
    activate_venv
    echo -e "${GREEN}🔍 크롤러 선택:${NC}"
    echo "1) KT"
    echo "2) SK"
    echo "3) LG"
    echo "4) 전체"
    read -p "선택 (1-4): " choice

    case $choice in
        1)
            echo -e "${BLUE}KT 크롤러 실행 중...${NC}"
            python3 price_crawler/kt_crawler.py
            ;;
        2)
            echo -e "${BLUE}SK 크롤러 실행 중...${NC}"
            python3 price_crawler/sk_crawler.py
            ;;
        3)
            echo -e "${BLUE}LG 크롤러 실행 중...${NC}"
            python3 price_crawler/lg_crawler.py
            ;;
        4)
            echo -e "${BLUE}전체 크롤러 실행 중...${NC}"
            python3 price_crawler/kt_crawler.py
            python3 price_crawler/sk_crawler.py
            python3 price_crawler/lg_crawler.py
            ;;
        *)
            echo -e "${RED}잘못된 선택${NC}"
            ;;
    esac
}

# 2) 전체 데이터 업데이트 크롤러
run_all_crawler() {
    activate_venv
    echo -e "${BLUE}전체 데이터 업데이트 크롤러 실행 중...${NC}"
    python3 price_crawler/kt_crawler.py && python3 price_crawler/sk_crawler.py && python3 price_crawler/lg_crawler.py
}

# 3) OCR 실행
run_ocr() {
    activate_venv
    echo -e "${BLUE}OCR 실행 중 (Batch Table)...${NC}"
    python3 image_ocr/clova_ocr.py batch --table
}

# 4) 머지 & 업로드
run_merge() {
    activate_venv
    echo -e "${BLUE}머지 & 업로드 실행 중...${NC}"
    python3 data_merge/data_merge_main.py all
}

# 5) Summary 생성
run_summary() {
    activate_venv
    echo -e "${BLUE}Summary 생성 중...${NC}"
    python3 price_summary/create_summary_clean.py
}

# 6) 공시지원금 정제
run_clean_support() {
    activate_venv
    echo -e "${BLUE}공시지원금 데이터 정제 중...${NC}"
    python3 price_summary/clean_support_sheet.py
}

# 7) 전체 파이프라인
run_full_pipeline() {
    activate_venv
    echo -e "${BLUE}"
    echo "=================================================="
    echo " 전체 파이프라인 실행"
    echo "=================================================="
    echo -e "${NC}"
    echo "1️⃣ 크롤러 실행"
    echo "2️⃣ 머지 & 업로드"
    echo "3️⃣ Summary 생성"
    echo ""
    read -p "계속하시겠습니까? (y/n): " confirm

    if [[ $confirm == [yY] ]]; then
        echo -e "${GREEN}📍 Step 1/3: 크롤러 실행${NC}"
        python3 price_crawler/kt_crawler.py && python3 price_crawler/sk_crawler.py && python3 price_crawler/lg_crawler.py

        echo ""
        echo -e "${GREEN}📍 Step 2/3: 머지 & 업로드${NC}"
        python3 data_merge/data_merge_main.py all

        echo ""
        echo -e "${GREEN}📍 Step 3/3: Summary 생성${NC}"
        python3 price_summary/create_summary_clean.py

        echo ""
        echo -e "${GREEN}✅ 전체 파이프라인 완료!${NC}"
    else
        echo -e "${YELLOW}취소됨${NC}"
    fi
}

# 8) 폴더 구조 보기
show_structure() {
    echo -e "${BLUE}📁 현재 폴더 구조 (루트 레벨):${NC}"
    echo ""
    echo "workspace-fee-price_crawler/"
    echo "├── price_crawler/          # 🔍 크롤러 기능"
    echo "│   ├── data/        # 크롤링 원본"
    echo "│   ├── checkpoints/ # 체크포인트"
    echo "│   └── logs/        # 크롤러 로그"
    echo "│"
    echo "├── image_ocr/             # 📊 OCR 기능"
    echo "│   ├── input/       # OCR 입력 이미지"
    echo "│   ├── output/      # OCR 결과"
    echo "│   │   ├── latest/  # 최신 파일"
    echo "│   │   └── archive/ # 날짜별 아카이브"
    echo "│   └── logs/        # OCR 로그"
    echo "│"
    echo "├── data_merge/           # 🔀 병합 기능"
    echo "│   ├── output/      # 병합 결과"
    echo "│   │   ├── latest/  # 최신 파일"
    echo "│   │   └── archive/ # 날짜별 아카이브"
    echo "│   └── logs/        # 머지 로그"
    echo "│"
    echo "├── price_summary/         # 📋 Summary 기능"
    echo "│   ├── output/      # Summary 결과"
    echo "│   │   ├── latest/  # 최신 파일"
    echo "│   │   └── archive/ # 날짜별 아카이브"
    echo "│   └── logs/        # Summary 로그"
    echo "│"
    echo "├── analysis/        # 📈 분석 결과 (공통)"
    echo "├── src/             # 소스 코드"
    echo "└── temp/            # 임시 파일"
    echo ""

    # 최신 파일 표시
    echo -e "${GREEN}📄 최신 파일:${NC}"
    echo ""
    if [ -d "data_merge/output/latest" ]; then
        echo "🔀 Merged 파일:"
        ls -lh data_merge/output/latest/ 2>/dev/null | tail -n +2 || echo "  (없음)"
    fi
    echo ""
    if [ -d "price_summary/output/latest" ]; then
        echo "📋 Summary 파일:"
        ls -lh price_summary/output/latest/ 2>/dev/null | tail -n +2 || echo "  (없음)"
    fi
    echo ""
    if [ -d "image_ocr/output/latest" ]; then
        echo "📊 OCR 파일:"
        ls -lh image_ocr/output/latest/ 2>/dev/null | tail -n +2 | head -5 || echo "  (없음)"
    fi
    echo ""
    if [ -d "price_crawler/data" ]; then
        echo "🔍 크롤러 데이터:"
        du -sh price_crawler/data 2>/dev/null || echo "  (없음)"
    fi
}

# 9) 설정 보기
show_settings() {
    echo -e "${BLUE}🔧 현재 설정:${NC}"
    echo ""
    echo "Python 버전: $(python3 --version)"
    echo "가상환경: $([ -d 'venv' ] && echo '✅ 존재' || echo '❌ 없음')"
    echo ""
    echo "프로젝트 루트: $(pwd)"
    echo ""

    if [ -f "src/config/paths.py" ]; then
        echo -e "${GREEN}✅ PathManager 설정됨${NC}"
    fi

    if [ -f "src/config/google_api_key.json" ]; then
        echo -e "${GREEN}✅ Google API 키 존재${NC}"
    else
        echo -e "${YELLOW}⚠️  Google API 키 없음${NC}"
    fi
}

# 메인 루프
while true; do
    show_menu
    read -p "선택 (0-9): " choice
    echo ""

    case $choice in
        1) run_crawlers ;;
        2) run_all_crawler ;;
        3) run_ocr ;;
        4) run_merge ;;
        5) run_summary ;;
        6) run_clean_support ;;
        7) run_full_pipeline ;;
        8) show_structure ;;
        9) show_settings ;;
        0)
            echo -e "${GREEN}종료합니다${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}잘못된 선택입니다 (0-9)${NC}"
            ;;
    esac

    echo ""
    echo -e "${YELLOW}계속하려면 Enter를 누르세요...${NC}"
    read
    clear
done
