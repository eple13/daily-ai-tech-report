# Operations Playbook

## 개요

Daily AI Briefing 자동화는 아래 순서로 동작한다.

1. Claude API를 통해 당일 AI 동향 요약 텍스트를 생성한다.
2. 결과를 파싱해 카테고리/중요도/태그/출처를 구조화한다.
3. Notion API로 지정된 데이터베이스에 페이지를 생성한다.
4. GitHub Actions가 매일 정해진 시각(기본: 09:00 KST)에 실행한다.

## 필수 환경변수

- `ANTHROPIC_API_KEY`: Claude API 키
- `NOTION_API_KEY`: Notion Integration 토큰
- `NOTION_DATABASE_ID`: 대상 Notion DB ID

로컬 실행 시 `.env.example`을 복사해 `.env`를 만든 후 채운다.

## GitHub Actions 설정

워크플로우 파일: `.github/workflows/daily-briefing.yml`

- `schedule`의 cron은 UTC 기준이다.
- 기본값 `0 0 * * *`는 KST 09:00 실행을 의미한다.
- 수동 실행은 `workflow_dispatch`를 사용한다.

## 운영 점검 루틴

1. 최근 실행 로그에서 API 오류/타임아웃 여부를 확인한다.
2. Notion 데이터베이스에 당일 항목이 정상 생성됐는지 검토한다.
3. 브리핑 품질(중복/출처 누락/태그 부정확)을 샘플 점검한다.

## 장애 대응

- 인증 오류(401/403): 키 만료/권한/DB 연결 재확인
- 스키마 오류(400): Notion 속성명과 코드 payload 불일치 점검
- 생성 품질 저하: 프롬프트(스크립트 내부) 조정 후 재실행
