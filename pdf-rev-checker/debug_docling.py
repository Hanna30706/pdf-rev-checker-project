#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Docling API 구조 파악"""

import sys
import os
from pathlib import Path

pdf_filename = "[P-MGG-0601-010]국내 업면허 관리_개정 전.pdf"
pdf_path = os.path.join(os.path.dirname(__file__), pdf_filename)

if not os.path.exists(pdf_path):
    print(f"PDF not found: {pdf_path}")
    sys.exit(1)

try:
    from docling.document_converter import DocumentConverter

    print("[LOAD] Loading Docling converter...")
    converter = DocumentConverter()

    print("[CONVERT] Converting PDF...")
    result = converter.convert(pdf_path)

    print("\n[STRUCTURE] Document Structure:")
    print(f"Type of result: {type(result)}")
    print(f"Type of result.document: {type(result.document)}")
    print(f"Dir of result.document: {[x for x in dir(result.document) if not x.startswith('_')][:20]}")

    doc = result.document

    print(f"\nPages type: {type(doc.pages)}")
    print(f"Pages length: {len(doc.pages)}")
    print(f"Pages keys (first 5): {list(doc.pages.keys())[:5] if hasattr(doc.pages, 'keys') else 'N/A'}")

    # 첫 번째 페이지 탐색
    if doc.pages:
        first_page = next(iter(doc.pages.values())) if hasattr(doc.pages, 'values') else doc.pages[0]
        print(f"\nFirst page type: {type(first_page)}")
        print(f"First page dir: {[x for x in dir(first_page) if not x.startswith('_')][:20]}")

        if hasattr(first_page, 'blocks'):
            print(f"First page blocks: {len(first_page.blocks)}")
            if first_page.blocks:
                print(f"First block type: {type(first_page.blocks[0])}")
                print(f"First block: {first_page.blocks[0]}")

    # Export to markdown
    print("\n[MARKDOWN] Exporting to markdown...")
    markdown = doc.export_to_markdown()
    print(f"Markdown length: {len(markdown)}")
    print(f"Markdown preview (first 500 chars):\n{markdown[:500]}")

except Exception as e:
    print(f"[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()
