# 🤖 Daily AI Briefing Automation

매일 아침 9시(KST)에 자동으로 AI 연구 동향을 브리핑하고 Notion 데이터베이스에 업데이트하는 GitHub Actions 워크플로우입니다.

## 📋 기능

- **Claude API**를 활용한 최신 AI 연구 동향 검색 및 분석
- **Notion API**를 통한 데이터베이스 자동 업데이트
- 매일 **오전 9시 KST** 자동 실행
- 수동 실행 지원 (`workflow_dispatch`)

## 🔧 설정 방법

### 1. Repository 생성

이 폴더를 새 GitHub 리포지토리로 푸시합니다:

```bash
git init
git add .
git commit -m "Initial commit: Daily AI Briefing automation"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai-briefing-automation.git
git push -u origin main
```

### 2. Notion Integration 설정

1. [Notion Integrations](https://www.notion.so/my-integrations) 페이지로 이동
2. **"+ New integration"** 클릭
3. 이름: `AI Briefing Bot`
4. Capabilities: **Read content**, **Insert content** 체크
5. **Submit** 후 **Internal Integration Token** 복사

### 3. Notion 데이터베이스 연결

1. Notion에서 **AI Research Updates** 데이터베이스 열기
2. 우측 상단 **···** 메뉴 → **Connections** → **AI Briefing Bot** 추가
3. 데이터베이스 URL에서 ID 추출:
   ```
   https://www.notion.so/f02daa4f5a7445cbbba409db6a7f97b7?v=...
                        └──────────── 이 부분이 Database ID ────────────┘
   ```

### 4. GitHub Secrets 설정

GitHub 리포지토리 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret Name | Value | 설명 |
|-------------|-------|------|
| `ANTHROPIC_API_KEY` | `sk-ant-api03-...` | [Claude Console](https://console.anthropic.com/)에서 발급 |
| `NOTION_API_KEY` | `secret_...` | Notion Integration Token |
| `NOTION_DATABASE_ID` | `385206fc-...` | AI Research Updates DB ID |

### 5. 워크플로우 실행 테스트

1. GitHub 리포지토리 → **Actions** 탭
2. **Daily AI Briefing** 워크플로우 선택
3. **Run workflow** 버튼 클릭

## 📁 파일 구조

```
ai-briefing-automation/
├── .github/
│   └── workflows/
│       └── daily-briefing.yml    # GitHub Actions 워크플로우
├── daily_ai_briefing.py          # 메인 Python 스크립트
├── requirements.txt              # Python 의존성
├── .env.example                  # 환경변수 템플릿
└── README.md                     # 이 파일
```

## ⏰ 스케줄 변경

`daily-briefing.yml`에서 cron 표현식 수정:

```yaml
schedule:
  # 매일 아침 9시 KST (00:00 UTC)
  - cron: '0 0 * * *'
  
  # 다른 예시:
  # 매일 오전 8시 KST: '0 23 * * *' (전날 23:00 UTC)
  # 평일만 오전 9시 KST: '0 0 * * 1-5'
  # 매주 월요일 오전 9시 KST: '0 0 * * 1'
```

## 📊 Notion 데이터베이스 스키마

| 속성 | 타입 | 설명 |
|------|------|------|
| Title | Title | 항목 제목 |
| Category | Select | 📄 논문/연구, 🚀 모델 릴리스, 📊 벤치마크, 💼 시장/기업, 🔧 기술/인프라 |
| Date | Date | 추가 날짜 |
| Tags | Multi-select | RLVR, GRPO, Mamba, Long Context, Anthropic, OpenAI 등 |
| Importance | Select | 🔥 High, ⭐ Medium, 📌 Low |
| Summary | Rich text | 요약 및 참고문헌 |
| Source | URL | 출처 링크 |

## 💰 비용 안내

- **GitHub Actions**: 월 2,000분 무료 (private repo 기준)
  - 이 워크플로우는 약 1-2분 소요 → 월 30-60분 사용
- **Claude API**: 약 $0.01-0.05/실행
  - 월 30회 실행 시 약 $0.3-1.5

## 🔧 로컬 테스트

```bash
# 환경변수 설정
cp .env.example .env
# .env 파일 편집하여 실제 키 입력

# 의존성 설치
pip install -r requirements.txt

# 실행
python daily_ai_briefing.py
```

## 📝 라이선스

MIT License

---

Made with ❤️ by Claude & eple
