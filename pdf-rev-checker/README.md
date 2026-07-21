# PDF 비교 도구

Python 백엔드(PyMuPDF)와 JavaScript 프론트엔드를 사용한 고급 PDF 비교 시스템입니다.

## 🎯 주요 기능

### ✨ 구조화된 데이터 추출
- **제목과 본문 자동 구분**: 폰트 크기 기반 스마트 분류
- **문단 및 줄 단위 구조**: 텍스트 레이아웃 보존
- **표와 셀 구조 추출**: 테이블 데이터 정확히 인식
- **페이지 및 좌표 정보**: 모든 요소의 위치 추적
- **서식 정보 유지**: 글꼴, 크기, 굵기, 색상 등 메타데이터

### 🔍 지능형 비교
- **추가(Added)**: 새로운 내용 녹색 하이라이트
- **삭제(Removed)**: 제거된 내용 빨강 하이라이트 + 취소선
- **수정(Modified)**: 변경된 내용 파랑 하이라이트
- **통계**: 변경사항 요약 (추가/삭제/수정 개수)

## 📁 프로젝트 구조

```
pdf-rev-checker/
├── backend/                 # Python Flask 백엔드
│   ├── app.py              # Flask 앱
│   ├── pdf_extractor.py    # PyMuPDF 기반 PDF 추출
│   ├── pdf_comparator.py   # PDF 비교 로직
│   ├── requirements.txt     # Python 의존성
│   └── README.md           # 백엔드 문서
├── frontend/               # JavaScript 프론트엔드
│   └── pdf-compare.html    # 웹 인터페이스
└── README.md              # 이 파일
```

## 🚀 시작하기

### 1️⃣ 백엔드 설정

#### Python 설치 확인
```bash
python --version  # Python 3.8 이상 필요
```

#### 의존성 설치
```bash
cd backend
pip install -r requirements.txt
```

#### 백엔드 서버 실행
```bash
python app.py
```

출력:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### 2️⃣ 프론트엔드 실행

#### 옵션 A: 직접 열기
- `frontend/pdf-compare.html`을 웹 브라우저에서 열기

#### 옵션 B: 로컬 서버로 실행 (권장)
```bash
# Python이 설치되어 있다면
python -m http.server 8000 --directory frontend

# Node.js가 있다면
npx http-server frontend -p 8000

# 또는 http://localhost:8000/pdf-compare.html 접속
```

## 🔌 API 엔드포인트

### 헬스 체크
```
GET http://127.0.0.1:5000/api/health
```

### 두 PDF 비교 (메인 기능)
```
POST http://127.0.0.1:5000/api/compare
```

**요청 파라미터:**
- `before` (file): 이전 버전 PDF
- `after` (file): 새 버전 PDF

**응답 구조:**
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
        "sections": [
          {
            "text": "변경된 내용",
            "change_type": "modified",
            "section_type": "text"
          }
        ]
      }
    ]
  }
}
```

### 단일 PDF 추출
```
POST http://127.0.0.1:5000/api/extract
```

자세한 API 문서는 [backend/README.md](backend/README.md) 참고

## 💻 사용 방법

### 기본 사용 흐름

1. **브라우저 열기**: `http://localhost:8000/pdf-compare.html`

2. **파일 선택**
   - "이전 버전(Before)" 상자에 원본 PDF 업로드
   - "새로운 버전(After)" 상자에 수정된 PDF 업로드
   - 드래그&드롭 지원

3. **비교 실행**
   - "비교하기" 버튼 클릭
   - 백엔드에서 PDF 분석 시작

4. **결과 확인**
   - 통계: 추가/삭제/수정 개수
   - 테이블: 줄 단위 비교 결과
   - 색상 코딩:
     - 🟢 **초록색**: 추가된 내용
     - 🔴 **빨강색**: 삭제된 내용
     - 🔵 **파랑색**: 수정된 내용

