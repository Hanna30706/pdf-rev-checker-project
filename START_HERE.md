# 🎬 빠른 시작 가이드 (1단계: PDF 추출)

## 📍 현재 상황

- ✅ 코드 준비 완료
- ⏳ 당신이 할 일: 패키지 설치 → PDF 추출 실행

---

## 🔧 Step 1: Python 패키지 설치 (5분)

**VS Code 터미널에서 다음을 실행하세요:**

```powershell
# 1. 가상환경 만들기
python -m venv venv

# 2. 가상환경 활성화 (Windows)
.\venv\Scripts\Activate.ps1

# 3. 패키지 설치
pip install -r requirements.txt
```

> 💡 **macOS/Linux 사용자:**
> ```bash
> python3 -m venv venv
> source venv/bin/activate
> pip install -r requirements.txt
> ```

**설치 완료 신호:**
```
Successfully installed docling pillow pandas
```

---

## 🚀 Step 2: PDF 추출 실행 (10분)

**터미널에서:**

```powershell
python backend/extract_pdf.py
```

**실행 중 화면:**
```
🚀 PDF 추출 시작...

[1/14]
📄 '[I-AGG-0101-C01]기준환율 수립 및 적용 지침_r0' 추출 중...
✅ 저장됨: extracted_data\[I-AGG-0101-C01]기준환율 수립 및 적용 지침_r0.json

[2/14]
📄 '[I-AGG-0101-C01]기준환율 수립 및 적용 지침_r1' 추출 중...
✅ 저장됨: extracted_data\[I-AGG-0101-C01]기준환율 수립 및 적용 지침_r1.json

...
============================================================
✅ 완료: 14/14
============================================================
```

---

## 📁 결과 확인

**VS Code 탐색기에서 `extracted_data` 폴더를 열어보세요:**

```
extracted_data/
├── [I-AGG-0101-C01]기준환율 수립 및 적용 지침_r0.json
├── [I-AGG-0101-C01]기준환율 수립 및 적용 지침_r1.json
├── [I-AGG-0101-C02]수주계획 수립 및 관리 지침_r0.json
├── [I-AGG-0101-C02]수주계획 수립 및 관리 지침_r1.json
└── ... (14개 파일)
```

---

## 📄 JSON 파일 구조 (한 개 열어보기)

`extracted_data` 폴더에서 아무 `.json` 파일이나 더블클릭해서 열어보세요.

**구조:**
```json
{
  "metadata": {
    "file_name": "[I-AGG-0101-C01]기준환율 수립 및 적용 지침_r0",
    "total_pages": 5,
    "extracted_at": "2026-07-21T10:30:00",
    "extraction_method": "Docling OCR"
  },
  "markdown": "# 기준환율 수립 및 적용 지침\n\n## 1. 목적\n...",
  "sections": [
    {
      "type": "content",
      "content": "내용이 여기 저장됨",
      "page_number": 1
    },
    {
      "type": "table",
      "content": { "headers": [...], "rows": [...] }
    }
  ]
}
```

---

## ✅ 확인 체크리스트

- [ ] `extracted_data` 폴더 생성됨
- [ ] JSON 파일들이 14개 생성됨
- [ ] 각 JSON 파일을 열었을 때 내용이 있음
- [ ] r0, r1 버전 파일들이 모두 있음 (비교 준비 완료!)

---

## 🎯 다음 단계

1단계 완료! 🎉

이제:
- **2단계**: 추출된 데이터 검증 (오류 수정)
- **3단계**: r0 vs r1 자동 비교 알고리즘 구현
- **4단계**: 웹사이트에서 시각화

다음 지시를 기다려주세요.

---

## ❓ 문제 해결

**Q: "docling 명령을 찾을 수 없습니다" 에러**
→ 가상환경이 활성화되지 않았나요? 
```powershell
.\venv\Scripts\Activate.ps1
```

**Q: 진행이 멈혔어요**
→ Ctrl+C로 중지하고 다시 실행해보세요

**Q: 특정 PDF만 추출하고 싶어요**
→ 아직 1단계이므로 모든 파일을 추출합니다. 나중에 선택 기능 추가 가능

