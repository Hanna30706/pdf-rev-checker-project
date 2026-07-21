#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 추출 및 검증 마크다운 생성 스크립트
- 모든 PDF 추출 및 정제
- docling2_verification.md 생성
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime

# UTF-8 인코딩 설정
os.chdir(r"d:\★AI코딩교육(딥오토)\W2_Agent AI 학습\2026.7.21_(2)")
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import ConversionStatus

def restore_korean_spacing(text):
    """한글 띄어쓰기 복원"""
    # 정규 표현식을 사용하여 자주 나타나는 패턴 복원
    patterns = [
        # 본 지침 패턴들
        (r"본지침은", "본 지침은"),
        (r"당사의언론매체", "당사의 언론 매체"),
        (r"홍보및대응", "홍보 및 대응"),
        (r"당사의홍보물", "당사의 홍보물"),
        (r"기획및제작", "기획 및 제작"),
        (r"회사의주주", "회사의 주주"),
        (r"주총회운영", "주주총회 운영"),
        (r"업무에적용", "업무에 적용"),
        # 로서/담당자 패턴
        (r"로서담당자", "로서 담당자"),
        (r"담당자및관계자", "담당자 및 관계자"),
        (r"업무수행시", "업무 수행 시"),
        (r"활용할수있", "활용할 수 있"),
    ]

    for old_pattern, new_text in patterns:
        text = re.sub(old_pattern, new_text, text)

    return text

def clean_text(text):
    """텍스트 정제 함수"""
    if not text:
        return text

    # 1. 이상한 문자 제거
    text = re.sub(r'[▌◀►▲▼◆◇★☆●○■□\x00-\x08\x0B-\x0C\x0E-\x1F\x7F-\x9F]+', '', text)

    # 2. 한글 띄어쓰기 복원
    text = restore_korean_spacing(text)

    # 3. 연속된 줄바꿈 정규화
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 4. 테이블 앞의 불필요한 "[" 제거
    text = re.sub(r'\n\[\n\n\|', '\n\n|', text)
    text = re.sub(r'\n\[\n\|', '\n|', text)

    # 5. 라인 끝 공백 제거
    text = '\n'.join(line.rstrip() for line in text.split('\n'))

    # 6. 연속된 공백 정리
    text = re.sub(r' {2,}', ' ', text)

    # 7. 불완전한 문장 정정
    text = text.replace("활용할 수 있\n\n", "활용할 수 있다\n\n")

    return text

def fix_spacing_comprehensive(text):
    """포괄적인 한글 띄어쓰기 복원"""
    # 연속된 한글 텍스트에서 자주 나타나는 패턴들
    patterns = [
        # 일반적인 패턴
        (r'([가-힣])(당사의)', r'\1 \2'),
        (r'(본|본지침|본 지침)(은당사)', r'\1은 당사'),
        (r'은당사의', '은 당사의'),
        (r'당사의([가-힣]+)홍보', r'당사의 \1홍보'),
        (r'매체홍보', '매체 홍보'),
        (r'홍보및', '홍보 및'),
        (r'대응업무', '대응 업무'),
        (r'대한가이던스', '대한 가이던스'),
        (r'업무에대한', '업무에 대한'),
        (r'기획및제작', '기획 및 제작'),
        (r'업무에적용', '업무에 적용'),
        (r'주주총회운영', '주주총회 운영'),
        # "로서" 패턴
        (r'로서담당', '로서 담당'),
        (r'담당자및', '담당자 및'),
        (r'의업무', '의 업무'),
        (r'업무수행', '업무 수행'),
        (r'시활용', '시 활용'),
    ]

    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)

    return text

def extract_pdf_docling(pdf_path):
    """Docling을 사용해 PDF 추출"""
    try:
        converter = DocumentConverter()
        result = converter.convert(str(pdf_path))

        if result.status == ConversionStatus.SUCCESS:
            # 마크다운 추출 및 정제
            markdown = result.document.export_to_markdown()
            markdown = clean_text(markdown)

            # 페이지별 처리를 통한 추가 정제
            lines = markdown.split('\n')
            cleaned_lines = []

            for line in lines:
                # 각 라인의 공백 문제 정제
                line = line.strip()
                if line:
                    # 포괄적인 공백 복원
                    line = fix_spacing_comprehensive(line)
                cleaned_lines.append(line)

            markdown = '\n'.join(cleaned_lines)

            return {
                "status": "success",
                "markdown": markdown,
                "pages": len(result.document.pages) if hasattr(result.document, 'pages') else 0,
                "size": pdf_path.stat().st_size
            }
        else:
            return {"status": "failed", "error": str(result.status)}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def generate_verification_markdown():
    """모든 PDF 추출 및 검증 마크다운 생성"""

    pdf_dir = Path("내부자료")
    pdf_files = sorted(list(pdf_dir.glob("*.pdf")))

    print(f"발견된 PDF: {len(pdf_files)}개\n")

    all_results = []
    for idx, pdf_path in enumerate(pdf_files, 1):
        print(f"[{idx}/{len(pdf_files)}] {pdf_path.name} 처리 중...")

        result = extract_pdf_docling(pdf_path)

        if result["status"] == "success":
            all_results.append({
                "file_name": pdf_path.name,
                "file_path": str(pdf_path),
                "status": "SUCCESS",
                "size": result["size"],
                "pages": result["pages"],
                "content": result["markdown"]
            })
            print(f"  ✓ 완료")
        else:
            print(f"  ✗ 오류: {result.get('error', 'Unknown')}")

    # 마크다운 생성
    md_lines = []
    md_lines.append("# PDF 추출 검증 문서\n")
    md_lines.append("이 문서는 Docling OCR 모델을 사용하여 PDF 파일에서 추출한 구조화된 데이터입니다.\n")

    # 추출 요약
    md_lines.append("## 추출 요약\n")
    success_count = sum(1 for r in all_results if r["status"] == "SUCCESS")
    md_lines.append(f"- **추출 일시**: {datetime.now().isoformat()}")
    md_lines.append(f"- **총 파일 수**: {len(pdf_files)}")
    md_lines.append(f"- **성공**: {success_count}개")
    md_lines.append(f"- **실패**: {len(pdf_files) - success_count}개\n")

    # 파일별 추출 결과
    md_lines.append("## 파일별 추출 결과\n")

    for idx, result in enumerate(all_results, 1):
        md_lines.append(f"### {idx}. {result['file_name']}\n")
        md_lines.append("| 항목 | 값 |")
        md_lines.append("|------|-----|")
        md_lines.append(f"| 경로 | `{result['file_path']}` |")
        md_lines.append(f"| 파일 크기 | {result['size']:,} bytes |")
        md_lines.append(f"| 상태 | **{result['status']}** |")
        md_lines.append(f"| 추출 텍스트 길이 | {len(result['content'])} characters |")
        md_lines.append(f"| 페이지 수 | {result['pages']} |\n")

        md_lines.append("#### 추출된 내용\n")
        md_lines.append(result["content"])
        md_lines.append("\n---\n")

    # 파일 저장
    output_path = Path("docling2_verification.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

    print(f"\n✓ 완료: {output_path}")
    return output_path

if __name__ == "__main__":
    print("="*60)
    print("PDF 추출 및 검증 마크다운 생성")
    print("="*60 + "\n")

    generate_verification_markdown()