5. **초기화**: "초기화" 버튼으로 다시 시작

## 🛠️ 트러블슈팅

### ❌ "백엔드 미연결" 에러
```
✗ 백엔드 미연결 (http://127.0.0.1:5000)
```

**해결:**
1. 백엔드 서버 실행 확인
```bash
cd backend
python app.py
```

2. 포트 충돌 확인
```bash
# Windows
netstat -ano | findstr :5000

# Mac/Linux
lsof -i :5000
```

### ❌ PyMuPDF 설치 실패
```
error: Microsoft Visual C++ 14.0 or greater is required
```

**해결:**
```bash
# Visual C++ 빌드 도구 설치 또는
pip install --upgrade pip
pip install PyMuPDF==1.23.8 --no-cache-dir
```

### ❌ 한국어 폰트 문제
PDF의 한국어가 제대로 인식되지 않으면:
- 시스템 폰트 확인
- PDF가 포함된 폰트 사용하는지 확인

### ❌ 메모리 부족 (대용량 PDF)
- 한 번에 하나의 비교만 수행
- 브라우저 재시작
- `backend/app.py`에서 `MAX_FILE_SIZE` 조정 필요시

## 📊 데이터 구조 예제

### 추출된 섹션 (Section)
```json
{
  "type": "section",
  "section_type": "heading",
  "text": "제목 텍스트",
  "bbox": [50, 100, 500, 130],
  "font_size": 18,
  "change_type": "modified",
  "lines": [
    {
      "text": "제목 텍스트",
      "type": "heading",
      "font_size": 18,
      "spans": [
        {
          "text": "제목 ",
          "font_name": "ArialBold",
          "font_size": 18,
          "bold": true,
          "italic": false
        }
      ]
    }
  ]
}
```

### 비교 결과 (Comparison)
```json
{
  "change_type": "modified",
  "before": {
    "text": "이전 내용"
  },
  "after": {
    "text": "새로운 내용"
  }
}
```

## 🔧 개발 가이드

### 백엔드 확장하기

#### 새 API 엔드포인트 추가
```python
@app.route('/api/new-feature', methods=['POST'])
def new_feature():
    try:
        # 처리 로직
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

#### PDF 추출 로직 커스터마이징
```python
from pdf_extractor import PDFExtractor

extractor = PDFExtractor("file.pdf")
# 필요한 메서드 오버라이드 또는 조정
custom_data = extractor.extract_all()
```

### 프론트엔드 확장하기

#### 커스텀 비교 결과 렌더링
```javascript
function displayCustomComparison(data) {
    // 기존 displayComparison() 함수 수정
    // data 구조에 맞게 커스터마이징
}
```

## 📝 환경 변수

백엔드는 기본적으로 `127.0.0.1:5000`에서 실행됩니다.

프로덕션 배포 시:
```bash
# backend/.env
FLASK_ENV=production
BACKEND_URL=https://your-domain.com
```

프론트엔드 수정:
```javascript
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://127.0.0.1:5000';
```

## 🐛 알려진 문제

1. **PDF 보안**: 보안 설정된 PDF는 추출이 제한될 수 있음
2. **복잡한 레이아웃**: 멀티 컬럼, 복잡한 표는 일부 인식 어려움
3. **이미지**: 이미지는 메타데이터만 추출 (이미지 내용 OCR 미지원)

## 📚 참고 자료

- [PyMuPDF 공식 문서](https://pymupdf.readthedocs.io/)
- [Flask 문서](https://flask.palletsprojects.com/)
- [pdf.js 공식 문서](https://mozilla.github.io/pdf.js/)

## 📄 라이선스

이 프로젝트는 개인용/학습용으로 자유롭게 사용할 수 있습니다.

## 👤 작성자

한나 (HNJUNG)
2026년 7월 21일

---

**문제 발생 시**: 각 폴더의 README.md 또는 코드 주석을 확인하세요.
