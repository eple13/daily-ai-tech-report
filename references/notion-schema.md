# Notion Database Schema Reference

자동화 스크립트가 기대하는 기본 속성 구조:

| 속성 | 타입 | 설명 |
|---|---|---|
| Title | Title | 항목 제목 |
| Category | Select | 📄 논문/연구, 🚀 모델 릴리스, 📊 벤치마크, 💼 시장/기업, 🔧 기술/인프라 |
| Date | Date | 추가 날짜 |
| Tags | Multi-select | 주제 태그 목록 |
| Importance | Select | 🔥 High, ⭐ Medium, 📌 Low |
| Summary | Rich text | 요약 및 참고문헌 |
| Source | URL | 원문 링크 |

## 변경 규칙

1. 속성명을 바꾸면 `daily_ai_briefing.py`의 payload 키를 같이 수정한다.
2. Select/Multi-select 옵션은 Notion DB에 미리 생성해둔다.
3. URL/Date 타입은 문자열 포맷 오류가 없도록 검증한다.
