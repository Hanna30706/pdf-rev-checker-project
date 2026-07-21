"""
PDF 구조화된 데이터 추출 테스트 스크립트
"""
import sys
import json
from pathlib import Path

# 콘솔 출력 인코딩 설정
if sys.stdout.encoding.lower() != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pdf_extractor import extract_structured_pdf, clean_text


def test_extract_pdf(pdf_path: str):
    """PDF 추출 테스트"""
    print(f"\n{'='*80}")
    print(f"[PDF] 추출 시작: {Path(pdf_path).name}")
    print(f"{'='*80}\n")

    try:
        # 추출 실행
        data, json_path = extract_structured_pdf(pdf_path)

        # 메타데이터 출력
        metadata = data["metadata"]
        print(f"[METADATA] 메타데이터:")
        print(f"   파일명: {metadata['filename']}")
        print(f"   페이지 수: {metadata['total_pages']}")
        print(f"   파일 크기: {metadata['file_size_kb']:.1f} KB")
        print(f"   추출 유형: {metadata['extraction_type']}\n")

        # 페이지별 요소 통계
        print(f"[ANALYSIS] 페이지별 요소 분석:")
        print(f"{'-'*80}")

        total_headings = 0
        total_paragraphs = 0
        total_lists = 0
        total_tables = 0

        for page in data["content"]:
            page_num = page["page_num"]
            elements = page["elements"]

            # 요소 타입별 분류
            headings = [e for e in elements if e["type"] == "heading"]
            paragraphs = [e for e in elements if e["type"] == "paragraph"]
            lists = [e for e in elements if e["type"] == "list"]
            tables = [e for e in elements if e["type"] == "table"]

            total_headings += len(headings)
            total_paragraphs += len(paragraphs)
            total_lists += len(lists)
            total_tables += len(tables)

            if elements:
                print(f"\n[PAGE {page_num}]")
                print(f"   Size: {page['width']:.0f} x {page['height']:.0f}")
                print(f"   Headings: {len(headings)}")
                print(f"   Paragraphs: {len(paragraphs)}")
                print(f"   Lists: {len(lists)}")
                print(f"   Tables: {len(tables)}")

                # 첫 몇 요소 미리보기
                if headings:
                    print(f"\n   [HEADINGS]")
                    for heading in headings[:2]:
                        text = clean_text(heading["text"])
                        preview = text[:60] + "..." if len(text) > 60 else text
                        print(f"      - {preview}")

                if paragraphs:
                    print(f"\n   [PARAGRAPHS]")
                    for para in paragraphs[:2]:
                        text = clean_text(para["text"])
                        preview = text[:60] + "..." if len(text) > 60 else text
                        print(f"      - {preview}")

                if tables:
                    print(f"\n   [TABLES]")
                    for i, table in enumerate(tables):
                        rows = len(table["rows"])
                        cols = len(table["rows"][0]) if table["rows"] else 0
                        print(f"      Table {i+1}: {rows} rows x {cols} cols")

        print(f"\n{'-'*80}")
        print(f"[SUMMARY] Total Statistics:")
        print(f"   Headings: {total_headings}")
        print(f"   Paragraphs: {total_paragraphs}")
        print(f"   Lists: {total_lists}")
        print(f"   Tables: {total_tables}")
        print(f"   Total: {total_headings + total_paragraphs + total_lists + total_tables}")

        # JSON 파일 저장 위치
        print(f"\n[SUCCESS] JSON saved: {json_path}")

        return data, json_path

    except Exception as e:
        print(f"[ERROR] Extraction failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None


def print_sample_json(data: dict, num_samples: int = 3):
    """샘플 JSON 출력"""
    print(f"\n{'='*80}")
    print(f"[SAMPLE] JSON Sample (first {num_samples} elements)")
    print(f"{'='*80}\n")

    sample_elements = []
    for page in data["content"]:
        for element in page["elements"][:num_samples]:
            sample_elements.append({
                "page_num": page["page_num"],
                "element": element
            })

        if sample_elements:
            break

    for i, item in enumerate(sample_elements, 1):
        print(f"[SAMPLE {i}]")
        print(json.dumps(item, ensure_ascii=False, indent=2))
        print()


def analyze_extraction_criteria(data: dict):
    """추출 기준 분석 및 설명"""
    print(f"\n{'='*80}")
    print(f"[CRITERIA] Extraction Criteria Analysis")
    print(f"{'='*80}\n")

    print("[1] HEADING (제목) - Criteria:")
    print("    - Font size >= average font size x 1.15")
    print("    - OR Bold text style")
    print("    - Single line or short text\n")

    print("[2] LIST (목록) - Criteria:")
    print("    - Numeric list: 1. 2. 3. or 1) 2) 3)")
    print("    - Alphabet: a. b. c. or A) B) C)")
    print("    - Bullet points: -, *, etc.")
    print("    - Indented text with above markers\n")

    print("[3] PARAGRAPH (문단) - Criteria:")
    print("    - General text (not heading or list)")
    print("    - Multiple consecutive lines")
    print("    - Same paragraph: line spacing <= line height x 1.2\n")

    print("[4] TABLE (표) - Criteria:")
    print("    - Auto-detected by PyMuPDF find_tables()")
    print("    - Grid-based structure with borders")
    print("    - Table cell text excluded from paragraph extraction\n")

    print("[5] BBOX (Bounding Box) - Format:")
    print("    - Format: [x0, y0, x1, y1]")
    print("    - x0: left start, y0: top start")
    print("    - x1: right end, y1: bottom end")
    print("    - Unit: PDF points (72 DPI)\n")

    # 실제 데이터로 기준 검증
    print("[6] DATA VALIDATION:")

    # 각 타입별 폰트 크기 분석
    font_sizes_by_type = {"heading": [], "paragraph": [], "list": [], "table": []}

    for page in data["content"]:
        for element in page["elements"]:
            if element["type"] in font_sizes_by_type:
                font_sizes_by_type[element["type"]].append(element.get("font_size", 0))

    for elem_type, sizes in font_sizes_by_type.items():
        if sizes:
            avg_size = sum(sizes) / len(sizes)
            min_size = min(sizes)
            max_size = max(sizes)
            print(f"    {elem_type:12}: avg={avg_size:.1f}pt, range={min_size:.1f}-{max_size:.1f}pt (n={len(sizes)})")


def main():
    """메인 테스트 함수"""
    # PDF 파일 경로
    pdf_dir = Path(__file__).parent.parent
    pdf_files = list(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        print("[ERROR] No PDF files found.")
        print(f"    Path: {pdf_dir}")
        return

    # 첫 번째 PDF 파일 사용
    pdf_path = str(pdf_files[0])

    # 추출 실행
    data, json_path = test_extract_pdf(pdf_path)

    if data and json_path:
        # 샘플 출력
        print_sample_json(data, num_samples=3)

        # 추출 기준 설명
        analyze_extraction_criteria(data)

        print(f"\n{'='*80}")
        print(f"[DONE] Test completed!")
        print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
