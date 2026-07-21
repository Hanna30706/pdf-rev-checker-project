#!/usr/bin/env python3
"""
PDF 추출 결과 검증 스크립트
- 원본 PDF와 추출된 마크다운을 페이지별로 비교
- 제목, 절 번호, 본문, 표, 이미지 등의 누락/중복/오류 검증
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple
import fitz  # PyMuPDF


class PDFValidator:
    def __init__(self, pdf_path: str, extracted_md: str):
        self.pdf_path = pdf_path
        self.extracted_md = extracted_md
        self.doc = fitz.open(pdf_path)
        self.findings = []

    def validate(self) -> Dict:
        """전체 검증 실행"""
        print(f"\n{'='*70}")
        print(f"검증: {Path(self.pdf_path).name}")
        print(f"{'='*70}\n")

        with open(self.extracted_md, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # 각 페이지별 검증
        self._check_page_count(md_content)
        self._check_headers_and_sections(md_content)
        self._check_text_integrity(md_content)
        self._check_tables(md_content)
        self._check_images(md_content)
        self._check_headers_footers(md_content)
        self._check_duplicates(md_content)
        self._check_page_order(md_content)

        return self._generate_report()

    def _check_page_count(self, md_content: str):
        """페이지 수 검증"""
        pdf_pages = len(self.doc)
        md_pages = len(re.findall(r'^## 페이지 \d+', md_content, re.MULTILINE))

        if pdf_pages != md_pages:
            self.findings.append({
                'category': '페이지 수',
                'severity': 'HIGH',
                'description': f"페이지 수 불일치",
                'detail': f"PDF: {pdf_pages}개, 추출: {md_pages}개"
            })
        else:
            print(f"[OK] 페이지 수: {pdf_pages}개 (일치)")

    def _check_headers_and_sections(self, md_content: str):
        """제목과 절 번호 검증"""
        print("\n[제목 및 절 번호 검증]")

        # 마크다운에서 제목 추출
        md_titles = re.findall(r'^(#{1,6})\s+(.+)$', md_content, re.MULTILINE)

        # PDF에서 제목 후보 추출 (행의 시작, 굵음 텍스트 등)
        pdf_titles = []
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            text = page.get_text(sort=True)
            # 제목처럼 보이는 줄 추출
            for line in text.split('\n'):
                line = line.strip()
                if line and (
                    re.match(r'^[\d\.]+\s+', line) or  # 숫자 시작
                    re.match(r'^[가-힣]+[\s]*[\d\.]+', line) or  # 한글 + 숫자
                    len(line) < 60 and line.isupper()  # 짧은 대문자
                ):
                    pdf_titles.append(line)

        # 제목 검증 (상세 검증 필요)
        print(f"  마크다운 제목: {len(md_titles)}개")
        print(f"  PDF 제목 후보: {len(pdf_titles)}개")

        if len(md_titles) < len(pdf_titles) * 0.5:
            self.findings.append({
                'category': '제목 누락',
                'severity': 'MEDIUM',
                'description': "PDF의 제목이 충분히 추출되지 않음",
                'detail': f"PDF 후보: {len(pdf_titles)}, 추출: {len(md_titles)}"
            })

    def _check_text_integrity(self, md_content: str):
        """본문 텍스트 무결성 검증"""
        print("\n[본문 텍스트 검증]")

        # 페이지별 텍스트 비교
        pages_match = 0
        pages_mismatch = 0

        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            pdf_text = page.get_text(sort=True).strip()

            # 마크다운에서 해당 페이지 텍스트 추출
            page_pattern = f"## 페이지 {page_num + 1}\n(.*?)(?=## 페이지|$)"
            md_page_match = re.search(page_pattern, md_content, re.DOTALL | re.MULTILINE)

            if md_page_match:
                md_text = md_page_match.group(1).strip()

                # 기본 검증: 텍스트 일부가 포함되는지 확인
                pdf_lines = [l.strip() for l in pdf_text.split('\n') if l.strip()]
                md_lines = [l.strip() for l in md_text.split('\n') if l.strip() and not l.startswith('---')]

                # 텍스트 커버리지 계산
                if pdf_lines and md_lines:
                    coverage = sum(1 for pdf_line in pdf_lines
                                   if any(pdf_line in md_line for md_line in md_lines)) / len(pdf_lines)

                    if coverage > 0.7:
                        pages_match += 1
                    else:
                        pages_mismatch += 1
                        print(f"  [WARNING]  페이지 {page_num + 1}: 텍스트 커버리지 {coverage*100:.1f}%")

        print(f"  [OK] 일치한 페이지: {pages_match}개")
        if pages_mismatch > 0:
            print(f"  [ERROR] 불일치한 페이지: {pages_mismatch}개")
            self.findings.append({
                'category': '텍스트 손실',
                'severity': 'MEDIUM',
                'description': "일부 페이지에서 텍스트 손실",
                'detail': f"{pages_mismatch}개 페이지에서 70% 미만 커버리지"
            })

    def _check_tables(self, md_content: str):
        """표 구조 검증"""
        print("\n[표 구조 검증]")

        # 마크다운 표 패턴
        table_pattern = r'\|.+\|'
        md_tables = len(re.findall(table_pattern, md_content))

        # PDF 표 후보 추출
        pdf_tables = []
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            tables = page.find_tables()
            pdf_tables.extend(tables)

        print(f"  마크다운 표: {md_tables}개")
        print(f"  PDF 표: {len(pdf_tables)}개")

        if pdf_tables and md_tables == 0:
            self.findings.append({
                'category': '표 누락',
                'severity': 'HIGH',
                'description': "PDF의 표가 추출되지 않음",
                'detail': f"PDF: {len(pdf_tables)}개, 추출: {md_tables}개"
            })

    def _check_images(self, md_content: str):
        """이미지 텍스트 검증"""
        print("\n[이미지 텍스트 검증]")

        image_count = 0
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            # 이미지 블록 검사
            text_dict = page.get_text("dict")
            for block in text_dict.get("blocks", []):
                if block.get("type") == 1:  # 이미지 블록
                    image_count += 1

        md_image_refs = len(re.findall(r'!\[.*?\]\(.*?\)', md_content))

        print(f"  PDF 이미지: {image_count}개")
        print(f"  마크다운 이미지 참조: {md_image_refs}개")

        if image_count > 0 and md_image_refs == 0:
            print(f"  [WARNING]  PDF에 이미지가 있지만 마크다운에 참조가 없음")

    def _check_headers_footers(self, md_content: str):
        """머리글/바닥글 및 반복 검증"""
        print("\n[머리글/바닥글 검증]")

        # 페이지 번호 패턴 감지
        page_num_pattern = r'페이지 \d+|P\d+|p\d+|^- \d+ -$'
        matches = len(re.findall(page_num_pattern, md_content))

        # 반복되는 텍스트 감지
        lines = md_content.split('\n')
        line_counts = {}
        for line in lines:
            if len(line.strip()) > 20:  # 짧은 줄은 무시
                line_counts[line] = line_counts.get(line, 0) + 1

        repeated_lines = {line: count for line, count in line_counts.items() if count > 3}

        if repeated_lines:
            print(f"  [WARNING]  반복되는 텍스트 발견:")
            for line, count in list(repeated_lines.items())[:5]:
                print(f"     '{line[:50]}...' ({count}회)")
            self.findings.append({
                'category': '반복 텍스트',
                'severity': 'MEDIUM',
                'description': "동일한 텍스트가 3회 이상 반복됨",
                'detail': f"{len(repeated_lines)}개 반복 텍스트"
            })
        else:
            print(f"  [OK] 반복 텍스트 없음")

    def _check_duplicates(self, md_content: str):
        """중복 검증"""
        print("\n[중복 검증]")

        # 문장 단위로 중복 검사
        sentences = re.split(r'[。！？\n]+', md_content)
        unique_sentences = set()
        duplicates = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 50:
                if sentence in unique_sentences:
                    duplicates += 1
                unique_sentences.add(sentence)

        print(f"  고유 문장: {len(unique_sentences)}개")
        if duplicates > 0:
            print(f"  [WARNING]  중복 발견: {duplicates}개")
            self.findings.append({
                'category': '중복 문장',
                'severity': 'LOW',
                'description': "일부 문장이 중복됨",
                'detail': f"{duplicates}개 중복"
            })

    def _check_page_order(self, md_content: str):
        """페이지 순서 검증"""
        print("\n[페이지 순서 검증]")

        page_refs = re.findall(r'## 페이지 (\d+)', md_content)
        if page_refs:
            page_nums = [int(p) for p in page_refs]
            if page_nums == sorted(page_nums):
                print(f"  [OK] 페이지 순서 정상")
            else:
                print(f"  [ERROR] 페이지 순서 오류: {page_nums}")
                self.findings.append({
                    'category': '페이지 순서',
                    'severity': 'HIGH',
                    'description': "페이지 순서가 바뀜",
                    'detail': f"순서: {page_nums}"
                })

    def _generate_report(self) -> Dict:
        """검증 보고서 생성"""
        print(f"\n{'='*70}")
        print(f"검증 결과 요약")
        print(f"{'='*70}\n")

        if not self.findings:
            print("[OK] 모든 검증 통과\n")
            return {'status': 'PASSED', 'findings': []}

        print(f"[WARNING]  {len(self.findings)}개 문제 발견:\n")

        # 심각도별 정렬
        severity_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        sorted_findings = sorted(self.findings,
                                 key=lambda x: severity_order.get(x['severity'], 3))

        for finding in sorted_findings:
            print(f"  [{finding['severity']}] {finding['category']}")
            print(f"      {finding['description']}")
            if finding.get('detail'):
                print(f"      → {finding['detail']}")
            print()

        return {'status': 'FAILED', 'findings': sorted_findings}


def main():
    """검증 실행"""
    base_dir = Path("d:/★AI코딩교육(딥오토)/W2_Agent AI 학습/2026.7.21_(2)")

    # 검증 대상
    targets = [
        {
            'pdf': base_dir / "내부자료/[I-AG1-0401-G01]언론홍보 및 대응 지침_r0.pdf",
            'md': base_dir / "docling3_verification.md"
        },
        {
            'pdf': base_dir / "내부자료/[P-MGG-0601-010]국내 업면허 관리_r0.pdf",
            'md': base_dir / "docling3_process_verification.md"
        }
    ]

    results = {}

    for target in targets:
        pdf_path = target['pdf']
        md_path = target['md']

        if not pdf_path.exists():
            print(f"[ERROR] PDF 파일 없음: {pdf_path}")
            continue

        if not md_path.exists():
            print(f"[ERROR] 마크다운 파일 없음: {md_path}")
            continue

        validator = PDFValidator(str(pdf_path), str(md_path))
        result = validator.validate()
        results[pdf_path.name] = result

    # 최종 요약
    print(f"\n{'='*70}")
    print("최종 검증 결과")
    print(f"{'='*70}\n")

    for pdf_name, result in results.items():
        status = result['status']
        emoji = "[OK]" if status == "PASSED" else "[ERROR]"
        print(f"{emoji} {pdf_name}: {status}")

    print()


if __name__ == "__main__":
    main()
