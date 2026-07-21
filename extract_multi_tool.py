#!/usr/bin/env python3
"""
다중 도구 기반 PDF 추출: PyMuPDF + Docling + PaddleOCR
- PyMuPDF: 원본 텍스트, 좌표, 페이지 정보 추출
- Docling: 제목, 본문, 표, 레이아웃 구조 추출
- PaddleOCR: 텍스트 추출 불가능한 이미지/표 영역에만 선택적 적용
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import fitz  # PyMuPDF
from docling.document_converter import DocumentConverter

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False

class PDFExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_name = Path(pdf_path).stem
        self.doc = None
        self.docling_result = None
        self.pymupdf_texts = None
        self.ocr_engine = None

    def extract_with_pymupdf(self) -> Dict:
        """PyMuPDF로 원본 텍스트 추출"""
        print(f"[PyMuPDF] {self.pdf_path} 처리 중...")
        self.doc = fitz.open(self.pdf_path)

        pymupdf_data = {
            'total_pages': len(self.doc),
            'pages': []
        }

        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            text = page.get_text(sort=True)  # sort=True: 읽기 순서 기준 정렬

            # 텍스트가 있는지 확인
            has_text = len(text.strip()) > 0

            page_info = {
                'page_num': page_num + 1,
                'has_text': has_text,
                'text': text,
                'text_length': len(text),
                'rects': []  # 텍스트 블록의 좌표
            }

            # 텍스트 블록과 좌표 정보
            if has_text:
                text_dict = page.get_text("dict")
                for block in text_dict.get("blocks", []):
                    if "lines" in block:
                        for line in block["lines"]:
                            bbox = line["bbox"]
                            page_info['rects'].append({
                                'bbox': bbox,
                                'type': 'text_block'
                            })

            pymupdf_data['pages'].append(page_info)

        self.pymupdf_texts = pymupdf_data
        print(f"  → {len(self.doc)} 페이지, 텍스트 포함: {sum(1 for p in pymupdf_data['pages'] if p['has_text'])}개")

        return pymupdf_data

    def extract_with_docling(self) -> Dict:
        """Docling으로 구조적 추출"""
        print(f"[Docling] {self.pdf_path} 처리 중...")

        try:
            converter = DocumentConverter()
            result = converter.convert(self.pdf_path)

            # Docling 결과 구조화
            docling_data = {
                'title': getattr(result, 'title', 'Unknown') if hasattr(result, 'title') else 'Unknown',
                'pages': []
            }

            # 문서 텍스트 추출
            if hasattr(result, 'document'):
                doc_text = result.document.export_to_markdown()
                docling_data['markdown'] = doc_text
            else:
                docling_data['markdown'] = ""

            self.docling_result = docling_data
            print(f"  → Docling 마크다운 추출 완료")

            return docling_data
        except Exception as e:
            print(f"  ⚠️  Docling 처리 중 오류: {str(e)}")
            return {'title': 'Unknown', 'pages': [], 'markdown': '', 'error': str(e)}

    def _extract_docling_element(self, element) -> Optional[Dict]:
        """Docling 요소를 딕셔너리로 변환"""
        element_data = {
            'type': type(element).__name__,
            'text': getattr(element, 'text', '')
        }

        # 추가 메타데이터
        if hasattr(element, 'level'):
            element_data['level'] = element.level
        if hasattr(element, 'label'):
            element_data['label'] = element.label

        return element_data if element_data.get('text') or element_data['type'] in ['Table', 'Image'] else None

    def extract_with_paddle_ocr(self, pages_to_ocr: List[int]) -> Dict:
        """선택적 PaddleOCR 처리 (텍스트 없는 페이지만)"""
        if not PADDLEOCR_AVAILABLE or not pages_to_ocr:
            return {}

        print(f"[PaddleOCR] 선택적 처리 {len(pages_to_ocr)}개 페이지...")

        if self.ocr_engine is None:
            self.ocr_engine = PaddleOCR(use_angle_cls=True, lang='korean')

        ocr_data = {'pages': {}}

        for page_num in pages_to_ocr:
            if not self.doc:
                self.doc = fitz.open(self.pdf_path)

            page = self.doc[page_num - 1]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2배 해상도
            img_data = pix.tobytes("ppm")

            # 임시 파일로 저장
            temp_img_path = f"/tmp/page_{page_num}.ppm"
            with open(temp_img_path, 'wb') as f:
                f.write(img_data)

            # OCR 처리
            result = self.ocr_engine.ocr(temp_img_path, cls=True)

            ocr_text = "\n".join([line[1][0] for line in result[0]]) if result and result[0] else ""
            ocr_data['pages'][page_num] = {
                'text': ocr_text,
                'lines': result[0] if result else []
            }

            # 임시 파일 삭제
            os.remove(temp_img_path)

        print(f"  → {len(ocr_data['pages'])} 페이지 OCR 완료")
        return ocr_data

    def merge_results(self, ocr_data: Optional[Dict] = None) -> str:
        """PyMuPDF + Docling + OCR 결과 통합"""
        print(f"[통합] 추출 결과 병합 중...")

        merged_output = []

        # 메타데이터
        merged_output.append(f"# {Path(self.pdf_path).stem}\n")
        merged_output.append(f"**파일명**: `{Path(self.pdf_path).name}`\n")
        merged_output.append(f"**페이지 수**: {self.pymupdf_texts['total_pages']}\n")
        merged_output.append(f"**추출 도구**: PyMuPDF + Docling" + (" + PaddleOCR" if ocr_data else "") + "\n\n")

        # Docling 마크다운 (있으면 우선 사용)
        if self.docling_result and self.docling_result.get('markdown'):
            merged_output.append("## 문서 내용 (Docling 추출)\n\n")
            merged_output.append(self.docling_result['markdown'])
            merged_output.append("\n\n---\n\n")

        # PyMuPDF 텍스트 (페이지별, Docling 보완용)
        merged_output.append("## 페이지별 원본 텍스트 (PyMuPDF)\n\n")
        for page_num in range(1, self.pymupdf_texts['total_pages'] + 1):
            pymupdf_page = self.pymupdf_texts['pages'][page_num - 1]

            merged_output.append(f"### 페이지 {page_num}\n\n")

            if pymupdf_page['has_text']:
                text = pymupdf_page['text'].strip()
                if text:
                    merged_output.append(text)
                    merged_output.append("\n\n")

            # OCR 텍스트 (텍스트 없는 영역만)
            if ocr_data and page_num in ocr_data.get('pages', {}):
                ocr_text = ocr_data['pages'][page_num].get('text', '').strip()
                if ocr_text and not pymupdf_page['has_text']:
                    merged_output.append("*[OCR 추출 텍스트]*\n\n")
                    merged_output.append(ocr_text)
                    merged_output.append("\n\n")

        return "".join(merged_output)

    def process(self, use_ocr: bool = False) -> str:
        """전체 처리 흐름"""
        print(f"\n{'='*60}")
        print(f"PDF 파일: {self.pdf_path}")
        print(f"{'='*60}\n")

        # 1. PyMuPDF 추출
        pymupdf_data = self.extract_with_pymupdf()

        # 2. Docling 추출
        docling_data = self.extract_with_docling()

        # 3. OCR 필요 페이지 판단 (비활성화 - 필요시만 사용)
        ocr_data = None
        if use_ocr and PADDLEOCR_AVAILABLE:
            text_missing_pages = [
                p['page_num'] for p in pymupdf_data['pages']
                if not p['has_text'] or p['text_length'] < 100
            ]
            if text_missing_pages:
                print(f"[OCR] {len(text_missing_pages)}개 페이지에서 선택적 OCR 실행...")
                ocr_data = self.extract_with_paddle_ocr(text_missing_pages)

        # 4. 결과 통합
        merged_text = self.merge_results(ocr_data)

        return merged_text


def main():
    """메인 처리"""
    base_dir = Path("d:/★AI코딩교육(딥오토)/W2_Agent AI 학습/2026.7.21_(2)")
    pdf_dir = base_dir / "내부자료"

    # 대상 파일 2개
    pdf_files = [
        pdf_dir / "[I-AG1-0401-G01]언론홍보 및 대응 지침_r0.pdf",
        pdf_dir / "[P-MGG-0601-010]국내 업면허 관리_r0.pdf"
    ]

    results = {}

    for pdf_path in pdf_files:
        if not pdf_path.exists():
            print(f"❌ 파일 없음: {pdf_path}")
            continue

        # 추출 실행
        extractor = PDFExtractor(str(pdf_path))
        extracted_text = extractor.process(use_ocr=True)

        # 결과 저장
        if "언론홍보" in pdf_path.name:
            output_file = base_dir / "docling3_verification.md"
        else:  # 국내 업면허
            output_file = base_dir / "docling3_process_verification.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(extracted_text)

        results[pdf_path.name] = str(output_file)
        print(f"\n✅ 저장 완료: {output_file}\n")

    # 요약
    print(f"\n{'='*60}")
    print("처리 완료")
    print(f"{'='*60}")
    for name, output in results.items():
        print(f"  {name}")
        print(f"    → {output}")


if __name__ == "__main__":
    main()
