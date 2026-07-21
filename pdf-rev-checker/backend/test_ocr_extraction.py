"""
OCR 기반 PDF 추출 및 비교 테스트
"""
import sys
from pathlib import Path

# backend 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from pdf_ocr_extractor import extract_pdf_with_ocr
from pdf_compare_markdown import compare_pdf_markdown


def test_ocr_extraction():
    """OCR 추출 테스트"""
    print("=" * 100)
    print("OCR 기반 PDF 추출 테스트")
    print("=" * 100 + "\n")

    # PDF 파일 찾기
    pdf_dir = Path(__file__).parent.parent
    pdf_files = list(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        print("❌ PDF 파일을 찾을 수 없습니다.")
        return

    # 첫 번째 PDF 추출
    pdf_path = pdf_files[0]
    print(f"📄 PDF 파일: {pdf_path.name}\n")

    print("🔄 OCR 추출 중... (이 과정은 시간이 걸릴 수 있습니다)")

    try:
        data, md_path, json_path = extract_pdf_with_ocr(str(pdf_path))

        print(f"✓ 추출 완료!\n")

        # 결과 정보
        metadata = data["metadata"]
        print(f"📊 추출 결과:")
        print(f"  - 파일: {metadata['filename']}")
        print(f"  - 페이지: {metadata['total_pages']}")
        print(f"  - 크기: {metadata['file_size_kb']:.1f}KB\n")

        # 페이지별 신뢰도
        print(f"📈 페이지별 OCR 신뢰도:")
        total_confidence = 0
        for page in data["content"]:
            confidence = page.get("ocr_confidence", 0)
            total_confidence += confidence
            print(f"  - 페이지 {page['page_num']}: {confidence:.1%}")

        avg_confidence = total_confidence / len(data["content"]) if data["content"] else 0
        print(f"\n  평균 신뢰도: {avg_confidence:.1%}\n")

        # 마크다운 미리보기
        print(f"📝 마크다운 파일 생성:")
        print(f"  - 마크다운: {md_path}")
        print(f"  - JSON: {json_path}\n")

        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
            lines = md_content.split('\n')
            print("마크다운 미리보기 (처음 30줄):")
            print("-" * 100)
            for i, line in enumerate(lines[:30]):
                print(line)
            if len(lines) > 30:
                print(f"\n... (생략: 총 {len(lines)}줄)")
            print("-" * 100 + "\n")

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


def test_ocr_comparison():
    """OCR 비교 테스트"""
    print("\n" + "=" * 100)
    print("OCR 기반 PDF 비교 테스트")
    print("=" * 100 + "\n")

    # 두 개 이상의 PDF 찾기
    pdf_dir = Path(__file__).parent.parent
    pdf_files = sorted(list(pdf_dir.glob("*.pdf")))

    if len(pdf_files) < 2:
        print("⚠ 비교할 PDF 파일이 2개 이상 필요합니다.")
        return

    pdf_path1 = pdf_files[0]
    pdf_path2 = pdf_files[1] if len(pdf_files) > 1 else pdf_files[0]

    print(f"📄 비교할 파일:")
    print(f"  - 이전 버전: {pdf_path1.name}")
    print(f"  - 현재 버전: {pdf_path2.name}\n")

    print("🔄 OCR 추출 및 비교 중...\n")

    try:
        # OCR 추출
        before_data, before_md_path, _ = extract_pdf_with_ocr(str(pdf_path1))
        after_data, after_md_path, _ = extract_pdf_with_ocr(str(pdf_path2))

        # 마크다운 읽기
        with open(before_md_path, 'r', encoding='utf-8') as f:
            before_text = f.read()
        with open(after_md_path, 'r', encoding='utf-8') as f:
            after_text = f.read()

        # 비교
        comparison_md, report_path = compare_pdf_markdown(
            before_text,
            after_text,
            f"{pdf_path1.stem}_vs_{pdf_path2.stem}"
        )

        print(f"✓ 비교 완료!\n")

        # 결과 정보
        print(f"📊 비교 결과:")
        print(f"  - 리포트 파일: {report_path}\n")

        # 비교 리포트 미리보기
        print("비교 리포트 미리보기:")
        print("-" * 100)
        lines = comparison_md.split('\n')
        for i, line in enumerate(lines[:50]):
            print(line)
        if len(lines) > 50:
            print(f"\n... (생략: 총 {len(lines)}줄)")
        print("-" * 100 + "\n")

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 PDF OCR 추출 및 비교 시스템 테스트\n")

    # OCR 추출 테스트
    test_ocr_extraction()

    # OCR 비교 테스트
    test_ocr_comparison()

    print("\n✅ 테스트 완료!\n")
