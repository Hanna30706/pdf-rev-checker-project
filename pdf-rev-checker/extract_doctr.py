#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path

def extract_with_doctr():
    """DocTR을 사용하여 PDF 추출"""
    try:
        from doctr.io import DocumentFile
        from doctr.models import ocr_predictor
        import json
    except ImportError as e:
        print(f"❌ 라이브러리 로드 오류: {str(e)}")
        return False

    pdf_filename = "[I-AGG-0301-030-A01]부표1. 현장점검 수행 및 평가기준_개정 전.pdf"
    pdf_path = os.path.join(os.path.dirname(__file__), pdf_filename)
    output_md_path = os.path.join(os.path.dirname(__file__), "doctr_verification.md")

    print(f"📄 PDF DocTR 추출 시작: {pdf_filename}")
    print(f"📁 경로: {pdf_path}")
    print(f"💾 출력: {output_md_path}")
    print("-" * 60)

    if not os.path.exists(pdf_path):
        print(f"❌ 오류: PDF 파일을 찾을 수 없습니다: {pdf_path}")
        return False

    try:
        print("🔄 DocTR 모델 로딩 중...")
        model = ocr_predictor(pretrained=True, assume_straight_pages=True)

        print("📖 PDF 문서 로드 중...")
        doc = DocumentFile.from_pdf(pdf_path)

        print("🔍 OCR 실행 중...")
        result = model(doc)

        print("✅ OCR 완료!")

        # 마크다운 생성
        markdown_content = generate_markdown(result, pdf_filename)

        # 마크다운 파일 저장
        with open(output_md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

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


def generate_markdown(result, pdf_filename):
    """DocTR 결과를 마크다운으로 변환"""

    md = f"""# {pdf_filename} - DocTR 추출 보고서

## 📋 문서 정보

| 항목 | 값 |
|------|-----|
| 파일명 | {pdf_filename} |
| 추출 타입 | DocTR (Document Text Recognition) |
| 총 페이지 | {len(result.pages)} |
| 추출 날짜 | 2026-07-21 |

---

## 📊 추출 통계

| 항목 | 값 |
|------|-----|
| 총 페이지 | {len(result.pages)} |

---

"""

    # 페이지별 내용 추출
    for page_idx, page in enumerate(result.pages, 1):
        md += f"""## 📄 페이지 {page_idx}

"""

        # 페이지 내용 추출
        if hasattr(page, 'blocks') and page.blocks:
            for block_idx, block in enumerate(page.blocks, 1):
                if hasattr(block, 'lines') and block.lines:
                    # 블록별로 섹션 생성
                    md += f"### 블록 {block_idx}\n\n"

                    for line in block.lines:
                        if hasattr(line, 'words') and line.words:
                            line_text = ""
                            for word in line.words:
                                if hasattr(word, 'value'):
                                    line_text += word.value + " "
                                elif isinstance(word, str):
                                    line_text += word + " "

                            if line_text.strip():
                                md += line_text.strip() + "\n"

                    md += "\n"

        md += "---\n\n"

    return md


if __name__ == "__main__":
    success = extract_with_doctr()
    sys.exit(0 if success else 1)
