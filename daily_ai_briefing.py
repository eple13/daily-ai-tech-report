#!/usr/bin/env python3
"""
Daily AI Briefing Generator
매일 아침 9시 자동 실행 - Claude API로 브리핑 생성 후 Notion DB 업데이트

Requirements:
    pip install anthropic requests python-dotenv

Environment Variables:
    ANTHROPIC_API_KEY: Claude API 키
    NOTION_API_KEY: Notion Integration 토큰
    NOTION_DATABASE_ID: AI Research Updates 데이터베이스 ID
"""

import os
import json
import re
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Optional
import anthropic
import requests
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────
# Logging 설정
# ──────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "briefing.log")

logger = logging.getLogger("daily_ai_briefing")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# ──────────────────────────────────────
# Configuration (환경변수로 오버라이드 가능)
# ──────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

NOTION_API_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "8000"))
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# KST 시간대
KST = timezone(timedelta(hours=9))

# Briefing prompt
BRIEFING_PROMPT = """AI Product Owner 시각에서, 오늘 날짜 기준 최신 AI 시장·연구 뉴스를 바탕으로 브리핑을 작성해줘.

중복 방지 원칙:
1) 같은 사건을 다른 표현으로 반복하지 말고 하나의 항목으로 통합해줘.
2) 이미 널리 알려진 오래된 이슈의 재요약은 제외하고, 최근 7일 내 새롭게 확인된 사실/발표/지표 변화 위주로 선별해줘.
3) 항목 간 핵심 포인트가 겹치면 더 영향도가 큰 항목만 남겨줘.

콘텐츠 구성 원칙:
- 연구(논문/기술)와 시장(기업/제품/투자/규제) 관점을 균형 있게 포함해줘.
- 각 항목은 "무엇이 새롭고 왜 중요한지"가 드러나도록 2-3문장으로 요약해줘.
- 설명의 근거가 되는 논문·공식 발표·신뢰 가능한 기사 링크를 references에 포함해줘.

응답은 반드시 다음 JSON 형식으로 제공해줘:

```json
{
  "items": [
    {
      "title": "항목 제목",
      "category": "📄 논문/연구" | "🚀 모델 릴리스" | "📊 벤치마크" | "💼 시장/기업" | "🔧 기술/인프라",
      "importance": "🔥 High" | "⭐ Medium" | "📌 Low",
      "tags": ["태그1", "태그2"],
      "summary": "2-3문장 요약",
      "source_url": "출처 URL (있는 경우)"
    }
  ],
  "references": [
    "[1] 참고문헌 설명 - URL",
    "[2] 참고문헌 설명 - URL"
  ]
}
```

태그는 자유롭게 생성 가능하며, 이슈의 핵심 주제를 가장 잘 설명하는 짧은 키워드 1-3개를 사용해줘.

오늘 날짜 기준으로 웹 검색을 활용해 최신 정보를 검증하고, 중복 없는 중요한 업데이트 3-5개만 포함해줘."""


# ──────────────────────────────────────
# 유틸리티
# ──────────────────────────────────────
VALID_CATEGORIES = {
    "📄 논문/연구", "🚀 모델 릴리스", "📊 벤치마크", "💼 시장/기업", "🔧 기술/인프라"
}
VALID_IMPORTANCES = {"🔥 High", "⭐ Medium", "📌 Low"}


def retry_with_backoff(func, max_retries: int = MAX_RETRIES, base_delay: float = 2.0):
    """지수 백오프를 적용한 재시도 래퍼"""
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    "Attempt %d/%d failed: %s — retrying in %.1fs",
                    attempt + 1, max_retries + 1, e, delay,
                )
                time.sleep(delay)
            else:
                logger.error(
                    "All %d attempts failed. Last error: %s",
                    max_retries + 1, e,
                )
    raise last_exception


