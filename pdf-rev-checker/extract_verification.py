#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os

# backend 폴더를 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from easy_ocr_extractor import extract_pdf_with_easyocr
from pathlib import Path

def main():
    pdf_filename = "[I-AGG-0301-030-A01]부표1. 현장점검 수행 및 평가기준_개정 전.pdf"
    pdf_path = os.path.join(os.path.dirname(__file__), pdf_filename)
    output_md_path = os.path.join(os.path.dirname(__file__), "first_verification.md")

    print(f"📄 PDF 추출 시작: {pdf_filename}")
    print(f"📁 경로: {pdf_path}")
    print(f"💾 출력: {output_md_path}")
    print("-" * 60)

    if not os.path.exists(pdf_path):
        print(f"❌ 오류: PDF 파일을 찾을 수 없습니다: {pdf_path}")
        return False

    try:
        # EasyOCR을 사용하여 PDF 추출
        print("🔄 EasyOCR 모델 로딩 중...")
        data, markdown_content = extract_pdf_with_easyocr(pdf_path)

        # 마크다운 파일 저장
        with open(output_md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"✅ 추출 완료!")
        print(f"📊 메타데이터:")
        print(f"   - 파일명: {data['metadata']['filename']}")
        print(f"   - 총 페이지: {data['metadata']['total_pages']}")
        print(f"   - 파일 크기: {data['metadata']['file_size_kb']:.1f} KB")
        print(f"   - 추출 타입: {data['metadata']['extraction_type']}")
        print()
        print(f"📝 마크다운 저장: {output_md_path}")
        print("-" * 60)

        # 마크다운 파일 크기 확인
        if os.path.exists(output_md_path):
            md_size = os.path.getsize(output_md_path) / 1024
            print(f"✨ 마크다운 파일 크기: {md_size:.1f} KB")
            print(f"📖 추출 완료: {output_md_path}")

        return True

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
