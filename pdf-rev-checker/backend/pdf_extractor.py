import fitz
import json
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple
import re


def clean_text(text: str) -> str:
    """텍스트 정제 (인코딩 문제 해결)"""
    if not isinstance(text, str):
        return ""

    # 공통 문제 문자 치환
    replacements = {
        '\xa0': ' ',      # Non-breaking space
        '​': '',     # Zero-width space
        '‌': '',     # Zero-width non-joiner
        '‍': '',     # Zero-width joiner
        '﻿': '',     # Zero-width no-break space
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # 인코딩 불가능한 문자 제거 (cp949로 인코딩할 수 없는 것들)
    try:
        # cp949로 인코딩 가능한 문자만 유지
        text = text.encode('cp949', errors='ignore').decode('cp949')
    except:
        # 실패시 ASCII 범위 + 일반적인 유니코드 문자만 유지
        text = ''.join(c for c in text if ord(c) < 0xAC00 or (0xAC00 <= ord(c) <= 0xD7A3))

    # 그래도 문제가 될 수 있는 제어 문자 제거
    text = ''.join(c for c in text if ord(c) >= 32 or c in '\n\t\r')

    return text.strip()


class StructuredPDFExtractor:
    """PDF에서 구조화된 데이터 추출 (제목, 문단, 목록, 표)"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.filename = Path(pdf_path).name
        self.table_cells_bbox = set()  # 표 셀에 속하는 좌표 추적
        self.extracted_data = {
            "metadata": {
                "filename": self.filename,
                "total_pages": self.doc.page_count,
                "file_size_kb": Path(pdf_path).stat().st_size / 1024,
                "extraction_type": "structured"
            },
            "content": []
        }

    def __del__(self):
        if hasattr(self, 'doc'):
            self.doc.close()

    def extract_all(self) -> Dict[str, Any]:
        """PDF 전체에서 구조화된 데이터 추출"""

        for page_num in range(self.doc.page_count):
            page = self.doc[page_num]
            self._extract_page(page, page_num + 1)

        return self.extracted_data

    def _extract_page(self, page: fitz.Page, page_num: int) -> None:
        """단일 페이지에서 테이블과 텍스트 추출"""

        # 1단계: 테이블 추출 및 셀 영역 기록
        tables_data = self._extract_tables(page, page_num)

        # 2단계: 텍스트 추출 (테이블 영역 제외)
        text_elements = self._extract_text_elements(page, page_num)

        # 페이지 데이터 구성
        page_content = {
            "page_num": page_num,
            "width": page.rect.width,
            "height": page.rect.height,
            "elements": text_elements + tables_data
        }

        # 페이지 내 요소들을 Y 좌표순으로 정렬
        page_content["elements"].sort(key=lambda x: x.get("bbox", [0, 0, 0, 0])[1])

        self.extracted_data["content"].append(page_content)

    def _extract_tables(self, page: fitz.Page, page_num: int) -> List[Dict]:
        """페이지에서 표 추출 (table.extract() 사용)"""
        tables_data = []
        self.table_cells_bbox.clear()

        try:
            table_finder = page.find_tables()
            tables = list(table_finder.tables)

            for table_idx, table in enumerate(tables):
                # table.extract()로 셀 데이터 직접 추출
                extracted_data = table.extract()

                # 표 데이터 구성
                table_data = {
                    "type": "table",
                    "page_num": page_num,
                    "bbox": list(table.bbox),
                    "rows": []
                }

                # 추출된 데이터를 행/열 형식으로 변환
                for row_idx, row in enumerate(extracted_data):
                    row_data = []

                    for col_idx, cell_text in enumerate(row):
                        # 텍스트 정제
                        cell_text = clean_text(cell_text) if cell_text else ""

                        cell_info = {
                            "row": row_idx,
                            "col": col_idx,
                            "text": cell_text
                        }

                        row_data.append(cell_info)

                    table_data["rows"].append(row_data)

                tables_data.append(table_data)

        except Exception as e:
            # 표 추출 실패는 무시
            pass

        return tables_data

    def _extract_text_elements(self, page: fitz.Page, page_num: int) -> List[Dict]:
        """페이지에서 텍스트 요소 추출 (표 영역 제외)"""
        text_elements = []

        text_dict = page.get_text("dict")
        font_sizes = self._analyze_font_sizes(text_dict)

        if not font_sizes:
            return text_elements

        avg_font_size = sum(font_sizes) / len(font_sizes)
        heading_threshold = avg_font_size * 1.15  # 평균의 15% 이상 크면 제목

        # 텍스트 블록 수집
        blocks = []
        for block in text_dict["blocks"]:
            if block["type"] == 0:  # 텍스트 블록
                for line in block["lines"]:
                    line_data = self._extract_line_data(line, avg_font_size, heading_threshold)
                    if line_data:
                        blocks.append(line_data)

        # 텍스트 블록을 섹션으로 그룹화
        sections = self._group_blocks_into_sections(blocks)

        # 각 섹션을 요소로 변환
        for section in sections:
            element = self._create_text_element(section, page_num)
            if element:
                text_elements.append(element)

        return text_elements

    def _analyze_font_sizes(self, text_dict: Dict) -> List[float]:
        """문서의 폰트 크기 분석"""
        font_sizes = []

        for block in text_dict["blocks"]:
            if block["type"] == 0:  # 텍스트 블록
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_sizes.append(span["size"])

        return font_sizes

    def _extract_line_data(self, line: Dict, avg_font_size: float, heading_threshold: float) -> Dict:
        """한 줄의 텍스트 데이터 추출"""
        spans = line["spans"]

        if not spans:
            return None

        # 모든 텍스트 수집
        text_content = []
        for span in spans:
            text = span.get("text", "")
            if text:
                text = clean_text(text)
                if text:
                    text_content.append(text)

        full_text = "".join(text_content).strip()

        if not full_text:
            return None

        # 줄의 특성 파악
        first_span = spans[0]
        font_size = first_span.get("size", 12)
        is_bold = bool(first_span.get("flags", 0) & 16)

        # 요소 타입 판단
        element_type = self._determine_element_type(full_text, font_size, heading_threshold, is_bold)

        return {
            "text": full_text,
            "type": element_type,
            "font_size": font_size,
            "is_bold": is_bold,
            "bbox": line["bbox"],
            "spans": spans
        }

    def _determine_element_type(self, text: str, font_size: float, heading_threshold: float, is_bold: bool) -> str:
        """텍스트의 타입 판단 (제목, 목록, 문단)"""

        # 제목 판단: 폰트 크기가 크거나 굵은 경우
        if font_size >= heading_threshold:
            return "heading"

        # 목록 판단: 숫자, 글머리 등으로 시작
        if self._is_list_item(text):
            return "list"

        # 기본: 문단
        return "paragraph"

    def _is_list_item(self, text: str) -> bool:
        """텍스트가 목록 항목인지 판단"""
        # 숫자 목록: 1. 2. 3.
        if re.match(r"^\d+[\.\)]\s", text):
            return True

        # 알파벳 목록: a. b. c. 또는 A) B) C)
        if re.match(r"^[a-zA-Z][\.\)]\s", text):
            return True

        # 글머리: •, ○, -, *, 등
        if re.match(r"^[\•○◦\-\*]\s", text):
            return True

        # 들여쓰기 + 특수 기호
        if re.match(r"^\s+([\•○◦\-\*]|[0-9]+[\.\)])\s", text):
            return True

        return False

    def _group_blocks_into_sections(self, blocks: List[Dict]) -> List[List[Dict]]:
        """블록들을 섹션으로 그룹화 (문단 단위)"""
        sections = []
        current_section = []
        last_y = None
        line_height = None

        for block in blocks:
            current_y = block["bbox"][1]

            # 줄 높이 계산 (첫 블록에서)
            if line_height is None:
                line_height = block["bbox"][3] - block["bbox"][1]

            # 현재 섹션 시작 또는 같은 문단 계속
            if last_y is None:
                current_section = [block]
                last_y = current_y
            elif block["type"] == "heading":
                # 제목은 항상 새 섹션 시작
                if current_section:
                    sections.append(current_section)
                current_section = [block]
                last_y = current_y
            elif (current_y - last_y) > line_height * 1.2:
                # 간격이 크면 새 섹션 시작
                if current_section:
                    sections.append(current_section)
                current_section = [block]
                last_y = current_y
            else:
                # 같은 섹션 계속
                current_section.append(block)
                last_y = current_y

        # 마지막 섹션 추가
        if current_section:
            sections.append(current_section)

        return sections

    def _create_text_element(self, section: List[Dict], page_num: int) -> Dict:
        """섹션을 텍스트 요소로 변환"""
        if not section:
            return None

        # 섹션의 타입 판단
        element_type = self._determine_section_type(section)

        # 텍스트 조합
        texts = [block["text"] for block in section]
        full_text = "\n".join(texts) if element_type == "list" else " ".join(texts)

        # 바운딩 박스 계산
        all_bboxes = [block["bbox"] for block in section]
        x0 = min(bbox[0] for bbox in all_bboxes)
        y0 = min(bbox[1] for bbox in all_bboxes)
        x1 = max(bbox[2] for bbox in all_bboxes)
        y1 = max(bbox[3] for bbox in all_bboxes)

        # 포맷 정보
        first_block = section[0]
        avg_font_size = sum(b["font_size"] for b in section) / len(section)
        is_bold = any(b["is_bold"] for b in section)

        return {
            "type": element_type,
            "page_num": page_num,
            "bbox": [x0, y0, x1, y1],
            "text": full_text,
            "font_size": avg_font_size,
            "is_bold": is_bold,
            "line_count": len(section)
        }

    def _determine_section_type(self, section: List[Dict]) -> str:
        """섹션의 타입 판단"""
        if not section:
            return "paragraph"

        # 모든 블록의 타입 수집
        types = [block["type"] for block in section]

        # 제목이 포함된 섹션은 제목
        if "heading" in types:
            return "heading"

        # 목록이 대부분인 섹션은 목록
        list_count = types.count("list")
        if list_count >= len(types) * 0.5:  # 50% 이상 목록이면 목록 섹션
            return "list"

        # 기본: 문단
        return "paragraph"

    def save_to_json(self, output_path: str = None) -> str:
        """추출 결과를 JSON으로 저장"""
        if output_path is None:
            # 기본 출력 경로: PDF 파일명 + _structured.json
            base_path = str(Path(self.pdf_path).with_suffix(''))
            output_path = f"{base_path}_structured.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.extracted_data, f, ensure_ascii=False, indent=2)

        return output_path


def extract_structured_pdf(pdf_path: str, output_json_path: str = None) -> Tuple[Dict[str, Any], str]:
    """PDF에서 구조화된 데이터 추출"""
    extractor = StructuredPDFExtractor(pdf_path)
    data = extractor.extract_all()

    # JSON으로 저장
    json_path = extractor.save_to_json(output_json_path)

    return data, json_path
