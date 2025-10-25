#!/usr/bin/env python3
"""
OCR 처리 실행 스크립트
"""
import sys
import os
from pathlib import Path
import subprocess

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def main():
    """OCR 처리 실행"""
    print("\n=== OCR 처리 시작 ===")
    
    # OCR 디렉토리로 이동
    ocr_dir = project_root / "src" / "ocr" / "OCR"
    if not ocr_dir.exists():
        print(f"오류: OCR 디렉토리가 없습니다: {ocr_dir}")
        return
    
    # 원래 디렉토리 저장
    original_dir = os.getcwd()
    
    try:
        # OCR 디렉토리로 이동
        os.chdir(ocr_dir)
        
        # OCR 실행 - 직접 clova_ocr.py 실행
        ocr_script = project_root / "src" / "ocr" / "clova_ocr.py"
        cmd = ['python3', str(ocr_script), 'batch', '--table']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"오류 발생: {result.stderr}")
            
    finally:
        # 원래 디렉토리로 복귀
        os.chdir(original_dir)

if __name__ == '__main__':
    main()