def validate_item(item: dict) -> dict:
    """브리핑 항목의 필수 필드를 검증하고 기본값으로 보완"""
    if not isinstance(item, dict):
        return None

    title = item.get("title", "").strip()
    if not title:
        logger.warning("Item skipped: missing title")
        return None

    category = item.get("category", "📄 논문/연구")
    if category not in VALID_CATEGORIES:
        logger.warning("Invalid category '%s' for '%s', defaulting", category, title)
        category = "📄 논문/연구"

    importance = item.get("importance", "⭐ Medium")
    if importance not in VALID_IMPORTANCES:
        logger.warning("Invalid importance '%s' for '%s', defaulting", importance, title)
        importance = "⭐ Medium"

    return {
        "title": title[:100],
        "category": category,
        "importance": importance,
        "tags": item.get("tags", []),
        "summary": item.get("summary", ""),
        "source_url": item.get("source_url", ""),
    }


def parse_json_response(text: str) -> Optional[dict]:
    """Claude 응답에서 JSON을 안전하게 추출"""
    # 1) ```json ... ``` 코드블록
    json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            logger.warning("JSON code block found but failed to parse")

    # 2) 가장 바깥쪽 { } 블록 (balanced braces)
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    start = None

    # 3) 전체 텍스트를 JSON으로 파싱 시도
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Could not parse JSON from response")
        logger.debug("Response preview: %s", text[:500])
        return None


# ──────────────────────────────────────
# Notion 중복 체크
# ──────────────────────────────────────
def check_existing_titles(date_str: str) -> set:
    """오늘 날짜로 이미 등록된 항목 제목 집합을 반환"""
    if not NOTION_API_KEY or not NOTION_DATABASE_ID:
        return set()

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }

    query = {
        "filter": {
            "property": "Date",
            "date": {"equals": date_str},
        },
        "page_size": 100,
    }

    try:
        resp = requests.post(
            f"{NOTION_API_URL}/databases/{NOTION_DATABASE_ID}/query",
            headers=headers,
            json=query,
            timeout=API_TIMEOUT,
        )
        if resp.status_code != 200:
            logger.warning("Failed to query existing titles: %s", resp.status_code)
            return set()

        results = resp.json().get("results", [])
        titles = set()
        for page in results:
            title_prop = page.get("properties", {}).get("Title", {}).get("title", [])
            if title_prop:
                titles.add(title_prop[0].get("text", {}).get("content", ""))
        logger.info("Found %d existing items for %s", len(titles), date_str)
        return titles
    except Exception as e:
        logger.warning("Error checking existing titles: %s", e)
        return set()


# ──────────────────────────────────────
# Core Functions
# ──────────────────────────────────────
def generate_briefing_with_claude() -> Optional[dict]:
    """Claude API를 사용하여 AI 브리핑 생성 (재시도 포함)"""
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set")
        return None

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def _call_claude():
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            tools=[
                {
                    "type": "web_search_20250305",
                    "name": "web_search",
                }
            ],
            messages=[
                {"role": "user", "content": BRIEFING_PROMPT}
            ],
        )

        full_response = ""
        for block in response.content:
            if hasattr(block, "text"):
                full_response += block.text

        result = parse_json_response(full_response)
        if result is None:
            raise ValueError("Failed to parse JSON from Claude response")
        return result

    try:
        return retry_with_backoff(_call_claude)
    except Exception as e:
        logger.error("Claude API call failed after retries: %s", e)
        return None


