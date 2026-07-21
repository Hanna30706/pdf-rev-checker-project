# PDF 비교 및 검증 시스템

> 두 버전의 PDF를 비교하고, OCR을 사용하여 이미지 기반 PDF도 처리하는 포괄적인 시스템

## ✨ 주요 기능

### 1️⃣ 구조화된 PDF 추출
- PyMuPDF를 사용한 텍스트 기반 PDF 분석
- 제목, 본문, 표, 목록 자동 분류
- 바운딩 박스 및 폰트 정보 보존
- JSON 및 마크다운 형식 출력

### 2️⃣ OCR 기반 추출 ⭐ NEW
- PaddleOCR을 사용한 한글/영문 인식
- 이미지 기반 PDF 텍스트 추출
- 신뢰도 점수 계산
- 마크다운 자동 생성

### 3️⃣ PDF 버전 비교
- 구조화된 비교 (제목, 본문, 표)
- 라인 기반 비교
- 추가/삭제/수정 사항 감지
- 유사도 점수 계산
- Unified Diff 형식 리포트

### 4️⃣ 웹 인터페이스
- 드래그 앤 드롭 PDF 업로드
- 실시간 비교 결과
- 색상 코딩 (추가/삭제/수정)
- 반응형 디자인

## 📦 시스템 구성

```
pdf-rev-checker/
├── backend/
│   ├── app.py                      # Flask REST API 서버
│   ├── pdf_extractor.py            # 구조화된 PDF 추출
│   ├── pdf_ocr_extractor.py        # ⭐ OCR 기반 추출
│   ├── pdf_comparator.py           # 기본 비교 로직
│   ├── pdf_compare_markdown.py     # ⭐ 마크다운 기반 비교
│   ├── test_ocr_extraction.py      # ⭐ OCR 테스트
│   └── requirements.txt
│
├── frontend/
│   └── pdf-compare.html            # 웹 UI
│
├── SYSTEM_README.md                # 이 파일
├── OCR_GUIDE.md                    # ⭐ OCR 상세 가이드
└── extraction_report.md            # 마크다운 추출 결과
```

## 🚀 빠른 시작

### 1. 설치

```bash
cd backend
pip install -r requirements.txt
```

### 2. 테스트

```bash
# OCR 기반 추출 및 비교 테스트
python test_ocr_extraction.py
```

### 3. 서버 시작

```bash
python app.py
# 또는
python backend/app.py
```

### 4. 웹 인터페이스 사용

브라우저에서 `frontend/pdf-compare.html` 열기

## 📋 새로운 API 엔드포인트

### ⭐ OCR 기반 추출
```bash
POST /api/extract-ocr
- 입력: PDF 파일
- 출력: 마크다운 텍스트 + 메타데이터
- 사용: 이미지 기반 PDF 처리
```

**예제:**
```bash
curl -X POST http://localhost:5000/api/extract-ocr \
  -F "pdf=@document.pdf"
```

### ⭐ OCR 기반 비교
```bash
POST /api/compare-ocr
- 입력: 두 개의 PDF 파일 (before, after)
- 출력: 비교 리포트 (마크다운)
- 사용: 두 PDF 버전 비교
```

**예제:**
```bash
curl -X POST http://localhost:5000/api/compare-ocr \
  -F "before=@document_v1.pdf" \
  -F "after=@document_v2.pdf"
```

## 💡 사용 예제

### Python에서 직접 사용

#### OCR 추출
```python
from pdf_ocr_extractor import extract_pdf_with_ocr

# PDF 추출
data, md_path, json_path = extract_pdf_with_ocr("document.pdf")

print(f"마크다운: {md_path}")      # document_ocr.md
print(f"JSON: {json_path}")        # document_ocr.json
```

#### 마크다운 기반 비교
```python
from pdf_compare_markdown import compare_pdf_markdown

# 텍스트 읽기
with open("doc_v1_ocr.md") as f:
    before = f.read()
with open("doc_v2_ocr.md") as f:
    after = f.read()

# 비교
comparison_md, report_path = compare_pdf_markdown(before, after)

print(f"비교 결과: {report_path}")  # comparison_comparison.md
```

