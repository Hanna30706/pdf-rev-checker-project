# PDF 비교 도구 - 백엔드

Python Flask 기반 PDF 분석 및 비교 백엔드입니다.

## 기능

### 1. PDF 추출 (`/api/extract`)
- 단일 PDF 파일에서 **구조화된 데이터** 추출
- **제목과 본문 자동 구분** (폰트 크기 기반)
- **문단 및 줄 단위 구조** 유지
- **표와 셀 구조** 추출
- **페이지와 좌표 정보** 포함
- **글꼴 크기, 굵기, 색상** 등 서식 정보

### 2. PDF 텍스트 추출 (`/api/extract-text`)
- 단순 텍스트 추출
- 라인 단위 분해

### 3. PDF 비교 (`/api/compare`)
- 두 PDF의 구조화된 데이터 비교
- **추가(Added)**, **삭제(Removed)**, **수정(Modified)** 항목 식별
- 섹션, 표, 셀 단위 변화 추적

### 4. 텍스트 비교 (`/api/compare-text`)
- 두 PDF의 라인 기반 간단한 비교

## 설치

### 1. 패키지 설치
```bash
cd backend
pip install -r requirements.txt
```

### 2. 서버 실행
```bash
python app.py
```

기본 포트: `http://127.0.0.1:5000`

## API 엔드포인트

### 헬스 체크
```
GET /api/health
```

**응답:**
```json
{
  "status": "ok",
  "service": "PDF Comparison Backend",
  "version": "1.0.0"
}
```

### PDF 추출
```
POST /api/extract
```

**요청:**
- `Form-Data` with file: `pdf` (PDF 파일)

**응답:**
```json
{
  "success": true,
  "data": {
    "metadata": {
      "filename": "example.pdf",
      "total_pages": 5,
      "file_size_kb": 250.5
    },
    "pages": [
      {
        "page_num": 1,
        "width": 595.276,
        "height": 841.890,
        "sections": [
          {
            "type": "section",
            "section_type": "heading",
            "bbox": [50, 100, 500, 130],
            "text": "제목입니다",
            "lines": [
              {
                "text": "제목입니다",
                "type": "heading",
                "font_size": 18,
                "bbox": [50, 100, 500, 130],
                "spans": [
                  {
                    "text": "제목입니다",
                    "font_name": "ArialBold",
                    "font_size": 18,
                    "bold": true,
                    "italic": false,
                    "color": [0, 0, 0],
                    "bbox": [50, 100, 500, 130]
                  }
                ]
              }
            ]
          }
        ],
        "tables": [
          {
            "table_index": 0,
            "bbox": [50, 300, 500, 400],
            "rows": 3,
            "cols": 4,
            "rows": [
              [
                {"row": 0, "col": 0, "text": "항목 1"},
                {"row": 0, "col": 1, "text": "값 1"}
              ]
            ]
          }
        ]
      }
    ]
  }
}
```

### 두 PDF 비교
```
POST /api/compare
```

**요청:**
- `Form-Data` with files:
  - `before` (이전 버전 PDF)
  - `after` (새 버전 PDF)

**응답:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "total_added": 5,
      "total_removed": 2,
      "total_modified": 3,
      "total_unchanged": 10
    },
    "pages": [
      {
        "page_num": 1,
        "status": "modified",
        "changes": {
          "added": 1,
          "removed": 1,
          "modified": 1,
          "unchanged": 5
        },
        "sections": [
          {
            "type": "section",
            "section_type": "text",
            "text": "수정된 내용입니다",
            "change_type": "modified",
            "after": {
              "type": "section",
              "text": "새로운 수정된 내용입니다"
            }
          }
        ]
      }
    ]
  }
}
```

## 사용 예제

### Python에서 직접 사용
```python
from pdf_extractor import extract_pdf
from pdf_comparator import compare_pdfs

# PDF 추출
pdf_data = extract_pdf("file.pdf")

# PDF 비교
comparison = compare_pdfs(pdf_data1, pdf_data2)
```

### JavaScript/Frontend에서 사용
```javascript
// PDF 추출
const formData = new FormData();
formData.append('pdf', pdfFile);

const response = await fetch('http://127.0.0.1:5000/api/extract', {
  method: 'POST',
  body: formData
});
const result = await response.json();

// 두 PDF 비교
const compareData = new FormData();
compareData.append('before', beforeFile);
compareData.append('after', afterFile);

const compareResponse = await fetch('http://127.0.0.1:5000/api/compare', {
  method: 'POST',
  body: compareData
});
const compareResult = await compareResponse.json();
```

## 데이터 구조

### Section (섹션)
```json
{
  "type": "section",
  "section_type": "heading|text|image",
  "bbox": [x0, y0, x1, y1],
  "text": "섹션 텍스트",
  "lines": [],
  "change_type": "unchanged|added|removed|modified"
}
```

### Line (줄)
```json
{
  "text": "줄 텍스트",
  "type": "heading|text",
  "font_size": 12,
  "bbox": [x0, y0, x1, y1],
  "spans": []
}
```

### Span (서식 정보 포함 텍스트)
```json
{
  "text": "텍스트",
  "font_name": "Arial",
  "font_size": 12,
  "bold": false,
  "italic": false,
  "color": [0, 0, 0],
  "bbox": [x0, y0, x1, y1]
}
```

### Table (표)
```json
{
  "table_index": 0,
  "bbox": [x0, y0, x1, y1],
  "rows": 3,
  "cols": 4,
  "rows": [
    [
      {"row": 0, "col": 0, "text": "셀 내용", "bbox": [...]},
      {"row": 0, "col": 1, "text": "셀 내용", "bbox": [...]}
    ]
  ]
}
```

## 주요 특징

1. **구조 인식**: 폰트 크기, 위치 정보로 제목/본문/표 자동 구분
2. **좌표 추적**: 모든 요소의 위치 정보(bbox) 유지
3. **서식 보존**: 글꼴, 크기, 굵기, 색상 등 메타데이터 포함
4. **지능형 비교**: SequenceMatcher 기반 정확한 변화 감지
5. **CORS 지원**: 크로스 오리진 요청 허용

## 트러블슈팅

### PyMuPDF 설치 실패
```bash
pip install --upgrade pip
pip install PyMuPDF==1.23.8
```

### 한국어 폰트 문제
PDF의 한국어 폰트가 제대로 인식되지 않으면 기본 폰트로 처리됩니다.

### 메모리 부족
대용량 PDF의 경우 메모리 사용량이 증가할 수 있습니다. 필요시 `MAX_FILE_SIZE` 조정.

## 성능 최적화

- 큰 PDF는 페이지 단위로 처리
- 임시 파일은 처리 후 즉시 삭제
- 구조화된 데이터를 JSON으로 직렬화하여 전송
