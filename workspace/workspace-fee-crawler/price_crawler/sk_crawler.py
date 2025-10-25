#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SKT T world 공시지원금 크롤러 - 통합 버전 (수정)
통일된 UI, 데이터 형식, 로깅 시스템

작성일: 2025-01-11
버전: 3.1
"""

import time
import json
import re
import os
import shutil
from urllib.parse import urlencode, quote_plus
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, UnexpectedAlertPresentException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import pandas as pd
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import List, Dict, Optional, Tuple
import traceback
import pickle
import argparse
import sys

# Rich library for better UI
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn, MofNCompleteColumn
    from rich.table import Table
    from rich.panel import Panel
    from rich.live import Live
    from rich.layout import Layout
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Warning: Rich library not installed. Install with: pip install rich")

# 콘솔 초기화
console = Console() if RICH_AVAILABLE else None

# Path imports
from shared_config.config.paths import PathManager, get_raw_data_path, get_checkpoint_path, get_log_path

# 경로 매니저 초기화
path_manager = PathManager()

# 로깅 설정
log_file = get_log_path('sk_crawler', 'crawlers')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler() if not RICH_AVAILABLE else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# 기본 설정
BASE_URL = "https://shop.tworld.co.kr"


class TworldCrawler:
    """SKT T world 크롤러 - 통합 버전"""
    
    def __init__(self, config=None):
        """초기화"""
        self.driver = None
        self.all_data = []
        self.data_lock = threading.Lock()
        self.rate_plans = []
        self.categories = []
        self.active_drivers = []  # 활성 드라이버 추적
        self.active_services = []  # 활성 서비스 추적
        self.drivers_lock = threading.Lock()  # 드라이버 목록 보호
        
        # 기본 설정
        self.config = {
            'headless': True,
            'max_workers': 3,  # 3개의 스레드로 병렬 처리
            'retry_count': 3,
            'page_load_timeout': 90,  # 증가 (45->90) 네트워크 안정성 확보
            'element_wait_timeout': 30,  # 증가 (20->30) 요소 대기 시간 확보
            'checkpoint_interval': 20,  # 더 자주 저장 (30->20)
            'save_formats': ['csv'],
            'output_dir': path_manager.data_dir,
            'max_rate_plans': 0,  # 0 = 모든 요금제
            'show_browser': False,
            'delay_between_requests': 5,  # 5초로 증가하여 안정성 확보
            'alert_wait_time': 3,
            'network_error_wait': 60,  # 증가 (30->60) 네트워크 오류 복구 대기
            'implicit_wait': 10,  # 암시적 대기 추가
            'page_load_strategy': 'eager'  # DOM 로드 완료 시점에 진행
        }
        
        if config:
            self.config.update(config)
        
        # 진행 상태 추적
        self.completed_count = 0
        self.failed_count = 0
        self.total_devices = 0
        self.start_time = None
        self.checkpoint_file = get_checkpoint_path('sk')
        
        # 스레드 안전 변수
        self.status_lock = threading.Lock()
        self.current_tasks = {}
        
        # 크롤링 조합
        self.all_combinations = []
        
    def setup_driver(self):
        """Chrome 드라이버 설정 - 개선된 버전"""
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
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        
        # 메모리 최적화
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max_old_space_size=4096')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-features=TranslateUI')
        
        # User-Agent 및 프로필 설정
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        options.add_argument(f'user-agent={user_agent}')
        
        # 차단 회피를 위한 추가 옵션
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--ignore-certificate-errors')
        
        # 이미지 로딩 비활성화로 속도 향상
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.media_stream": 2,
            "profile.default_content_setting_values.automatic_downloads": 2
        }
        options.add_experimental_option("prefs", prefs)
        
        # 페이지 로드 전략 설정
        options.page_load_strategy = self.config.get('page_load_strategy', 'normal')
        
        if self.config['headless'] and not self.config.get('show_browser'):
            options.add_argument('--headless=new')
        
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
                
                # ChromeDriver 다운로드 및 설치
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
                
                # Track both driver and service
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
        driver.set_page_load_timeout(self.config['page_load_timeout'])
        driver.implicitly_wait(self.config.get('implicit_wait', 10))
        
        # JavaScript로 webdriver 속성 숨기기 및 추가 위장
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
    
    def create_driver(self):
        """스레드용 드라이버 생성"""
        driver = self.setup_driver()
        # Note: driver is already added to active_drivers in setup_driver
        return driver
    
    def handle_alert(self, driver):
        """Alert 처리"""
        try:
            # 알림 대기 시간을 짧게 설정 (2초)
            WebDriverWait(driver, 2).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert_text = alert.text
            logger.warning(f"Alert detected: {alert_text}")
            alert.accept()
            time.sleep(1)
            
            # 특정 alert 메시지에 대한 처리
            if "네트워크" in alert_text or "오류" in alert_text:
                logger.warning("네트워크 오류 감지")
                return 'network_error'
            elif "실패" in alert_text or "새로고침" in alert_text:
                logger.warning("조회 실패")
                return 'refresh_needed'
                
            return 'handled'
        except TimeoutException:
            # 알림이 없음 - 정상
            return None
        except Exception as e:
            logger.debug(f"Alert 처리 오류: {e}")
            return False
    
    def wait_for_page_ready(self, driver, timeout=None):
        """페이지 로딩 대기"""
        if timeout is None:
            timeout = self.config.get('element_wait_timeout', 30)
            
        try:
            # document ready 상태 확인 (더 짧은 시간)
            WebDriverWait(driver, min(timeout, 10)).until(
                lambda d: d.execute_script("return document.readyState") in ["complete", "interactive"]
            )
            
            # 페이지에 특정 요소가 나타날 때까지 대기
            selectors_to_check = [
                "table",
                ".disclosure-list",
                ".data-list",
                ".result-table",
                "td"
            ]
            
            # 여러 선택자 중 하나라도 발견되면 OK
            WebDriverWait(driver, timeout).until(
                lambda d: any(d.find_elements(By.CSS_SELECTOR, selector) for selector in selectors_to_check)
            )
            
        except TimeoutException:
            logger.warning("페이지 요소 대기 타임아웃, 현재 상태로 계속 진행")
        except Exception as e:
            logger.debug(f"페이지 대기 중 오류: {e}")
        
        time.sleep(2)  # 약간의 추가 대기
    
    def collect_rate_plans(self):
        """모든 요금제 수집"""
        if RICH_AVAILABLE:
            console.print(Panel.fit(
                "[bold cyan]요금제 목록 수집 시작...[/bold cyan]",
                border_style="cyan"
            ))
        else:
            print("\n요금제 목록 수집 시작...")
        
        driver = self.setup_driver()
        
        try:
            # 요금제 목록 페이지 접속
            url = "https://shop.tworld.co.kr/wireless/product/subscription/list"
            logger.info(f"요금제 목록 페이지 접속: {url}")
            
            driver.get(url)
            self.wait_for_page_ready(driver, 10)
            
            # 카테고리 목록 수집
            self.collect_categories(driver)
            
            if not self.categories:
                logger.error("카테고리를 찾을 수 없습니다.")
                return
            
            if RICH_AVAILABLE:
                console.print(f"\n[green]✓[/green] 총 {len(self.categories)}개 카테고리 발견")
                
                # Progress bar로 카테고리별 요금제 수집
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    MofNCompleteColumn(),
                    TimeRemainingColumn(),
                    console=console
                ) as progress:
                    
                    task = progress.add_task(
                        "[cyan]카테고리 처리",
                        total=len(self.categories)
                    )
                    
                    for idx, category in enumerate(self.categories, 1):
                        progress.update(
                            task,
                            description=f"[cyan]{category['name']} 처리 중..."
                        )
                        
                        try:
                            # 카테고리 클릭
                            self.click_category(driver, category['id'])
                            time.sleep(2)
                            
                            # 해당 카테고리의 요금제 수집
                            plans = self.collect_plans_in_category(driver, category)
                            
                            if plans:
                                console.print(f"[green]✓[/green] {category['name']}: {len(plans)}개 요금제")
                                self.rate_plans.extend(plans)
                            else:
                                console.print(f"[yellow]-[/yellow] {category['name']}: 요금제 없음")
                            
                            progress.advance(task)
                            
                        except Exception as e:
                            logger.error(f"카테고리 처리 오류: {e}")
                            progress.advance(task)
                            continue
            else:
                # Rich 없을 때
                logger.info(f"\n총 {len(self.categories)}개 카테고리 발견")
                
                for idx, category in enumerate(self.categories, 1):
                    logger.info(f"\n[{idx}/{len(self.categories)}] {category['name']} 카테고리 요금제 수집 중...")
                    
                    try:
                        self.click_category(driver, category['id'])
                        time.sleep(2)
                        plans = self.collect_plans_in_category(driver, category)
                        
                        if plans:
                            logger.info(f"  ✓ {len(plans)}개 요금제 수집")
                            self.rate_plans.extend(plans)
                    except Exception as e:
                        logger.error(f"  카테고리 처리 오류: {e}")
                        continue
            
            # 중복 제거
            unique_plans = {}
            for plan in self.rate_plans:
                unique_plans[plan['id']] = plan
            self.rate_plans = list(unique_plans.values())
            
            # 요금제 수 제한
            if self.config['max_rate_plans'] > 0:
                self.rate_plans = self.rate_plans[:self.config['max_rate_plans']]
            
            # 결과 출력
            if RICH_AVAILABLE:
                table = Table(title="수집된 요금제 현황", show_header=True)
                table.add_column("구분", style="cyan")
                table.add_column("개수", justify="right", style="yellow")
                
                # 카테고리별 통계
                cat_stats = {}
                for plan in self.rate_plans:
                    cat = plan['category']
                    cat_stats[cat] = cat_stats.get(cat, 0) + 1
                
                for cat, count in sorted(cat_stats.items()):
                    table.add_row(cat, f"{count}개")
                table.add_row("총계", f"{len(self.rate_plans)}개", style="bold")
                
                console.print("\n")
                console.print(table)
            else:
                logger.info(f"\n총 {len(self.rate_plans)}개 요금제 수집 완료")
                
        finally:
            if driver:
                try:
                    driver.quit()
                    with self.drivers_lock:
                        if driver in self.active_drivers:
                            idx = self.active_drivers.index(driver)
                            self.active_drivers.remove(driver)
                            # Stop and remove corresponding service
                            if idx < len(self.active_services):
                                try:
                                    self.active_services[idx].stop()
                                except:
                                    pass
                                self.active_services.pop(idx)
                except Exception as e:
                    logger.debug(f"드라이버 종료 중 오류: {e}")
    
    def collect_categories(self, driver):
        """카테고리 목록 수집"""
        try:
            # 페이지 로딩 대기
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.phone-charge-type"))
            )
            
            category_elements = driver.find_elements(
                By.CSS_SELECTOR, 
                "ul.phone-charge-type li.type-item"
            )
            
            for element in category_elements:
                try:
                    category_id = element.get_attribute("data-category-id")
                    category_name = element.find_element(By.TAG_NAME, "a").text.strip()
                    
                    if category_id and category_name:
                        self.categories.append({
                            'id': category_id,
                            'name': category_name
                        })
                        
                except Exception as e:
                    logger.debug(f"카테고리 추출 오류: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"카테고리 목록 수집 오류: {e}")
    
    def click_category(self, driver, category_id):
        """특정 카테고리 클릭"""
        try:
            category_element = driver.find_element(
                By.CSS_SELECTOR, 
                f"li.type-item[data-category-id='{category_id}']"
            )
            
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(category_element)
            )
            
            driver.execute_script("arguments[0].scrollIntoView(true);", category_element)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", category_element)
            
        except Exception as e:
            logger.error(f"카테고리 클릭 오류: {e}")
            raise
    
    def collect_plans_in_category(self, driver, category):
        """현재 카테고리의 요금제 수집"""
        plans = []
        
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.phone-charge-list"))
            )
            
            # JavaScript로 요금제 데이터 추출
            js_code = """
            var plans = [];
            document.querySelectorAll('li.charge-item').forEach(function(el) {
                var id = el.getAttribute('data-subscription-id');
                var name = el.getAttribute('data-subscription-nm');
                if(id && name && id.startsWith('NA')) {
                    var priceElement = el.querySelector('.price .num');
                    var monthlyFee = 0;
                    if(priceElement) {
                        var priceText = priceElement.textContent.trim();
                        monthlyFee = parseInt(priceText.replace(/[^0-9]/g, '')) || 0;
                    }
                    
                    plans.push({
                        id: id,
                        name: name,
                        monthlyFee: monthlyFee
                    });
                }
            });
            return JSON.stringify(plans);
            """
            
            result = driver.execute_script(js_code)
            if result:
                category_plans = json.loads(result)
                for plan in category_plans:
                    plan['category'] = category['name']
                    plan['monthly_fee'] = plan.pop('monthlyFee')
                    plans.append(plan)
                    
        except TimeoutException:
            logger.debug(f"카테고리 {category['name']}에 요금제가 없습니다.")
        except Exception as e:
            logger.error(f"요금제 수집 오류: {e}")
            
        return plans
    
    def prepare_combinations(self):
        """크롤링 조합 준비"""
        if not self.rate_plans:
            return
        
        # 가입유형별로 수집
        scrb_types = [
            {'value': '31', 'name': '기기변경'},
            {'value': '11', 'name': '신규가입'}, 
            {'value': '20', 'name': '번호이동'}  # value 수정: 41 -> 20
        ]
        
        # 모든 요금제에 대해 5G와 4G 모두 검색
        network_types = [
            {'code': '5G', 'name': '5G'},
            {'code': 'PHONE', 'name': 'LTE'}
        ]
        
        # 모든 가입유형에 대해 크롤링
        for plan in self.rate_plans:
            for network in network_types:
                for scrb_type in scrb_types:
                    self.all_combinations.append({
                        'plan': plan,
                        'network': network,
                        'scrb_type': scrb_type
                    })
        
        if RICH_AVAILABLE:
            console.print(f"\n[cyan]총 {len(self.all_combinations)}개 조합 준비 완료[/cyan]")
        else:
            logger.info(f"\n총 {len(self.all_combinations)}개 조합 준비 완료")
    
    def process_combination(self, combo_index, progress=None, task_id=None):
        """단일 조합 처리"""
        combo = self.all_combinations[combo_index]
        driver = None
        thread_id = threading.current_thread().name
        retry_count = 0
        
        # 현재 작업 상태 업데이트
        with self.status_lock:
            self.current_tasks[thread_id] = f"{combo['plan']['name'][:30]} - {combo['network']['name']}"
        
        while retry_count < self.config['retry_count']:
            try:
                driver = self.create_driver()
                
                # 진행 상황 업데이트
                if progress and task_id is not None:
                    desc = f"[{combo_index+1}/{len(self.all_combinations)}] {combo['plan']['name'][:30]}... ({combo['network']['name']})"
                    if retry_count > 0:
                        desc += f" (재시도 {retry_count+1}/{self.config['retry_count']})"
                    progress.update(task_id, description=desc)
                
                # URL 생성
                params = {
                    'modelNwType': combo['network']['code'],
                    'saleMonth': '24',
                    'prodId': combo['plan']['id'],
                    'prodNm': combo['plan']['name'],
                    'saleYn': 'Y',
                    'order': 'CHANGEPRICE',  # 최근 변경 순 정렬
                    'scrbTypCd': combo['scrb_type']['value']
                }
                url = f"{BASE_URL}/notice?{urlencode(params, quote_via=quote_plus)}"
                
                # 페이지 로드 (타임아웃 처리 개선)
                page_loaded = False
                logger.info(f"URL 접속 시도: {url[:100]}...")
                logger.info(f"정렬 파라미터: order={params.get('order')}")
                
                try:
                    driver.get(url)
                    page_loaded = True
                    logger.info("페이지 로드 성공")
                except TimeoutException:
                    logger.warning(f"페이지 로드 타임아웃: {combo['plan']['name']}")
                    # JavaScript로 로딩 중단
                    try:
                        driver.execute_script("window.stop();")
                        time.sleep(2)
                        # 현재 페이지 URL 확인
                        current_url = driver.current_url
                        logger.info(f"현재 URL: {current_url[:100]}...")
                        if url in current_url or current_url.startswith(BASE_URL):
                            logger.info("페이지가 부분적으로 로드됨, 계속 진행")
                            page_loaded = True
                    except Exception as e:
                        logger.error(f"window.stop() 실행 중 오류: {e}")
                
                if page_loaded:
                    logger.info("페이지 로드 완료, 요소 대기 중...")
                    self.wait_for_page_ready(driver)
                    logger.info("페이지 준비 완료")
                else:
                    raise TimeoutException("페이지 로드 실패")
                
                # Alert 처리
                alert_result = self.handle_alert(driver)
                if alert_result == 'network_error':
                    logger.warning("네트워크 에러로 인한 alert, 재시도")
                    raise TimeoutException("네트워크 에러")
                elif alert_result == 'refresh_needed':
                    logger.warning("페이지 새로고침 필요")
                    time.sleep(3)
                
                # 데이터 수집
                logger.info(f"데이터 수집 시작: {combo['plan']['name'][:30]}...")
                items_count = self._collect_all_pages_data(driver, combo)
                logger.info(f"데이터 수집 완료: {items_count}개 항목")
                
                with self.status_lock:
                    if items_count > 0:
                        self.completed_count += 1
                        self.total_devices += items_count
                        
                        if RICH_AVAILABLE and items_count > 0:
                            console.print(f"[green]✓[/green] [{combo_index+1}/{len(self.all_combinations)}] {combo['plan']['name'][:40]}... - [bold]{items_count}개[/bold]")
                    else:
                        self.failed_count += 1
                
                return True
                
            except (TimeoutException, WebDriverException, UnexpectedAlertPresentException) as e:
                logger.error(f"처리 오류 [{combo_index+1}] (시도 {retry_count+1}): {str(e)}")
                
                # TimeoutException 처리
                if isinstance(e, TimeoutException):
                    logger.warning(f"Timeout 발생 ({retry_count+1}/{self.config['retry_count']}) - 네트워크 상태 확인")
                    if driver:
                        try:
                            # 현재 페이지 상태 확인
                            current_url = driver.current_url
                            logger.info(f"현재 URL: {current_url}")
                            
                            # JavaScript 실행 가능 여부 확인
                            try:
                                ready_state = driver.execute_script("return document.readyState")
                                logger.info(f"Document ready state: {ready_state}")
                                
                                if ready_state in ['complete', 'interactive']:
                                    # 페이지가 어느 정도 로드됨
                                    logger.info("페이지 부분 로드 상태 - 데이터 확인 시도")
                                    # 데이터 테이블 존재 확인
                                    tables = driver.find_elements(By.CSS_SELECTOR, "table")
                                    if tables:
                                        logger.info(f"{len(tables)}개 테이블 발견 - 데이터 수집 시도")
                                        # 다시 데이터 수집 시도를 위해 continue 대신 드라이버 유지
                                        retry_count += 1
                                        time.sleep(self.config['delay_between_requests'])
                                        continue
                                else:
                                    logger.info("페이지 새로고침 시도")
                                    driver.refresh()
                                    time.sleep(5)
                            except:
                                logger.warning("JavaScript 실행 불가 - 드라이버 재생성 필요")
                        except:
                            pass
                
                # UnexpectedAlertPresentException 처리
                elif isinstance(e, UnexpectedAlertPresentException):
                    try:
                        alert = driver.switch_to.alert
                        alert_text = alert.text
                        alert.accept()
                        logger.warning(f"Alert 처리: {alert_text}")
                        time.sleep(3)
                    except:
                        pass
                
                retry_count += 1
                
                if driver:
                    try:
                        driver.quit()
                        with self.drivers_lock:
                            if driver in self.active_drivers:
                                self.active_drivers.remove(driver)
                    except:
                        pass
                    driver = None
                
                if retry_count < self.config['retry_count']:
                    # 네트워크 에러 시 더 긴 대기
                    wait_time = self.config.get('network_error_wait', 30) if isinstance(e, TimeoutException) else self.config['delay_between_requests'] * 2
                    logger.info(f"{wait_time}초 대기 후 재시도...")
                    time.sleep(wait_time)
                    continue
                else:
                    with self.status_lock:
                        self.failed_count += 1
                    return False
                    
            except Exception as e:
                logger.error(f"처리 오류 [{combo_index+1}]: {str(e)}")
                with self.status_lock:
                    self.failed_count += 1
                return False
                
            finally:
                if driver:
                    try:
                        driver.quit()
                        with self.drivers_lock:
                            if driver in self.active_drivers:
                                self.active_drivers.remove(driver)
                    except Exception as e:
                        logger.debug(f"드라이버 종료 중 오류: {e}")
                # 작업 상태 제거
                with self.status_lock:
                    self.current_tasks.pop(thread_id, None)
                
                # 요청 간 지연
                time.sleep(self.config['delay_between_requests'])
    
    def _collect_all_pages_data(self, driver, combo):
        """모든 페이지 데이터 수집"""
        all_items = 0
        current_page = 1
        max_pages = 10
        
        logger.debug(f"데이터 수집 시작: {combo['plan']['name']} - {combo['network']['name']} - {combo['scrb_type']['name']}")
        
        while current_page <= max_pages:
            logger.debug(f"페이지 {current_page} 데이터 수집 중...")
            items = self._collect_current_page_data(driver, combo)
            
            if not items:
                logger.debug(f"페이지 {current_page}에 데이터 없음")
                break
                
            all_items += len(items)
            logger.debug(f"페이지 {current_page}에서 {len(items)}개 항목 수집")
            
            # 다음 페이지 확인
            try:
                pagination = driver.find_element(By.CSS_SELECTOR, ".pagination, .paginate, .paging")
                logger.debug("페이지네이션 발견")
                
                next_page = current_page + 1
                try:
                    # JavaScript로 페이지 이동
                    driver.execute_script(f"javascript:goPage({next_page});")
                    time.sleep(2)
                    
                    # 페이지 변경 확인
                    active = pagination.find_element(By.CSS_SELECTOR, ".active, .on, .current")
                    if int(active.text.strip()) == next_page:
                        current_page = next_page
                        logger.debug(f"페이지 {next_page}로 이동 성공")
                    else:
                        logger.debug("더 이상 페이지 없음")
                        break
                except Exception as e:
                    logger.debug(f"페이지 이동 실패: {e}")
                    break
                    
            except NoSuchElementException:
                logger.debug("페이지네이션 없음 - 단일 페이지")
                break
            except Exception as e:
                logger.debug(f"페이지네이션 처리 오류: {e}")
                break
        
        logger.info(f"총 {all_items}개 항목 수집 완료")
        return all_items
    
    def _collect_current_page_data(self, driver, combo):
        """현재 페이지 데이터 수집"""
        items = []
        
        try:
            # 테이블 찾기 시도
            logger.debug("테이블 검색 중...")
            
            # 다양한 선택자로 테이블 찾기
            table_selectors = [
                "table.disclosure-list",
                "table.data-list",
                "table.result-table",
                "table[id*='disclosure']",
                "table[class*='list']",
                "table"
            ]
            
            tables = []
            for selector in table_selectors:
                found_tables = driver.find_elements(By.CSS_SELECTOR, selector)
                if found_tables:
                    tables.extend(found_tables)
                    logger.debug(f"선택자 '{selector}'로 {len(found_tables)}개 테이블 발견")
                    break
            
            if not tables:
                logger.warning("테이블을 찾을 수 없음")
                # 페이지 소스 확인
                page_text = driver.find_element(By.TAG_NAME, "body").text
                if "데이터가 없습니다" in page_text or "조회된 데이터가 없습니다" in page_text:
                    logger.info("데이터 없음 메시지 확인")
                return items
            
            for table in tables:
                tbody = table.find_element(By.TAG_NAME, "tbody")
                rows = tbody.find_elements(By.TAG_NAME, "tr")
                
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cells) == 1 and ('데이터가 없습니다' in cells[0].text or
                                           '조회된 데이터가 없습니다' in cells[0].text):
                        return items
                    
                    if len(cells) >= 6:
                        device_nm = cells[0].text.strip().replace('\n', ' ').replace('\r', ' ')
                        date_text = cells[1].text.strip()
                        release_price = self.clean_price(cells[2].text)
                        
                        # SK 사이트에서 용어 변경 (2024)
                        # cells[3] = 공통지원금(=공시지원금), cells[4] = 전환지원금(=추가지원금), cells[5] = T 다이렉트샵 판매 가격
                        # twoLine 클래스가 있는 셀은 중첩된 div 구조를 가지고 있음
                        try:
                            # 공통지원금 추출 - 중첩된 구조에서 span.num 찾기
                            price_span = cells[3].find_element(By.CSS_SELECTOR, "span.num")
                            public_fee = self.clean_price(price_span.text) if price_span else self.clean_price(cells[3].text)
                        except:
                            public_fee = self.clean_price(cells[3].text)
                            
                        # 전환지원금(추가지원금) 추출 - cells[4]
                        # 전환지원금은 대부분 "-"로 표시되어 0원임
                        try:
                            if len(cells) > 4:
                                add_span = cells[4].find_element(By.CSS_SELECTOR, "span.num")
                                add_text = add_span.text if add_span else cells[4].text
                                # "-" 이거나 빈값이면 0으로 처리
                                if "-" in add_text or not add_text.strip():
                                    add_fee = 0
                                else:
                                    add_fee = self.clean_price(add_text)
                            else:
                                add_fee = 0
                        except:
                            add_fee = 0
                            
                        # 디버깅용 로그
                        if device_nm and "갤럭시 Z" in device_nm:
                            logger.info(f"디버깅: {device_nm} - 공통지원금: {public_fee}, 전환지원금: {add_fee}")
                        
                        if device_nm:
                            # day7 옵션이 켜져있을 때 날짜 확인
                            if self.config.get('day7', False):
                                try:
                                    # 날짜 형식이 다양할 수 있으므로 파싱 시도 (YYYY.MM.DD 형식 등)
                                    date_obj = pd.to_datetime(date_text.replace('.', '-'))
                                    now = datetime.now(ZoneInfo('Asia/Seoul'))
                                    seven_days_ago = now - pd.Timedelta(days=7)
                                    
                                    if date_obj < seven_days_ago:
                                        logger.debug(f"날짜({date_text})가 7일 이전이므로 건너뜀")
                                        continue
                                except Exception as e:
                                    logger.debug(f"날짜 파싱 오류: {e}, 데이터 포함")
                            # 통합 데이터 형식
                            item = {
                                'date': date_text,
                                'crawled_at': datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S'),
                                'carrier': 'SK',
                                'manufacturer': self.get_manufacturer(device_nm),
                                'scrb_type_name': combo['scrb_type']['name'],
                                'network_type': combo['network']['name'],
                                'device_nm': device_nm,
                                'plan_name': combo['plan']['name'],
                                'monthly_fee': combo['plan']['monthly_fee'],
                                'release_price': release_price,
                                'public_support_fee': public_fee,
                                'additional_support_fee': add_fee,
                                'total_support_fee': public_fee + add_fee,
                                'total_price': release_price - (public_fee + add_fee) if release_price > 0 else 0
                            }
                            items.append(item)
                            
                            with self.data_lock:
                                self.all_data.append(item)
                            
        except Exception as e:
            logger.debug(f"페이지 데이터 수집 오류: {e}")
        
        return items
    
    def clean_price(self, price_str):
        """가격 정리"""
        if not price_str:
            return 0
        cleaned = re.sub(r'[^0-9]', '', str(price_str))
        try:
            return int(cleaned) if cleaned else 0
        except:
            return 0
    
    def get_manufacturer(self, device_nm):
        """제조사 추출"""
        name_lower = device_nm.lower()
        if '갤럭시' in name_lower or 'galaxy' in name_lower:
            return '삼성'
        elif '아이폰' in name_lower or 'iphone' in name_lower or 'ipad' in name_lower:
            return '애플'
        elif 'lg' in name_lower:
            return 'LG'
        elif '샤오미' in name_lower or 'xiaomi' in name_lower:
            return '샤오미'
        elif '모토로라' in name_lower:
            return '모토로라'
        else:
            return '기타'
    
    def run_parallel_crawling(self):
        """병렬 크롤링 실행"""
        self.start_time = time.time()
        
        if RICH_AVAILABLE:
            console.print(Panel.fit(
                f"[bold cyan]공시지원금 데이터 수집 시작[/bold cyan]\n"
                f"[yellow]워커: {self.config['max_workers']}개[/yellow]",
                border_style="cyan"
            ))
        else:
            print("\n공시지원금 데이터 수집 시작")
            print(f"워커: {self.config['max_workers']}개")
        
        # 체크포인트 확인
        start_index = self.load_checkpoint()
        
        with ThreadPoolExecutor(max_workers=self.config['max_workers']) as executor:
            
            if RICH_AVAILABLE:
                # Rich Progress 사용
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
                        total=len(self.all_combinations) - start_index,
                        status=f"수집: 0개"
                    )
                    
                    # 작업 제출
                    futures = []
                    for i in range(start_index, len(self.all_combinations)):
                        future = executor.submit(self.process_combination, i, progress, main_task)
                        futures.append((future, i))
                    
                    # 결과 수집 - as_completed 사용
                    for future in as_completed([f[0] for f in futures]):
                        try:
                            # 완료된 future의 인덱스 찾기
                            idx = None
                            for f, i in futures:
                                if f == future:
                                    idx = i
                                    break
                            
                            result = future.result()
                            progress.advance(main_task)
                            
                            # 상태 업데이트
                            elapsed = time.time() - self.start_time
                            speed = self.completed_count / (elapsed / 60) if elapsed > 0 else 0
                            
                            progress.update(
                                main_task,
                                status=f"수집: {self.total_devices:,}개 | 속도: {speed:.1f}개/분"
                            )
                            
                            # 체크포인트 저장
                            if idx is not None and (idx + 1) % self.config['checkpoint_interval'] == 0:
                                self.save_checkpoint(idx + 1)
                            
                        except Exception as e:
                            logger.error(f"Future 오류: {str(e)}")
                            progress.advance(main_task)
            else:
                # Rich 없을 때
                futures = []
                future_to_idx = {}
                for i in range(start_index, len(self.all_combinations)):
                    future = executor.submit(self.process_combination, i)
                    futures.append(future)
                    future_to_idx[future] = i
                
                completed = 0
                total = len(self.all_combinations) - start_index
                for future in as_completed(futures):
                    completed += 1
                    idx = future_to_idx[future]
                    print(f"진행: {completed}/{total} ({completed/total*100:.1f}%)")
                    
                    if (idx + 1) % self.config['checkpoint_interval'] == 0:
                        self.save_checkpoint(idx + 1)
        
        # 다른 가입유형 데이터 복사 (제거)
        # self._duplicate_data_for_other_types()
        
        # 최종 통계
        elapsed = time.time() - self.start_time
        
        if RICH_AVAILABLE:
            # 통계 테이블
            table = Table(title="크롤링 완료", show_header=True, header_style="bold magenta")
            table.add_column("항목", style="cyan", width=20)
            table.add_column("수치", justify="right", style="yellow")
            
            table.add_row("소요 시간", f"{elapsed/60:.1f}분")
            table.add_row("성공", f"{self.completed_count:,}개")
            table.add_row("실패", f"{self.failed_count:,}개")
            table.add_row("총 수집 데이터", f"{len(self.all_data):,}개")
            table.add_row("평균 속도", f"{self.completed_count/(elapsed/60):.1f}개/분" if elapsed > 0 else "0개/분")
            
            console.print("\n")
            console.print(table)
        else:
            print(f"\n크롤링 완료!")
            print(f"소요 시간: {elapsed/60:.1f}분")
            print(f"성공: {self.completed_count}개")
            print(f"실패: {self.failed_count}개")
            print(f"총 수집 데이터: {len(self.all_data)}개")
        
        # 체크포인트 삭제
        self.clear_checkpoint()
    
    def _duplicate_data_for_other_types(self):
        """다른 가입유형용 데이터 복사"""
        if RICH_AVAILABLE:
            console.print("\n[cyan]다른 가입유형 데이터 생성 중...[/cyan]")
        else:
            logger.info("\n다른 가입유형 데이터 생성 중...")
        
        original_data = [d for d in self.all_data if d['scrb_type_name'] == '기기변경']
        other_types = ['신규가입', '번호이동']
        
        for scrb_type in other_types:
            for item in original_data:
                new_item = item.copy()
                new_item['scrb_type_name'] = scrb_type
                self.all_data.append(new_item)
        
        if RICH_AVAILABLE:
            console.print(f"[green]✓[/green] 총 {len(self.all_data):,}개 데이터 생성 완료")
        else:
            logger.info(f"✓ 총 {len(self.all_data)}개 데이터 생성 완료")
    
    def save_checkpoint(self, index):
        """체크포인트 저장"""
        checkpoint_data = {
            'index': index,
            'all_data': self.all_data,
            'rate_plans': self.rate_plans,
            'categories': self.categories,
            'all_combinations': self.all_combinations,
            'completed_count': self.completed_count,
            'failed_count': self.failed_count,
            'total_devices': self.total_devices,
            'timestamp': datetime.now(ZoneInfo('Asia/Seoul')).isoformat()
        }
        
        try:
            with open(str(self.checkpoint_file), 'wb') as f:
                pickle.dump(checkpoint_data, f)
            logger.debug(f"체크포인트 저장: {index}")
        except Exception as e:
            logger.error(f"체크포인트 저장 실패: {e}")
    
    def load_checkpoint(self):
        """체크포인트 로드"""
        if not self.checkpoint_file.exists():
            return 0
        
        try:
            with open(str(self.checkpoint_file), 'rb') as f:
                checkpoint_data = pickle.load(f)
            
            self.all_data = checkpoint_data.get('all_data', [])
            self.rate_plans = checkpoint_data.get('rate_plans', [])
            self.categories = checkpoint_data.get('categories', [])
            self.all_combinations = checkpoint_data.get('all_combinations', [])
            self.completed_count = checkpoint_data.get('completed_count', 0)
            self.failed_count = checkpoint_data.get('failed_count', 0)
            self.total_devices = checkpoint_data.get('total_devices', 0)
            saved_index = checkpoint_data.get('index', 0)
            
            if RICH_AVAILABLE:
                console.print(f"[yellow]체크포인트 로드: {saved_index}번째부터 재개[/yellow]")
            else:
                logger.info(f"체크포인트 로드: {saved_index}번째부터 재개")
            
            return saved_index
        except Exception as e:
            logger.error(f"체크포인트 로드 실패: {e}")
            return 0
    
    def clear_checkpoint(self):
        """체크포인트 삭제"""
        if self.checkpoint_file.exists():
            try:
                self.checkpoint_file.unlink()
                logger.debug("체크포인트 파일 삭제")
            except:
                pass
    
    def save_results(self):
        """결과 저장"""
        if not self.all_data:
            if RICH_AVAILABLE:
                console.print("[red]저장할 데이터가 없습니다.[/red]")
            else:
                logger.warning("저장할 데이터가 없습니다.")
            return []
        
        timestamp = datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%d_%H%M%S')
        saved_files = []
        
        try:
            # DataFrame 생성
            df = pd.DataFrame(self.all_data)
            
            # CSV 저장
            if 'csv' in self.config['save_formats']:
                csv_file = get_raw_data_path('sk', 'csv')
                df.to_csv(csv_file, index=False, encoding='utf-8-sig')
                saved_files.append(str(csv_file))
                
                if RICH_AVAILABLE:
                    console.print(f"[green]✅ CSV 저장:[/green] {csv_file}")
                else:
                    logger.info(f"CSV 저장: {csv_file}")
            
            # Excel 저장
            if 'excel' in self.config['save_formats']:
                excel_file = get_raw_data_path('sk', 'xlsx')
                
                with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                    # 전체 데이터
                    df.to_excel(writer, sheet_name='전체데이터', index=False)
                    
                    # 요약 시트
                    summary = df.groupby(['network_type', 'scrb_type_name']).agg({
                        'device_nm': 'count',
                        'public_support_fee': 'mean',
                        'total_support_fee': 'mean'
                    }).round(0)
                    summary.columns = ['디바이스수', '평균공시지원금', '평균총지원금']
                    summary.to_excel(writer, sheet_name='요약')
                
                saved_files.append(str(excel_file))
                
                if RICH_AVAILABLE:
                    console.print(f"[green]✅ Excel 저장:[/green] {excel_file}")
                else:
                    logger.info(f"Excel 저장: {excel_file}")
            
            # 통계 출력
            self._print_statistics(df)
            
        except Exception as e:
            logger.error(f"파일 저장 중 오류 발생: {e}")
            traceback.print_exc()
        
        return saved_files
    
    def _print_statistics(self, df):
        """통계 출력"""
        if RICH_AVAILABLE:
            # 요약 테이블
            summary_table = Table(title="크롤링 결과 요약", show_header=True, header_style="bold cyan")
            summary_table.add_column("항목", style="yellow")
            summary_table.add_column("수치", justify="right", style="green")
            
            summary_table.add_row("총 데이터", f"{len(df):,}개")
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
            print(f"요금제: {df['plan_name'].nunique()}개")
            print(f"디바이스: {df['device_nm'].nunique()}개")
            print(f"평균 월요금: {df['monthly_fee'].mean():,.0f}원")
            print(f"평균 공시지원금: {df['public_support_fee'].mean():,.0f}원")
            print(f"최대 공시지원금: {df['public_support_fee'].max():,.0f}원")
    
    def run(self):
        """전체 실행"""
        try:
            if RICH_AVAILABLE:
                console.print(Panel.fit(
                    "[bold cyan]SK Telecom 공시지원금 크롤러[/bold cyan]\n"
                    "[yellow]통합 버전 v3.1[/yellow]",
                    border_style="cyan"
                ))
            else:
                print("\n" + "="*50)
                print("SK Telecom 공시지원금 크롤러")
                print("통합 버전 v3.1")
                print("="*50)
            
            # day7 옵션 확인
            if self.config.get('day7', False):
                if RICH_AVAILABLE:
                    console.print(Panel.fit(
                        "[bold yellow]최근 7일치 데이터만 수집 모드[/bold yellow]",
                        border_style="yellow"
                    ))
                else:
                    print("\n*** 최근 7일치 데이터만 수집 모드 ***\n")
                logger.info("최근 7일치 데이터만 수집하도록 설정됨")
            
            # 체크포인트 확인
            if self.config.get('resume'):
                start_index = self.load_checkpoint()
                if start_index > 0 and self.all_combinations:
                    # 체크포인트에서 재개
                    self.run_parallel_crawling()
                    saved_files = self.save_results()
                    return saved_files
            
            # 1. 요금제 수집
            self.collect_rate_plans()
            
            if not self.rate_plans:
                if RICH_AVAILABLE:
                    console.print("[red]수집된 요금제가 없어 크롤링을 중단합니다.[/red]")
                else:
                    logger.error("수집된 요금제가 없어 크롤링을 중단합니다.")
                return []
            
            # 2. 조합 준비
            self.prepare_combinations()
            
            # 3. 병렬 크롤링
            self.run_parallel_crawling()
            
            # 4. 결과 저장
            saved_files = self.save_results()
            
            return saved_files
            
        except KeyboardInterrupt:
            if RICH_AVAILABLE:
                console.print("\n[yellow]사용자에 의해 중단되었습니다.[/yellow]")
            else:
                print("\n사용자에 의해 중단되었습니다.")
            
            # 중단 시점까지의 데이터 저장
            if self.all_data:
                saved_files = self.save_results()
                return saved_files
            return []
            
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"\n[red]오류 발생: {str(e)}[/red]")
            else:
                logger.error(f"크롤링 중 오류: {e}")
            traceback.print_exc()
            return []
    
    def __del__(self):
        """객체 소멸자 - 모든 드라이버 정리"""
        try:
            # 메인 드라이버 정리
            if hasattr(self, 'driver') and self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            
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
    """메인 실행"""
    parser = argparse.ArgumentParser(
        description='SK Telecom 공시지원금 크롤러',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--workers', type=int, default=3,
                        help='동시 실행 워커 수 (기본: 3)')
    parser.add_argument('--sequential', action='store_true',
                        help='순차 처리 모드 (workers=1, 안정성 우선)')
    parser.add_argument('--max-plans', type=int, default=0,
                        help='최대 요금제 수 (0=전체)')
    parser.add_argument('--show-browser', action='store_true',
                        help='브라우저 표시')
    parser.add_argument('--output', type=str, default='data',
                        help='출력 디렉토리')
    parser.add_argument('--format', nargs='+', choices=['excel', 'csv'],
                        default=['csv'],
                        help='저장 형식')
    parser.add_argument('--test', action='store_true',
                        help='테스트 모드 (처음 10개 요금제만)')
    parser.add_argument('--resume', action='store_true',
                        help='체크포인트에서 재개')
    parser.add_argument('--delay', type=int, default=2,
                        help='요청 간 지연 시간(초) (기본: 2)')
    parser.add_argument('--day7', action='store_true',
                        help='최근 7일치 데이터만 수집')
    
    args = parser.parse_args()
    
    # 설정
    config = {
        'max_workers': 1 if args.sequential else args.workers,
        'max_rate_plans': 10 if args.test else args.max_plans,
        'show_browser': args.show_browser,
        'headless': not args.show_browser,
        'output_dir': args.output,
        'save_formats': args.format,
        'resume': args.resume,
        'delay_between_requests': args.delay,
        'day7': args.day7
    }
    
    # 크롤러 실행
    crawler = TworldCrawler(config)
    saved_files = crawler.run()
    
    if saved_files:
        if RICH_AVAILABLE:
            console.print(f"\n[bold green]✅ 완료! {len(saved_files)}개 파일 저장됨[/bold green]")
            for file in saved_files:
                console.print(f"  [dim]• {file}[/dim]")
        else:
            print(f"\n✅ 완료! {len(saved_files)}개 파일 저장됨")
            for file in saved_files:
                print(f"  • {file}")
        sys.exit(0)
    else:
        if RICH_AVAILABLE:
            console.print("\n[red]⚠️ 저장된 파일이 없습니다.[/red]")
        else:
            print("\n⚠️ 저장된 파일이 없습니다.")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # 기본 실행 (3 workers - 성능 향상)
        config = {'max_workers': 3}
        crawler = TworldCrawler(config)
        crawler.run()
    else:
        main()