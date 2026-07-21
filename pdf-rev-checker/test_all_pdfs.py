#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
모든 PDF 파일 처리 및 검증
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docling_postprocessor import process_pdf


def main():
    """모든 PDF 처리"""
    project_dir = os.path.dirname(os.path.abspath(__file__))

    # 모든 PDF 파일 찾기
    pdf_files = []
    for file in os.listdir(project_dir):
        if file.endswith('.pdf'):
            pdf_files.append(file)

    if not pdf_files:
        print("[ERROR] No PDF files found")
        return False

    print("=" * 70)
    print("[TEST] Testing all PDF files with Docling postprocessor")
    print("=" * 70)
    print(f"\n[FOUND] {len(pdf_files)} PDF files:\n")

    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"  {i}. {pdf_file}")

    print("\n" + "-" * 70)

    results = []

    for pdf_file in sorted(pdf_files):
        print(f"\n[PROCESSING] {pdf_file}")
        print("-" * 70)

        pdf_path = os.path.join(project_dir, pdf_file)
        output_path = os.path.join(project_dir, f"docling_{Path(pdf_file).stem}.md")

        try:
            processor, report_path = process_pdf(pdf_path, output_path)

            if report_path:
                # 통계
                total_elements = len(processor.elements)
                total_duplicates = len(processor.duplicates)
                high_count = len([d for d in processor.duplicates if d.confidence.value == 'high'])
                medium_count = len([d for d in processor.duplicates if d.confidence.value == 'medium'])

                results.append({
                    'file': pdf_file,
                    'total_elements': total_elements,
                    'total_duplicates': total_duplicates,
                    'high_confidence': high_count,
                    'medium_confidence': medium_count,
                    'status': 'OK'
                })

                print(f"[OK] {pdf_file}")
                print(f"    Elements: {total_elements}")
                print(f"    Duplicates: {total_duplicates} (HIGH: {high_count}, MEDIUM: {medium_count})")
                print(f"    Report: {report_path}")
            else:
                results.append({
                    'file': pdf_file,
                    'status': 'FAILED'
                })
                print(f"[FAILED] {pdf_file}")

        except Exception as e:
            results.append({
                'file': pdf_file,
                'status': 'ERROR',
                'error': str(e)
            })
            print(f"[ERROR] {pdf_file}: {str(e)}")

    # 최종 결과 요약
    print("\n" + "=" * 70)
    print("[SUMMARY] Test Results")
    print("=" * 70 + "\n")

    print("| PDF File | Elements | Duplicates | HIGH | MEDIUM | Status |")
    print("|---|---|---|---|---|---|")

    for result in results:
        if result['status'] == 'OK':
            print(f"| {result['file']} | {result['total_elements']} | {result['total_duplicates']} | "
                  f"{result['high_confidence']} | {result['medium_confidence']} | OK |")
        else:
            print(f"| {result['file']} | - | - | - | - | {result['status']} |")

    print("\n" + "=" * 70)
    print("[COMPLETE] All tests finished")
    print("=" * 70)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
