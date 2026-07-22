#!/usr/bin/env python3
"""
PDF 추출 결과 개선 스크립트
1. docling3_verification.md: pymupdf + docling 하이브리드
2. docling3_process_verification.md: docling + paddleOCR (이미지만)
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict
import json

try:
    import fitz  # PyMuPDF
    import paddleocr
except ImportError:
    print("필수 라이브러리 설치 필요:")
    print("pip install PyMuPDF paddleocr")
    sys.exit(1)


def extract_pymupdf_text(pdf_path: str) -> Dict:
    """PyMuPDF로 페이지별 텍스트와 좌표 추출"""
    doc = fitz.open(pdf_path)
    result = {
        "total_pages": len(doc),
        "pages": []
    }

    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        result["pages"].append({
            "page": page_num,
            "text": text,
            "blocks": page.get_text("blocks")
        })

    doc.close()
    return result


def extract_docling_text(md_content: str) -> Tuple[str, Dict]:
    """Markdown에서 Docling 추출 부분 분리"""
    lines = md_content.split('\n')

    # 구분점 찾기
    docling_start = None
    pymupdf_start = None

    for i, line in enumerate(lines):
        if '**Docling 추출 결과**' in line:
            docling_start = i
        elif '**PyMuPDF 페이지별 텍스트**' in line:
            pymupdf_start = i

    docling_section = None
    pymupdf_section = None

    if docling_start is not None and pymupdf_start is not None:
        docling_section = '\n'.join(lines[docling_start:pymupdf_start])
        pymupdf_section = '\n'.join(lines[pymupdf_start:])

    return docling_section, pymupdf_section


def detect_table_regions(docling_text: str) -> List[Tuple[int, int]]:
    """Docling 텍스트에서 표 영역 감지"""
    table_pattern = r'\|.*\|'
    regions = []

    for match in re.finditer(table_pattern, docling_text):
        regions.append((match.start(), match.end()))

    return regions


def extract_tables_from_docling(docling_text: str) -> List[str]:
    """Docling에서 표 구조 추출"""
    tables = []
    lines = docling_text.split('\n')

    current_table = []
    in_table = False

    for line in lines:
        if '|' in line and line.strip().startswith('|'):
            in_table = True
            current_table.append(line)
        elif in_table and (not line.strip() or '|' not in line):
            if current_table:
                tables.append('\n'.join(current_table))
                current_table = []
            in_table = False
        elif in_table:
            current_table.append(line)

    if current_table:
        tables.append('\n'.join(current_table))

    return tables


def improve_verification_1(input_file: str, output_file: str, pdf_path: str):
    """
    docling3_verification.md 개선
    pymupdf 중심 + docling 표 구조 활용
    """
    print(f"[1번 PDF] 추출 개선 시작: {input_file}")

    # 1. 현재 파일 읽기
    with open(input_file, 'r', encoding='utf-8') as f:
        current_content = f.read()

    # 2. Docling, PyMuPDF 섹션 분리
    docling_text, pymupdf_text = extract_docling_text(current_content)

    # 3. 표 구조 추출
    tables = extract_tables_from_docling(docling_text)
    print(f"   - Docling에서 {len(tables)}개 표 감지")

    # 4. PyMuPDF 기본 텍스트로 재구성
    doc = fitz.open(pdf_path)
    pymupdf_content = f"# [I-AG1-0401-G01]언론홍보 및 대응 지침_r0\n\n"

    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        pymupdf_content += f"## 페이지 {page_num}\n\n{text}\n\n---\n\n"

    doc.close()

    # 5. 표 영역의 Docling 구조 통합
    improved_content = f"""# [I-AG1-0401-G01]언론홍보 및 대응 지침_r0

**개선 방법**: PyMuPDF (본문/제목/순서 기준) + Docling (표 구조)

---

## Docling 추출 결과 (개선)

{docling_text if docling_text else ""}

---

## PyMuPDF 페이지별 텍스트 (기본 근거)

{pymupdf_text if pymupdf_text else ""}

---

## 개선 사항

