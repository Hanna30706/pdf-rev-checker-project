#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docling 기반 PDF 추출 후처리 모듈
- 일반화된 중복 검출 및 제거
- 확실한 중복은 자동 제거, 애매한 항목은 검토 필요로 표시
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from difflib import SequenceMatcher
import hashlib


class ElementType(Enum):
    """Docling 요소 타입"""
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    LIST = "list"
    IMAGE = "image"
    CODE = "code"
    UNKNOWN = "unknown"


class DuplicateConfidence(Enum):
    """중복 검출 신뢰도"""
    HIGH = "high"           # 확실한 중복 (자동 제거)
    MEDIUM = "medium"       # 애매한 중복 (검토 필요)
    LOW = "low"            # 중복 가능성 낮음


@dataclass
class BoundingBox:
    """좌표 기반 경계 상자"""
    x0: float
    y0: float
    x1: float
    y1: float

    def area(self) -> float:
        """면적 계산"""
        return max(0, self.x1 - self.x0) * max(0, self.y1 - self.y0)

    def overlap_ratio(self, other: 'BoundingBox') -> float:
        """다른 bounding box와의 겹침 비율"""
        x_overlap = max(0, min(self.x1, other.x1) - max(self.x0, other.x0))
        y_overlap = max(0, min(self.y1, other.y1) - max(self.y0, other.y0))
        overlap_area = x_overlap * y_overlap

        if self.area() == 0 or other.area() == 0:
            return 0.0

        return overlap_area / min(self.area(), other.area())

    def distance_to(self, other: 'BoundingBox') -> float:
        """다른 bounding box까지의 거리"""
        dx = max(self.x0, other.x0) - min(self.x1, other.x1)
        dy = max(self.y0, other.y0) - min(self.y1, other.y1)
        return max(0, dx) + max(0, dy)


@dataclass
class DocumentElement:
    """추출된 문서 요소"""
    element_id: str
    element_type: ElementType
    text: str
    bbox: Optional[BoundingBox]
    page_num: int
    confidence: float = 1.0
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def text_hash(self) -> str:
        """텍스트 해시값"""
        normalized = self.text.strip().lower()
        return hashlib.md5(normalized.encode()).hexdigest()

    def similarity_to(self, other: 'DocumentElement') -> float:
        """다른 요소와의 유사도 (0.0 ~ 1.0)"""
        if not self.text or not other.text:
            return 0.0
        return SequenceMatcher(None, self.text, other.text).ratio()


@dataclass
class DuplicateRecord:
    """중복 검출 기록"""
    primary_id: str
    duplicate_id: str
    confidence: DuplicateConfidence
    reason: str
    similarity_score: float = 0.0
    bbox_overlap: float = 0.0


