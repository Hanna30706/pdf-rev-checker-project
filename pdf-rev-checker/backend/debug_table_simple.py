"""
표 텍스트 추출 상세 분석 - 간단한 버전
"""
import fitz
import sys
import io
from pathlib import Path

# UTF-8 출력 설정
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def analyze_tables(pdf_path: str):
    """PDF의 표 텍스트 추출 분석"""

    print("\n" + "=" * 120)
    print("TABLE TEXT EXTRACTION ANALYSIS")
    print("=" * 120 + "\n")

    doc = fitz.open(pdf_path)
    page = doc[0]

    print(f"PDF File: {Path(pdf_path).name}")
    print(f"Page: 1")
    print(f"Page Size: {page.rect.width} x {page.rect.height}\n")

    # 표 찾기
    table_finder = page.find_tables()
    tables = list(table_finder.tables)

    print(f"[FOUND] {len(tables)} tables\n")

    # Table 1 분석
    if len(tables) > 0:
        print("=" * 120)
        print("TABLE 1 - DETAILED ANALYSIS")
        print("=" * 120 + "\n")

        table = tables[0]

        print(f"Table Information:")
        print(f"  BBox: {table.bbox}")
        print(f"  Rows: {len(table.cells)}")
        print(f"  Cols: {len(table.cells[0]) if table.cells else 0}\n")

        # 각 행의 데이터 출력
        print(f"{'Row':<5} {'Col':<5} {'BBox':<45} {'Text Content':<40} {'Status'}")
        print("-" * 120)

        total_cells = 0
        cells_with_text = 0

        for row_idx, row in enumerate(table.cells):
            for col_idx, cell in enumerate(row):
                total_cells += 1

                # cell은 Rect 객체
                if cell:
                    try:
                        # 셀에서 텍스트 추출
                        text = page.get_text(clip=cell).strip()

                        if text:
                            cells_with_text += 1
                            status = "✓ HAS TEXT"
                            text_display = text[:38]
                        else:
                            status = "✗ EMPTY"
                            text_display = "(no text)"

                        bbox_display = f"[{cell.x0:.1f},{cell.y0:.1f},{cell.x1:.1f},{cell.y1:.1f}]"

                        print(f"{row_idx:<5} {col_idx:<5} {bbox_display:<45} {text_display:<40} {status}")

                    except Exception as e:
                        print(f"{row_idx:<5} {col_idx:<5} {'ERROR':<45} {str(e):<40} ERROR")
                else:
                    print(f"{row_idx:<5} {col_idx:<5} {'(None)':<45} {'(None)':<40} SKIP")

        print()
        print("-" * 120)
        print(f"\nSummary:")
        print(f"  Total Cells: {total_cells}")
        print(f"  Cells with Text: {cells_with_text} ({100*cells_with_text/total_cells:.1f}%)")
        print(f"  Empty Cells: {total_cells - cells_with_text} ({100*(total_cells - cells_with_text)/total_cells:.1f}%)")

    # Table 2 분석
    if len(tables) > 1:
        print("\n" + "=" * 120)
        print("TABLE 2 - DETAILED ANALYSIS")
        print("=" * 120 + "\n")

        table = tables[1]

        print(f"Table Information:")
        print(f"  BBox: {table.bbox}")
        print(f"  Rows: {len(table.cells)}")
        print(f"  Cols: {len(table.cells[0]) if table.cells else 0}\n")

        # 각 행의 데이터 출력 (처음 5행만)
        print(f"{'Row':<5} {'Col':<5} {'BBox':<45} {'Text Content':<40} {'Status'}")
        print("-" * 120)

        total_cells = 0
        cells_with_text = 0

        for row_idx, row in enumerate(table.cells):
            if row_idx >= 5:
                print(f"... ({len(table.cells) - 5} more rows)")
                break

            for col_idx, cell in enumerate(row):
                total_cells += 1

                if cell:
                    try:
                        text = page.get_text(clip=cell).strip()

                        if text:
                            cells_with_text += 1
                            status = "✓ HAS TEXT"
                            text_display = text[:38]
                        else:
                            status = "✗ EMPTY"
                            text_display = "(no text)"

                        bbox_display = f"[{cell.x0:.1f},{cell.y0:.1f},{cell.x1:.1f},{cell.y1:.1f}]"

                        print(f"{row_idx:<5} {col_idx:<5} {bbox_display:<45} {text_display:<40} {status}")

                    except Exception as e:
                        print(f"{row_idx:<5} {col_idx:<5} {'ERROR':<45} {str(e):<40} ERROR")
                else:
                    print(f"{row_idx:<5} {col_idx:<5} {'(None)':<45} {'(None)':<40} SKIP")

        print()
        print("-" * 120)
        print(f"\nSummary:")
        print(f"  Total Cells (first 5 rows): {total_cells}")
        print(f"  Cells with Text: {cells_with_text} ({100*cells_with_text/total_cells:.1f}%)" if total_cells > 0 else "  No cells")

        # 전체 통계
        all_cells = len(table.cells) * len(table.cells[0])
        print(f"  Total Cells (all rows): {all_cells}")

    print("\n" + "=" * 120)
    print("CONCLUSION")
    print("=" * 120)

    if cells_with_text == 0:
        print("\n✗ OCR 필요함: 이 PDF의 표들은 이미지(스캔) 형태입니다.")
        print("   - PyMuPDF는 표의 구조(행/열/셀 위치)는 인식합니다")
        print("   - 하지만 표 안의 텍스트는 이미지로 되어있어 추출 불가능합니다")
        print("   - 텍스트를 추출하려면 OCR(광학 문자 인식) 도구가 필요합니다")
        print("   - 하지만 구조 비교(행/열 개수, 레이아웃 변화)는 가능합니다\n")
    else:
        print("\n✓ OCR 불필요: 이 PDF의 표들에서 텍스트를 추출할 수 있습니다\n")

    doc.close()


if __name__ == "__main__":
    pdf_dir = Path(__file__).parent.parent
    pdf_files = list(pdf_dir.glob("*.pdf"))

    if pdf_files:
        analyze_tables(str(pdf_files[0]))
    else:
        print("No PDF files found")
