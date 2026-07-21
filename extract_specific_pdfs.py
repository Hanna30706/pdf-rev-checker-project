import os
from pathlib import Path
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import ConversionStatus

def extract_single_pdf(pdf_path, output_filename):
    """Extract a single PDF using Docling and generate verification markdown"""

    pdf_path_obj = Path(pdf_path)

    if not pdf_path_obj.exists():
        print(f"Error: File not found - {pdf_path}")
        return False

    print(f"Processing: {pdf_path_obj.name}")

    try:
        # Docling converter 초기화
        converter = DocumentConverter()

        # PDF 변환
        result = converter.convert(str(pdf_path_obj))

        if result.status == ConversionStatus.SUCCESS:
            # 마크다운 추출
            markdown_text = result.document.export_to_markdown()

            # 문서 메타데이터
            file_info = {
                "file_name": pdf_path_obj.name,
                "file_path": str(pdf_path_obj),
                "file_size_bytes": pdf_path_obj.stat().st_size,
                "status": "success",
                "content_length": len(markdown_text),
                "page_count": len(result.document.pages) if hasattr(result.document, 'pages') else 'N/A',
                "content": markdown_text
            }

            # 마크다운 생성
            generate_single_verification_markdown(file_info, output_filename)
            print(f"✓ Successfully created: {output_filename}")
            return True
        else:
            print(f"✗ Conversion failed: {result.status}")
            return False

    except Exception as e:
        print(f"✗ Error processing {pdf_path_obj.name}: {str(e)}")
        return False

def generate_single_verification_markdown(file_info, output_filename):
    """Generate verification markdown for a single PDF"""

    md_content = []
    md_content.append("# PDF 추출 검증 문서")
    md_content.append("")
    md_content.append("이 문서는 Docling OCR 모델을 사용하여 PDF 파일에서 추출한 구조화된 데이터입니다.")
    md_content.append("")

    # 파일 정보
    md_content.append("## 파일 정보")
    md_content.append("")
    md_content.append(f"| 항목 | 값 |")
    md_content.append("|------|-----|")
    md_content.append(f"| 파일명 | `{file_info['file_name']}` |")
    md_content.append(f"| 파일 경로 | `{file_info['file_path']}` |")
    md_content.append(f"| 파일 크기 | {file_info['file_size_bytes']:,} bytes |")
    md_content.append(f"| 상태 | **{file_info['status'].upper()}** |")
    md_content.append(f"| 추출 텍스트 길이 | {file_info['content_length']} characters |")
    md_content.append(f"| 페이지 수 | {file_info['page_count']} |")
    md_content.append("")

    # 추출된 내용
    md_content.append("## 추출된 내용")
    md_content.append("")
    md_content.append(file_info['content'])
    md_content.append("")

    # 검증 체크리스트
    md_content.append("---")
    md_content.append("")
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
    output_path = Path(output_filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_content))

if __name__ == "__main__":
    # PDF 파일 경로
    pdf_file_1 = r"내부자료\[I-AG1-0401-G01]언론홍보 및 대응 지침_r0.pdf"
    pdf_file_2 = r"내부자료\[I-AG1-0401-G01]언론홍보 및 대응 지침_r1.pdf"

    print("=" * 50)
    print("PDF 추출 시작")
    print("=" * 50)

    # 첫 번째 파일 처리
    print("\n[1/2] 첫 번째 파일 처리 중...")
    extract_single_pdf(pdf_file_1, "test1_verification.md")

    print("\n" + "=" * 50)

    # 두 번째 파일 처리
    print("\n[2/2] 두 번째 파일 처리 중...")
    extract_single_pdf(pdf_file_2, "test2_verification.md")

    print("\n" + "=" * 50)
    print("✓ 모든 파일 처리 완료")
    print("=" * 50)