class DoclingPostprocessor:
    """Docling 추출 결과 후처리"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.filename = Path(pdf_path).name
        self.elements: List[DocumentElement] = []
        self.duplicates: List[DuplicateRecord] = []

        # 중복 검출 임계값
        self.thresholds = {
            'text_exact': 0.95,          # 텍스트 유사도 (확실)
            'text_high': 0.85,           # 텍스트 유사도 (중간)
            'bbox_overlap_high': 0.8,    # bounding box 겹침 (확실)
            'bbox_overlap_medium': 0.5,  # bounding box 겹침 (중간)
        }

    def extract_with_docling(self) -> bool:
        """Docling을 사용하여 PDF 추출"""
        try:
            from docling.document_converter import DocumentConverter
            from docling.datamodel.base_models import BoundingBox as DoclingBBox
        except ImportError as e:
            print(f"[ERROR] Docling library error: {str(e)}")
            return False

        if not os.path.exists(self.pdf_path):
            print(f"[ERROR] PDF file not found: {self.pdf_path}")
            return False

        try:
            print("[LOAD] Loading Docling converter...")
            converter = DocumentConverter()

            print("[CONVERT] Converting PDF document...")
            result = converter.convert(self.pdf_path)

            print("[OK] Docling conversion complete!")

            # 모든 요소 추출
            element_id = 0
            doc = result.document

            # Texts 추출
            if hasattr(doc, 'texts') and doc.texts:
                for text_item in doc.texts:
                    element_id += 1
                    page_num = self._get_page_num(text_item)
                    self._process_element(text_item, page_num, element_id)

            # Tables 추출
            if hasattr(doc, 'tables') and doc.tables:
                for table_item in doc.tables:
                    element_id += 1
                    page_num = self._get_page_num(table_item)
                    self._process_element(table_item, page_num, element_id)

            # Body의 하위 요소들은 texts와 tables의 참조이므로 무시

            print(f"[EXTRACTED] Elements extracted: {len(self.elements)}")
            return True

        except Exception as e:
            print(f"[ERROR] Docling processing error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def _get_page_num(self, element: Any) -> int:
        """요소의 페이지 번호 추출"""
        if hasattr(element, 'prov') and element.prov and len(element.prov) > 0:
            prov = element.prov[0]
            if hasattr(prov, 'page_no'):
                return prov.page_no
            elif hasattr(prov, 'page'):
                return prov.page
        return 1

    def _process_body_group(self, group: Any, element_id: int) -> None:
        """Body GroupItem의 하위 요소 처리"""
        if not hasattr(group, 'children'):
            return

        for child in group.children:
            element_id += 1
            page_num = self._get_page_num(child)
            self._process_element(child, page_num, element_id)

    def _process_element(self, element: Any, page_num: int, element_id: int) -> None:
        """개별 요소 처리"""
        element_type = self._detect_element_type(element)
        text = self._extract_text(element)

        # 빈 요소는 스킵
        if not text and element_type not in [ElementType.TABLE, ElementType.IMAGE]:
            return

        # Bounding box 추출 (prov 또는 element에서)
        bbox = None
        bbox_source = None

        # prov에서 bbox 추출
        if hasattr(element, 'prov') and element.prov and len(element.prov) > 0:
            prov = element.prov[0]
            if hasattr(prov, 'bbox') and prov.bbox:
                bbox_source = prov.bbox

        # element 자체에 bbox가 있으면 사용
        if not bbox_source and hasattr(element, 'bbox') and element.bbox:
            bbox_source = element.bbox

        if bbox_source:
            try:
                bbox = BoundingBox(
                    x0=float(bbox_source.l),
                    y0=float(bbox_source.t),
                    x1=float(bbox_source.r),
                    y1=float(bbox_source.b)
                )
            except (AttributeError, TypeError):
                pass

        doc_element = DocumentElement(
            element_id=f"elem_{element_id}",
            element_type=element_type,
            text=text,
            bbox=bbox,
            page_num=page_num,
            raw_data={'element': str(type(element).__name__)}
        )

        self.elements.append(doc_element)

    def _detect_element_type(self, element: Any) -> ElementType:
        """요소 타입 감지"""
        element_type_name = type(element).__name__.lower()

        if 'heading' in element_type_name:
            return ElementType.HEADING
        elif 'tableitem' in element_type_name or 'table' in element_type_name:
            return ElementType.TABLE
        elif 'listitem' in element_type_name or 'list' in element_type_name:
            return ElementType.LIST
        elif 'picture' in element_type_name or 'image' in element_type_name or 'figure' in element_type_name:
            return ElementType.IMAGE
        elif 'code' in element_type_name:
            return ElementType.CODE
        elif 'textitem' in element_type_name or 'paragraph' in element_type_name or 'text' in element_type_name:
            return ElementType.PARAGRAPH
        else:
            return ElementType.UNKNOWN

    def _extract_text(self, element: Any) -> str:
        """요소에서 텍스트 추출"""
        try:
            # TextItem인 경우
            if hasattr(element, 'text') and element.text:
                text = str(element.text).strip()
                if text and not text.startswith('cref='):
                    return text[:300]

            # TableItem인 경우 - markdown으로 변환
            if hasattr(element, 'export_to_markdown'):
                try:
                    text = element.export_to_markdown().strip()
                    if text and not text.startswith('cref='):
                        return text[:300]
                except Exception:
                    pass

            return ""
        except Exception:
            return ""

    def detect_duplicates(self) -> List[DuplicateRecord]:
        """중복 검출"""
        self.duplicates = []

        print("\n[DETECT] Detecting duplicates...")

        # 각 요소 쌍 비교
        for i, elem1 in enumerate(self.elements):
            for j, elem2 in enumerate(self.elements[i + 1:], i + 1):
                duplicate = self._check_duplicate(elem1, elem2)
                if duplicate:
                    self.duplicates.append(duplicate)

        print(f"[FOUND] Duplicates found: {len(self.duplicates)}")
        return self.duplicates

    def _check_duplicate(self, elem1: DocumentElement, elem2: DocumentElement) -> Optional[DuplicateRecord]:
        """두 요소 간의 중복 검출"""

        # 같은 페이지 같은 타입의 연속 요소는 일단 제외
        if (elem1.page_num == elem2.page_num and
            elem1.element_type == elem2.element_type and
            not elem1.text and not elem2.text):
            return None

        # 텍스트 기반 중복 검출
        if elem1.text and elem2.text:
            text_sim = elem1.similarity_to(elem2)

            if text_sim >= self.thresholds['text_exact']:
                return DuplicateRecord(
                    primary_id=elem1.element_id,
                    duplicate_id=elem2.element_id,
                    confidence=DuplicateConfidence.HIGH,
                    reason=f"정확한 텍스트 일치 (유사도: {text_sim:.1%})",
                    similarity_score=text_sim
                )

            if text_sim >= self.thresholds['text_high']:
                return DuplicateRecord(
                    primary_id=elem1.element_id,
                    duplicate_id=elem2.element_id,
                    confidence=DuplicateConfidence.MEDIUM,
                    reason=f"높은 텍스트 유사도 (유사도: {text_sim:.1%})",
                    similarity_score=text_sim
                )

        # Bounding box 기반 중복 검출 (같은 페이지에서)
        if (elem1.page_num == elem2.page_num and
            elem1.bbox and elem2.bbox):

            overlap = elem1.bbox.overlap_ratio(elem2.bbox)

            if overlap >= self.thresholds['bbox_overlap_high']:
                return DuplicateRecord(
                    primary_id=elem1.element_id,
                    duplicate_id=elem2.element_id,
                    confidence=DuplicateConfidence.HIGH,
                    reason=f"높은 bounding box 겹침 ({overlap:.1%})",
                    bbox_overlap=overlap
                )

            if overlap >= self.thresholds['bbox_overlap_medium']:
                return DuplicateRecord(
                    primary_id=elem1.element_id,
                    duplicate_id=elem2.element_id,
                    confidence=DuplicateConfidence.MEDIUM,
                    reason=f"중간 bounding box 겹침 ({overlap:.1%})",
                    bbox_overlap=overlap
                )

        return None

    def get_elements_to_remove(self) -> Dict[str, DuplicateConfidence]:
        """제거할 요소 목록 (신뢰도별)"""
        to_remove = {}

        for dup in self.duplicates:
            if dup.confidence == DuplicateConfidence.HIGH:
                to_remove[dup.duplicate_id] = DuplicateConfidence.HIGH

        return to_remove

    def get_elements_to_review(self) -> List[DuplicateRecord]:
        """검토 필요한 중복 목록"""
        return [d for d in self.duplicates if d.confidence == DuplicateConfidence.MEDIUM]

    def export_to_markdown(self, include_removed: bool = False) -> str:
        """마크다운으로 내보내기"""
        md = f"""# {self.filename} - Docling 후처리 검증 보고서

