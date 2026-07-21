import os
import json
from pathlib import Path
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import ConversionStatus

def extract_pdfs_to_markdown():
    """Extract PDFs using Docling and generate verification markdown"""

    # 현재 디렉토리
    base_dir = Path(".")

    # PDF 파일 검색
    pdf_files = sorted(base_dir.glob("**/*.pdf"))

    if not pdf_files:
        print("No PDF files found.")
        return

    print(f"Found {len(pdf_files)} PDF files")

    # 결과 저장소
    results = {
        "extraction_date": __import__('datetime').datetime.now().isoformat(),
        "total_files": len(pdf_files),
        "files": []
    }

    # Docling converter 초기화
    converter = DocumentConverter()

    # 각 PDF 처리
    for idx, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{idx}/{len(pdf_files)}] Processing: {pdf_path.name}")

        try:
            # PDF 변환
            result = converter.convert(str(pdf_path))

            if result.status == ConversionStatus.SUCCESS:
                # 마크다운 추출
                markdown_text = result.document.export_to_markdown()

                # 문서 메타데이터
                file_info = {
                    "file_name": pdf_path.name,
                    "relative_path": str(pdf_path.relative_to(base_dir)),
                    "file_size_bytes": pdf_path.stat().st_size,
                    "status": "success",
                    "content_length": len(markdown_text),
                    "page_count": len(result.document.pages) if hasattr(result.document, 'pages') else 'N/A',
                    "preview": markdown_text[:500] if markdown_text else "",
                    "content": markdown_text
                }
            else:
                file_info = {
                    "file_name": pdf_path.name,
                    "relative_path": str(pdf_path.relative_to(base_dir)),
                    "file_size_bytes": pdf_path.stat().st_size,
                    "status": "failed",
                    "error": str(result.status)
                }

            results["files"].append(file_info)
            print(f"✓ Completed: {pdf_path.name}")

        except Exception as e:
            print(f"✗ Error processing {pdf_path.name}: {str(e)}")
            results["files"].append({
                "file_name": pdf_path.name,
                "relative_path": str(pdf_path.relative_to(base_dir)),
                "status": "error",
                "error": str(e)
            })

    # 마크다운 생성
    generate_verification_markdown(results)
    print("\n✓ Markdown verification file created: docling_verification.md")

def generate_verification_markdown(results):
    """Generate verification markdown from extraction results"""

    md_content = []
    md_content.append("# PDF 추출 검증 문서")
    md_content.append("")
    md_content.append("이 문서는 Docling OCR 모델을 사용하여 PDF 파일에서 추출한 구조화된 데이터입니다.")
    md_content.append("")

    # 요약
    md_content.append("## 추출 요약")
    md_content.append("")
    md_content.append(f"- **추출 일시**: {results['extraction_date']}")
    md_content.append(f"- **총 파일 수**: {results['total_files']}")

    successful = sum(1 for f in results['files'] if f.get('status') == 'success')
    failed = sum(1 for f in results['files'] if f.get('status') in ['failed', 'error'])
    md_content.append(f"- **성공**: {successful}개")
    md_content.append(f"- **실패**: {failed}개")
    md_content.append("")

    # 파일별 상세 정보
    md_content.append("## 파일별 추출 결과")
    md_content.append("")

    for idx, file_info in enumerate(results['files'], 1):
        md_content.append(f"### {idx}. {file_info['file_name']}")
        md_content.append("")
        md_content.append(f"| 항목 | 값 |")
        md_content.append("|------|-----|")
        md_content.append(f"| 경로 | `{file_info['relative_path']}` |")
        md_content.append(f"| 파일 크기 | {file_info['file_size_bytes']:,} bytes |")
        md_content.append(f"| 상태 | **{file_info['status'].upper()}** |")

        if file_info['status'] == 'success':
            md_content.append(f"| 추출 텍스트 길이 | {file_info['content_length']} characters |")
            md_content.append(f"| 페이지 수 | {file_info['page_count']} |")

        if 'error' in file_info:
            md_content.append(f"| 오류 메시지 | {file_info['error']} |")

        md_content.append("")

        # 성공한 경우 미리보기 및 전체 내용
        if file_info['status'] == 'success' and 'content' in file_info:
            md_content.append("#### 추출된 내용")
            md_content.append("")
            md_content.append(file_info['content'])
            md_content.append("")
            md_content.append("---")
            md_content.append("")

    # 검증 체크리스트
    md_content.append("## 검증 체크리스트")
    md_content.append("")
    md_content.append("이 추출 결과를 검증할 때 다음을 확인하세요:")
    md_content.append("")
    md_content.append("- [ ] 추출된 텍스트가 원본 PDF와 일치하는가?")
    md_content.append("- [ ] 표 형식이 올바르게 추출되었는가?")
    md_content.append("- [ ] 이미지나 그래프의 캡션이 추출되었는가?")
    md_content.append("- [ ] 특수 문자나 한글이 올바르게 인코딩되었는가?")
    md_content.append("- [ ] 제목, 부제목 등 구조가 보존되었는가?")
    md_content.append("- [ ] 레이아웃이 원본을 반영하고 있는가?")
    md_content.append("")

    # 주석
    md_content.append("## 주석")
    md_content.append("")
    md_content.append("- 이 문서는 Docling 1.0.0을 사용하여 생성되었습니다.")
    md_content.append("- OCR 정확도는 PDF 품질에 따라 달라질 수 있습니다.")
    md_content.append("- 부정확한 추출 결과는 직접 수정하여 검증할 수 있습니다.")

    # 마크다운 파일 저장
    output_path = Path("docling_verification.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_content))

if __name__ == "__main__":
    extract_pdfs_to_markdown()
