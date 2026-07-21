#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path

def extract_with_docling():
    """Docling을 사용하여 PDF 추출"""
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as e:
        print(f"❌ 라이브러리 로드 오류: {str(e)}")
        return False

    pdf_filename = "[I-AGG-0301-030-A01]부표1. 현장점검 수행 및 평가기준_개정 전.pdf"
    pdf_path = os.path.join(os.path.dirname(__file__), pdf_filename)
    output_md_path = os.path.join(os.path.dirname(__file__), "docling_verification.md")

    print(f"📄 PDF Docling 추출 시작: {pdf_filename}")
    print(f"📁 경로: {pdf_path}")
    print(f"💾 출력: {output_md_path}")
    print("-" * 60)

    if not os.path.exists(pdf_path):
        print(f"❌ 오류: PDF 파일을 찾을 수 없습니다: {pdf_path}")
        return False

    try:
        print("🔄 Docling 변환기 로드 중...")
        converter = DocumentConverter()

        print("📖 PDF 문서 변환 중...")
        result = converter.convert(pdf_path)

        print("✅ 변환 완료!")
        print(f"📊 페이지 수: {len(result.document.pages)}")

        # 마크다운으로 내보내기
        print("📝 마크다운 생성 중...")
        markdown_content = result.document.export_to_markdown()

        # 헤더 추가
        header = f"""# {pdf_filename} - Docling 추출 보고서

## 📋 문서 정보

| 항목 | 값 |
|------|-----|
| 파일명 | {pdf_filename} |
| 추출 타입 | Docling (문서 파싱 AI) |
| 총 페이지 | {len(result.document.pages)} |
| 추출 날짜 | 2026-07-21 |

---

## 📖 추출된 문서 내용

"""

        full_markdown = header + markdown_content

        # 마크다운 파일 저장
        with open(output_md_path, 'w', encoding='utf-8') as f:
            f.write(full_markdown)

        print(f"📝 마크다운 저장: {output_md_path}")
        print("-" * 60)

        # 파일 크기 확인
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
    success = extract_with_docling()
    sys.exit(0 if success else 1)
