import fitz
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
import easyocr
import json


class EasyOCRExtractor:
    """EasyOCR을 사용한 PDF 추출"""

    def __init__(self):
        # EasyOCR 초기화 (한글 지원)
        self.reader = easyocr.Reader(['ko', 'en'], gpu=False)

    def extract_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """OCR을 사용하여 PDF 추출"""
        doc = fitz.open(pdf_path)
        filename = Path(pdf_path).name

        extracted_data = {
            "metadata": {
                "filename": filename,
                "total_pages": doc.page_count,
                "file_size_kb": Path(pdf_path).stat().st_size / 1024,
                "extraction_type": "ocr_easyocr"
            },
            "content": []
        }

        try:
            for page_num in range(doc.page_count):
                page = doc[page_num]

                # 페이지를 이미지로 렌더링
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                img_array = np.frombuffer(pix.samples, dtype=np.uint8)
                img_array = img_array.reshape((pix.height, pix.width, pix.n))

                # BGR로 변환
                if pix.n == 3:
                    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                else:
                    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)

                # OCR 실행
                results = self.reader.readtext(img_bgr)

                # 텍스트 추출 및 포맷팅
                text_content = self._format_results(results)
                confidence = self._calculate_confidence(results)

                page_content = {
                    "page_num": page_num + 1,
                    "width": page.rect.width,
                    "height": page.rect.height,
                    "text": text_content,
                    "confidence": confidence,
                    "lines_detected": len(results)
                }

                extracted_data["content"].append(page_content)

        finally:
            doc.close()

        return extracted_data

    def _format_results(self, results: List) -> str:
        """OCR 결과를 마크다운 형식으로 포맷"""
        text = ""
        for detection in results:
            if len(detection) >= 2:
                extracted_text = detection[1]
                confidence = detection[2]

                # 신뢰도가 낮으면 주석 표시
                if confidence > 0.5:
                    text += extracted_text + "\n"
                else:
                    text += f"> {extracted_text} *(신뢰도: {confidence:.0%})*\n"

        return text

    def _calculate_confidence(self, results: List) -> float:
        """평균 신뢰도 계산"""
        if not results:
            return 0.0

        confidences = [detection[2] for detection in results if len(detection) >= 3]
        return sum(confidences) / len(confidences) if confidences else 0.0

    def to_markdown(self, data: Dict[str, Any]) -> str:
        """추출 데이터를 마크다운으로 변환"""
        metadata = data["metadata"]
        content = data["content"]

        md = f"""# {metadata['filename']} - OCR 추출 보고서

## 문서 정보

| 항목 | 값 |
|------|-----|
| 파일명 | {metadata['filename']} |
| 총 페이지 | {metadata['total_pages']} |
| 파일 크기 | {metadata['file_size_kb']:.1f} KB |
| 추출 타입 | EasyOCR (한글/영문) |

---

## 추출 통계

| 항목 | 값 |
|------|-----|
| 총 페이지 | {len(content)} |
| 평균 신뢰도 | {self._avg_confidence(content):.1%} |

---

"""

        # 페이지별 내용
        for page in content:
            md += f"""## 페이지 {page['page_num']}

**OCR 신뢰도:** {page['confidence']:.1%}
**감지된 라인:** {page['lines_detected']}개

### 추출된 텍스트

{page['text']}

---

"""

        return md

    def _avg_confidence(self, content: List) -> float:
        """평균 신뢰도"""
        if not content:
            return 0.0
        return sum(p['confidence'] for p in content) / len(content)


def extract_pdf_with_easyocr(pdf_path: str) -> Tuple[Dict[str, Any], str]:
    """EasyOCR을 사용한 PDF 추출 및 마크다운 생성"""
    extractor = EasyOCRExtractor()
    data = extractor.extract_pdf(pdf_path)

    # 마크다운 생성
    markdown_content = extractor.to_markdown(data)

    return data, markdown_content
