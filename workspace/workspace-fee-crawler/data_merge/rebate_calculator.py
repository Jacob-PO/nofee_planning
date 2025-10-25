import re
from typing import Dict, List, Tuple
from datetime import datetime
import json
from pathlib import Path


class RebateCalculator:
    """대리점별 리베이트 계산을 관리하는 클래스"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or Path(__file__).parent / 'rebate_config.json'
        self.rebate_rules = self.load_rebate_config()
        self.calculations_log = []
        
    def load_rebate_config(self) -> Dict:
        """리베이트 설정을 JSON 파일에서 로드"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 기본 설정
            return {
                "SK_케이": {
                    "enabled": True,
                    "min_rate_plan": 79,
                    "rules": [
                        {
                            "models": ["S25", "아이폰16", "IP16", "IPHONE16", "SM-S931", "SM-S936", "SM-S938", "아이폰 16"],
                            "rebate": 7,
                            "description": "S25계열, IP16계열"
                        },
                        {
                            "models": ["F766", "SM-F766", "S23", "SM-S911", "SM-S916", "SM-S918"],
                            "rebate": 10,
                            "description": "F766, S23계열"
                        },
                        {
                            "models": ["A165", "SM-A165"],
                            "rebate": 5,
                            "description": "A165"
                        }
                    ]
                }
            }
    
    def save_rebate_config(self, config: Dict):
        """리베이트 설정을 JSON 파일로 저장 (메타데이터 자동 업데이트)"""
        # 메타데이터 업데이트
        if 'metadata' not in config:
            config['metadata'] = {
                'version': '1.0.0',
                'update_history': []
            }
        config['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def match_product(self, text: str, keywords) -> bool:
        """텍스트에 키워드가 포함되어 있는지 확인"""
        # "ALL" 키워드 처리
        if keywords == "ALL" or (isinstance(keywords, list) and "ALL" in keywords):
            return True

        if not text:
            return False
        text_lower = str(text).lower()
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    def apply_dealer_rebate(self, dealer_name: str, model_name: str, rate_plan: int, original_value: float, support_type: str = None, join_type: str = None, product_group_nm: str = None) -> Tuple[float, str]:
        """대리점별 리베이트 적용

        Args:
            dealer_name: 대리점명
            model_name: 모델명
            rate_plan: 요금제
            original_value: 원본 값
            support_type: 지원 타입 (공시/선택약정)
            join_type: 가입 유형 (신규가입/번호이동/기기변경)
            product_group_nm: 상품 그룹명
            
        Returns:
            (리베이트 적용 값, 적용 설명)
        """
        # 대리점명 정규화 (SK_대교 → 대교)
        normalized_dealer = dealer_name.replace("SK_", "").replace("LG_", "").replace("KT_", "")
        
        if normalized_dealer not in self.rebate_rules:
            return original_value, ""
            
        dealer_config = self.rebate_rules[normalized_dealer]
        
        # 비활성화된 경우
        if not dealer_config.get("enabled", True):
            return original_value, ""
            
        # 대리점 전체 지원 타입 조건 확인
        required_support = dealer_config.get("require_support_type")
        if required_support and support_type != required_support:
            return original_value, ""
            
        # 최소 요금제 확인
        min_rate = dealer_config.get("min_rate_plan", 0)
        if rate_plan < min_rate:
            return original_value, ""
            
        # 규칙 적용 (누적 적용)
        total_rebate = 0
        applied_descriptions = []

        # 디버그 출력 (임시)
        # if normalized_dealer == "대교":
        #     print(f"[DEBUG] Checking {len(dealer_config.get('rules', []))} rules for {normalized_dealer}, product={product_group_nm}")

        for rule in dealer_config.get("rules", []):
            # product_matched 체크 - product_group_names 또는 models 중 하나라도 매칭되면 True
            product_matched = False

            # product_group_names로 매칭
            if "product_group_names" in rule and product_group_nm:
                if product_group_nm in rule["product_group_names"]:
                    product_matched = True

            # models로 매칭 (product_group_names가 없거나 매칭되지 않은 경우도 체크)
            if "models" in rule:
                if self.match_product(model_name, rule["models"]):
                    product_matched = True

            if product_matched:
                # if normalized_dealer == "대교":
                #     print(f"  [DEBUG] Rule {rule.get('description')} matched product")
                # exclude_models 체크 (제외 모델)
                if "exclude_models" in rule:
                    exclude_models = rule["exclude_models"]
                    if model_name and any(exc_model.lower() in model_name.lower() for exc_model in exclude_models):
                        continue
                    if product_group_nm and any(exc_model.lower() in product_group_nm.lower() for exc_model in exclude_models):
                        continue

                # 규칙별 지원 타입 조건 확인
                rule_support = rule.get("require_support_type")
                if rule_support and support_type != rule_support:
                    continue
                    
                # 규칙별 가입 유형 조건 확인 (단일)
                rule_join = rule.get("require_join_type")
                if rule_join and join_type != rule_join:
                    continue
                
                # 규칙별 가입 유형 조건 확인 (복수)
                rule_joins = rule.get("require_join_types")
                if rule_joins and join_type not in rule_joins:
                    continue

                # 규칙별 요금제 조건 확인
                rule_rate_plan = rule.get("require_rate_plan")
                if rule_rate_plan:
                    # rate_plan이 숫자로 들어오면 문자열로 변환
                    if isinstance(rate_plan, (int, float)):
                        rate_plan_str = f"{int(rate_plan)}k"
                    else:
                        rate_plan_str = str(rate_plan)

                    # 규칙의 요금제와 비교
                    if rule_rate_plan != rate_plan_str:
                        continue

                # 규칙별 최소 요금제 조건 확인
                rule_min_rate = rule.get("min_rate_plan")
                if rule_min_rate and rate_plan < rule_min_rate:
                    continue

                # 유효기간 체크
                if "valid_from" in rule or "valid_to" in rule:
                    from datetime import datetime as dt
                    today = dt.now()

                    if "valid_from" in rule:
                        valid_from = dt.strptime(rule["valid_from"], "%Y-%m-%d")
                        if today < valid_from:
                            continue

                    if "valid_to" in rule:
                        valid_to = dt.strptime(rule["valid_to"], "%Y-%m-%d")
                        if today > valid_to:
                            continue

                # 리베이트 누적 (만원 단위를 원 단위로 변환)
                total_rebate += rule["rebate"] * 10000
                applied_descriptions.append(f"{rule['description']} +{rule['rebate']}만원")
        
        if total_rebate != 0:
            new_value = original_value + total_rebate
            description = ", ".join(applied_descriptions)
            return new_value, description

        return original_value, ""
    
    def update_rebate_rule(self, dealer_name: str, rules: List[Dict], update_note: str = None):
        """특정 대리점의 리베이트 규칙 업데이트 (업데이트 기록 포함)"""
        if dealer_name not in self.rebate_rules:
            self.rebate_rules[dealer_name] = {"enabled": True, "rules": []}

        self.rebate_rules[dealer_name]["rules"] = rules
        self.rebate_rules[dealer_name]["last_updated"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 업데이트 히스토리 추가
        if 'metadata' not in self.rebate_rules:
            self.rebate_rules['metadata'] = {'update_history': []}

        history_entry = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'dealer': dealer_name,
            'description': update_note or f"{dealer_name} 규칙 업데이트"
        }

        # 히스토리가 리스트가 아닌 경우 초기화
        if 'update_history' not in self.rebate_rules['metadata']:
            self.rebate_rules['metadata']['update_history'] = []

        self.rebate_rules['metadata']['update_history'].append(history_entry)

        # 최근 100개만 유지 (로그 크기 제한)
        self.rebate_rules['metadata']['update_history'] = \
            self.rebate_rules['metadata']['update_history'][-100:]

        self.save_rebate_config(self.rebate_rules)
        
    def toggle_dealer_rebate(self, dealer_name: str, enabled: bool):
        """특정 대리점의 리베이트 활성화/비활성화 (업데이트 기록 포함)"""
        if dealer_name in self.rebate_rules:
            self.rebate_rules[dealer_name]["enabled"] = enabled
            self.rebate_rules[dealer_name]["last_updated"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 업데이트 히스토리 추가
            if 'metadata' not in self.rebate_rules:
                self.rebate_rules['metadata'] = {'update_history': []}

            if 'update_history' not in self.rebate_rules['metadata']:
                self.rebate_rules['metadata']['update_history'] = []

            history_entry = {
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'dealer': dealer_name,
                'description': f"{dealer_name} {'활성화' if enabled else '비활성화'}"
            }

            self.rebate_rules['metadata']['update_history'].append(history_entry)

            # 최근 100개만 유지
            self.rebate_rules['metadata']['update_history'] = \
                self.rebate_rules['metadata']['update_history'][-100:]

            self.save_rebate_config(self.rebate_rules)
    
    def get_rebate_summary(self) -> str:
        """현재 리베이트 설정 요약 (업데이트 날짜 포함)"""
        summary = []

        # 메타데이터 정보 출력
        if 'metadata' in self.rebate_rules:
            metadata = self.rebate_rules['metadata']
            summary.append(f"=== 리베이트 설정 현황 ===")
            summary.append(f"버전: {metadata.get('version', '1.0.0')}")
            summary.append(f"최종 업데이트: {metadata.get('last_updated', 'N/A')}")
            summary.append("")
        else:
            summary.append(f"=== 리베이트 설정 현황 ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===")
            summary.append("")

        # 대리점별 설정
        for dealer, config in self.rebate_rules.items():
            if dealer == 'metadata':
                continue

            status = "활성" if config.get("enabled", True) else "비활성"
            last_updated = config.get("last_updated", "N/A")
            summary.append(f"[{dealer}] - {status} (업데이트: {last_updated})")

            if config.get("min_rate_plan"):
                summary.append(f"  최소 요금제: {config['min_rate_plan']}K 이상")

            for rule in config.get("rules", []):
                summary.append(f"  • {rule['description']}: +{rule['rebate']}만원")

            summary.append("")

        # 최근 업데이트 히스토리 (최근 5개)
        if 'metadata' in self.rebate_rules and 'update_history' in self.rebate_rules['metadata']:
            history = self.rebate_rules['metadata']['update_history']
            if history:
                summary.append("\n📅 최근 업데이트 기록:")
                for entry in history[-5:]:  # 최근 5개만 표시
                    summary.append(f"  • {entry['date']} - {entry['dealer']}: {entry['description']}")

        return "\n".join(summary)


# 사용 예시
if __name__ == "__main__":
    calculator = RebateCalculator()
    
    # 현재 설정 출력
    print(calculator.get_rebate_summary())
    
    # 리베이트 적용 테스트
    new_value, desc = calculator.apply_dealer_rebate("SK_케이", "아이폰16 프로", 100, 50)
    print(f"\n테스트: 50 -> {new_value} ({desc})")