#!/usr/bin/env python3
"""PDF 비교 기능 테스트"""

from pdf_compare_markdown import compare_pdf_markdown

# 테스트용 샘플 텍스트
before_text = """# 현장점검 기준

## 개요

이 문서는 현장점검 수행 및 평가기준을 설정합니다.

### 점검 범위

- 안전 점검
- 위생 점검

### 점검 주기

정기적인 점검을 실시합니다.

## 점검 체크리스트

1. 시설 안전 확인
2. 보안 장치 점검
3. 환경 위생 점검

---

**작성자**: 관리자
**작성일**: 2026-01-01
"""

after_text = """# 현장점검 기준 (개정)

## 개요

이 문서는 현장점검 수행 및 평가기준을 설정합니다.
개정사항이 반영되었습니다.

### 점검 범위

- 안전 점검
- 위생 점검
- 품질 점검

### 점검 주기

정기적인 점검을 월 1회 이상 실시합니다.

## 점검 체크리스트

1. 시설 안전 확인
2. 보안 장치 점검
3. 환경 위생 점검
4. 품질 기준 충족도 점검
5. 고객 만족도 조사

### 평가 기준

- 만족: 90점 이상
- 보통: 70-89점
- 미흡: 70점 미만

---

**작성자**: 관리팀
**작성일**: 2026-07-21
**검토자**: 품질담당자
"""

if __name__ == "__main__":
    print("=" * 80)
    print("PDF 비교 기능 테스트")
    print("=" * 80)

    # 비교 수행
    print("\n📊 비교 수행 중...")
    comparison_md, report_path = compare_pdf_markdown(before_text, after_text, "test_comparison")

    print(f"\n✅ 비교 완료!")
    print(f"📄 리포트 저장 위치: {report_path}")

    # 생성된 리포트 출력
    print("\n" + "=" * 80)
    print("생성된 리포트:")
    print("=" * 80)
    print(comparison_md)

    print("\n" + "=" * 80)
    print("✅ 테스트 완료!")
    print("=" * 80)
