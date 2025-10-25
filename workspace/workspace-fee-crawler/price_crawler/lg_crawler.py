#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LG U+ 휴대폰 지원금 크롤러 - 통합 버전 (수정)
통일된 UI, 데이터 형식, 로깅 시스템

작성일: 2025-01-11
버전: 6.1
파일명: lg_crawler.py
"""

import os
import sys
import time
from pathlib import Path
import json
import shutil
import logging
import argparse
import traceback
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue
import pickle

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, NoAlertPresentException, UnexpectedAlertPresentException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# Rich UI 지원 (선택사항)
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn, MofNCompleteColumn
    from rich.table import Table
    from rich.panel import Panel
    from rich.live import Live
    from rich.layout import Layout
    from rich import print as rprint
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

# Path imports
from shared_config.config.paths import PathManager, get_raw_data_path, get_checkpoint_path, get_log_path

# 경로 매니저 초기화
path_manager = PathManager()

# 로깅 설정
log_file = get_log_path('lg_crawler', 'crawlers')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler() if not RICH_AVAILABLE else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)


# 데이터 클래스 정의
@dataclass
class RatePlan:
    """요금제 정보"""
    id: str
    name: str
    value: str
    category: str
    monthly_fee: int = 0

@dataclass
class DeviceData:
    """기기 데이터 - 통합 형식"""
    date: str = ""
    crawled_at: str = field(default_factory=lambda: datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S'))
    carrier: str = "LG"
    manufacturer: str = "전체"
    scrb_type_name: str = ""
    network_type: str = ""
    device_nm: str = ""
    plan_name: str = ""
    monthly_fee: int = 0
    release_price: int = 0
    public_support_fee: int = 0
    additional_support_fee: int = 0
    total_support_fee: int = 0
    total_price: int = 0

@dataclass
class CrawlTask:
    """크롤링 작업"""
    subscription_type: Tuple[str, str]
    device_type: Tuple[str, str]
    rate_plan: RatePlan
    task_id: int = 0


class LGUPlusCrawler:
    """LG U+ 크롤러 - 통합 버전"""
    
    BASE_URL = "https://www.lguplus.com/mobile/financing-model"
    
    # 요금제 카테고리
    PLAN_CATEGORIES_5G = [
        '5g-category', '5g-unlimited', '5g-standard', '5g-data',
        '5g-young', '5g-youth', '5g-senior', '5g-welfare',
        '5g-premium', '5g-special', '5g-basic', '5g-value'
    ]
    
    PLAN_CATEGORIES_LTE = [
        'lte-general', 'lte-standard', 'lte-unlimited', 'lte-data',
        'lte-youth', 'lte-senior', 'lte-welfare', 'lte-basic',
        'lte-premium', 'lte-special', 'lte-value'
    ]
    
    def __init__(self, config: Dict[str, Any] = None):
        """초기화"""
        # 기본 설정
        self.config = {
            'headless': True,
            'max_workers': 3,
            'max_pages': 10,
            'page_timeout': 20,  # 감소
            'element_timeout': 10,  # 감소
            'retry_count': 2,  # 감소
            'fast_mode': True,
            'skip_price_check': True,  # 가격 조회 스킵
            'output_dir': 'data',
            'checkpoint_interval': 20,  # 감소
            'use_rich': RICH_AVAILABLE,
            'debug': False,
            'delay_between_requests': 1,  # 감소
            'max_rate_plans': 0  # 추가
        }
        
        if config:
            self.config.update(config)
        
        # 디렉토리 생성
        os.makedirs(self.config['output_dir'], exist_ok=True)
        
        # 데이터 저장소
        self.all_data: List[DeviceData] = []
        self.data_lock = threading.Lock()
        self.active_drivers = []  # 활성 드라이버 추적
        self.active_services = []  # 활성 서비스 추적
        self.drivers_lock = threading.Lock()  # 드라이버 목록 보호
        
        # 요금제 정보
        self.rate_plans: Dict[str, Dict[str, List[RatePlan]]] = {}
        
        # 가격 캐시
        self.price_cache: Dict[str, str] = {}
        self.cache_lock = threading.Lock()
        
        # 진행 상태
        self.completed_count = 0
        self.failed_count = 0
        self.total_devices = 0
        self.status_lock = threading.Lock()
        self.start_time = None
        
        # 체크포인트
        self.checkpoint_file = get_checkpoint_path('lg')
        
        # 크롤링 조합
        self.all_combinations = []
        
    def create_driver(self) -> webdriver.Chrome:
        """Chrome 드라이버 생성 - 개선된 버전"""
        options = Options()
        
        # 기본 옵션 (안정성 중심)
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 로깅 비활성화
        options.add_argument('--log-level=3')
        options.add_argument('--silent')
        options.add_argument('--disable-logging')
        
        # 크래시 방지
        options.add_argument('--disable-crash-reporter')
        options.add_argument('--disable-breakpad')
        options.add_argument('--disable-background-networking')
        
        # macOS 특정 안정성 옵션
        import platform
        if platform.system() == 'Darwin':
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--force-device-scale-factor=1')
        
        # 성능 최적화 (선택적)
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # 메모리 최적화
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max_old_space_size=4096')
        
        # User-Agent 및 프로필 설정
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        options.add_argument(f'user-agent={user_agent}')
        
        # 차단 회피를 위한 추가 옵션
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--ignore-certificate-errors')
        
        # 헤드리스 모드
        if self.config['headless']:
            options.add_argument('--headless=new')
        
        # 성능 최적화 (fast_mode)
        if self.config['fast_mode']:
            prefs = {
                'profile.default_content_setting_values': {
                    'images': 2,
                    'plugins': 2,
                    'popups': 2,
                    'geolocation': 2,
                    'notifications': 2,
                    'media_stream': 2,
                }
            }
            options.add_experimental_option('prefs', prefs)
        
        # ChromeDriver 설정 개선
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 캐시 정리 (첫 시도에서만)
                if attempt == 0:
                    import shutil
                    cache_dir = os.path.expanduser("~/.wdm")
                    if os.path.exists(cache_dir):
                        try:
                            shutil.rmtree(cache_dir)
                            logger.info(f"ChromeDriver 캐시 정리: {cache_dir}")
                        except:
                            pass
                
                # ChromeDriver 다운로듍 및 설치
                chromedriver_path = ChromeDriverManager().install()
                
                # macOS에서 quarantine 속성 제거
                if platform.system() == 'Darwin':
                    try:
                        import subprocess
                        subprocess.run(['xattr', '-cr', os.path.dirname(chromedriver_path)], 
                                     capture_output=True, check=False)
                        subprocess.run(['chmod', '+x', chromedriver_path], 
                                     capture_output=True, check=False)
                    except:
                        pass
                
                # Service 객체 생성 (로그 비활성화)
                service = Service(
                    executable_path=chromedriver_path,
                    log_output=os.devnull  # 로그 출력 비활성화
                )
                
                # Driver 생성
                driver = webdriver.Chrome(service=service, options=options)
                
                # 활성 드라이버 목록에 추가
                with self.drivers_lock:
                    self.active_drivers.append(driver)
                    self.active_services.append(service)
                
                logger.info(f"ChromeDriver 생성 성공 (시도 {attempt + 1}/{max_retries})")
                break
                
            except Exception as e:
                logger.error(f"ChromeDriver 생성 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)  # 재시도 전 대기
                else:
                    raise Exception(f"ChromeDriver를 시작할 수 없습니다: {str(e)}")
        driver.set_page_load_timeout(self.config['page_timeout'])
        driver.implicitly_wait(5)
        
        # JavaScript로 자동화 탐지 방지 및 추가 위장
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Chrome 속성 위장
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['ko-KR', 'ko', 'en-US', 'en']
                });
                
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'MacIntel'
                });
                
                Object.defineProperty(navigator, 'vendor', {
                    get: () => 'Google Inc.'
                });
                
                // Permissions API 오버라이드
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            '''
        })
        
        return driver
    
    def wait_for_page_ready(self, driver: webdriver.Chrome, timeout: int = None):
        """페이지 로딩 대기"""
        if timeout is None:
            timeout = self.config['element_timeout']
        
        wait_time = timeout if not self.config['fast_mode'] else min(timeout, 5)
        
        try:
            WebDriverWait(driver, wait_time).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            # jQuery가 있는 경우 대기
            WebDriverWait(driver, wait_time).until(
                lambda d: d.execute_script(
                    "return typeof jQuery === 'undefined' || jQuery.active == 0"
                )
            )
            time.sleep(1 if self.config['fast_mode'] else 2)  # 대기 시간 증가
        except TimeoutException:
            logger.debug("페이지 로딩 타임아웃")
        except:
            pass
    
    def handle_alert(self, driver: webdriver.Chrome) -> bool:
        """Alert 처리"""
        try:
            # Alert 대기 (3초)
            alert = WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert_text = alert.text
            logger.warning(f"Alert 감지: {alert_text}")
            
            # Alert 수락
            alert.accept()
            
            # 네트워크 오류나 조회 실패 메시지 감지
            if any(keyword in alert_text for keyword in ['네트워크', '오류', '실패', '조회할 수 없습니다']):
                logger.error(f"조회 실패 Alert: {alert_text}")
                return True  # Alert 발생했음을 알림
            
            return True
        except TimeoutException:
            # Alert 없음
            return False
        except NoAlertPresentException:
            return False
        except Exception as e:
            logger.debug(f"Alert 처리 중 오류: {e}")
            return False
    
    def collect_rate_plans(self):
        """모든 요금제 수집"""
        if RICH_AVAILABLE:
            console.print(Panel.fit(
                "[bold cyan]요금제 목록 수집 시작...[/bold cyan]",
                border_style="cyan"
            ))
        else:
            print("\n요금제 목록 수집 시작...")
        
        driver = self.create_driver()
        
        try:
            # 가입유형별로 수집
            subscription_types = [
                ('1', '기기변경'),
                ('2', '번호이동'),
                ('3', '신규가입')
            ]
            
            device_types = [
                ('00', '5G'),
                ('01', 'LTE')
            ]
            
            total_plans = 0
            
            # Progress 표시
            if self.config['use_rich'] and console:
                progress = Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    console=console
                )
                
                with progress:
                    task = progress.add_task(
                        "[cyan]요금제 수집 중...", 
                        total=len(subscription_types) * len(device_types)
                    )
                    
                    for sub_type in subscription_types:
                        for dev_type in device_types:
                            plans = self._collect_plans_for_combination(
                                driver, sub_type, dev_type
                            )
                            
                            # 저장
                            if dev_type[0] not in self.rate_plans:
                                self.rate_plans[dev_type[0]] = {}
                            self.rate_plans[dev_type[0]][sub_type[0]] = plans
                            
                            total_plans += len(plans)
                            progress.advance(task)
                            
                            desc = f"{sub_type[1]} - {dev_type[1]}: {len(plans)}개"
                            logger.info(desc)
                            
                            # 요청 간 지연
                            time.sleep(self.config['delay_between_requests'])
            else:
                # 일반 출력
                for sub_type in subscription_types:
                    for dev_type in device_types:
                        plans = self._collect_plans_for_combination(
                            driver, sub_type, dev_type
                        )
                        
                        if dev_type[0] not in self.rate_plans:
                            self.rate_plans[dev_type[0]] = {}
                        self.rate_plans[dev_type[0]][sub_type[0]] = plans
                        
                        total_plans += len(plans)
                        time.sleep(self.config['delay_between_requests'])
            
            # 결과 출력
            if RICH_AVAILABLE:
                table = Table(title="수집된 요금제 현황", show_header=True)
                table.add_column("구분", style="cyan")
                table.add_column("개수", justify="right", style="yellow")
                
                # 가입유형별 통계
                for sub_type in subscription_types:
                    count = sum(len(self.rate_plans.get(dev[0], {}).get(sub_type[0], [])) 
                               for dev in device_types)
                    table.add_row(sub_type[1], f"{count}개")
                
                table.add_row("총계", f"{total_plans}개", style="bold")
                
                console.print("\n")
                console.print(table)
            else:
                print(f"\n총 {total_plans}개 요금제 수집 완료")
            
        except Exception as e:
            logger.error(f"요금제 수집 오류: {e}")
            if self.config['debug']:
                traceback.print_exc()
        finally:
            if driver:
                try:
                    driver.quit()
                    with self.drivers_lock:
                        if driver in self.active_drivers:
                            idx = self.active_drivers.index(driver)
                            self.active_drivers.remove(driver)
                            # 해당 서비스도 정지 및 제거
                            if idx < len(self.active_services):
                                try:
                                    self.active_services[idx].stop()
                                except:
                                    pass
                                self.active_services.pop(idx)
                except Exception as e:
                    logger.debug(f"드라이버 종료 중 오류: {e}")
    
    def _collect_plans_for_combination(self, driver: webdriver.Chrome, 
                                     sub_type: Tuple[str, str], 
                                     dev_type: Tuple[str, str]) -> List[RatePlan]:
        """특정 조합의 요금제 수집"""
        plans = []
        retry_count = 0
        
        while retry_count < self.config['retry_count']:
            try:
                # 페이지 로드
                driver.get(self.BASE_URL)
                self.wait_for_page_ready(driver)
                
                # 페이지 구조 디버깅
                logger.info(f"현재 URL: {driver.current_url}")
                
                # 가입유형 선택
                result = self._select_option(driver, '가입유형', sub_type[0])
                logger.info(f"가입유형 선택 결과 ({sub_type[1]}): {result}")
                time.sleep(1)
                
                # 기기종류 선택
                result = self._select_option(driver, '기기종류', dev_type[0])
                logger.info(f"기기종류 선택 결과 ({dev_type[1]}): {result}")
                time.sleep(1)
                
                # 요금제 목록 열기 (_open_rate_plan_modal이 이미 "더 많은 요금제 보기"를 클릭함)
                if self._open_rate_plan_modal(driver):
                    # 요금제 목록 추출
                    plan_elements = driver.execute_script("""
                        var plans = [];
                        
                        // 모달 내에서 요금제 찾기
                        var modal = document.querySelector('.modal-content:not([style*="display: none"])');
                        if (!modal) {
                            modal = document.querySelector('[class*="modal"]:not([style*="display: none"])');
                        }
                        
                        if (modal) {
                            // 모달 내 모든 라디오 버튼 찾기
                            var radios = modal.querySelectorAll('input[type="radio"]');
                            
                            radios.forEach(function(radio) {
                                // 가입유형, 기기종류 제외
                                if (radio.name !== '가입유형' && radio.name !== '기기종류' && radio.id) {
                                    var label = modal.querySelector('label[for="' + radio.id + '"]');
                                    if (label) {
                                        // 요금제 이름 추출 - Vue.js 구조 고려
                                        var titleElem = label.querySelector('.contents__title, p.contents__title');
                                        var planName = titleElem ? titleElem.textContent.trim() : '';
                                        
                                        // 가격 정보 추출
                                        var priceElem = label.querySelector('.contents__price, p.contents__price');
                                        var priceText = priceElem ? priceElem.textContent.trim() : '';
                                        
                                        if (planName) {
                                            plans.push({
                                                id: radio.id,
                                                value: radio.value || radio.id,  // value가 없으면 id 사용
                                                name: planName,
                                                category: 'Unknown',
                                                price: priceText
                                            });
                                        }
                                    }
                                }
                            });
                        } else {
                            // 모달이 없는 경우 전체 페이지에서 찾기
                            var allRadios = document.querySelectorAll('input[type="radio"]');
                            
                            allRadios.forEach(function(radio) {
                                // 가입유형, 기기종류 제외
                                if (radio.name !== '가입유형' && radio.name !== '기기종류' && radio.id) {
                                    var label = document.querySelector('label[for="' + radio.id + '"]');
                                    if (label) {
                                        // 요금제 이름 추출 - Vue.js 구조 고려
                                        var titleElem = label.querySelector('.contents__title, p.contents__title');
                                        var planName = titleElem ? titleElem.textContent.trim() : '';
                                        
                                        // 가격 정보 추출
                                        var priceElem = label.querySelector('.contents__price, p.contents__price');
                                        var priceText = priceElem ? priceElem.textContent.trim() : '';
                                        
                                        if (planName) {
                                            plans.push({
                                                id: radio.id,
                                                value: radio.value || radio.id,  // value가 없으면 id 사용
                                                name: planName,
                                                category: 'Unknown',
                                                price: priceText
                                            });
                                        }
                                    }
                                }
                            });
                        }
                        
                        console.log('Total plans found:', plans.length);
                        return plans;
                    """)
                    
                    logger.info(f"추출된 요금제 수: {len(plan_elements)}")
                    
                    # RatePlan 객체로 변환
                    for p in plan_elements:
                        if p.get('id') and p.get('name'):
                            # 가격 정보 파싱
                            price = 0
                            price_text = p.get('price', '')
                            if price_text:
                                # "월 37,000원" 형식에서 숫자만 추출
                                match = re.search(r'(\d{1,3}(?:,\d{3})*)', price_text)
                                if match:
                                    price = int(match.group(1).replace(',', ''))
                            
                            rate_plan = RatePlan(
                                id=p['id'],
                                name=p['name'],
                                value=p.get('value', ''),
                                category=p.get('category', '')
                            )
                            rate_plan.monthly_fee = price
                            plans.append(rate_plan)
                    
                    # 모달 닫기
                    driver.execute_script("""
                        var closeBtn = document.querySelector('button.c-btn-close');
                        if (closeBtn) closeBtn.click();
                    """)
                    
                    logger.info(f"수집된 요금제 수: {len(plans)}")
                    return plans
                else:
                    logger.warning(f"요금제 모달을 열 수 없음 ({sub_type[1]}, {dev_type[1]})")
                    
            except TimeoutException as e:
                logger.error(f"요금제 수집 타임아웃 ({sub_type[1]}, {dev_type[1]}): {e}")
                retry_count += 1
                if retry_count < self.config['retry_count']:
                    time.sleep(2)
                    continue
            except Exception as e:
                logger.error(f"요금제 수집 오류 ({sub_type[1]}, {dev_type[1]}): {e}")
                if self.config['debug']:
                    traceback.print_exc()
                retry_count += 1
                if retry_count < self.config['retry_count']:
                    time.sleep(2)
                    continue
        
        return plans
    
    def _select_option(self, driver: webdriver.Chrome, name: str, value: str) -> bool:
        """옵션 선택"""
        try:
            script = """
                var name = arguments[0];
                var value = arguments[1];
                var radio = null;
                
                if (name === "가입유형") {
                    // 가입유형: 1=기기변경(index 0), 2=번호이동(index 1), 3=신규가입(index 2)
                    var radios = document.querySelectorAll('input[name="가입유형"]');
                    var index = parseInt(value) - 1;  // 1,2,3 -> 0,1,2
                    if (index >= 0 && index < radios.length) {
                        radio = radios[index];
                    }
                } else if (name === "기기종류") {
                    // 기기종류: 00=5G(index 0), 01=LTE(index 1), 02=태블릿/워치(index 2)
                    var radios = document.querySelectorAll('input[name="기기종류"]');
                    var index = parseInt(value);  // 00,01,02 -> 0,1,2
                    if (index >= 0 && index < radios.length) {
                        radio = radios[index];
                    }
                } else {
                    radio = document.querySelector('input[name="' + name + '"][value="' + value + '"]');
                }
                
                if (radio && !radio.checked) {
                    radio.checked = true;
                    radio.dispatchEvent(new Event('change', { bubbles: true }));
                    
                    if (radio.id) {
                        var label = document.querySelector('label[for="' + radio.id + '"]');
                        if (label) label.click();
                    }
                    
                    return true;
                }
                return false;
            """
            return driver.execute_script(script, name, value)
        except Exception as e:
            logger.error(f"옵션 선택 오류: {e}")
            return False
    
    def _open_rate_plan_modal(self, driver: webdriver.Chrome) -> bool:
        """요금제 모달 열기"""
        try:
            # "더 많은 요금제 보기" 버튼 클릭 (모달 역할)
            clicked = driver.execute_script("""
                var buttons = document.querySelectorAll('button');
                for (var btn of buttons) {
                    if (btn.textContent.includes('더 많은 요금제') || 
                        btn.textContent.includes('요금제 보기') ||
                        btn.classList.contains('c-btn-rect-2')) {
                        console.log('요금제 버튼 발견:', btn.textContent);
                        btn.scrollIntoView({behavior: 'smooth', block: 'center'});
                        btn.click();
                        return true;
                    }
                }
                
                // 요금제 선택 버튼도 확인 (일부 페이지에서 사용)
                for (var btn of buttons) {
                    if (btn.textContent.includes('요금제') && 
                        btn.textContent.includes('선택')) {
                        console.log('요금제 선택 버튼 발견:', btn.textContent);
                        btn.click();
                        return true;
                    }
                }
                return false;
            """)
            
            if clicked:
                time.sleep(2)  # 모달 로딩 대기 시간 증가
                
                # 요금제 목록 확인 (모달이 아닌 확장된 영역)
                plans_visible = driver.execute_script("""
                    // 요금제 라디오 버튼이 표시되는지 확인
                    var planRadios = document.querySelectorAll('input[type="radio"]');
                    var visiblePlans = 0;
                    
                    planRadios.forEach(function(radio) {
                        if (radio.name !== '가입유형' && radio.name !== '기기종류' && 
                            radio.offsetParent !== null) {
                            visiblePlans++;
                        }
                    });
                    
                    console.log('표시된 요금제 수:', visiblePlans);
                    return visiblePlans > 0;
                """)
                
                if plans_visible:
                    logger.info("요금제 목록이 표시되었습니다.")
                else:
                    logger.warning("요금제 목록이 표시되지 않았습니다.")
                    
                return plans_visible
            
            return False
        except Exception as e:
            logger.error(f"모달 열기 오류: {e}")
            return False
    
    def prepare_tasks(self) -> List[CrawlTask]:
        """크롤링 작업 준비"""
        tasks = []
        task_id = 0
        
        subscription_types = [
            ('1', '기기변경'),
            ('2', '번호이동'),
            ('3', '신규가입')
        ]
        
        device_types = [
            ('00', '5G'),
            ('01', 'LTE')
        ]
        
        # 작업 생성
        for sub_type in subscription_types:
            for dev_type in device_types:
                plans = self.rate_plans.get(dev_type[0], {}).get(sub_type[0], [])
                
                # 요금제 수 제한
                if self.config.get('max_rate_plans', 0) > 0:
                    plans = plans[:self.config['max_rate_plans']]
                
                for plan in plans:
                    tasks.append(CrawlTask(
                        subscription_type=sub_type,
                        device_type=dev_type,
                        rate_plan=plan,
                        task_id=task_id
                    ))
                    task_id += 1
        
        self.all_combinations = tasks
        return tasks
    
    def process_task(self, task: CrawlTask, progress=None, main_task=None) -> int:
        """단일 작업 처리"""
        driver = None
        extracted_count = 0
        retry_count = 0
        
        while retry_count < self.config['retry_count']:
            try:
                driver = self.create_driver()
                
                # 진행 상황 업데이트
                if progress and main_task is not None:
                    desc = f"[{task.task_id+1}/{len(self.all_combinations)}] {task.rate_plan.name[:30]}... ({task.device_type[1]}, {task.subscription_type[1]})"
                    if retry_count > 0:
                        desc += f" (재시도 {retry_count}/{self.config['retry_count']})"
                    progress.update(main_task, description=desc)
                
                # 페이지 로드
                driver.get(self.BASE_URL)
                self.wait_for_page_ready(driver)
                
                # 옵션 선택
                self._select_option(driver, '가입유형', task.subscription_type[0])
                time.sleep(1)
                
                self._select_option(driver, '기기종류', task.device_type[0])
                time.sleep(1)
                
                # 요금제 목록 열기 및 선택
                if self._open_rate_plan_modal(driver):
                    time.sleep(1)  # 요금제 목록 로딩 대기
                    
                    # 요금제 선택
                    selected = driver.execute_script("""
                        var planId = arguments[0];
                        var radio = document.getElementById(planId);
                        if (radio) {
                            // 라디오 버튼 직접 체크
                            radio.checked = true;
                            radio.dispatchEvent(new Event('change', { bubbles: true }));
                            radio.dispatchEvent(new Event('click', { bubbles: true }));
                            
                            // 라벨 클릭
                            var label = document.querySelector('label[for="' + planId + '"]');
                            if (label) {
                                label.click();
                                
                                // 라벨 내의 아이콘도 클릭 시도
                                var icon = label.querySelector('i.icon');
                                if (icon) {
                                    icon.click();
                                }
                            }
                            
                            return true;
                        }
                        return false;
                    """, task.rate_plan.id)
                    
                    if not selected:
                        raise Exception("요금제 선택 실패")
                    
                    time.sleep(1)  # 선택 후 대기 시간 증가
                    
                    # 적용 버튼 클릭
                    applied = driver.execute_script("""
                        // 다양한 방법으로 적용 버튼 찾기
                        var buttons = document.querySelectorAll('button');
                        for (var i = 0; i < buttons.length; i++) {
                            if (buttons[i].textContent.trim() === '적용' && 
                                buttons[i].offsetParent !== null) {
                                console.log('적용 버튼 발견:', buttons[i].className);
                                buttons[i].click();
                                return true;
                            }
                        }
                        
                        // 클래스명으로도 시도
                        var btn = document.querySelector('button.c-btn-solid-1-m');
                        if (btn && btn.textContent.includes('적용')) {
                            btn.click();
                            return true;
                        }
                        
                        return false;
                    """)
                    
                    if not applied:
                        raise Exception("적용 버튼 클릭 실패")
                        
                    time.sleep(2)  # 모달 닫히고 데이터 로딩 대기
                
                # 제조사 전체 선택
                driver.execute_script("""
                    var checkbox = document.getElementById('전체');
                    if (checkbox && !checkbox.checked) {
                        checkbox.checked = true;
                        checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                        
                        var label = document.querySelector('label[for="전체"]');
                        if (label) label.click();
                    }
                """)
                
                time.sleep(2)  # 데이터 로딩 대기 시간 증가
                
                # 정렬순서를 "최신 공시일자 순"으로 변경
                sort_changed = driver.execute_script("""
                    var select = document.querySelector('select#cfrmSelect-1-1');
                    if (select) {
                        // 최신 공시일자 순 = value "01"
                        select.value = '01';
                        select.dispatchEvent(new Event('change', { bubbles: true }));
                        console.log('정렬순서 변경: 최신 공시일자 순');
                        return true;
                    }
                    return false;
                """)
                
                if sort_changed:
                    logger.info("정렬순서를 '최신 공시일자 순'으로 변경했습니다.")
                    time.sleep(2)  # 정렬 변경 후 데이터 재로딩 대기
                
                # 요금제 가격 조회
                monthly_price = task.rate_plan.monthly_fee  # 이미 수집한 가격 사용
                if monthly_price == 0 and not self.config['skip_price_check'] and task.rate_plan.value:
                    # 가격이 없을 경우에만 추가 조회
                    monthly_price = self._get_rate_plan_price(driver, task.rate_plan)
                
                # 데이터 추출
                extracted_count = self._extract_data(driver, task, monthly_price)
                
                with self.status_lock:
                    self.completed_count += 1
                    self.total_devices += extracted_count
                
                if RICH_AVAILABLE:
                    console.print(f"[green]✓[/green] {task.rate_plan.name}: {extracted_count}개")
                else:
                    logger.info(f"✓ {task.rate_plan.name}: {extracted_count}개")
                
                return extracted_count
                
            except TimeoutException as e:
                logger.error(f"작업 처리 타임아웃: {e}")
                retry_count += 1
                if driver:
                    driver.quit()
                    driver = None
                if retry_count < self.config['retry_count']:
                    time.sleep(self.config['delay_between_requests'] * 2)
                    continue
            except UnexpectedAlertPresentException as e:
                logger.warning(f"Unexpected Alert 발생: {e}")
                if driver:
                    # Alert 처리 시도
                    self.handle_alert(driver)
                    time.sleep(3)
                retry_count += 1
                if driver:
                    driver.quit()
                    driver = None
                if retry_count < self.config['retry_count']:
                    time.sleep(self.config['delay_between_requests'] * 2)
                    continue
            except Exception as e:
                logger.error(f"작업 처리 오류: {e}")
                retry_count += 1
                if driver:
                    driver.quit()
                    driver = None
                if retry_count < self.config['retry_count']:
                    time.sleep(self.config['delay_between_requests'] * 2)
                    continue
            finally:
                if driver:
                    try:
                        driver.quit()
                        with self.drivers_lock:
                            if driver in self.active_drivers:
                                self.active_drivers.remove(driver)
                    except Exception as e:
                        logger.debug(f"드라이버 종료 중 오류: {e}")
                # 요청 간 지연
                time.sleep(self.config['delay_between_requests'])
        
        with self.status_lock:
            self.failed_count += 1
        
        return extracted_count
    
    def _get_rate_plan_price(self, driver: webdriver.Chrome, rate_plan: RatePlan) -> int:
        """요금제 가격 조회"""
        # 캐시 확인
        with self.cache_lock:
            if rate_plan.value in self.price_cache:
                return int(self.price_cache[rate_plan.value])
        
        price = 0
        
        try:
            # 새 탭에서 조회
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            
            # URL 패턴 생성
            categories = self.PLAN_CATEGORIES_5G if 'LPZ1' in rate_plan.value else self.PLAN_CATEGORIES_LTE
            network = '5g-all' if 'LPZ1' in rate_plan.value else 'lte-all'
            
            # 최대 5개 카테고리만 시도
            for category in categories[:5]:
                url = f"https://www.lguplus.com/mobile/plan/mplan/{network}/{category}/{rate_plan.value}"
                
                try:
                    driver.get(url)
                    self.wait_for_page_ready(driver, 3)
                    
                    # 404 체크
                    if driver.execute_script("return document.title.includes('404')"):
                        continue
                    
                    # 가격 추출
                    price_text = driver.execute_script(r"""
                        var selectors = ['p.price', '.price strong', '.monthly-price'];
                        for (var sel of selectors) {
                            var elems = document.querySelectorAll(sel);
                            for (var elem of elems) {
                                var match = elem.textContent.match(/(\d{1,3}(?:,\d{3})*)\s*원/);
                                if (match) {
                                    var p = parseInt(match[1].replace(/,/g, ''));
                                    if (p >= 5000 && p <= 500000) {
                                        return p;
                                    }
                                }
                            }
                        }
                        return 0;
                    """)
                    
                    if price_text > 0:
                        price = price_text
                        break
                        
                except:
                    continue
            
            # 캐시 저장
            with self.cache_lock:
                self.price_cache[rate_plan.value] = str(price)
            
        except Exception as e:
            logger.debug(f"가격 조회 오류: {e}")
        finally:
            # 원래 탭으로 돌아가기
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        
        return price
    
    def _extract_data(self, driver: webdriver.Chrome, task: CrawlTask, monthly_price: int) -> int:
        """데이터 추출"""
        extracted_count = 0
        page = 1
        max_pages = self.config['max_pages']
        
        while page <= max_pages:
            try:
                # 현재 페이지 데이터 추출 - 실제 HTML 구조에 맞게 수정
                page_data = driver.execute_script("""
                    try {
                        var data = [];
                        
                        // 테이블 찾기 - 여러 개의 테이블이 있을 수 있음
                        var tables = document.querySelectorAll('table.b-table');
                        var table = null;
                        
                        console.log('Found ' + tables.length + ' tables with class b-table');
                        
                        // 데이터가 있는 테이블 찾기 (보통 두 번째 테이블)
                        for (var t = 0; t < tables.length; t++) {
                            var tbody = tables[t].querySelector('tbody');
                            if (tbody && tbody.querySelectorAll('tr').length > 10) {
                                // 10개 이상의 행이 있는 테이블이 데이터 테이블
                                table = tables[t];
                                console.log('Using table index:', t, 'with', tbody.querySelectorAll('tr').length, 'rows');
                                break;
                            }
                        }
                        
                        if (!table && tables.length > 0) {
                            // 10개 이상의 행이 있는 테이블이 없으면 마지막 테이블 사용
                            table = tables[tables.length - 1];
                            console.log('Using last table');
                        }
                        
                        if (!table) {
                            // b-table 클래스가 없을 경우, 일반 table 태그 찾기
                            tables = document.querySelectorAll('table');
                            console.log('No b-table found, trying regular tables: ' + tables.length);
                            
                            for (var t = 0; t < tables.length; t++) {
                                var tbody = tables[t].querySelector('tbody');
                                if (tbody && tbody.querySelectorAll('tr').length > 5) {
                                    table = tables[t];
                                    console.log('Using regular table index:', t, 'with', tbody.querySelectorAll('tr').length, 'rows');
                                    break;
                                }
                            }
                        }
                        
                        if (!table) {
                            console.log('No table found at all');
                            return data;
                        }
                        
                        var tbody = table.querySelector('tbody');
                        if (!tbody) {
                            console.log('No tbody found');
                            return data;
                        }
                        
                        var rows = tbody.querySelectorAll('tr');
                        console.log('Found ' + rows.length + ' rows in tbody');
                        
                        var currentDevice = null;
                        var currentPrice = null;
                        var currentDate = null;
                        
                        for (var i = 0; i < rows.length; i++) {
                            var row = rows[i];
                            var cells = row.querySelectorAll('td');
                            
                            if (cells.length === 0) continue;
                            
                            // 새로운 기기 정보 (첫 번째 셀에 rowspan이 있는 경우)
                            if (cells[0] && cells[0].hasAttribute('rowspan')) {
                                // 기기명 추출 - a 태그 내부의 span.tit 찾기
                                var deviceSpan = cells[0].querySelector('a span.tit');
                                if (deviceSpan) {
                                    currentDevice = deviceSpan.textContent.trim();
                                } else {
                                    // span.tit이 없으면 a 태그 전체 텍스트
                                    var deviceLink = cells[0].querySelector('a');
                                    if (deviceLink) {
                                        currentDevice = deviceLink.textContent.trim();
                                    } else {
                                        currentDevice = cells[0].textContent.trim();
                                    }
                                }
                                
                                // 출고가 (두 번째 셀)
                                if (cells[1]) {
                                    currentPrice = cells[1].textContent.replace(/[원,]/g, '').trim();
                                }
                                
                                // 공시일자는 세 번째 셀에 있습니다 (rowspan된 셀)
                                if (cells[2] && cells[2].hasAttribute('rowspan')) {
                                    currentDate = cells[2].textContent.trim();
                                }
                                
                                console.log('Found device: ' + currentDevice + ', price: ' + currentPrice + ', date: ' + currentDate);
                            }
                            
                            // 24개월 유지 데이터 찾기
                            var planDurationIndex = -1;
                            for (var j = 0; j < cells.length; j++) {
                                var cellText = cells[j].textContent.trim();
                                if (cellText === '24개월 유지') {
                                    planDurationIndex = j;
                                    break;
                                }
                            }
                            
                            // 24개월 유지 데이터가 있는 경우
                            if (planDurationIndex >= 0 && currentDevice) {
                                console.log('Processing 24-month row for device:', currentDevice);
                                
                                // 새로운 HTML 구조에 맞게 인덱스 사용
                                // 테이블 헤더: 기기명/모델명 | 출고가 | 공시일자 | 요금제 유지 기간 | 이통사지원금 | 유통망지원금 | 지원금 총액 | 추천 할인 | 구매가 | 구매하기
                                var subsidy = '0';
                                var distributorSubsidy = '0';
                                var totalSubsidy = '0';
                                var finalPrice = '0';
                                
                                // 이통사지원금 (24개월 유지 다음 셀)
                                if (cells[planDurationIndex + 1]) {
                                    subsidy = cells[planDurationIndex + 1].textContent.replace(/[원,]/g, '').trim();
                                }
                                
                                // 유통망지원금 (이통사지원금 다음 셀)
                                if (cells[planDurationIndex + 2]) {
                                    distributorSubsidy = cells[planDurationIndex + 2].textContent.replace(/[원,]/g, '').trim();
                                }
                                
                                // 지원금 총액 (유통망지원금 다음 셀, p.fw-b.point 클래스를 가진 요소)
                                if (cells[planDurationIndex + 3]) {
                                    var totalElement = cells[planDurationIndex + 3].querySelector('p.fw-b.point');
                                    if (totalElement) {
                                        totalSubsidy = totalElement.textContent.replace(/[원,]/g, '').trim();
                                    } else {
                                        totalSubsidy = cells[planDurationIndex + 3].textContent.replace(/[원,]/g, '').trim();
                                    }
                                }
                                
                                // 구매가 (추천할인 다음 셀)
                                if (cells[planDurationIndex + 5]) {
                                    finalPrice = cells[planDurationIndex + 5].textContent.replace(/[원,]/g, '').trim();
                                }
                                
                                console.log('Extracted data:', {
                                    device: currentDevice,
                                    subsidy: subsidy,
                                    total: totalSubsidy,
                                    final: finalPrice
                                });
                                
                                data.push({
                                    device: currentDevice,
                                    price: currentPrice,
                                    date: currentDate,
                                    subsidy: subsidy,
                                    additionalSubsidy: distributorSubsidy,  // 유통망지원금 = 추가지원금
                                    totalSubsidy: totalSubsidy,
                                    finalPrice: finalPrice,
                                    planDuration: '24개월 유지'
                                });
                            }
                        }
                        
                        console.log('Total data extracted: ' + data.length);
                        return data;
                    } catch(e) {
                        console.error('Error in data extraction:', e);
                        return [];
                    }
                """)
                
                # 데이터 저장 - 통합 형식으로 변환
                for item in page_data:
                    # 제조사 추출
                    device_nm = item.get('device', '')
                    manufacturer = '기타'
                    if '갤럭시' in device_nm or 'Galaxy' in device_nm.lower():
                        manufacturer = '삼성'
                    elif '아이폰' in device_nm or 'iPhone' in device_nm:
                        manufacturer = '애플'
                    elif 'LG' in device_nm:
                        manufacturer = 'LG'
                    elif '샤오미' in device_nm or 'Xiaomi' in device_nm:
                        manufacturer = '샤오미'
                    
                    # 월정액이 0원인 경우 로그만 남기고 계속 진행
                    if monthly_price <= 0:
                        logger.debug(f"월정액 0원 데이터: {task.rate_plan.name} - {device_nm}")
                    
                    # 공시일 파싱
                    date_str = item.get('date', '')
                    if date_str:
                        try:
                            # "2025.01.10" 형식을 "2025-01-10"으로 변환
                            date_str = date_str.replace('.', '-')
                            # 날짜가 올바른 형식인지 확인
                            datetime.strptime(date_str, '%Y-%m-%d')
                        except:
                            # 파싱 실패 시 현재 날짜 사용
                            date_str = datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d')
                    else:
                        date_str = datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d')
                    
                    # 지원금 계산
                    public_support = int(item.get('subsidy', '0'))  # 이통사지원금 (공시지원금)
                    additional_support = int(item.get('additionalSubsidy', '0'))  # 유통망지원금 (추가지원금)
                    
                    # 지원금 총액 = 이통사지원금 + 유통망지원금
                    total_support = public_support + additional_support
                    
                    # 통합 데이터 형식
                    device_data = DeviceData(
                        date=date_str,
                        crawled_at=datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S'),
                        carrier='LG',
                        manufacturer=manufacturer,
                        scrb_type_name=task.subscription_type[1],
                        network_type=task.device_type[1],
                        device_nm=device_nm,
                        plan_name=task.rate_plan.name,
                        monthly_fee=monthly_price,
                        release_price=int(item.get('price', '0')),
                        public_support_fee=public_support,  # 이통사지원금
                        additional_support_fee=additional_support,  # 추가지원금 (추가이통사 + 유통망)
                        total_support_fee=total_support,  # 지원금 총액
                        total_price=int(item.get('finalPrice', '0'))
                    )
                    
                    with self.data_lock:
                        self.all_data.append(device_data)
                    
                    extracted_count += 1
                
                # 다음 페이지 확인
                if page >= max_pages or len(page_data) == 0:
                    break
                
                # 다음 페이지로 이동
                has_next = driver.execute_script("""
                    var pagination = document.querySelector('.pagination');
                    if (!pagination) return false;
                    
                    var buttons = pagination.querySelectorAll('li');
                    for (var i = 0; i < buttons.length; i++) {
                        if (buttons[i].classList.contains('active')) {
                            if (i + 1 < buttons.length) {
                                var nextBtn = buttons[i + 1].querySelector('button, a');
                                if (nextBtn && !buttons[i + 1].classList.contains('disabled')) {
                                    nextBtn.click();
                                    return true;
                                }
                            }
                            break;
                        }
                    }
                    return false;
                """)
                
                if not has_next:
                    break
                
                page += 1
                time.sleep(1)
                
            except Exception as e:
                logger.debug(f"페이지 {page} 데이터 추출 오류: {e}")
                break
        
        return extracted_count
    
    def run_single_thread(self, tasks: List[CrawlTask]):
        """단일 스레드 실행"""
        logger.info("단일 스레드 모드로 실행 중...")
        
        if RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TextColumn("• {task.fields[status]}"),
                TimeRemainingColumn(),
                console=console,
                refresh_per_second=2
            ) as progress:
                
                main_task = progress.add_task(
                    "[green]전체 진행률",
                    total=len(tasks),
                    status=f"수집: 0개"
                )
                
                for task in tasks:
                    self.process_task(task, progress, main_task)
                    progress.advance(main_task)
                    
                    # 상태 업데이트
                    elapsed = time.time() - self.start_time
                    speed = self.completed_count / (elapsed / 60) if elapsed > 0 else 0
                    
                    progress.update(
                        main_task,
                        status=f"수집: {self.total_devices:,}개 | 속도: {speed:.1f}개/분"
                    )
                    
                    # 체크포인트 저장
                    if (self.completed_count + self.failed_count) % self.config['checkpoint_interval'] == 0:
                        self.save_checkpoint()
        else:
            for i, task in enumerate(tasks):
                self.process_task(task)
                print(f"진행: {i+1}/{len(tasks)} ({(i+1)/len(tasks)*100:.1f}%)")
                
                if (self.completed_count + self.failed_count) % self.config['checkpoint_interval'] == 0:
                    self.save_checkpoint()
    
    def run_multi_thread(self, tasks: List[CrawlTask]):
        """멀티 스레드 실행"""
        logger.info(f"멀티스레드 모드로 실행 중... (워커: {self.config['max_workers']}개)")
        
        with ThreadPoolExecutor(max_workers=self.config['max_workers']) as executor:
            # 작업 제출
            futures = {executor.submit(self.process_task, task): task for task in tasks}
            
            # Progress 표시
            if self.config['use_rich'] and console:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    MofNCompleteColumn(),
                    TextColumn("• {task.fields[status]}"),
                    TimeRemainingColumn(),
                    console=console,
                    refresh_per_second=2
                ) as progress:
                    
                    task_progress = progress.add_task(
                        "[green]전체 진행률",
                        total=len(tasks),
                        status=f"수집: 0개"
                    )
                    
                    for future in as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            logger.error(f"스레드 오류: {e}")
                        
                        progress.advance(task_progress)
                        
                        # 상태 업데이트
                        elapsed = time.time() - self.start_time
                        speed = self.completed_count / (elapsed / 60) if elapsed > 0 else 0
                        
                        progress.update(
                            task_progress,
                            status=f"수집: {self.total_devices:,}개 | 속도: {speed:.1f}개/분"
                        )
                        
                        # 체크포인트 저장
                        if (self.completed_count + self.failed_count) % self.config['checkpoint_interval'] == 0:
                            self.save_checkpoint()
            else:
                # 일반 출력
                completed = 0
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"스레드 오류: {e}")
                    
                    completed += 1
                    print(f"진행: {completed}/{len(tasks)} ({completed/len(tasks)*100:.1f}%)")
                    
                    # 체크포인트 저장
                    if (self.completed_count + self.failed_count) % self.config['checkpoint_interval'] == 0:
                        self.save_checkpoint()
    
    def save_checkpoint(self):
        """체크포인트 저장"""
        checkpoint_data = {
            'completed': self.completed_count,
            'failed': self.failed_count,
            'data': [vars(d) for d in self.all_data],
            'price_cache': self.price_cache.copy(),
            'rate_plans': self.rate_plans,
            'all_combinations': self.all_combinations,
            'timestamp': datetime.now(ZoneInfo('Asia/Seoul')).isoformat()
        }
        
        try:
            with open(self.checkpoint_file, 'wb') as f:
                pickle.dump(checkpoint_data, f)
            logger.debug("체크포인트 저장 완료")
        except Exception as e:
            logger.error(f"체크포인트 저장 실패: {e}")
    
    def load_checkpoint(self) -> bool:
        """체크포인트 로드"""
        if not os.path.exists(self.checkpoint_file):
            return False
        
        try:
            with open(self.checkpoint_file, 'rb') as f:
                data = pickle.load(f)
            
            self.completed_count = data.get('completed', 0)
            self.failed_count = data.get('failed', 0)
            self.all_data = [DeviceData(**d) for d in data.get('data', [])]
            self.price_cache = data.get('price_cache', {})
            self.rate_plans = data.get('rate_plans', {})
            self.all_combinations = data.get('all_combinations', [])
            
            logger.info(f"체크포인트 로드: {data['timestamp']}")
            return True
        except Exception as e:
            logger.error(f"체크포인트 로드 실패: {e}")
            return False
    
    def save_results(self):
        """결과 저장"""
        if not self.all_data:
            if RICH_AVAILABLE:
                console.print("[red]저장할 데이터가 없습니다.[/red]")
            else:
                logger.warning("저장할 데이터가 없습니다.")
            return []
        
        # DataFrame 생성
        df = pd.DataFrame([vars(d) for d in self.all_data])
        
        # 파일 저장
        timestamp = datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%d_%H%M%S')
        saved_files = []
        
        # Excel generation removed - only keeping CSV
        
        # CSV
        csv_file = get_raw_data_path('lg', 'csv')
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        saved_files.append(str(csv_file))
        
        if RICH_AVAILABLE:
            console.print(f"[green]✅ CSV 저장:[/green] {csv_file}")
        else:
            logger.info(f"✅ CSV 저장: {csv_file}")
        
        # 통계 출력
        self._print_statistics(df)
        
        return saved_files
    
    def _print_statistics(self, df: pd.DataFrame):
        """통계 출력"""
        if self.config['use_rich'] and console:
            # 요약 테이블
            summary_table = Table(title="크롤링 결과 요약", show_header=True, header_style="bold cyan")
            summary_table.add_column("항목", style="yellow")
            summary_table.add_column("수치", justify="right", style="green")
            
            summary_table.add_row("총 데이터", f"{len(df):,}개")
            summary_table.add_row("가입유형", f"{df['scrb_type_name'].nunique()}개")
            summary_table.add_row("기기종류", f"{df['network_type'].nunique()}개")
            summary_table.add_row("요금제", f"{df['plan_name'].nunique()}개")
            summary_table.add_row("디바이스", f"{df['device_nm'].nunique()}개")
            summary_table.add_row("평균 월요금", f"{df['monthly_fee'].mean():,.0f}원")
            summary_table.add_row("평균 공시지원금", f"{df['public_support_fee'].mean():,.0f}원")
            summary_table.add_row("최대 공시지원금", f"{df['public_support_fee'].max():,.0f}원")
            
            console.print("\n")
            console.print(summary_table)
        else:
            print("\n" + "="*50)
            print("크롤링 결과 요약")
            print("="*50)
            print(f"총 데이터: {len(df):,}개")
            print(f"가입유형: {df['scrb_type_name'].nunique()}개")
            print(f"기기종류: {df['network_type'].nunique()}개")
            print(f"요금제: {df['plan_name'].nunique()}개")
            print(f"디바이스: {df['device_nm'].nunique()}개")
            print(f"평균 월요금: {df['monthly_fee'].mean():,.0f}원")
            print(f"평균 공시지원금: {df['public_support_fee'].mean():,.0f}원")
            print(f"최대 공시지원금: {df['public_support_fee'].max():,.0f}원")
    
    def run(self):
        """메인 실행"""
        self.start_time = time.time()
        
        try:
            # 헤더 출력
            if self.config['use_rich'] and console:
                console.print(Panel.fit(
                    "[bold cyan]LG U+ 공시지원금 크롤러[/bold cyan]\n"
                    "[yellow]통합 버전 v6.1[/yellow]",
                    border_style="cyan"
                ))
            else:
                print("\n" + "="*60)
                print("LG U+ 공시지원금 크롤러")
                print("통합 버전 v6.1")
                print("="*60)
            
            # 체크포인트 확인
            if self.config.get('resume') and self.load_checkpoint():
                if RICH_AVAILABLE:
                    console.print("[yellow]체크포인트에서 재개합니다.[/yellow]")
                else:
                    logger.info("체크포인트에서 재개합니다.")
                
                # 이미 작업이 있으면 계속 진행
                if self.all_combinations:
                    tasks = self.all_combinations
                else:
                    tasks = self.prepare_tasks()
            else:
                # 요금제 수집
                self.collect_rate_plans()
                
                if not self.rate_plans:
                    if RICH_AVAILABLE:
                        console.print("[red]수집된 요금제가 없습니다.[/red]")
                    else:
                        logger.error("수집된 요금제가 없습니다.")
                    return []
                
                # 작업 준비
                tasks = self.prepare_tasks()
            
            if not tasks:
                if RICH_AVAILABLE:
                    console.print("[red]크롤링할 작업이 없습니다.[/red]")
                else:
                    logger.error("크롤링할 작업이 없습니다.")
                return []
            
            if RICH_AVAILABLE:
                console.print(f"\n[cyan]총 {len(tasks)}개 작업 준비 완료[/cyan]")
            else:
                logger.info(f"\n총 {len(tasks)}개 작업 준비 완료")
            
            # 크롤링 실행
            if RICH_AVAILABLE:
                console.print(Panel.fit(
                    f"[bold cyan]공시지원금 데이터 수집 시작[/bold cyan]\n"
                    f"[yellow]워커: {self.config['max_workers']}개[/yellow]",
                    border_style="cyan"
                ))
            else:
                print(f"\n공시지원금 데이터 수집 시작")
                print(f"워커: {self.config['max_workers']}개")
            
            if self.config['max_workers'] > 1:
                self.run_multi_thread(tasks)
            else:
                self.run_single_thread(tasks)
            
            # 결과 저장
            saved_files = self.save_results()
            
            # 완료 메시지
            elapsed = time.time() - self.start_time
            
            if RICH_AVAILABLE:
                # 통계 테이블
                table = Table(title="크롤링 완료", show_header=True, header_style="bold magenta")
                table.add_column("항목", style="cyan", width=20)
                table.add_column("수치", justify="right", style="yellow")
                
                table.add_row("소요 시간", f"{elapsed/60:.1f}분")
                table.add_row("성공", f"{self.completed_count:,}개")
                table.add_row("실패", f"{self.failed_count:,}개")
                table.add_row("총 수집 데이터", f"{self.total_devices:,}개")
                table.add_row("평균 속도", f"{self.completed_count/(elapsed/60):.1f}개/분" if elapsed > 0 else "0개/분")
                
                console.print("\n")
                console.print(table)
            else:
                print(f"\n크롤링 완료!")
                print(f"소요 시간: {elapsed/60:.1f}분")
                print(f"성공: {self.completed_count}개")
                print(f"실패: {self.failed_count}개")
                print(f"총 수집 데이터: {self.total_devices}개")
            
            # 체크포인트 삭제
            if self.checkpoint_file.exists():
                self.checkpoint_file.unlink()
            
            return saved_files
            
        except KeyboardInterrupt:
            if RICH_AVAILABLE:
                console.print("\n[yellow]사용자에 의해 중단되었습니다.[/yellow]")
            else:
                print("\n사용자에 의해 중단되었습니다.")
            self.save_checkpoint()
            # 중단 시점 데이터 저장
            if self.all_data:
                saved_files = self.save_results()
                return saved_files
            return []
        except Exception as e:
            logger.error(f"크롤링 오류: {e}")
            if self.config['debug']:
                traceback.print_exc()
            self.save_checkpoint()
            # 오류 시 데이터 저장
            if self.all_data:
                saved_files = self.save_results()
                return saved_files
            return []
    
    def __del__(self):
        """객체 소멸자 - 모든 드라이버 정리"""
        try:
            # 활성 드라이버 모두 정리
            if hasattr(self, 'active_drivers') and hasattr(self, 'drivers_lock'):
                with self.drivers_lock:
                    for driver in self.active_drivers:
                        try:
                            driver.quit()
                        except:
                            pass
                    self.active_drivers.clear()
                    
                    # 활성 서비스 모두 정리
                    if hasattr(self, 'active_services'):
                        for service in self.active_services:
                            try:
                                service.stop()
                            except:
                                pass
                        self.active_services.clear()
        except:
            pass


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='LG U+ 공시지원금 크롤러',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # 기본 옵션
    parser.add_argument('--workers', type=int, default=3,
                        help='워커 수 (기본: 3)')
    parser.add_argument('--headless', action='store_true', 
                        help='헤드리스 모드 강제 실행 (deprecated, 기본값)')
    parser.add_argument('--show-browser', action='store_true',
                        help='브라우저 표시 (헤드리스 모드 무시)')
    parser.add_argument('--no-headless', dest='headless', action='store_false',
                        help='GUI 모드로 실행 (deprecated, --show-browser 사용 권장)')
    
    # 크롤링 옵션
    parser.add_argument('--max-pages', type=int, default=10,
                        help='최대 페이지 수 (기본값: 10)')
    parser.add_argument('--max-rate-plans', type=int, default=0,
                        help='최대 요금제 수 (0=전체, 기본값: 0)')
    parser.add_argument('--skip-price-check', action='store_true',
                        help='요금제 가격 조회 스킵')
    
    # 기타 옵션
    parser.add_argument('--output', type=str, default='data',
                        help='출력 디렉토리 (기본값: data)')
    parser.add_argument('--resume', action='store_true',
                        help='체크포인트에서 재개')
    parser.add_argument('--debug', action='store_true',
                        help='디버그 모드')
    parser.add_argument('--no-rich', action='store_true',
                        help='Rich UI 비활성화')
    parser.add_argument('--test', action='store_true',
                        help='테스트 모드 (처음 5개 요금제만)')
    parser.add_argument('--delay', type=int, default=2,
                        help='요청 간 지연 시간(초) (기본: 2)')
    
    args = parser.parse_args()
    
    # 설정
    config = {
        'max_workers': args.workers,
        'headless': True if not args.show_browser else False,  # 기본적으로 헤드리스 모드
        'max_pages': args.max_pages,
        'max_rate_plans': 5 if args.test else args.max_rate_plans,
        'skip_price_check': args.skip_price_check,
        'output_dir': args.output,
        'resume': args.resume,
        'debug': args.debug,
        'use_rich': RICH_AVAILABLE and not args.no_rich,
        'delay_between_requests': args.delay
    }
    
    # 크롤러 실행
    crawler = LGUPlusCrawler(config)
    saved_files = crawler.run()
    
    sys.exit(0 if saved_files else 1)


if __name__ == '__main__':
    # 인자 없이 실행시 기본 실행 (3 workers)
    if len(sys.argv) == 1:
        config = {'max_workers': 3}
        crawler = LGUPlusCrawler(config)
        crawler.run()
    else:
        main()