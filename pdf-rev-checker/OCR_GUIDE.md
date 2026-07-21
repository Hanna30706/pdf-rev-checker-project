# PDF OCR 추출 및 비교 시스템 가이드

## 📋 개요

이미지 기반 PDF를 OCR(광학 문자 인식)을 사용하여 텍스트로 추출하고, 마크다운 문서로 변환한 후 두 버전을 비교하는 시스템입니다.

## 🛠 설치

### 1. 의존성 설치

```bash
cd backend
pip install -r requirements.txt
```

**필수 라이브러리:**
- `paddleocr` - 한글 OCR (PaddleOCR)
- `opencv-python` - 이미지 처리
- `Pillow` - 이미지 포맷 지원
- `Flask` - REST API 서버

### 2. PaddleOCR 모델 다운로드

첫 실행 시 자동으로 다운로드됩니다 (~500MB):
```bash
# 수동 다운로드 (선택사항)
python -c "from paddleocr import PaddleOCR; PaddleOCR(use_angle_cls=True, lang='ch')"
```

## 🚀 사용 방법

### 방법 1: Python API 직접 사용

#### OCR 추출
```python
from pdf_ocr_extractor import extract_pdf_with_ocr

# PDF 추출
data, md_path, json_path = extract_pdf_with_ocr("document.pdf")

# 결과
# - md_path: document_ocr.md (마크다운)
# - json_path: document_ocr.json (구조화된 데이터)
```

#### PDF 비교
```python
from pdf_compare_markdown import compare_pdf_markdown

# 텍스트 읽기
with open("doc_v1_ocr.md") as f:
    before = f.read()
with open("doc_v2_ocr.md") as f:
    after = f.read()

# 비교
comparison_md, report_path = compare_pdf_markdown(before, after, "comparison")

# 결과: comparison_comparison.md
```

### 방법 2: REST API 사용

#### 시작
```bash
python app.py
```

#### OCR 추출 API
```bash
curl -X POST http://localhost:5000/api/extract-ocr \
  -F "pdf=@document.pdf"
```

**응답:**
```json
{
  "success": true,
  "filename": "document.pdf",
  "markdown": "# 추출된 마크다운...",
  "data": { ... }
}
```

#### PDF 비교 API
```bash
curl -X POST http://localhost:5000/api/compare-ocr \
  -F "before=@document_v1.pdf" \
  -F "after=@document_v2.pdf"
```

**응답:**
```json
{
  "success": true,
  "before_file": "document_v1.pdf",
  "after_file": "document_v2.pdf",
  "comparison_report": "# 비교 리포트...",
  "before_extracted": "# 이전 버전 텍스트...",
  "after_extracted": "# 현재 버전 텍스트..."
}
```

### 방법 3: 테스트 스크립트

```bash
python backend/test_ocr_extraction.py
```

**실행 결과:**
- ✓ OCR 추출 테스트
- ✓ 페이지별 신뢰도 출력
- ✓ PDF 비교 테스트
- ✓ 비교 리포트 생성

## 📊 출력 형식

### 마크다운 문서 (document_ocr.md)

```markdown
# document.pdf - OCR 추출 보고서

## 📋 문서 정보
| 항목 | 값 |
|------|-----|
| 파일명 | document.pdf |
| 총 페이지 | 2 |
| 파일 크기 | 201.5 KB |

## 📄 페이지 1

**OCR 신뢰도:** 87.3%

### 텍스트 내용

추출된 텍스트가 여기에 표시됩니다.
신뢰도가 낮은 텍스트는 > 로 표시됩니다.
```

### 비교 리포트 (comparison_comparison.md)

```markdown
# PDF 비교 리포트: comparison

## 📊 비교 요약
| 항목 | 값 |
|------|-----|
| 유사도 | 75.3% |
| 추가된 라인 | 12 |
| 삭제된 라인 | 8 |
| 변경되지 않은 라인 | 145 |

## 🔄 변경 사항

### ✅ 추가된 내용
+ 새로 추가된 라인 1
+ 새로 추가된 라인 2

### ❌ 삭제된 내용
- 삭제된 라인 1
- 삭제된 라인 2

### 📝 상세 비교 (Unified Diff)
...
```

## 🎯 OCR 신뢰도

각 페이지의 OCR 신뢰도 점수:
- **90% 이상**: 우수 (거의 완벽)
- **70-90%**: 양호 (약간의 오류 가능)
- **50-70%**: 보통 (검수 필요)
- **50% 미만**: 저하 (OCR 모델 개선 필요)

**신뢰도 점수 낮음 시 대처:**
1. PDF 품질 확인 (스캔 품질, 해상도)
2. OCR 모델 설정 조정
3. 사용자가 직접 검증

## 📁 파일 구조

```
pdf-rev-checker/
├── backend/
│   ├── app.py                      # Flask API 서버
│   ├── pdf_ocr_extractor.py        # OCR 추출 모듈
│   ├── pdf_compare_markdown.py     # 마크다운 비교 모듈
│   ├── pdf_extractor.py            # 기본 추출 모듈
│   ├── pdf_comparator.py           # 기본 비교 모듈
│   ├── test_ocr_extraction.py      # OCR 테스트
│   └── requirements.txt
├── frontend/
│   └── pdf-compare.html
├── OCR_GUIDE.md                    # 이 파일
└── *.pdf                           # PDF 파일들
```

## 🔧 주요 기능

### 1. OCR 추출 (`pdf_ocr_extractor.py`)
- PDF 페이지를 이미지로 렌더링
- PaddleOCR을 사용하여 한글/영문 텍스트 추출
- 신뢰도 점수 계산
- 마크다운 및 JSON 형식으로 저장

### 2. 마크다운 비교 (`pdf_compare_markdown.py`)
- 추가된 라인 감지
- 삭제된 라인 감지
- 변경된 라인 감지
- Unified Diff 형식으로 상세 표시
- 유사도 점수 계산

### 3. REST API (`app.py`)
- `/api/extract-ocr` - OCR 추출
- `/api/compare-ocr` - OCR 기반 비교
- 기존 API도 계속 사용 가능

## 📈 성능 고려사항

### 처리 시간
- 단일 페이지: 2-5초
- 10페이지 문서: 20-50초
- 복잡한 레이아웃: 더 길어질 수 있음

### 메모리 사용
- PaddleOCR 모델: ~500MB
- 처리 중: 페이지당 50-100MB

### 최적화 팁
1. 고해상도 이미지 사용 (DPI 300 이상 권장)
2. 불필요한 페이지는 미리 필터링
3. 배치 처리 시 진행 표시 추가

## 🐛 문제 해결

### PaddleOCR 모델 다운로드 오류
```bash
# 수동으로 다운로드
python -c "from paddleocr import PaddleOCR; PaddleOCR(use_angle_cls=True, lang='ch')"
```

### 메모리 부족
- 작은 PDF부터 시작하여 테스트
- 시스템 메모리 확인
- 동시 처리 작업 제한

### OCR 정확도 낮음
- PDF의 이미지 품질 확인
- 회전되거나 왜곡된 텍스트 확인
- 폰트 설치 상태 확인

## 📚 참고 자료

- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - OCR 엔진
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF 처리
- [OpenCV](https://opencv.org/) - 이미지 처리

## 📝 라이센스

- PaddleOCR: Apache 2.0
- PyMuPDF: AGPL 3.0
- 본 프로젝트: MIT

## 🤝 기여

개선 사항이나 버그 리포트는 언제든지 환영합니다!

---

**마지막 업데이트:** 2026-07-21
**버전:** 1.0.0
