# 🤖 Daily AI Briefing Automation

매일 아침 AI 연구 동향을 생성해 Notion 데이터베이스로 적재하는 자동화 저장소입니다.

## SKILL.md 기반 구조

이 저장소는 운영/수정 작업을 빠르게 수행할 수 있도록 `SKILL.md` 중심으로 구조화되어 있습니다.

- `SKILL.md`: 작업 절차, 우선순위, 검증 체크리스트
- `references/ops-playbook.md`: 운영 가이드(시크릿, 스케줄, 장애 대응)
- `references/notion-schema.md`: Notion 스키마 기준 문서

## 빠른 시작

```bash
cp .env.example .env
# .env에 API 키/DB ID 입력
pip install -r requirements.txt
python daily_ai_briefing.py
```

## GitHub Actions

- 워크플로우: `.github/workflows/daily-briefing.yml`
- 기본 스케줄: `0 0 * * *` (매일 09:00 KST)
- 수동 실행: `workflow_dispatch`
