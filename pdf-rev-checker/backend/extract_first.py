import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pdf_ocr_extractor import extract_pdf_with_ocr

pdf_path = Path(__file__).parent.parent / "[I-AGG-0301-030-A01]부표1. 현장점검 수행 및 평가기준_개정 전.pdf"

print(f"PDF 파일: {pdf_path.name}")
print(f"OCR 추출 중... (이 과정은 시간이 걸릴 수 있습니다)\n")

try:
    data, md_path, json_path = extract_pdf_with_ocr(str(pdf_path))

    # first.md로 저장
    output_path = Path(__file__).parent.parent / "first.md"

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[OK] 완료!\n")
    print(f"[OUTPUT] 출력 파일:")
    print(f"   - {output_path.name}")
    print(f"   - 크기: {len(content) / 1024:.1f} KB")
    print(f"   - 라인 수: {len(content.split(chr(10)))}")

    # 통계
    metadata = data["metadata"]
    print(f"\n[STATS] 추출 통계:")
    print(f"   - 파일: {metadata['filename']}")
    print(f"   - 페이지: {metadata['total_pages']}")
    print(f"   - 파일크기: {metadata['file_size_kb']:.1f}KB")

    # 페이지별 신뢰도
    print(f"\n[CONFIDENCE] 페이지별 OCR 신뢰도:")
    for page in data["content"]:
        confidence = page.get("ocr_confidence", 0)
        print(f"   - 페이지 {page['page_num']}: {confidence:.1%}")

    total_confidence = sum(p.get("ocr_confidence", 0) for p in data["content"])
    avg_confidence = total_confidence / len(data["content"]) if data["content"] else 0
    print(f"\n   평균 신뢰도: {avg_confidence:.1%}")

except Exception as e:
    print(f"❌ 오류 발생: {str(e)}")
    import traceback
    traceback.print_exc()
