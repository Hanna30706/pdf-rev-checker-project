import fitz
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from paddleocr import PaddleOCR
import json


class PDFOCRExtractor:
    """OCR을 포함한 PDF 추출 (텍스트 기반 + 이미지 기반)"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.filename = Path(pdf_path).name

        # PaddleOCR 초기화 (한글 지원)
        self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')

        self.extracted_data = {
            "metadata": {
                "filename": self.filename,
                "total_pages": self.doc.page_count,
                "file_size_kb": Path(pdf_path).stat().st_size / 1024,
                "extraction_type": "ocr_comprehensive"
            },
            "content": []
        }

    def __del__(self):
        if hasattr(self, 'doc'):
            self.doc.close()

    def extract_all_with_ocr(self) -> Dict[str, Any]:
        """OCR을 포함하여 PDF 전체 추출"""
        for page_num in range(self.doc.page_count):
            page = self.doc[page_num]
            self._extract_page_with_ocr(page, page_num + 1)

        return self.extracted_data

    def _extract_page_with_ocr(self, page: fitz.Page, page_num: int) -> None:
        """OCR을 포함하여 단일 페이지 추출"""

        # 페이지를 이미지로 렌더링
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        img_array = np.frombuffer(pix.samples, dtype=np.uint8)
        img_array = img_array.reshape((pix.height, pix.width, pix.n))

        # BGR로 변환 (OpenCV 형식)
        if pix.n == 3:
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        else:
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)

        # OCR 실행
        ocr_results = self.ocr.ocr(img_bgr, cls=True)

        # 추출된 텍스트를 정리하고 마크다운으로 변환
        page_content = {
            "page_num": page_num,
            "width": page.rect.width,
            "height": page.rect.height,
            "text": self._format_ocr_results(ocr_results),
            "ocr_confidence": self._calculate_average_confidence(ocr_results)
        }

        self.extracted_data["content"].append(page_content)

    def _format_ocr_results(self, ocr_results: List) -> str:
        """OCR 결과를 마크다운 형식으로 포맷"""
        markdown_text = ""

        for line_idx, line in enumerate(ocr_results):
            if line is None:
                continue

            line_text = ""
            line_confidence = 0

            for word_data in line:
                text = word_data[1]
                confidence = word_data[2]
                line_text += text
                line_confidence += confidence

            if line_text.strip():
                # 신뢰도 기반으로 처리
                if line_confidence / len(line) > 0.7:
                    markdown_text += line_text + "\n"
                else:
                    # 낮은 신뢰도는 주석으로 표시
                    markdown_text += f"> {line_text} *(신뢰도: {line_confidence/len(line):.1%})*\n"

        return markdown_text

    def _calculate_average_confidence(self, ocr_results: List) -> float:
        """OCR 결과의 평균 신뢰도 계산"""
        if not ocr_results or not ocr_results[0]:
            return 0.0

        total_confidence = 0
        total_words = 0

        for line in ocr_results:
            if line is None:
                continue
            for word_data in line:
                total_confidence += word_data[2]
                total_words += 1

        return total_confidence / total_words if total_words > 0 else 0.0

    def save_to_markdown(self, output_path: str = None) -> str:
        """추출 결과를 마크다운으로 저장"""
        if output_path is None:
            base_path = str(Path(self.pdf_path).with_suffix(''))
            output_path = f"{base_path}_ocr.md"

        md_content = self._generate_markdown()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        return output_path

    def save_to_json(self, output_path: str = None) -> str:
        """추출 결과를 JSON으로 저장"""
        if output_path is None:
            base_path = str(Path(self.pdf_path).with_suffix(''))
            output_path = f"{base_path}_ocr.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.extracted_data, f, ensure_ascii=False, indent=2)

        return output_path

    def _generate_markdown(self) -> str:
        """마크다운 문서 생성"""
        md = f"""# {self.filename} - OCR 추출 보고서

## 📋 문서 정보

| 항목 | 값 |
|------|-----|
| 파일명 | {self.metadata['filename']} |
| 총 페이지 | {self.metadata['total_pages']} |
| 파일 크기 | {self.metadata['file_size_kb']:.1f} KB |
| 추출 타입 | OCR (광학 문자 인식) |

---

"""

        # 페이지별 내용
        for page in self.extracted_data["content"]:
            md += f"""## 📄 페이지 {page['page_num']}

**OCR 신뢰도:** {page['ocr_confidence']:.1%}

### 텍스트 내용

{page['text']}

---

"""

        return md

    @property
    def metadata(self):
        return self.extracted_data["metadata"]


def extract_pdf_with_ocr(pdf_path: str, output_md_path: str = None, output_json_path: str = None) -> Tuple[Dict[str, Any], str, str]:
    """OCR을 사용하여 PDF 추출"""
    extractor = PDFOCRExtractor(pdf_path)
    data = extractor.extract_all_with_ocr()

    # 마크다운과 JSON으로 저장
    md_path = extractor.save_to_markdown(output_md_path)
    json_path = extractor.save_to_json(output_json_path)

    return data, md_path, json_path
