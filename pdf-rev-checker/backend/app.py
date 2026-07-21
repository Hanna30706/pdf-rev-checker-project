from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
from pathlib import Path
from werkzeug.utils import secure_filename
import tempfile

from pdf_extractor import extract_pdf, extract_pdf_text
from pdf_comparator import compare_pdfs
from pdf_ocr_extractor import extract_pdf_with_ocr
from pdf_compare_markdown import compare_pdf_markdown

app = Flask(__name__)
CORS(app)

# 설정
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


def allowed_file(filename):
    """허용된 파일 확인"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/health', methods=['GET'])
def health():
    """헬스 체크"""
    return jsonify({
        "status": "ok",
        "service": "PDF Comparison Backend",
        "version": "1.0.0"
    })


@app.route('/api/extract', methods=['POST'])
def extract():
    """단일 PDF 추출"""
    try:
        if 'pdf' not in request.files:
            return jsonify({"error": "PDF 파일이 없습니다"}), 400

        file = request.files['pdf']

        if file.filename == '':
            return jsonify({"error": "파일이 선택되지 않았습니다"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "PDF 파일만 허용됩니다"}), 400

        # 임시 파일 저장
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)

        try:
            # PDF 추출
            pdf_data = extract_pdf(temp_path)

            response = {
                "success": True,
                "data": pdf_data
            }

            return jsonify(response)

        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        return jsonify({
            "error": f"PDF 추출 중 오류 발생: {str(e)}"
        }), 500


@app.route('/api/extract-text', methods=['POST'])
def extract_text():
    """단일 PDF에서 텍스트만 추출"""
    try:
        if 'pdf' not in request.files:
            return jsonify({"error": "PDF 파일이 없습니다"}), 400

        file = request.files['pdf']

        if file.filename == '':
            return jsonify({"error": "파일이 선택되지 않았습니다"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "PDF 파일만 허용됩니다"}), 400

        # 임시 파일 저장
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)

        try:
            # PDF 텍스트 추출
            pdf_data = extract_pdf_text(temp_path)

            response = {
                "success": True,
                "data": pdf_data
            }

            return jsonify(response)

        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        return jsonify({
            "error": f"PDF 추출 중 오류 발생: {str(e)}"
        }), 500


@app.route('/api/compare', methods=['POST'])
def compare():
    """두 PDF 비교"""
    try:
        if 'before' not in request.files or 'after' not in request.files:
            return jsonify({"error": "두 PDF 파일이 필요합니다"}), 400

        file_before = request.files['before']
        file_after = request.files['after']

        if file_before.filename == '' or file_after.filename == '':
            return jsonify({"error": "두 파일 모두 선택되어야 합니다"}), 400

        if not (allowed_file(file_before.filename) and allowed_file(file_after.filename)):
            return jsonify({"error": "PDF 파일만 허용됩니다"}), 400

        # 임시 파일 저장
        filename_before = secure_filename(file_before.filename)
        filename_after = secure_filename(file_after.filename)
        temp_path_before = os.path.join(app.config['UPLOAD_FOLDER'], filename_before)
        temp_path_after = os.path.join(app.config['UPLOAD_FOLDER'], filename_after)

        file_before.save(temp_path_before)
        file_after.save(temp_path_after)

        try:
            # PDF 추출
            pdf1_data = extract_pdf(temp_path_before)
            pdf2_data = extract_pdf(temp_path_after)

            # PDF 비교
            comparison_result = compare_pdfs(pdf1_data, pdf2_data)

            response = {
                "success": True,
                "data": comparison_result
            }

            return jsonify(response)

        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_path_before):
                os.remove(temp_path_before)
            if os.path.exists(temp_path_after):
                os.remove(temp_path_after)

    except Exception as e:
        return jsonify({
            "error": f"PDF 비교 중 오류 발생: {str(e)}"
        }), 500


@app.route('/api/extract-ocr', methods=['POST'])
def extract_ocr():
    """OCR을 사용한 PDF 추출 (마크다운)"""
    try:
        if 'pdf' not in request.files:
            return jsonify({"error": "PDF 파일이 없습니다"}), 400

        file = request.files['pdf']

        if file.filename == '':
            return jsonify({"error": "파일이 선택되지 않았습니다"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "PDF 파일만 허용됩니다"}), 400

        # 임시 파일 저장
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)

        try:
            # OCR 추출
            data, md_path, json_path = extract_pdf_with_ocr(temp_path)

            # 마크다운 파일 읽기
            with open(md_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            response = {
                "success": True,
                "filename": file.filename,
                "markdown": markdown_content,
                "data": data
            }

            return jsonify(response)

        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        return jsonify({
            "error": f"OCR 추출 중 오류 발생: {str(e)}"
        }), 500


@app.route('/api/compare-ocr', methods=['POST'])
def compare_ocr():
    """OCR 기반 PDF 비교 (마크다운 리포트)"""
    try:
        if 'before' not in request.files or 'after' not in request.files:
            return jsonify({"error": "두 PDF 파일이 필요합니다"}), 400

        file_before = request.files['before']
        file_after = request.files['after']

        if not (allowed_file(file_before.filename) and allowed_file(file_after.filename)):
            return jsonify({"error": "PDF 파일만 허용됩니다"}), 400

        # 임시 파일 저장
        filename_before = secure_filename(file_before.filename)
        filename_after = secure_filename(file_after.filename)
        temp_path_before = os.path.join(app.config['UPLOAD_FOLDER'], filename_before)
        temp_path_after = os.path.join(app.config['UPLOAD_FOLDER'], filename_after)

        file_before.save(temp_path_before)
        file_after.save(temp_path_after)

        try:
            # OCR 추출
            before_data, before_md_path, _ = extract_pdf_with_ocr(temp_path_before)
            after_data, after_md_path, _ = extract_pdf_with_ocr(temp_path_after)

            # 마크다운 내용 읽기
            with open(before_md_path, 'r', encoding='utf-8') as f:
                before_text = f.read()
            with open(after_md_path, 'r', encoding='utf-8') as f:
                after_text = f.read()

            # 비교 수행
            comparison_md, report_path = compare_pdf_markdown(
                before_text,
                after_text,
                f"{Path(file_before.filename).stem}_vs_{Path(file_after.filename).stem}"
            )

            response = {
                "success": True,
                "before_file": file_before.filename,
                "after_file": file_after.filename,
                "comparison_report": comparison_md,
                "before_extracted": before_text,
                "after_extracted": after_text
            }

            return jsonify(response)

        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_path_before):
                os.remove(temp_path_before)
            if os.path.exists(temp_path_after):
                os.remove(temp_path_after)

    except Exception as e:
        return jsonify({
            "error": f"OCR 비교 중 오류 발생: {str(e)}"
        }), 500


@app.route('/api/compare-text', methods=['POST'])
def compare_text():
    """두 PDF의 텍스트 비교 (간단한 방식)"""
    try:
        if 'before' not in request.files or 'after' not in request.files:
            return jsonify({"error": "두 PDF 파일이 필요합니다"}), 400

        file_before = request.files['before']
        file_after = request.files['after']

        if not (allowed_file(file_before.filename) and allowed_file(file_after.filename)):
            return jsonify({"error": "PDF 파일만 허용됩니다"}), 400

        # 임시 파일 저장
        filename_before = secure_filename(file_before.filename)
        filename_after = secure_filename(file_after.filename)
        temp_path_before = os.path.join(app.config['UPLOAD_FOLDER'], filename_before)
        temp_path_after = os.path.join(app.config['UPLOAD_FOLDER'], filename_after)

        file_before.save(temp_path_before)
        file_after.save(temp_path_after)

        try:
            # PDF 텍스트 추출
            pdf1_data = extract_pdf_text(temp_path_before)
            pdf2_data = extract_pdf_text(temp_path_after)

            # 간단한 라인 비교
            lines1 = []
            lines2 = []

            for page in pdf1_data.get("pages", []):
                lines1.extend(page.get("lines", []))

            for page in pdf2_data.get("pages", []):
                lines2.extend(page.get("lines", []))

            # 비교 결과
            comparison = {
                "before_file": file_before.filename,
                "after_file": file_after.filename,
                "before_lines": lines1,
                "after_lines": lines2,
                "comparison": []
            }

            # 간단한 라인 기반 비교
            max_lines = max(len(lines1), len(lines2))
            for i in range(max_lines):
                line1 = lines1[i] if i < len(lines1) else ""
                line2 = lines2[i] if i < len(lines2) else ""

                if line1 == line2:
                    comparison["comparison"].append({
                        "type": "unchanged",
                        "before": line1,
                        "after": line2
                    })
                elif line1 and not line2:
                    comparison["comparison"].append({
                        "type": "removed",
                        "before": line1,
                        "after": ""
                    })
                elif not line1 and line2:
                    comparison["comparison"].append({
                        "type": "added",
                        "before": "",
                        "after": line2
                    })
                else:
                    comparison["comparison"].append({
                        "type": "modified",
                        "before": line1,
                        "after": line2
                    })

            response = {
                "success": True,
                "data": comparison
            }

            return jsonify(response)

        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_path_before):
                os.remove(temp_path_before)
            if os.path.exists(temp_path_after):
                os.remove(temp_path_after)

    except Exception as e:
        return jsonify({
            "error": f"PDF 비교 중 오류 발생: {str(e)}"
        }), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """파일 크기 초과 에러"""
    return jsonify({
        "error": f"파일이 너무 큽니다. 최대 {MAX_FILE_SIZE / 1024 / 1024}MB까지 허용됩니다"
    }), 413


@app.errorhandler(404)
def not_found(error):
    """404 에러"""
    return jsonify({"error": "찾을 수 없는 엔드포인트입니다"}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 에러"""
    return jsonify({"error": "서버 내부 오류가 발생했습니다"}), 500


if __name__ == '__main__':
    # 개발 서버
    app.run(debug=True, host='127.0.0.1', port=5000)
