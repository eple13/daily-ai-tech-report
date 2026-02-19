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
from datetime import datetime, timezone
from typing import Optional
import anthropic
import requests
from dotenv import load_dotenv

load_dotenv()

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "385206fc-e3c4-4687-8e71-657c2ab78de4")

NOTION_API_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# Briefing prompt (웹 검색 없이 최신 지식 기반)
BRIEFING_PROMPT = """당신은 AI Product Owner를 위한 브리핑 전문가입니다.

다음 주제에 대해 당신이 알고 있는 가장 최신 정보를 바탕으로 브리핑을 작성해주세요:
1. LLM 모델 학습 방법론 (RLVR, GRPO, 합성 데이터 등)
2. 롱 컨텍스트 처리 기술 (KV 캐시 최적화, Sparse Attention 등)
3. 글로벌 AI 연구 및 논문 동향
4. 시장 반응 및 기업 동향

응답은 반드시 아래 JSON 형식으로만 제공해주세요. 다른 텍스트 없이 JSON만 출력하세요:

{
  "items": [
    {
      "title": "항목 제목 (한국어)",
      "category": "📄 논문/연구",
      "importance": "🔥 High",
      "tags": ["RLVR", "DeepSeek"],
      "summary": "2-3문장 요약 (한국어)",
      "source_url": ""
    }
  ],
  "references": [
    "[1] 참고문헌 설명"
  ]
}

카테고리 옵션: "📄 논문/연구", "🚀 모델 릴리스", "📊 벤치마크", "💼 시장/기업", "🔧 기술/인프라"
중요도 옵션: "🔥 High", "⭐ Medium", "📌 Low"
태그는 자유롭게 생성 가능 (예: RLVR, GRPO, Mamba, Long Context, Anthropic, OpenAI, World Model, Agent 등)

3-5개의 중요한 AI 업데이트 항목을 포함해주세요."""



def generate_briefing_with_claude() -> Optional[dict]:
    """Claude API를 사용하여 AI 브리핑 생성"""
    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY not set")
        return None
    
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    try:
        # Claude API 호출 (웹 검색 도구 사용)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            tools=[
                {
                    "type": "web_search_20250305",
                    "name": "web_search"
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": BRIEFING_PROMPT
                }
            ]
        )
        
        # 응답에서 텍스트 추출
        full_response = ""
        for block in response.content:
            if hasattr(block, 'text'):
                full_response += block.text
        
        # JSON 파싱
        json_match = re.search(r'```json\s*(.*?)\s*```', full_response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # JSON 블록 없이 직접 JSON인 경우
        try:
            return json.loads(full_response)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse JSON from response")
            print(f"Response preview: {full_response[:500]}")
            return None
            
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        return None


def add_to_notion_database(item: dict, references: list) -> bool:
    """Notion 데이터베이스에 항목 추가"""
    if not NOTION_API_KEY:
        print("Error: NOTION_API_KEY not set")
        return False
    
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    
    # 참고문헌을 요약에 추가
    summary_with_refs = item.get("summary", "")
    if references:
        summary_with_refs += "\n\n참고: " + " | ".join(references[:3])
    
    # 태그 JSON 배열로 변환
    tags = item.get("tags", [])
    valid_tags = ["RLVR", "GRPO", "Mamba", "Long Context", "Synthetic Data", 
                  "KV Cache", "Anthropic", "OpenAI", "Google", "DeepSeek", "Meta", "Enterprise"]
    filtered_tags = [t for t in tags if t in valid_tags]
    
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
                "date": {"start": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
            },
            "Importance": {
                "select": {"name": item.get("importance", "⭐ Medium")}
            },
            "Summary": {
                "rich_text": [{"text": {"content": summary_with_refs[:2000]}}]
            },
            "Tags": {
                "multi_select": [{"name": tag} for tag in filtered_tags]
            }
        }
    }
    
    # Source URL 추가 (있는 경우)
    source_url = item.get("source_url")
    if source_url and source_url.startswith("http"):
        page_data["properties"]["Source"] = {"url": source_url}
    
    try:
        response = requests.post(
            f"{NOTION_API_URL}/pages",
            headers=headers,
            json=page_data
        )
        
        if response.status_code == 200:
            print(f"✅ Added: {item.get('title', 'Untitled')}")
            return True
        else:
            print(f"❌ Failed to add: {item.get('title', 'Untitled')}")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Error adding to Notion: {e}")
        return False


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print(f"🤖 Daily AI Briefing - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # 1. Claude API로 브리핑 생성
    print("\n📡 Generating briefing with Claude API...")
    briefing = generate_briefing_with_claude()
    
    if not briefing:
        print("❌ Failed to generate briefing")
        return 1
    
    items = briefing.get("items", [])
    references = briefing.get("references", [])
    
    print(f"✅ Generated {len(items)} items")
    
    # 2. Notion 데이터베이스에 추가
    print(f"\n📝 Adding items to Notion database...")
    
    success_count = 0
    for item in items:
        if add_to_notion_database(item, references):
            success_count += 1
    
    # 3. 결과 요약
    print("\n" + "=" * 60)
    print(f"📊 Summary: {success_count}/{len(items)} items added successfully")
    print("=" * 60)
    
    return 0 if success_count == len(items) else 1


if __name__ == "__main__":
    exit(main())