def add_to_notion_database(item: dict, references: list) -> bool:
    """Notion 데이터베이스에 항목 추가 (재시도 포함)"""
    if not NOTION_API_KEY:
        logger.error("NOTION_API_KEY not set")
        return False

    if not NOTION_DATABASE_ID:
        logger.error("NOTION_DATABASE_ID not set")
        return False

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }

    # 참고문헌을 요약에 추가
    summary_with_refs = item.get("summary", "")
    if references:
        summary_with_refs += "\n\n참고: " + " | ".join(references[:3])

    # 태그 정규화
    tags = item.get("tags", [])
    if not isinstance(tags, list):
        tags = []

    normalized_tags = []
    for tag in tags:
        if not isinstance(tag, str):
            continue
        cleaned = tag.strip()
        if cleaned and cleaned not in normalized_tags:
            normalized_tags.append(cleaned)

    # KST 기준 날짜 사용
    today_kst = datetime.now(KST).strftime("%Y-%m-%d")

    # Notion 페이지 데이터 구성
    page_data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Title": {
                "title": [{"text": {"content": item.get("title", "Untitled")[:100]}}]
            },
            "Category": {
                "select": {"name": item.get("category", "📄 논문/연구")}
            },
            "Date": {
                "date": {"start": today_kst}
            },
            "Importance": {
                "select": {"name": item.get("importance", "⭐ Medium")}
            },
            "Summary": {
                "rich_text": [{"text": {"content": summary_with_refs[:2000]}}]
            },
            "Tags": {
                "multi_select": [{"name": tag} for tag in normalized_tags]
            },
        },
    }

    # Source URL 추가 (있는 경우)
    source_url = item.get("source_url", "")
    if source_url and source_url.startswith("http"):
        page_data["properties"]["Source"] = {"url": source_url}

    def _post_to_notion():
        response = requests.post(
            f"{NOTION_API_URL}/pages",
            headers=headers,
            json=page_data,
            timeout=API_TIMEOUT,
        )

        if response.status_code in (200, 201):
            return True

        # Rate limit 시 재시도를 위해 예외 발생
        if response.status_code == 429:
            raise RuntimeError(f"Notion rate limit: {response.text[:200]}")

        # 그 외 오류는 재시도 없이 실패 처리
        logger.error(
            "Notion API error for '%s': %s — %s",
            item.get("title", "Untitled"),
            response.status_code,
            response.text[:300],
        )
        return False

    try:
        result = retry_with_backoff(_post_to_notion, max_retries=2, base_delay=1.0)
        if result:
            logger.info("Added: %s", item.get("title", "Untitled"))
        return result
    except Exception as e:
        logger.error("Failed to add '%s' to Notion: %s", item.get("title", "Untitled"), e)
        return False


# ──────────────────────────────────────
# Main
# ──────────────────────────────────────
def main():
    """메인 실행 함수"""
    logger.info("=" * 60)
    logger.info("Daily AI Briefing - %s", datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"))
    logger.info("=" * 60)

    # 1. Claude API로 브리핑 생성
    logger.info("Generating briefing with Claude API (model: %s)...", CLAUDE_MODEL)
    briefing = generate_briefing_with_claude()

    if not briefing:
        logger.error("Failed to generate briefing")
        return 1

    items = briefing.get("items", [])
    references = briefing.get("references", [])

    # 2. 항목 검증
    validated_items = []
    for item in items:
        validated = validate_item(item)
        if validated:
            validated_items.append(validated)
        else:
            logger.warning("Dropped invalid item: %s", item)

    logger.info("Generated %d valid items (of %d total)", len(validated_items), len(items))

    if not validated_items:
        logger.error("No valid items to add")
        return 1

    # 3. 중복 체크
    today_kst = datetime.now(KST).strftime("%Y-%m-%d")
    existing_titles = check_existing_titles(today_kst)

    new_items = []
    for item in validated_items:
        if item["title"] in existing_titles:
            logger.info("Skipping duplicate: %s", item["title"])
        else:
            new_items.append(item)

    if not new_items:
        logger.info("All items already exist in Notion — nothing to add")
        return 0

    logger.info("%d new items to add (skipped %d duplicates)",
                len(new_items), len(validated_items) - len(new_items))

    # 4. Notion 데이터베이스에 추가
    logger.info("Adding items to Notion database...")

    success_count = 0
    for item in new_items:
        if add_to_notion_database(item, references):
            success_count += 1

    # 5. 결과 요약
    logger.info("=" * 60)
    logger.info("Summary: %d/%d items added successfully", success_count, len(new_items))
    logger.info("=" * 60)

    return 0 if success_count == len(new_items) else 1


if __name__ == "__main__":
    exit(main())
