#!/usr/bin/env python3
"""
PDF 추출 스크립트 (Docling OCR)
- 텍스트, 테이블, 이미지를 구조화된 JSON으로 변환
- Docling은 OCR을 포함한 고급 문서 분석 제공
- 후처리로 텍스트 정확도 개선
"""

from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
import json
import os
import re
from pathlib import Path
from datetime import datetime

def clean_text(text):
    """텍스트 후처리: 공백 정정, 특수 문자 정리, 중복 제거"""
    if not text:
        return text

    # 1. 이상한 문자 제거 (▌, 등 형태의 문자)
    text = re.sub(r'[▌◀►▲▼◆◇★☆●○■□]+', '', text)

    # 2. 여러 줄바꿈을 2개로 정규화
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 3. 문장 중간에 공백이 없는 한글 텍스트 복원 (간단한 규칙)
    # 예: "본지침은당사의언론매체" -> 이런 경우는 문맥에서 판단하기 어려우므로
    # 마크다운의 구조와 함께 처리

    # 4. 괄호 안의 한글이 제대로 되어있는지 확인
    text = re.sub(r'\(\s+', '(', text)
    text = re.sub(r'\s+\)', ')', text)

    # 5. 줄 끝의 공백 제거
    text = '\n'.join(line.rstrip() for line in text.split('\n'))

    # 6. 연속된 공백 정리 (문장 내)
    text = re.sub(r' {2,}', ' ', text)

    return text

def fix_korean_spacing(text):
    """한글 텍스트의 공백 복원 시도"""
    # 이 함수는 명백한 오류만 정정합니다
    # 예: "로서담당자및관계자의업무수행시활용할수있" 형태의 텍스트

    replacements = [
        # 원본 PDF에서 찾은 패턴들
        ("본지침은당사의언론매체홍보및대응업무에대한가이던스", "본 지침은 당사의 언론 매체 홍보 및 대응 업무에 대한 가이던스"),
        ("본지침은당사의홍보물기획및제작업무에대한가이던스", "본 지침은 당사의 홍보물 기획 및 제작 업무에 대한 가이던스"),
        ("본지침은회사의주주총회운영업무에적용한", "본 지침은 회사의 주주총회 운영 업무에 적용한다"),
        ("로서담당자및관계자의업무수행시활용할수있", "로서 담당자 및 관계자의 업무 수행 시 활용할 수 있다"),
        ("(Guidance)", "(Guidance)"),  # 이미 올바름
    ]

    for old, new in replacements:
        text = text.replace(old, new)

    return text

def extract_pdf(pdf_path):
    """Docling을 사용해 PDF에서 구조화된 데이터 추출"""

    pdf_name = Path(pdf_path).stem
    print(f"📄 '{pdf_name}' 추출 중...")

    # Docling으로 문서 변환
    converter = DocumentConverter()
    doc = converter.convert(pdf_path)

    # 마크다운으로 변환 (구조 유지)
    markdown_text = doc.document_to_markdown()

    # 후처리: 텍스트 정제
    markdown_text = clean_text(markdown_text)
    markdown_text = fix_korean_spacing(markdown_text)

    # 페이지별 청킹
    chunker = HybridChunker()
    chunks = chunker.chunk(doc)

    sections = []
    for chunk in chunks:
        section = {
            "type": "content",
            "content": clean_text(chunk.text),
            "page_number": chunk.meta.page_number if chunk.meta else None
        }
        sections.append(section)

    # 테이블 추출
    for element in doc.document.iter_tables():
        table_data = element.export_to_dict()
        sections.append({
            "type": "table",
            "content": table_data
        })

    return {
        "metadata": {
            "file_name": pdf_name,
            "file_path": pdf_path,
            "total_pages": len(doc.pages),
            "extracted_at": datetime.now().isoformat(),
            "extraction_method": "Docling OCR"
        },
        "markdown": markdown_text,
        "sections": sections,
        "raw_document": doc.document_to_dict()
    }


def save_extracted_data(data, output_dir="extracted_data"):
    """추출된 데이터를 JSON으로 저장"""

    os.makedirs(output_dir, exist_ok=True)

    file_name = data["metadata"]["file_name"]
    output_path = os.path.join(output_dir, f"{file_name}.json")

    # raw_document는 너무 크므로 저장 전 제거 (필요시 별도 저장)
    data_to_save = {k: v for k, v in data.items() if k != "raw_document"}

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, indent=2, ensure_ascii=False)

    print(f"✅ 저장됨: {output_path}")
    return output_path


def extract_multiple_pdfs(pdf_dir):
    """디렉토리의 모든 PDF 추출"""

    pdf_files = sorted(list(Path(pdf_dir).glob("*.pdf")))

    if not pdf_files:
        print(f"❌ {pdf_dir}에 PDF 파일이 없습니다.")
        return []

    results = []
    for idx, pdf_path in enumerate(pdf_files, 1):
        try:
            print(f"\n[{idx}/{len(pdf_files)}]")
            data = extract_pdf(str(pdf_path))
            output_path = save_extracted_data(data)
            results.append({
                "file": str(pdf_path),
                "output": output_path,
                "status": "success"
            })
        except Exception as e:
            print(f"❌ 오류: {pdf_path}")
            print(f"   {str(e)}")
            results.append({
                "file": str(pdf_path),
                "error": str(e),
                "status": "error"
            })

    return results


if __name__ == "__main__":
    print("🚀 PDF 추출 시작...\n")

    # 내부자료 폴더의 모든 PDF 추출
    results = extract_multiple_pdfs("내부자료")

    print("\n" + "="*60)
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"✅ 완료: {success_count}/{len(results)}")
    print("="*60)

    for r in results:
        status_icon = "✓" if r['status'] == 'success' else "✗"
        print(f"  {status_icon} {Path(r['file']).name}")
