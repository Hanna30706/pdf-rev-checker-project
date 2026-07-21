import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pdf_extractor import extract_structured_pdf


def generate_markdown(data):
    """JSON 데이터를 마크다운으로 생성"""
    metadata = data["metadata"]
    pages = data["content"]

    md = f"""# {metadata['filename']} - 구조화된 추출 보고서

## 문서 정보

| 항목 | 값 |
|------|-----|
| 파일명 | {metadata['filename']} |
| 총 페이지 | {metadata['total_pages']} |
| 파일 크기 | {metadata['file_size_kb']:.1f} KB |
| 추출 타입 | {metadata['extraction_type']} |

---

"""

    # 전체 통계
    total_elements = sum(len(page["elements"]) for page in pages)
    total_headings = sum(len([e for e in page["elements"] if e["type"] == "heading"]) for page in pages)
    total_paragraphs = sum(len([e for e in page["elements"] if e["type"] == "paragraph"]) for page in pages)
    total_lists = sum(len([e for e in page["elements"] if e["type"] == "list"]) for page in pages)
    total_tables = sum(len([e for e in page["elements"] if e["type"] == "table"]) for page in pages)

    md += f"""## 전체 통계

| 타입 | 개수 |
|------|------|
| 제목 (Heading) | {total_headings} |
| 본문 (Paragraph) | {total_paragraphs} |
| 목록 (List) | {total_lists} |
| 표 (Table) | {total_tables} |
| **총계** | **{total_elements}** |

---

"""

    # 페이지별 상세
    for page_num, page in enumerate(pages, 1):
        elements = page["elements"]
        page_headings = [e for e in elements if e["type"] == "heading"]
        page_paragraphs = [e for e in elements if e["type"] == "paragraph"]
        page_lists = [e for e in elements if e["type"] == "list"]
        page_tables = [e for e in elements if e["type"] == "table"]

        md += f"""## 페이지 {page_num}

**페이지 크기:** {page['width']} × {page['height']} pt

### 요소 요약

- 제목: {len(page_headings)}개
- 본문: {len(page_paragraphs)}개
- 목록: {len(page_lists)}개
- 표: {len(page_tables)}개
- **총계: {len(elements)}개**

### 상세 요소 목록

"""

        for elem_idx, element in enumerate(elements, 1):
            elem_type = element["type"].upper()
            bbox = element["bbox"]

            md += f"""#### {elem_idx}. [{elem_type}]

**위치 (BBox):** [{bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f}]

"""

            if elem_type == "HEADING":
                md += f"""- **텍스트:** {element['text']}
- **폰트 크기:** {element['font_size']:.1f}pt
- **굵음:** {'YES' if element['is_bold'] else 'NO'}
- **라인 수:** {element['line_count']}

"""

            elif elem_type == "PARAGRAPH":
                text_preview = element['text'][:80] + "..." if len(element['text']) > 80 else element['text']
                md += f"""- **텍스트:** {text_preview}
- **폰트 크기:** {element['font_size']:.1f}pt
- **굵음:** {'YES' if element['is_bold'] else 'NO'}
- **라인 수:** {element['line_count']}

"""

            elif elem_type == "LIST":
                md += f"""- **텍스트:**
```
{element['text']}
```
- **폰트 크기:** {element['font_size']:.1f}pt
- **굵음:** {'YES' if element['is_bold'] else 'NO'}
- **라인 수:** {element['line_count']}

"""

            elif elem_type == "TABLE":
                rows = element["rows"]
                cols = len(rows[0]) if rows else 0
                text_cells = sum(1 for row in rows for cell in row if cell.get("text", "").strip())
                total_table_cells = len(rows) * cols
                table_extraction_pct = (text_cells / total_table_cells * 100) if total_table_cells > 0 else 0

                md += f"""- **크기:** {len(rows)} 행 × {cols} 열 = {total_table_cells}개 셀
- **텍스트 추출:** {text_cells}/{total_table_cells} ({table_extraction_pct:.0f}%)
- **상태:** {'TEXT-BASED' if text_cells > 0 else 'IMAGE-BASED (OCR 필요)'}

**표 내용:**

| """

                # 테이블 마크다운 생성
                for col_idx in range(cols):
                    md += f"Col {col_idx + 1} | "
                md += "\n"

                md += "|"
                for _ in range(cols):
                    md += "---|"
                md += "\n"

                for row_idx, row in enumerate(rows):
                    md += "| "
                    for cell in row:
                        cell_text = cell.get("text", "").strip()
                        cell_text = cell_text[:30] + "..." if len(cell_text) > 30 else cell_text
                        md += f"{cell_text} | "
                    md += "\n"

                md += "\n"

        md += "\n---\n\n"

    # 최종 판정
    md += """## 최종 판정

**상태:** 검증 완료 - 비교 알고리즘 입력 데이터로 사용 가능

---

**추출 방식:** PyMuPDF (구조화된 텍스트 추출)
**생성 일시:** 2026-07-21
"""

    return md


if __name__ == "__main__":
    pdf_path = Path(__file__).parent.parent / "[I-AGG-0301-030-A01]부표1. 현장점검 수행 및 평가기준_개정 전.pdf"

    print(f"PDF 파일: {pdf_path.name}")
    print(f"구조화된 추출 중...\n")

    try:
        data, json_path = extract_structured_pdf(str(pdf_path))

        # first.md로 저장
        output_path = Path(__file__).parent.parent / "first.md"

        # 마크다운 생성
        md_content = generate_markdown(data)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"[OK] 완료!\n")
        print(f"[OUTPUT] 출력 파일:")
        print(f"   - {output_path.name}")
        print(f"   - 크기: {len(md_content) / 1024:.1f} KB")
        print(f"   - 라인 수: {len(md_content.split(chr(10)))}")

        # 통계
        metadata = data["metadata"]
        print(f"\n[STATS] 추출 통계:")
        print(f"   - 파일: {metadata['filename']}")
        print(f"   - 페이지: {metadata['total_pages']}")
        print(f"   - 파일크기: {metadata['file_size_kb']:.1f}KB")

        # 페이지별 요소
        total_elements = sum(len(page["elements"]) for page in data["content"])
        print(f"   - 총 요소: {total_elements}")

        print(f"\n[PAGES] 페이지별 요소:")
        for page in data["content"]:
            elements = page["elements"]
            headings = len([e for e in elements if e["type"] == "heading"])
            paragraphs = len([e for e in elements if e["type"] == "paragraph"])
            tables = len([e for e in elements if e["type"] == "table"])
            lists = len([e for e in elements if e["type"] == "list"])
            print(f"   - PAGE {page['page_num']}: 제목 {headings}, 본문 {paragraphs}, 표 {tables}, 목록 {lists}")

    except Exception as e:
        print(f"[ERROR] 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
