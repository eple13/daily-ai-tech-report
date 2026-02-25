---
name: daily-ai-tech-report-ops
description: Maintain and operate the Daily AI Briefing automation (Claude + Notion + GitHub Actions). Use when setting up secrets, updating schedules, validating Notion schema compatibility, or modifying briefing generation behavior in this repository.
---

# Daily AI Tech Report Skill

이 저장소는 `daily_ai_briefing.py`와 GitHub Actions 워크플로우를 통해
매일 AI 동향을 수집/요약하고 Notion 데이터베이스에 적재한다.

## 1) 작업 시작 절차

1. `README.md`에서 빠른 실행 절차를 확인한다.
2. 상세 운영 문서는 `references/ops-playbook.md`를 먼저 읽는다.
3. Notion 속성 변경이 필요한 경우 `references/notion-schema.md`를 기준으로 수정한다.

## 2) 변경 우선순위

1. **데이터 스키마 정합성**: `daily_ai_briefing.py`의 Notion payload와 DB 속성명을 먼저 맞춘다.
2. **스케줄/런타임 안정성**: `.github/workflows/daily-briefing.yml`의 cron과 Python 버전을 확인한다.
3. **문서 최신화**: 구조/설정 변경 시 `README.md`와 `references/*`를 함께 갱신한다.

## 3) 검증 체크리스트

- `python -m py_compile daily_ai_briefing.py`
- `python daily_ai_briefing.py` (필요한 환경변수가 채워진 경우)
- 워크플로우 문법 점검(수동 검토)

## 4) 파일별 역할

- `daily_ai_briefing.py`: 브리핑 생성 + Notion 업로드 메인 로직
- `.github/workflows/daily-briefing.yml`: 정기 실행/수동 실행 설정
- `references/ops-playbook.md`: 설치, 시크릿, 운영 가이드
- `references/notion-schema.md`: Notion DB 속성 규격

## 5) 변경 가이드

- 속성명 변경 시 코드와 문서를 **동시에** 업데이트한다.
- cron 변경 시 KST/UTC 변환 주석을 남긴다.
- 실패 대응은 재현 가능한 로그 메시지 중심으로 개선한다.
