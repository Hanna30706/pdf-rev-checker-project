# PDF 추출 & 검증 프로젝트 - 진행 상황

**작업 날짜**: 2026-07-21  
**현재 단계**: 2개 대표 PDF 추출 & 검증 완료  
**상태**: 진행 중

---

## 완료된 작업

### 1. 추출 스크립트 개발
- ✅ PyMuPDF 기반 텍스트 추출 (원본 텍스트, 좌표, 페이지 정보)
- ✅ Docling 기반 구조적 추출 (제목, 절, 표, 레이아웃)
- ✅ 2개 추출 스크립트 작성
  - `extract_multi_tool.py`: 전체 기능 포함 (OCR 포함)
  - `extract_simple.py`: 간소화 버전 (OCR 제외, 빠른 실행)

### 2. 검증 스크립트 개발
- ✅ 원본 PDF 대비 추출 결과 검증
- ✅ 8가지 검증 항목 자동 확인
- ✅ `validate_extraction.py` 작성 완료

### 3. 2개 대표 PDF 처리 완료
- ✅ `[I-AG1-0401-G01]언론홍보 및 대응 지침_r0.pdf` (4페이지)
  - 추출 파일: `docling3_verification.md` (24KB)
  - 검증 결과: 부분 통과 (중복 텍스트 3개)
  
- ✅ `[P-MGG-0601-010]국내 업면허 관리_r0.pdf` (3페이지)
  - 추출 파일: `docling3_process_verification.md` (26KB)
  - 검증 결과: 완전 통과

### 4. 패키지 설치
- ✅ PyMuPDF (>=1.25.0)
- ✅ paddleocr (>=2.8.0) - 의존성 부족
- ✅ docling (1.0.0) - 이미 설치
- ✅ Pillow, pandas - 이미 설치

---

## 아직 해결되지 않은 문제

### 1. 이미지 내 텍스트 미추출
- **문제**: PDF의 이미지(4~6개)에 포함된 텍스트가 추출되지 않음
- **원인**: PaddleOCR이 적용되지 않음
- **해결책**: `paddlepaddle` 의존성 설치 후 OCR 활성화
- **우선순위**: 낮음 (필요시에만)

### 2. 1번 PDF의 중복 텍스트
- **문제**: `docling3_verification.md`에서 일부 텍스트가 반복됨 (3개)
- **원인**: Docling 추출 과정에서 발생
- **해결책**: 수동 검토 또는 Docling 설정 조정 필요
- **우선순위**: 중간

### 3. PaddleOCR 의존성 부족
```
RuntimeError: Engine 'paddle_static' is unavailable because dependency 
'paddlepaddle' is not installed.
```
- **원인**: paddleocr만으로는 부족, paddlepaddle 별도 설치 필요
- **설치 방법**: `pip install paddlepaddle` (pytorch, cuda 등 많은 의존성)
- **소요 시간**: 10~30분
- **우선순위**: 낮음 (필요시에만)

---

## 다음에 이어서 해야 할 작업

### Phase 1: 추출 규칙 최종화 (현재 단계)
- [ ] 1번 PDF 중복 텍스트 원인 분석
- [ ] Docling 설정 최적화 또는 수동 정제
- [ ] 두 파일 모두 최종 검증 (사용자 수동 검토)

### Phase 2: OCR 적용 (선택사항)
- [ ] `paddlepaddle` 설치 (필요시만)
- [ ] 이미지 텍스트 추출 활성화
- [ ] 2개 PDF 재추출 및 검증

### Phase 3: 전체 PDF 적용
- [ ] 14개 PDF 전체 대상으로 확대
- [ ] 배치 처리 스크립트 작성
- [ ] 일괄 검증 및 결과 정리

---

## 수정한 파일 목록

| 파일명 | 상태 | 설명 |
|-------|------|------|
| `requirements.txt` | 수정 | PyMuPDF, paddleocr 추가 |
| `extract_multi_tool.py` | 신규 | 전체 기능 포함 (개발용) |
| `extract_simple.py` | 신규 | 간소화 버전 (현재 사용 중) |
| `validate_extraction.py` | 신규 | 검증 자동화 스크립트 |
| `docling3_verification.md` | 신규 | 1번 PDF 추출 결과 |
| `docling3_process_verification.md` | 신규 | 2번 PDF 추출 결과 |

---

## 설치한 라이브러리

```
docling==1.0.0           (이미 설치)
Pillow==11.1.0           (이미 설치)
pandas==2.2.0            (이미 설치)
PyMuPDF>=1.25.0          (새로 설치)
paddleocr>=2.8.0         (새로 설치, 의존성 부족)
```

### 추가 선택 라이브러리 (필요시)
```
paddlepaddle             (OCR 활성화용)
```

---

## 실행 방법

### 1. 추출만 실행 (현재 방식, 빠름)
```bash
cd "d:/★AI코딩교육(딥오토)/W2_Agent AI 학습/2026.7.21_(2)"
python extract_simple.py
```
**소요 시간**: 2~3분  
**결과 파일**:
- `docling3_verification.md`
- `docling3_process_verification.md`

### 2. 검증만 실행
```bash
python validate_extraction.py
```
**소요 시간**: 30초  
**출력**: 각 PDF별 검증 결과

### 3. 추출 + 검증 모두 실행
```bash
python extract_simple.py && python validate_extraction.py
```

### 4. OCR 포함 추출 (미적용, 의존성 필요)
```bash
# 1단계: paddlepaddle 설치 (처음 1회만)
pip install paddlepaddle

# 2단계: OCR 포함 스크립트 실행
python extract_multi_tool.py
```
**주의**: 패키지 설치에 10~30분 소요, 전체 실행 시간 5~10분

---

## 검증 결과 요약

### 1번 PDF: 언론홍보 및 대응 지침 (부분 통과)
```
페이지 수:        4개 ✓
본문 텍스트:      일치 ✓
페이지 순서:      정상 ✓
이미지 감지:      4개 (미추출)
중복 텍스트:      3개 발견 ⚠️
상태:            FAILED (1개 이슈)
```

### 2번 PDF: 국내 업면허 관리 (완전 통과)
```
페이지 수:        3개 ✓
본문 텍스트:      일치 ✓
페이지 순서:      정상 ✓
이미지 감지:      6개 (미추출)
중복/오류:        없음 ✓
상태:            PASSED
```

---

## 다음 우선순위

1. **HIGH**: 1번 PDF 중복 텍스트 원인 분석 및 수정
2. **MEDIUM**: 두 파일 모두 사용자 수동 검토 및 승인
3. **LOW**: OCR 의존성 설치 및 이미지 텍스트 추출 (필요시만)
4. **PENDING**: 14개 PDF 전체 적용 (사용자 결정 후)

---

## 메모

- 모든 스크립트는 **일반화된 규칙**으로 작성되어 다른 PDF에도 적용 가능
- Windows 콘솔 인코딩 문제로 emoji 제거함 (한글 처리에는 영향 없음)
- 현재 사용 중인 `extract_simple.py`는 OCR 없이도 텍스트 추출 충분
- PaddleOCR은 **선택사항**이며, 필요시에만 설치 권장
