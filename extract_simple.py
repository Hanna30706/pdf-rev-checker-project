#!/usr/bin/env python3
"""
간단한 PDF 추출: PyMuPDF + Docling
- 2개 PDF 파일만 처리
- OCR은 나중에 필요시 추가
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional
import fitz  # PyMuPDF

try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    print("⚠️  Docling을 사용할 수 없습니다. PyMuPDF만 사용합니다.")


class SimplePDFExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_name = Path(pdf_path).stem

    def extract_with_pymupdf(self) -> str:
        """PyMuPDF로 모든 텍스트 추출"""
        print(f"[PyMuPDF] {Path(self.pdf_path).name} 처리 중...")

        doc = fitz.open(self.pdf_path)
        output = []

        # 메타데이터
        output.append(f"# {self.pdf_name}\n")
        output.append(f"**파일명**: `{Path(self.pdf_path).name}`\n")
        output.append(f"**페이지 수**: {len(doc)}\n")
        output.append(f"**추출 도구**: PyMuPDF\n\n")

        # 페이지별 텍스트 추출
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text(sort=True)  # sort=True: 읽기 순서 기준

            output.append(f"## 페이지 {page_num + 1}\n\n")

            if text.strip():
                output.append(text)
            else:
                output.append("*[텍스트 없음]*")

            output.append("\n\n---\n\n")

        doc.close()
        return "".join(output)

    def extract_with_docling(self) -> str:
        """Docling으로 구조적 추출"""
        if not DOCLING_AVAILABLE:
            return ""

        print(f"[Docling] {Path(self.pdf_path).name} 처리 중...")

        try:
            converter = DocumentConverter()
            result = converter.convert(self.pdf_path)

            # 마크다운으로 내보내기
            if hasattr(result, 'document'):
                markdown = result.document.export_to_markdown()
                return markdown
            else:
                return ""
        except Exception as e:
            print(f"  ⚠️  Docling 오류: {str(e)}")
            return ""

    def process(self) -> str:
        """전체 처리"""
        print(f"\n{'='*70}")
        print(f"PDF 파일: {Path(self.pdf_path).name}")
        print(f"{'='*70}\n")

        # 1. PyMuPDF 추출
        pymupdf_text = self.extract_with_pymupdf()

        # 2. Docling 추출 (선택)
        docling_text = ""
        if DOCLING_AVAILABLE:
            try:
                docling_text = self.extract_with_docling()
            except Exception as e:
                print(f"  Docling 처리 실패: {str(e)}")

        # 결과 통합 (Docling이 있으면 우선, 없으면 PyMuPDF만)
        if docling_text:
            result = f"# {self.pdf_name}\n\n**Docling 추출 결과**\n\n{docling_text}\n\n---\n\n**PyMuPDF 페이지별 텍스트**\n\n{pymupdf_text}"
        else:
            result = pymupdf_text

        print(f"[완료] 추출 완료\n")
        return result


def main():
    """메인 처리"""
    base_dir = Path("d:/★AI코딩교육(딥오토)/W2_Agent AI 학습/2026.7.21_(2)")
    pdf_dir = base_dir / "내부자료"

    # 대상 파일 2개
    targets = [
        {
            'pdf': pdf_dir / "[I-AG1-0401-G01]언론홍보 및 대응 지침_r0.pdf",
            'output': base_dir / "docling3_verification.md"
        },
        {
            'pdf': pdf_dir / "[P-MGG-0601-010]국내 업면허 관리_r0.pdf",
            'output': base_dir / "docling3_process_verification.md"
        }
    ]

    for target in targets:
        pdf_path = target['pdf']
        output_path = target['output']

        if not pdf_path.exists():
            print(f"[ERROR] 파일 없음: {pdf_path}")
            continue

        # 추출
        extractor = SimplePDFExtractor(str(pdf_path))
        extracted_text = extractor.process()

        # 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)

        print(f"[저장] {output_path}\n")

    # 결과 파일 확인
    print(f"\n{'='*70}")
    print("추출 완료")
    print(f"{'='*70}\n")
    for target in targets:
        output_path = target['output']
        if output_path.exists():
            size = output_path.stat().st_size
            print(f"  [OK] {output_path.name} ({size} bytes)")


if __name__ == "__main__":
    main()
