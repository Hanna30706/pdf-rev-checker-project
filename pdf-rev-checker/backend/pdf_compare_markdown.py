from difflib import SequenceMatcher, unified_diff
from typing import List, Dict, Tuple, Any
from pathlib import Path
import re


class PDFCompareMarkdown:
    """마크다운 기반 PDF 비교 및 리포트 생성"""

    def __init__(self, before_text: str, after_text: str, filename: str = "comparison"):
        self.before_text = before_text
        self.after_text = after_text
        self.filename = filename
        self.before_lines = before_text.split('\n')
        self.after_lines = after_text.split('\n')

    def extract_sections(self, text: str) -> Dict[str, List[str]]:
        """마크다운 섹션 추출 (제목 기준)"""
        sections = {}
        current_section = "Introduction"
        current_content = []

        for line in text.split('\n'):
            if line.startswith('#'):
                if current_section and current_content:
                    sections[current_section] = current_content
                current_section = line.strip('#').strip()
                current_content = []
            else:
                current_content.append(line)

        if current_section and current_content:
            sections[current_section] = current_content

        return sections

    def extract_paragraphs(self, text: str) -> List[str]:
        """단락 단위로 추출 (빈 줄로 구분)"""
        paragraphs = []
        current = []

        for line in text.split('\n'):
            if line.strip():
                current.append(line)
            elif current:
                paragraphs.append('\n'.join(current))
                current = []

        if current:
            paragraphs.append('\n'.join(current))

        return [p for p in paragraphs if p.strip()]

    def compare(self) -> Dict[str, Any]:
        """상세한 텍스트 비교 수행"""
        matcher = SequenceMatcher(None, self.before_text, self.after_text)
        similarity = matcher.ratio()

        # 라인별 비교
        before_set = set(self.before_lines)
        after_set = set(self.after_lines)

        added_lines = after_set - before_set
        removed_lines = before_set - after_set
        unchanged_lines = before_set & after_set

        # 단락 단위 비교
        before_paragraphs = self.extract_paragraphs(self.before_text)
        after_paragraphs = self.extract_paragraphs(self.after_text)

        # 섹션 단위 비교
        before_sections = self.extract_sections(self.before_text)
        after_sections = self.extract_sections(self.after_text)

        # 단어 수준 변경 추적
        before_words = set(self.before_text.split())
        after_words = set(self.after_text.split())
        added_words = after_words - before_words
        removed_words = before_words - after_words

        return {
            "similarity": similarity,
            "added_count": len(added_lines),
            "removed_count": len(removed_lines),
            "unchanged_count": len(unchanged_lines),
            "added_words_count": len(added_words),
            "removed_words_count": len(removed_words),
            "before_lines_total": len([l for l in self.before_lines if l.strip()]),
            "after_lines_total": len([l for l in self.after_lines if l.strip()]),
            "before_paragraphs_total": len(before_paragraphs),
            "after_paragraphs_total": len(after_paragraphs),
            "added_lines": sorted(list(added_lines)),
            "removed_lines": sorted(list(removed_lines)),
            "unchanged_lines": sorted(list(unchanged_lines)),
            "before_sections": before_sections,
            "after_sections": after_sections,
            "added_words": sorted(list(added_words))[:50],
            "removed_words": sorted(list(removed_words))[:50],
        }

    def _get_similarity_badge(self, similarity: float) -> Tuple[str, str]:
        """유사도 기반 배지 및 설명 반환"""
        if similarity > 0.9:
            return "🟢 거의 동일", "90% 이상 유사 - 미세한 수정"
        elif similarity > 0.7:
            return "🟡 부분 변경", "70-90% 유사 - 일부 내용 변경"
        elif similarity > 0.5:
            return "🟠 상당한 변경", "50-70% 유사 - 상당한 양의 내용 변경"
        else:
            return "🔴 대폭 변경", "50% 미만 유사 - 문서 재작성"

    def _get_change_type(self, added: int, removed: int) -> str:
        """변경 유형 판단"""
        total_changes = added + removed
        if total_changes == 0:
            return "변경 없음"

        added_ratio = added / total_changes if total_changes > 0 else 0

        if added_ratio > 0.7:
            return "🆕 추가 위주"
        elif added_ratio < 0.3:
            return "🗑️ 삭제 위주"
        else:
            return "🔄 균형적 변경"

    def generate_comparison_markdown(self) -> str:
        """향상된 비교 결과를 마크다운으로 생성"""
        comparison = self.compare()
        badge, badge_desc = self._get_similarity_badge(comparison['similarity'])
        change_type = self._get_change_type(comparison['added_count'], comparison['removed_count'])

        md = f"""# 📄 PDF 비교 리포트: {self.filename}

## 📊 비교 요약

| 항목 | 값 | 설명 |
|------|-----|------|
| **유사도** | {comparison['similarity']:.1%} | {badge_desc} |
| **라인 추가** | {comparison['added_count']} | 새로 추가된 라인 |
| **라인 삭제** | {comparison['removed_count']} | 제거된 라인 |
| **라인 유지** | {comparison['unchanged_count']} | 변경되지 않은 라인 |
| **전체 라인** | 이전: {comparison['before_lines_total']} / 현재: {comparison['after_lines_total']} | 라인 수 변화 |
| **단락 변화** | {comparison['before_paragraphs_total']} → {comparison['after_paragraphs_total']} | 단락 수 변화 |
| **단어 변화** | 추가: {comparison['added_words_count']} / 삭제: {comparison['removed_words_count']} | 고유 단어 변화 |

### 변경 평가

- **유사도**: {badge} ({comparison['similarity']:.1%})
- **변경 유형**: {change_type}
- **변경 규모**: {comparison['added_count'] + comparison['removed_count']} 라인 변경

---

## 🔄 변경 사항 상세

### ✅ 추가된 라인 ({comparison['added_count']}개)

"""
        if comparison['added_lines']:
            md += "```diff\n"
            for line in comparison['added_lines'][:30]:
                if line.strip():
                    md += f"+ {line}\n"
            if len(comparison['added_lines']) > 30:
                md += f"+ ... 외 {len(comparison['added_lines']) - 30}개 라인\n"
            md += "```\n"
        else:
            md += "추가된 라인이 없습니다.\n"

        md += f"""
### ❌ 삭제된 라인 ({comparison['removed_count']}개)

"""
        if comparison['removed_lines']:
            md += "```diff\n"
            for line in comparison['removed_lines'][:30]:
                if line.strip():
                    md += f"- {line}\n"
            if len(comparison['removed_lines']) > 30:
                md += f"- ... 외 {len(comparison['removed_lines']) - 30}개 라인\n"
            md += "```\n"
        else:
            md += "삭제된 라인이 없습니다.\n"

        md += f"""
### ⭕ 유지된 라인 ({comparison['unchanged_count']}개)

"""
        if comparison['unchanged_lines']:
            md += "```\n"
            for line in comparison['unchanged_lines'][:15]:
                if line.strip():
                    md += f"{line}\n"
            if len(comparison['unchanged_lines']) > 15:
                md += f"\n... 외 {len(comparison['unchanged_lines']) - 15}개 라인\n"
            md += "```\n"
        else:
            md += "모든 라인이 변경되었습니다.\n"

        # 섹션별 분석
        md += f"""
---

## 📍 섹션별 분석

### 이전 버전 섹션
"""
        if comparison['before_sections']:
            for section, content in comparison['before_sections'].items():
                content_str = '\n'.join(content).strip()
                line_count = len([l for l in content if l.strip()])
                md += f"- **{section}**: {line_count}개 라인\n"
        else:
            md += "섹션 정보 없음\n"

        md += f"""
### 현재 버전 섹션
"""
        if comparison['after_sections']:
            for section, content in comparison['after_sections'].items():
                content_str = '\n'.join(content).strip()
                line_count = len([l for l in content if l.strip()])
                md += f"- **{section}**: {line_count}개 라인\n"
        else:
            md += "섹션 정보 없음\n"

        # 단어 수준 변경
        md += f"""
---

## 📝 단어 수준 변경

### 추가된 키워드 ({comparison['added_words_count']}개)

```
{' | '.join(comparison['added_words'][:30])}
"""
        if comparison['added_words_count'] > 30:
            md += f"... (외 {comparison['added_words_count'] - 30}개)\n"
        md += "```\n"

        md += f"""
### 삭제된 키워드 ({comparison['removed_words_count']}개)

```
{' | '.join(comparison['removed_words'][:30])}
"""
        if comparison['removed_words_count'] > 30:
            md += f"... (외 {comparison['removed_words_count'] - 30}개)\n"
        md += "```\n"

        # Unified Diff
        md += """
---

## 📋 상세 Unified Diff

```diff
"""
        diff = list(unified_diff(
            self.before_lines,
            self.after_lines,
            fromfile='개정 전',
            tofile='개정 후',
            lineterm=''
        ))

        diff_lines = diff[:150]
        for line in diff_lines:
            md += line + "\n"

        if len(diff) > 150:
            md += f"\n... (생략: 총 {len(diff)}줄)\n"

        md += """```

---

## 📈 분석 결과

### 변경 요약

"""
        total_changes = comparison['added_count'] + comparison['removed_count']
        if total_changes == 0:
            md += "- ✅ 두 문서가 완벽히 동일합니다.\n"
        else:
            md += f"- 🔄 총 **{total_changes}**개 라인이 변경되었습니다.\n"
            md += f"- 📊 추가: **{comparison['added_count']}**개, 삭제: **{comparison['removed_count']}**개\n"
            md += f"- 📈 단어 수준 변화: 추가 {comparison['added_words_count']}개, 삭제 {comparison['removed_words_count']}개\n"

        md += f"""
### 결론

- **유사도**: {badge} ({comparison['similarity']:.1%})
- **변경 유형**: {change_type}
"""

        if comparison['similarity'] > 0.9:
            md += "- **권장사항**: 미세한 개정으로 보이며, 검토 후 병합 가능합니다.\n"
        elif comparison['similarity'] > 0.7:
            md += "- **권장사항**: 부분적 변경이므로 세밀한 검토가 필요합니다.\n"
        elif comparison['similarity'] > 0.5:
            md += "- **권장사항**: 상당한 변경이 있으므로 상세 검토가 권장됩니다.\n"
        else:
            md += "- **권장사항**: 대폭적인 변경이므로 전문가 검토가 필요합니다.\n"

        md += f"""

---

**보고서 생성**: {self.filename}
**비교 기준**: 라인 기반 + 단락 기반 + 단어 기반
"""
        return md

    def save_comparison_report(self, output_path: str = None) -> str:
        """비교 리포트를 마크다운으로 저장 (comparison_report.md 형식)"""
        if output_path is None:
            output_path = "comparison_report.md"

        md_content = self.generate_comparison_markdown()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        return output_path


def compare_pdf_markdown(before_text: str, after_text: str, filename: str = "comparison") -> Tuple[str, str]:
    """두 PDF 텍스트를 비교하고 마크다운 리포트 생성"""
    comparator = PDFCompareMarkdown(before_text, after_text, filename)
    report_path = comparator.save_comparison_report()
    md_report = comparator.generate_comparison_markdown()

    return md_report, report_path
