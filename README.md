# 📄 PDF 전후비교 웹사이트

개정 전후의 PDF를 비교하여 변경사항을 시각화하는 웹 도구

## 🎯 최종 목표

- ✅ PDF 텍스트, 표, 이미지를 구조화된 데이터로 추출
- ✅ 개정 전후 PDF 자동 비교
- ✅ 변경사항을 웹에서 시각화
- 🔄 이후: 기존 절차서 저장 후 새 파일 하나만 업로드해서 자동 비교

---

## 📋 현재 진행 상황: 1단계 (PDF 추출)

### 📦 설치 방법

#### Windows (Anaconda 추천)

```powershell
# 1. Python 가상환경 만들기
python -m venv venv

# 2. 가상환경 활성화
.\venv\Scripts\Activate.ps1

# 3. 패키지 설치
pip install -r requirements.txt
```

#### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🚀 실행 방법

### 1단계: PDF 추출

```powershell
python backend/extract_pdf.py
```

**무엇을 하는가?**
- `내부자료` 폴더의 모든 PDF를 읽음
- Docling OCR을 사용해 텍스트, 표, 이미지 추출
- 구조화된 JSON으로 `extracted_data` 폴더에 저장

**결과 확인**

추출 후 `extracted_data` 폴더가 생기고, 각 PDF별로 `.json` 파일이 생깁니다:
```
extracted_data/
├── [I-AGG-0101-C01]기준환율 수립 및 적용 지침_r0.json
├── [I-AGG-0101-C01]기준환율 수립 및 적용 지침_r1.json
└── ...
```

**JSON 파일 구조 확인**

`extracted_data`의 JSON 파일을 메모장이나 VS Code에서 열어보면:
- `metadata`: 파일 정보, 추출 시간
- `markdown`: 추출된 전체 텍스트 (마크다운 형식)
- `sections`: 각 섹션별 상세 데이터
- `raw_document`: 모든 구조화된 정보

---

## ⚠️ 현재 알려진 제한사항

- 단계별 개발 중이므로 아직 웹 UI는 없습니다
- 1단계 완료 후 2단계(검증) → 3단계(비교 알고리즘) → 4단계(웹사이트)로 진행합니다

---

## 📝 각 단계별 설명

### 1단계: PDF 추출 ✅ (현재)
- **담당**: Python + Docling
- **입력**: `내부자료/*.pdf`
- **출력**: `extracted_data/*.json`
- **목표**: 구조화된 데이터 생성

### 2단계: 검증 (다음)
- 추출된 데이터가 원본과 일치하는지 확인
- 오류 수정

### 3단계: 비교 알고리즘
- 두 JSON 데이터 비교
- 추가/삭제/변경 항목 감지

### 4단계: 웹사이트
- React 기반 UI
- 전후비교 시각화

---

## 🛠️ 기술 스택

| 항목 | 선택 |
|------|------|
| PDF 추출 | Docling (OCR 포함) |
| 비교 | Python |
| 웹 UI | React 18 + TypeScript |
| 데이터 포맷 | JSON |

---

## ❓ 문제 해결

### "docling" 설치 오류
```
pip install docling --upgrade
```

### PDF가 추출되지 않음
- PDF 파일이 `내부자료` 폴더에 있는지 확인
- PDF 파일명에 특수문자가 있으면 수정 필요

