#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docling 후처리 검증 테스트
- [P-MGG-0601-010]국내 업면허 관리_개정 전.pdf 사용
- 다양한 표 구조에서의 중복 검출 검증
"""

import sys
import os
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docling_postprocessor import process_pdf


def main():
    """테스트 실행"""
    # 테스트할 PDF 파일명
    pdf_filename = "[P-MGG-0601-010]국내 업면허 관리_개정 전.pdf"
    pdf_path = os.path.join(os.path.dirname(__file__), pdf_filename)

    # 출력 경로
    output_md_path = os.path.join(os.path.dirname(__file__), "docling_process_verification.md")

    print("=" * 70)
    print("[*] Docling 후처리 검증 테스트")
    print("=" * 70)
    print(f"\n[INPUT] PDF: {pdf_filename}")
    print(f"[PATH] {pdf_path}")
    print(f"[OUTPUT] {output_md_path}\n")

    # 파일 존재 확인
    if not os.path.exists(pdf_path):
        print(f"[ERROR] PDF file not found: {pdf_path}")
        print("\n[FILES] PDF files in current directory:")
        for file in os.listdir(os.path.dirname(__file__)):
            if file.endswith('.pdf'):
                print(f"   - {file}")
        return False

    print("-" * 70)
    print("[START] Processing...\n")

    try:
        # PDF 처리
        processor, report_path = process_pdf(pdf_path, output_md_path)

        if report_path is None:
            print("[ERROR] PDF processing failed")
            return False

        # 결과 출력
        print("\n" + "=" * 70)
        print("[OK] Processing Complete!")
        print("=" * 70)

        print(f"\n[STATS] Extraction Statistics:")
        print(f"   - Total Elements: {len(processor.elements)}")
        print(f"   - Duplicates Found: {len(processor.duplicates)}")

        high_count = len([d for d in processor.duplicates if d.confidence.value == 'high'])
        medium_count = len([d for d in processor.duplicates if d.confidence.value == 'medium'])

        print(f"\n[CLASSIFICATION] Duplicate Classification:")
        print(f"   - HIGH (Certain, Auto-Remove): {high_count}")
        print(f"   - MEDIUM (Review Needed): {medium_count}")

        # 요소 타입별 통계
        type_counts = {}
        for elem in processor.elements:
            key = elem.element_type.value
            type_counts[key] = type_counts.get(key, 0) + 1

        print(f"\n[DISTRIBUTION] Element Type Distribution:")
        for elem_type in sorted(type_counts.keys()):
            count = type_counts[elem_type]
            print(f"   - {elem_type.capitalize()}: {count}")

        # HIGH 신뢰도 중복 표시
        if high_count > 0:
            print(f"\n[REMOVE] Elements to be Auto-Removed:")
            for dup in processor.duplicates:
                if dup.confidence.value == 'high':
                    print(f"   - {dup.duplicate_id}: {dup.reason}")

        # MEDIUM 신뢰도 중복 표시
        if medium_count > 0:
            print(f"\n[REVIEW] Items Requiring Review:")
            for dup in processor.duplicates:
                if dup.confidence.value == 'medium':
                    print(f"   - {dup.duplicate_id}: {dup.reason}")

        print(f"\n[REPORT] Detailed Report Saved:")
        print(f"   {report_path}")

        # 파일 크기 확인
        if os.path.exists(report_path):
            file_size = os.path.getsize(report_path) / 1024
            print(f"\n[SIZE] Markdown File Size: {file_size:.1f} KB")

        print("\n" + "=" * 70)
        print("[COMPLETE] Test Finished!")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"[ERROR] Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