## 📋 문서 정보

| 항목 | 값 |
|------|-----|
| 파일명 | {self.filename} |
| 추출 도구 | Docling |
| 처리 날짜 | 2026-07-21 |
| 총 요소 개수 | {len(self.elements)} |
| 검출된 중복 | {len(self.duplicates)} |

---

## 📊 처리 통계

### 요소 분류

"""
        # 요소 타입별 통계
        type_counts = {}
        for elem in self.elements:
            key = elem.element_type.value
            type_counts[key] = type_counts.get(key, 0) + 1

        for elem_type, count in sorted(type_counts.items()):
            md += f"| {elem_type.capitalize()} | {count} |\n"

        md += "\n### 중복 검출 결과\n\n"
        md += f"| 신뢰도 | 개수 |\n|------|------|\n"

        high_count = len([d for d in self.duplicates if d.confidence == DuplicateConfidence.HIGH])
        medium_count = len([d for d in self.duplicates if d.confidence == DuplicateConfidence.MEDIUM])

        md += f"| HIGH (자동 제거) | {high_count} |\n"
        md += f"| MEDIUM (검토 필요) | {medium_count} |\n"

        md += "\n---\n\n"

        # 중복 상세 내용
        md += "## 🔍 중복 검출 상세\n\n"

        if self.duplicates:
            # HIGH 신뢰도 중복
            high_dups = [d for d in self.duplicates if d.confidence == DuplicateConfidence.HIGH]
            if high_dups:
                md += "### ✅ HIGH 신뢰도 (확실한 중복 - 자동 제거)\n\n"
                for dup in high_dups:
                    elem1 = next(e for e in self.elements if e.element_id == dup.primary_id)
                    elem2 = next(e for e in self.elements if e.element_id == dup.duplicate_id)

                    md += f"#### {dup.primary_id} ↔ {dup.duplicate_id}\n\n"
                    md += f"**이유:** {dup.reason}\n\n"
                    md += f"**Primary Element (유지):**\n"
                    md += f"- 타입: {elem1.element_type.value}\n"
                    md += f"- 페이지: {elem1.page_num}\n"
                    md += f"- 텍스트: {elem1.text[:100]}{'...' if len(elem1.text) > 100 else ''}\n\n"

                    md += f"**Duplicate Element (제거 예정):**\n"
                    md += f"- 타입: {elem2.element_type.value}\n"
                    md += f"- 페이지: {elem2.page_num}\n"
                    md += f"- 텍스트: {elem2.text[:100]}{'...' if len(elem2.text) > 100 else ''}\n\n"
                    md += "---\n\n"

            # MEDIUM 신뢰도 중복
            medium_dups = [d for d in self.duplicates if d.confidence == DuplicateConfidence.MEDIUM]
            if medium_dups:
                md += "### ⚠️  MEDIUM 신뢰도 (검토 필요)\n\n"
                md += "> **검토자 주의:** 아래 항목들은 자동으로 제거되지 않습니다. 수동으로 검토하고 필요시 제거해주세요.\n\n"

                for dup in medium_dups:
                    elem1 = next(e for e in self.elements if e.element_id == dup.primary_id)
                    elem2 = next(e for e in self.elements if e.element_id == dup.duplicate_id)

                    md += f"#### {dup.primary_id} ↔ {dup.duplicate_id}\n\n"
                    md += f"**이유:** {dup.reason}\n\n"
                    md += f"**첫 번째 요소 (보존 추천):**\n"
                    md += f"- 타입: {elem1.element_type.value}\n"
                    md += f"- 페이지: {elem1.page_num}\n"
                    md += f"- 위치: {elem1.bbox if elem1.bbox else 'N/A'}\n"
                    md += f"- 텍스트: {elem1.text[:100]}{'...' if len(elem1.text) > 100 else ''}\n\n"

                    md += f"**두 번째 요소 (검토 필요):**\n"
                    md += f"- 타입: {elem2.element_type.value}\n"
                    md += f"- 페이지: {elem2.page_num}\n"
                    md += f"- 위치: {elem2.bbox if elem2.bbox else 'N/A'}\n"
                    md += f"- 텍스트: {elem2.text[:100]}{'...' if len(elem2.text) > 100 else ''}\n\n"
                    md += "---\n\n"
        else:
            md += "검출된 중복이 없습니다.\n\n"

        # 모든 요소 목록
        md += "## 📄 전체 추출 요소 목록\n\n"
        md += "| ID | 타입 | 페이지 | 텍스트 | 상태 |\n"
        md += "|---|---|---|---|---|\n"

        removed_ids = self.get_elements_to_remove()
        to_review = {d.duplicate_id for d in self.get_elements_to_review()}

        for elem in self.elements:
            text_preview = elem.text[:50].replace('\n', ' ').replace('|', '') if elem.text else "(빈 요소)"

            if elem.element_id in removed_ids:
                status = "🗑️  제거됨"
            elif elem.element_id in to_review:
                status = "⚠️  검토필요"
            else:
                status = "✅ 유지"

            md += f"| {elem.element_id} | {elem.element_type.value} | {elem.page_num} | {text_preview}... | {status} |\n"

        return md

    def save_report(self, output_path: str = None) -> str:
        """보고서 저장"""
        if output_path is None:
            base_path = str(Path(self.pdf_path).with_suffix(''))
            output_path = f"{base_path}_docling_process.md"

        markdown_content = self.export_to_markdown()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        return output_path


def process_pdf(pdf_path: str, output_md_path: str = None) -> Tuple[DoclingPostprocessor, str]:
    """PDF 처리 및 보고서 생성"""
    processor = DoclingPostprocessor(pdf_path)

    if not processor.extract_with_docling():
        return processor, None

    processor.detect_duplicates()

    report_path = processor.save_report(output_md_path)
    return processor, report_path