## 📊 출력 예시

### 마크다운 추출 결과 (document_ocr.md)

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

부표1. 현장점검 수행 및 평가기준
점검유형 점검주기 관리방안
...
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
+ 새로 추가된 내용 1
+ 새로 추가된 내용 2

### ❌ 삭제된 내용
- 제거된 내용 1
- 제거된 내용 2

### 📝 상세 비교 (Unified Diff)
```diff
 변경되지 않은 라인
-삭제된 라인
+추가된 라인
 변경되지 않은 라인
```
```

## 🎯 워크플로우

### OCR 기반 처리
```
PDF 입력
  ↓
이미지로 렌더링 (2배 확대)
  ↓
PaddleOCR로 텍스트 인식
  ↓
신뢰도 점수 계산
  ↓
마크다운 + JSON 출력
```

### PDF 비교
```
PDF 파일 A & B
  ↓
OCR 또는 구조화된 추출
  ↓
텍스트 추출
  ↓
라인 기반 비교
  ↓
추가/삭제/수정 감지
  ↓
마크다운 리포트 생성
```

## 🔧 기술 스택

### Backend
- **Flask** 2.3.3 - REST API
- **PyMuPDF** 1.23.8 - PDF 처리
- **PaddleOCR** 2.7.0.3 - 광학 문자 인식 ⭐
- **OpenCV** 4.8.1.78 - 이미지 처리 ⭐
- **Pillow** 10.0.1 - 이미지 포맷 ⭐

### Features
- 한글/영문 OCR 지원
- Unified Diff 형식
- 신뢰도 기반 마킹
- 자동 레이아웃 분석

## 📈 성능

| 작업 | 시간 |
|------|------|
| 단일 페이지 OCR | 2-5초 |
| 10페이지 문서 | 20-50초 |
| PDF 비교 | <1초 |
| 마크다운 생성 | <1초 |

## 🔍 상세 가이드

- **[OCR 완전 가이드](OCR_GUIDE.md)** - 모든 OCR 기능 설명
- **[추출 검증 보고서](EXTRACTION_REPORT.md)** - 품질 검증
- **[마크다운 샘플](extraction_report.md)** - 출력 형식 예시

## 🐛 문제 해결

### OCR 신뢰도가 낮은 경우
1. PDF 스캔 품질 확인
2. 이미지 해상도 확인 (300 DPI 이상 권장)
3. 글꼴 지원 확인

### 메모리 부족
1. 한 번에 한 페이지씩 처리
2. 불필요한 페이지 필터링
3. 배치 크기 감소

### PaddleOCR 모델 다운로드 오류
```bash
python -c "from paddleocr import PaddleOCR; PaddleOCR(use_angle_cls=True, lang='ch')"
```

## 📚 API 문서

### 기존 API

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| `POST` | `/api/extract` | 구조화된 PDF 추출 |
| `POST` | `/api/compare` | 구조화된 비교 |
| `POST` | `/api/compare-text` | 텍스트 기반 비교 |

### 새 API (⭐)

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| `POST` | `/api/extract-ocr` | OCR 추출 → 마크다운 |
| `POST` | `/api/compare-ocr` | OCR 비교 → 마크다운 리포트 |

## 💬 Q&A

**Q: 텍스트 기반 PDF는 어떻게?**
A: 기존 `/api/extract` 또는 `/api/compare` 사용

**Q: 이미지 기반 PDF는?**
A: 새 `/api/extract-ocr` 또는 `/api/compare-ocr` 사용

**Q: 둘 다 사용할 수 있나?**
A: 예, 두 시스템이 독립적으로 작동합니다

**Q: OCR 정확도는?**
A: 일반적으로 85-95% (PDF 품질에 따라 변동)

## 📝 라이센스

- **PaddleOCR**: Apache 2.0
- **PyMuPDF**: AGPL 3.0
- **본 프로젝트**: MIT

---

**업데이트:** 2026-07-21  
**버전:** 1.1.0 (OCR 추가)

⭐ = 새로 추가된 기능
