#!/usr/bin/env python3
"""PDF 추출 결과 개선"""

import re
from pathlib import Path
from typing import List, Dict

try:
    import fitz
except ImportError:
    print("PyMuPDF 필요: pip install PyMuPDF")
    exit(1)


def parse_pymupdf_section(content: str) -> Dict[int, str]:
    """PyMuPDF 섹션에서 페이지별 텍스트 추출"""
    pages = {}
    pattern = r'## 페이지 (\d+)\n(.*?)(?=^## 페이지|\Z)'
    matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)

    for match in matches:
        page_num = int(match.group(1))
        page_text = match.group(2).strip()
        pages[page_num] = page_text

    return pages


def extract_tables_from_docling(content: str) -> List[str]:
    """Docling 섹션에서 마크다운 표 추출"""
    tables = []
    lines = content.split('\n')

    current_table = []
    in_table = False

    for line in lines:
        if line.strip().startswith('|'):
            if not in_table:
                in_table = True
            current_table.append(line)
        elif in_table:
            if line.strip() == '' or not line.strip().startswith('|'):
                if current_table:
                    tables.append('\n'.join(current_table))
                current_table = []
                in_table = False

    if current_table:
        tables.append('\n'.join(current_table))

    return tables


def improve_verification_v1(input_file: str, output_file: str, pdf_path: str):
    """1번 PDF 개선: PyMuPDF 중심 본문 + Docling 표"""
    print("[1번] 개선 시작: {}".format(input_file))

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 섹션 분리
    docling_match = re.search(
        r'(?:^|\n)## Docling 추출 결과|(?:^|\n)\*\*Docling 추출 결과\*\*',
        content, re.MULTILINE)
    pymupdf_match = re.search(
        r'(?:^|\n)## PyMuPDF 페이지별 텍스트|(?:^|\n)\*\*PyMuPDF 페이지별 텍스트\*\*',
        content, re.MULTILINE)

    if not docling_match or not pymupdf_match:
        print("  [ERROR] 섹션 구분 실패")
        return False

    docling_section = content[docling_match.start():pymupdf_match.start()]
    pymupdf_section = content[pymupdf_match.start():]

    # PyMuPDF에서 페이지별 텍스트 추출
    pymupdf_pages = parse_pymupdf_section(pymupdf_section)
    print("  [INFO] PyMuPDF 페이지: {}개".format(len(pymupdf_pages)))

    # Docling에서 표 추출
    tables = extract_tables_from_docling(docling_section)
    print("  [INFO] Docling 표: {}개".format(len(tables)))

    # 개선된 출력 작성
    improved = """# [I-AG1-0401-G01]언론홍보 및 대응 지침_r0

**추출 방법**: PyMuPDF (본문/제목/절/순서 기준) + Docling (표 구조)

---

## 개선된 본문 (PyMuPDF 기준)

"""

    # PyMuPDF 페이지별 텍스트를 그대로 유지하되, 정리
    for page_num in sorted(pymupdf_pages.keys()):
        improved += "### 페이지 {}\n\n".format(page_num)
        page_text = pymupdf_pages[page_num].strip()
        improved += page_text + "\n\n"

    improved += "\n---\n\n## 표 구조 (Docling 기반)\n\n"

    # 표 추가
    for idx, table in enumerate(tables, 1):
        improved += "### 표 {}\n\n{}\n\n".format(idx, table)

    # 원본 섹션 참고자료로 추가
    improved += """---

## 원본 추출 결과 (참고)

{}

{}
""".format(docling_section, pymupdf_section)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(improved)

    print("  [OK] 완료: {}".format(output_file))
    return True


def improve_verification_v2(input_file: str, output_file: str, pdf_path: str):
    """2번 PDF 개선: Docling 중심 + PaddleOCR (선택)"""
    print("[2번] 개선 시작: {}".format(input_file))

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # OCR 시도 (PaddleOCR이 없으면 건너뜀)
    ocr_section = "\n\n---\n\n## 프로세스 맵 이미지 텍스트 (PaddleOCR)\n\n"

    try:
        import paddleocr

        print("  [INFO] PaddleOCR으로 이미지 텍스트 추출 중...")
        doc = fitz.open(pdf_path)

        ocr = paddleocr.PaddleOCR(use_angle_cls=True, lang='ch')
        extracted_count = 0

        for page_num, page in enumerate(doc, 1):
            images = page.get_images()

            for img_index, xref in enumerate(images):
                try:
                    pix = fitz.Pixmap(doc, xref)
                    img_file = "/tmp/ocr_{}_{}.png".format(page_num, img_index)
                    pix.save(img_file)

                    result = ocr.ocr(img_file, cls=True)

                    if result:
                        ocr_section += "### 페이지 {}, 이미지 {}\n\n".format(
                            page_num, img_index + 1)

                        for line in result:
                            if line:
                                for word_info in line:
                                    if word_info[1][0]:
                                        ocr_section += word_info[1][0] + "\n"

                        ocr_section += "\n"
                        extracted_count += 1

                except Exception as e:
                    pass

        doc.close()
        print("  [INFO] {}개 이미지에서 텍스트 추출".format(extracted_count))

    except ImportError:
        ocr_section += "PaddleOCR이 설치되지 않았습니다.\n"
        ocr_section += "설치: pip install paddleocr paddlepaddle\n"
        print("  [WARN] PaddleOCR 미설치 (선택사항)")

    except Exception as e:
        ocr_section += "OCR 오류: {}\n".format(str(e))
        print("  [WARN] OCR 오류: {}".format(e))

    # 결과 작성
    improved = content + ocr_section

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(improved)

    print("  [OK] 완료: {}".format(output_file))
    return True


def main():
    print("\n=== PDF 추출 결과 개선 ===\n")

    # 1번: 언론홍보 및 대응 지침
    pdf1 = './내부자료/[I-AG1-0401-G01]언론홍보 및 대응 지침_r0.pdf'
    if Path(pdf1).exists():
        improve_verification_v1(
            'docling3_verification.md',
            'docling4_verification.md',
            pdf1
        )
    else:
        print("[ERROR] PDF 파일 없음: {}".format(pdf1))

    print()

    # 2번: 국내 업면허 관리
    pdf2 = './내부자료/[P-MGG-0601-010]국내 업면허 관리_r0.pdf'
    if Path(pdf2).exists():
        improve_verification_v2(
            'docling3_process_verification.md',
            'docling4_process_verification.md',
            pdf2
        )
    else:
        print("[ERROR] PDF 파일 없음: {}".format(pdf2))

    print("\n=== 완료 ===\n")


if __name__ == '__main__':
    main()