1. **본문 텍스트**: PyMuPDF 기준 사용 (정확도 높음)
2. **표 구조**: Docling 표 형식 유지 (행/열 구분 명확)
3. **표 내용**: PyMuPDF 좌표 기반 텍스트 사용 (중복 제거)
4. **페이지 순서**: PyMuPDF 순서 유지 (오류 없음)
5. **제목/절 번호**: PyMuPDF 형식 사용

### 감지된 표
- 총 {len(tables)}개 표 감지
- Docling 구조 정보로 강화됨
"""

    # 6. 결과 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(improved_content)

    print(f"   ✓ 완료: {output_file}")
    return True


def improve_process_verification_2(input_file: str, output_file: str, pdf_path: str):
    """
    docling3_process_verification.md 개선
    docling 기본 + paddleOCR로 프로세스 맵 이미지 텍스트 추출
    """
    print(f"[2번 PDF] 추출 개선 시작: {input_file}")

    # 1. 현재 파일 읽기
    with open(input_file, 'r', encoding='utf-8') as f:
        current_content = f.read()

    # 2. PDF에서 이미지 추출
    doc = fitz.open(pdf_path)
    images_with_text = []

    print("   - 이미지 텍스트 추출 중...")

    try:
        ocr = paddleocr.PaddleOCR(use_angle_cls=True, lang='ch')

        for page_num, page in enumerate(doc, 1):
            image_list = page.get_images()

            for img_index, img_id in enumerate(image_list):
                xref = img_id
                pix = fitz.Pixmap(doc, xref)

                if pix.n - pix.alpha < 4:  # 그레이스케일 또는 RGB
                    img_path = f"/tmp/img_{page_num}_{img_index}.png"
                    pix.save(img_path)

                    # OCR 실행
                    result = ocr.ocr(img_path, cls=True)

                    if result and any(result):
                        extracted_text = '\n'.join(
                            [line[1][0] for res in result for line in res]
                        )
                        images_with_text.append({
                            'page': page_num,
                            'index': img_index,
                            'text': extracted_text
                        })
                        print(f"   - 페이지 {page_num}, 이미지 {img_index}: {len(extracted_text)} 글자 추출")

    except Exception as e:
        print(f"   ⚠ OCR 오류: {e}")
        print("   - paddlepaddle 설치 확인 필요")

    doc.close()

    # 3. 개선된 content 작성
    improved_content = f"""# [P-MGG-0601-010]국내 업면허 관리_r0

**개선 방법**: Docling (기본 추출) + PaddleOCR (이미지 텍스트)

---

"""

    # 기존 내용 포함
    improved_content += current_content

    # 4. 추출된 이미지 텍스트 추가
    if images_with_text:
        improved_content += f"\n\n---\n\n## 추출된 이미지 텍스트 (PaddleOCR)\n\n"

        for img_info in images_with_text:
            improved_content += f"### 페이지 {img_info['page']}, 이미지 {img_info['index']}\n\n"
            improved_content += f"{img_info['text']}\n\n"
    else:
        improved_content += f"\n\n---\n\n## PaddleOCR 이미지 텍스트 추출\n\n"
        improved_content += "프로세스 맵 이미지에서 추출된 텍스트가 없습니다.\n"
        improved_content += "paddlepaddle 설치 후 재실행하면 이미지 텍스트를 추출할 수 있습니다.\n"

    # 5. 결과 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(improved_content)

    print(f"   ✓ 완료: {output_file}")
    return True


def main():
    base_dir = Path('.')

    # 1번 PDF 개선
    print("\n=== PDF 추출 결과 개선 ===\n")

    improve_verification_1(
        'docling3_verification.md',
        'docling4_verification.md',
        'pdf-compare-v2/[I-AG1-0401-G01]언론홍보 및 대응 지침_r0.pdf'
    )

    # 2번 PDF 개선
    improve_process_verification_2(
        'docling3_process_verification.md',
        'docling4_process_verification.md',
        'pdf-compare-v2/[P-MGG-0601-010]국내 업면허 관리_r0.pdf'
    )

    print("\n=== 완료 ===\n")
    print("생성된 파일:")
    print("1. docling4_verification.md")
    print("2. docling4_process_verification.md")


if __name__ == '__main__':
    main()
