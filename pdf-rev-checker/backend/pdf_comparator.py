from typing import List, Dict, Any
from difflib import SequenceMatcher, unified_diff
import json


class PDFComparator:
    """두 PDF의 구조화된 데이터를 비교"""

    def __init__(self, pdf1_data: Dict, pdf2_data: Dict):
        self.pdf1_data = pdf1_data
        self.pdf2_data = pdf2_data
        self.comparison_result = {
            "before": pdf1_data,
            "after": pdf2_data,
            "summary": {
                "total_added": 0,
                "total_removed": 0,
                "total_modified": 0,
                "total_unchanged": 0
            },
            "pages": []
        }

    def compare(self) -> Dict[str, Any]:
        """전체 PDF 비교"""
        pages1 = self.pdf1_data.get("pages", [])
        pages2 = self.pdf2_data.get("pages", [])

        max_pages = max(len(pages1), len(pages2))

        for page_idx in range(max_pages):
            page1 = pages1[page_idx] if page_idx < len(pages1) else None
            page2 = pages2[page_idx] if page_idx < len(pages2) else None

            page_comparison = self._compare_pages(page1, page2, page_idx + 1)
            self.comparison_result["pages"].append(page_comparison)

        self._update_summary()
        return self.comparison_result

    def _compare_pages(self, page1: Dict, page2: Dict, page_num: int) -> Dict[str, Any]:
        """단일 페이지 비교"""
        page_result = {
            "page_num": page_num,
            "status": "modified",  # modified, added, removed
            "sections": [],
            "tables": [],
            "changes": {
                "added": 0,
                "removed": 0,
                "modified": 0,
                "unchanged": 0
            }
        }

        if page1 is None:
            # 새로 추가된 페이지
            page_result["status"] = "added"
            if page2:
                page_result["sections"] = self._mark_sections_as_added(page2.get("sections", []))
                page_result["tables"] = self._mark_tables_as_added(page2.get("tables", []))
                page_result["changes"]["added"] = len(page_result["sections"])

        elif page2 is None:
            # 삭제된 페이지
            page_result["status"] = "removed"
            if page1:
                page_result["sections"] = self._mark_sections_as_removed(page1.get("sections", []))
                page_result["tables"] = self._mark_tables_as_removed(page1.get("tables", []))
                page_result["changes"]["removed"] = len(page_result["sections"])

        else:
            # 둘 다 존재 - 상세 비교
            sections_comparison = self._compare_sections(
                page1.get("sections", []),
                page2.get("sections", [])
            )
            page_result["sections"] = sections_comparison["sections"]
            page_result["changes"]["added"] = sections_comparison["added"]
            page_result["changes"]["removed"] = sections_comparison["removed"]
            page_result["changes"]["modified"] = sections_comparison["modified"]
            page_result["changes"]["unchanged"] = sections_comparison["unchanged"]

            # 표 비교
            tables_comparison = self._compare_tables(
                page1.get("tables", []),
                page2.get("tables", [])
            )
            page_result["tables"] = tables_comparison["tables"]

        return page_result

    def _compare_sections(self, sections1: List[Dict], sections2: List[Dict]) -> Dict[str, Any]:
        """섹션(텍스트 블록) 비교"""
        result = {
            "sections": [],
            "added": 0,
            "removed": 0,
            "modified": 0,
            "unchanged": 0
        }

        # 텍스트만 추출
        texts1 = [s.get("text", "") for s in sections1 if s.get("section_type") != "image"]
        texts2 = [s.get("text", "") for s in sections2 if s.get("section_type") != "image"]

        # SequenceMatcher로 유사한 항목 매칭
        matcher = SequenceMatcher(None, texts1, texts2)
        matching_blocks = matcher.get_matching_blocks()

        # 비교 결과 저장
        compared = []
        idx1, idx2 = 0, 0

        for block in matching_blocks:
            i, j, size = block.i, block.j, block.size

            # 매칭 전의 항목들 처리
            while idx1 < i:
                section = sections1[idx1].copy()
                section["change_type"] = "removed"
                compared.append(section)
                result["removed"] += 1
                idx1 += 1

            while idx2 < j:
                section = sections2[idx2].copy()
                section["change_type"] = "added"
                compared.append(section)
                result["added"] += 1
                idx2 += 1

            # 매칭된 항목 처리
            for k in range(size):
                section1 = sections1[idx1 + k]
                section2 = sections2[idx2 + k]

                # 정확히 같은지 확인
                if section1.get("text") == section2.get("text"):
                    section = section1.copy()
                    section["change_type"] = "unchanged"
                    compared.append(section)
                    result["unchanged"] += 1
                else:
                    # 수정됨
                    section = section1.copy()
                    section["change_type"] = "modified"
                    section["after"] = section2
                    compared.append(section)
                    result["modified"] += 1

            idx1 = i + size
            idx2 = j + size

        # 끝에 남은 항목들
        while idx1 < len(sections1):
            section = sections1[idx1].copy()
            section["change_type"] = "removed"
            compared.append(section)
            result["removed"] += 1
            idx1 += 1

        while idx2 < len(sections2):
            section = sections2[idx2].copy()
            section["change_type"] = "added"
            compared.append(section)
            result["added"] += 1
            idx2 += 1

        result["sections"] = compared
        return result

    def _compare_tables(self, tables1: List[Dict], tables2: List[Dict]) -> Dict[str, Any]:
        """표 비교"""
        result = {"tables": []}

        max_tables = max(len(tables1), len(tables2))

        for idx in range(max_tables):
            table1 = tables1[idx] if idx < len(tables1) else None
            table2 = tables2[idx] if idx < len(tables2) else None

            table_comparison = {
                "table_index": idx,
                "change_type": "unchanged",
                "rows": []
            }

            if table1 is None:
                table_comparison["change_type"] = "added"
                table_comparison["after"] = table2
            elif table2 is None:
                table_comparison["change_type"] = "removed"
                table_comparison["before"] = table1
            else:
                # 표 내용 비교
                rows_comparison = self._compare_table_rows(
                    table1.get("rows", []),
                    table2.get("rows", [])
                )
                table_comparison["rows"] = rows_comparison
                table_comparison["change_type"] = "modified" if rows_comparison else "unchanged"

            result["tables"].append(table_comparison)

        return result

    def _compare_table_rows(self, rows1: List[List[Dict]], rows2: List[List[Dict]]) -> List[Dict]:
        """표의 행 비교"""
        result = []
        max_rows = max(len(rows1), len(rows2))

        for row_idx in range(max_rows):
            row1 = rows1[row_idx] if row_idx < len(rows1) else None
            row2 = rows2[row_idx] if row_idx < len(rows2) else None

            row_comparison = {"row_index": row_idx, "cells": []}

            if row1 is None:
                # 새 행 추가
                row_comparison["change_type"] = "added"
                for cell in row2:
                    cell_copy = cell.copy()
                    cell_copy["change_type"] = "added"
                    row_comparison["cells"].append(cell_copy)
            elif row2 is None:
                # 행 삭제
                row_comparison["change_type"] = "removed"
                for cell in row1:
                    cell_copy = cell.copy()
                    cell_copy["change_type"] = "removed"
                    row_comparison["cells"].append(cell_copy)
            else:
                # 행 내용 비교
                max_cols = max(len(row1), len(row2))
                row_comparison["change_type"] = "modified"

                for col_idx in range(max_cols):
                    cell1 = row1[col_idx] if col_idx < len(row1) else None
                    cell2 = row2[col_idx] if col_idx < len(row2) else None

                    cell_comparison = {"col_index": col_idx}

                    if cell1 is None:
                        cell_comparison["change_type"] = "added"
                        cell_comparison["after"] = cell2
                    elif cell2 is None:
                        cell_comparison["change_type"] = "removed"
                        cell_comparison["before"] = cell1
                    else:
                        text1 = cell1.get("text", "")
                        text2 = cell2.get("text", "")

                        if text1 == text2:
                            cell_comparison["change_type"] = "unchanged"
                            cell_comparison["text"] = text1
                        else:
                            cell_comparison["change_type"] = "modified"
                            cell_comparison["before"] = cell1
                            cell_comparison["after"] = cell2

                    row_comparison["cells"].append(cell_comparison)

            result.append(row_comparison)

        return result

    def _mark_sections_as_added(self, sections: List[Dict]) -> List[Dict]:
        """섹션 모두를 추가됨으로 표시"""
        marked = []
        for section in sections:
            section_copy = section.copy()
            section_copy["change_type"] = "added"
            marked.append(section_copy)
        return marked

    def _mark_sections_as_removed(self, sections: List[Dict]) -> List[Dict]:
        """섹션 모두를 삭제됨으로 표시"""
        marked = []
        for section in sections:
            section_copy = section.copy()
            section_copy["change_type"] = "removed"
            marked.append(section_copy)
        return marked

    def _mark_tables_as_added(self, tables: List[Dict]) -> List[Dict]:
        """표 모두를 추가됨으로 표시"""
        marked = []
        for table in tables:
            table_copy = table.copy()
            table_copy["change_type"] = "added"
            marked.append(table_copy)
        return marked

    def _mark_tables_as_removed(self, tables: List[Dict]) -> List[Dict]:
        """표 모두를 삭제됨으로 표시"""
        marked = []
        for table in tables:
            table_copy = table.copy()
            table_copy["change_type"] = "removed"
            marked.append(table_copy)
        return marked

    def _update_summary(self) -> None:
        """요약 통계 계산"""
        total_added = 0
        total_removed = 0
        total_modified = 0
        total_unchanged = 0

        for page in self.comparison_result["pages"]:
            total_added += page["changes"]["added"]
            total_removed += page["changes"]["removed"]
            total_modified += page["changes"]["modified"]
            total_unchanged += page["changes"]["unchanged"]

        self.comparison_result["summary"]["total_added"] = total_added
        self.comparison_result["summary"]["total_removed"] = total_removed
        self.comparison_result["summary"]["total_modified"] = total_modified
        self.comparison_result["summary"]["total_unchanged"] = total_unchanged


def compare_pdfs(pdf1_data: Dict, pdf2_data: Dict) -> Dict[str, Any]:
    """두 PDF 비교"""
    comparator = PDFComparator(pdf1_data, pdf2_data)
    return comparator.compare()
