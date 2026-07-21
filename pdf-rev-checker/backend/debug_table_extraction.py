"""
표 텍스트 추출 상세 분석 스크립트
PyMuPDF의 find_tables()에서 각 셀의 텍스트를 직접 확인
"""
import fitz
from pathlib import Path


def analyze_table_text(pdf_path: str):
    """PDF의 표에서 텍스트 추출 상세 분석"""

    print("\n" + "=" * 120)
    print("TABLE TEXT EXTRACTION ANALYSIS")
    print("=" * 120)

    doc = fitz.open(pdf_path)

    # 페이지 1 분석
    page = doc[0]

    print(f"\nPDF: {Path(pdf_path).name}")
    print(f"Page: 1")
    print(f"Page Size: {page.rect.width} x {page.rect.height}\n")

    # 표 찾기
    try:
        table_finder = page.find_tables()
        tables = list(table_finder.tables)  # TableFinder를 리스트로 변환
        print(f"Found Tables: {len(tables)}\n")

        # 각 표 분석
        for table_idx, table in enumerate(tables):
            print(f"{'-' * 120}")
            print(f"TABLE {table_idx + 1}")
            print(f"{'-' * 120}")

            print(f"\nTable Info:")
            print(f"  Bbox: {table.bbox}")
            print(f"  Rows: {len(table.cells)}")
            print(f"  Cols: {len(table.cells[0]) if table.cells else 0}")
            print(f"  Total Cells: {len(table.cells) * len(table.cells[0]) if table.cells else 0}")

            # 각 셀의 텍스트 추출 상세 분석
            print(f"\n[CELL TEXT EXTRACTION]")
            print(f"{'Row':<5} {'Col':<5} {'BBox':<50} {'get_text()':<30} {'Status'}")
            print(f"{'-' * 120}")

            text_cells_found = 0
            empty_cells = 0

            for row_idx, row_cells in enumerate(table.cells):
                for col_idx, cell_bbox in enumerate(row_cells):
                    if cell_bbox:
                        # 셀에서 텍스트 추출 (rect 기반)
                        try:
                            # cell_bbox는 이미 Rect 객체
                            cell_text = page.get_text(clip=cell_bbox).strip()
                        except Exception as e:
                            cell_text = ""

                        # 셀 분석
                        if cell_text:
                            text_cells_found += 1
                            status = f"✓ TEXT FOUND"
                            text_display = cell_text[:28]
                        else:
                            empty_cells += 1
                            status = f"✗ EMPTY"
                            text_display = "(empty)"

                        bbox_str = f"[{cell_bbox[0]:.1f},{cell_bbox[1]:.1f},{cell_bbox[2]:.1f},{cell_bbox[3]:.1f}]"

                        # 처음 5개 행만 상세 출력
                        if row_idx < 5:
                            print(f"{row_idx:<5} {col_idx:<5} {bbox_str:<50} {text_display:<30} {status}")
                    else:
                        if row_idx < 5:
                            print(f"{row_idx:<5} {col_idx:<5} {'(None)':<50} {'(None)':<30} INVALID")
                        empty_cells += 1

            print(f"\n{'-' * 120}")
            print(f"Summary for Table {table_idx + 1}:")
            print(f"  Total Cells: {len(table.cells) * len(table.cells[0])}")
            print(f"  Cells with Text: {text_cells_found} ({100*text_cells_found/(len(table.cells) * len(table.cells[0])):.1f}%)")
            print(f"  Empty Cells: {empty_cells} ({100*empty_cells/(len(table.cells) * len(table.cells[0])):.1f}%)")
            print()

        # 테이블 1 상세 분석
        print(f"\n{'=' * 120}")
        print(f"DETAILED ANALYSIS - TABLE 1 (First Table)")
        print(f"{'=' * 120}\n")

        if len(tables) > 0:
            table = tables[0]
            print(f"Table Bbox: {table.bbox}")
            print(f"  Left (x0): {table.bbox[0]:.2f}")
            print(f"  Top (y0): {table.bbox[1]:.2f}")
            print(f"  Right (x1): {table.bbox[2]:.2f}")
            print(f"  Bottom (y1): {table.bbox[3]:.2f}")
            print(f"  Width: {table.bbox[2] - table.bbox[0]:.2f} pt")
            print(f"  Height: {table.bbox[3] - table.bbox[1]:.2f} pt\n")

            print("All Cells Content (Row by Row):\n")
            for row_idx, row_cells in enumerate(table.cells):
                print(f"Row {row_idx}:")
                for col_idx, cell_bbox in enumerate(row_cells):
                    if cell_bbox:
                        try:
                            cell_text = page.get_text(clip=cell_bbox).strip()
                        except Exception as e:
                            cell_text = ""

                        print(f"  Col {col_idx}: bbox={cell_bbox}")
                        print(f"           text='{cell_text}' (length: {len(cell_text)})")

                        # 추가 분석: 다양한 get_text() 방식 시도
                        if not cell_text:
                            print(f"           [Trying alternative extraction methods...]")

                            # Method 1: dict 모드로 블록 확인
                            try:
                                text_dict = page.get_text("dict", clip=cell_bbox)
                                blocks = text_dict.get("blocks", [])
                                print(f"           - blocks found: {len(blocks)}")
                                if blocks:
                                    for block in blocks:
                                        if block.get("type") == 0:  # 텍스트 블록
                                            lines = block.get("lines", [])
                                            print(f"             text block with {len(lines)} lines")
                            except Exception as e:
                                print(f"           - dict method: {str(e)}")

                print()

    except Exception as e:
        print(f"Error analyzing tables: {str(e)}")
        import traceback
        traceback.print_exc()

    doc.close()


def main():
    """메인 함수"""
    # PDF 파일 경로
    pdf_dir = Path(__file__).parent.parent
    pdf_files = list(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found.")
        return

    # 첫 번째 PDF 분석
    pdf_path = str(pdf_files[0])
    analyze_table_text(pdf_path)


if __name__ == "__main__":
    main()
