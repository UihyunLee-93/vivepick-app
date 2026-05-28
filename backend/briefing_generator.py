import os
import json
import logging
from anthropic import Anthropic
from database import SessionLocal, Article, Briefing
from datetime import datetime
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = Anthropic()


class BriefingGenerator:
    """VibePick 카테고리별 종합 분석 브리핑"""
    
    def __init__(self):
        self.model = "claude-opus-4-6"
        self.max_tokens = 800
    
    def get_articles_by_category(self, db) -> dict:
        """✅ Briefing이 없는 최신 기사만 그룹화 (각 카테고리 최소 3개, 최대 10개)"""
        
        # 1️⃣ 이미 Briefing이 있는 article_id 조회
        analyzed_article_ids = db.query(Briefing.article_id).distinct().all()
        analyzed_ids = {row[0] for row in analyzed_article_ids}
        
        logger.info(f"이미 분석된 기사: {len(analyzed_ids)}개")
        
        # 2️⃣ Briefing이 없는 최신 기사 100개 조회
        unanalyzed_articles = db.query(Article).filter(
            ~Article.id.isin(analyzed_ids) if analyzed_ids else True
        ).order_by(
            Article.crawled_at.desc()
        ).limit(100).all()
        
        logger.info(f"분석 대상 기사: {len(unanalyzed_articles)}개")
        
        # 3️⃣ source_name에서 카테고리 추출: "네이버뉴스 - AI · 기술"
        categorized = defaultdict(list)
        for article in unanalyzed_articles:
            if " - " in article.source_name:
                category = article.source_name.split(" - ")[-1]
            else:
                category = "기타"
            
            categorized[category].append(article)
        
        # 4️⃣ 각 카테고리별 3~10개 (기사가 적으면 그것만 사용)
        result = {}
        for cat, cat_articles in categorized.items():
            if len(cat_articles) >= 3:  # 최소 3개 이상만
                result[cat] = cat_articles[:10]  # 최대 10개
            # 3개 미만은 제외 (분석 품질 보장)
        
        logger.info(f"📂 카테고리별 기사 그룹화: {len(result)}개 카테고리")
        for cat, arts in result.items():
            logger.info(f"   {cat}: {len(arts)}개 (신규)")
        
        return result
    
    def generate_category_briefing(self, category: str, articles: list) -> dict:
        """카테고리별 종합 분석 브리핑 생성"""
        
        # 기사들을 요약 문자열로
        articles_summary = "\n".join([
            f"- {article.title}: {article.original_content[:300]}"
            for article in articles
        ])
        
        prompt = f"""당신은 시장 트렌드 분석가입니다.
다음 카테고리의 최근 기사들을 분석하고,
**그 카테고리의 현재 시장 흐름과 트렌드**를 종합 분석하세요.

[카테고리] {category}

[최근 기사 {len(articles)}개]
{articles_summary}

## 📊 분석 요구사항:

### 1️⃣ 카테고리 분위기
현재 이 섹터의 시장 심리를 평가하세요.
- **긍정적**: 수요 증가, 기술 혁신, 호실적 지속 등
- **중립**: 기다리는 중, 엇갈린 신호, 통합 구간 등
- **부정적**: 규제, 경기 부진, 공급 부족 등

### 2️⃣ 핵심 흐름 (20자 이내, 이모지 1개)
```
예시:
- AI: "수요 폭발, 공급 경쟁 시작 🚀" (16자)
- 금융: "금리 인상 기다림, 변동성 확대 ⚠️" (18자)
- 에너지: "유가 변동성 높음, 관망 중 →" (16자)
```

### 3️⃣ 트렌드 분석 (정확히 3개)
최근 기사에서 보이는 주요 트렌드:
```
예시 (AI · 기술):
1. "AI 칩 수요 사상 최고 기록"
2. "공급사 확대 투자 경쟁 심화"
3. "가격 인상 여력 확대"

예시 (금융):
1. "금리 인상 예상에 대출 수요 축소"
2. "은행권 수익성 개선 기대"
3. "환율 변동성 확대 중"
```

### 4️⃣ 관련 주요 종목 (3-5개)
최근 기사에 언급된 주요 기업들:
```
예시:
["삼성전자", "SK하이닉스", "엔비디아", "현대차", "LG전자"]
```

### 5️⃣ 투자자 심리 (2-3문장)
이 카테고리에 투자하는 사람들이 지금 어떤 심리 상태인지:
```
예시 (AI · 기술):
"AI 붐이 지속될 것으로 보고 매수 심리 강함. 
다만 밸류에이션 우려로 변동성 큼. 
기술주 중심으로 양극화 진행 중"

예시 (금융):
"금리 인상 시나리오에 조심스러운 관망 중.
은행주 수익성 개선은 기대하나,
대출 성장 부진이 상쇄 효과"
```

## 📋 JSON 응답 형식 (반드시 JSON만):
{{
    "category": "{category}",
    "mood": "긍정적|중립|부정적",
    "headline": "20자 이내 (이모지 1개)",
    "trends": [
        "트렌드 1 (15자 이내)",
        "트렌드 2 (15자 이내)",
        "트렌드 3 (15자 이내)"
    ],
    "related_stocks": ["종목1", "종목2", "종목3"],
    "investor_sentiment": "투자자 심리 2-3문장"
}}

## ✅ 좋은 예시:

### AI · 기술 카테고리
{{
    "category": "AI · 기술",
    "mood": "긍정적",
    "headline": "AI 수요 폭발, 공급 경쟁 심화 🚀",
    "trends": [
        "AI 칩 수요 사상 최고",
        "공급사 확대 투자 경쟁",
        "가격 인상 여력 확대"
    ],
    "related_stocks": ["삼성전자", "SK하이닉스", "엔비디아"],
    "investor_sentiment": "AI 성장 스토리로 매수 심화. 다만 밸류에이션 우려로 변동성 커짐. 기술주 양극화 중"
}}

### 금융 카테고리
{{
    "category": "금융",
    "mood": "중립",
    "headline": "금리 인상 시장, 수익성 기대 vs 대출 부담 ⚖️",
    "trends": [
        "금리 인상 시나리오 진행",
        "은행 수익성 개선 기대",
        "대출 수요 축소 우려"
    ],
    "related_stocks": ["KB금융", "신한지주", "하나금융"],
    "investor_sentiment": "금리 인상 혜택 기대하나 대출 부진 우려. 은행주 변동성 클 전망. 선별 투자 중"
}}

### 에너지 카테고리
{{
    "category": "에너지",
    "mood": "부정적",
    "headline": "유가 약세, 공급 과잉 신호 📉",
    "trends": [
        "국제유가 하락 추세",
        "공급 과잉 우려 확산",
        "정제 마진 축소 중"
    ],
    "related_stocks": ["S-Oil", "SK이노베이션", "GS칼텍스"],
    "investor_sentiment": "유가 약세로 에너지주 약함. 공급 과잉 신호에 투자 주춤. 장기 회복 기대 필요"
}}

## 🎯 중요 포인트:
- **개별 기사 분석 X** → 카테고리 전체의 흐름 분석
- **트렌드는 기사에서 반복되는 내용** (공통 주제)
- **투자자 심리는 시장 참여자의 실제 행동** 기반
- JSON만 응답 (설명 없음)
"""
        
        try:
            message = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_text = message.content[0].text.strip()
            
            # JSON 파싱
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            briefing_data = json.loads(response_text)
            
            logger.info(f"✅ {category} 분석 완료")
            logger.info(f"   분위기: {briefing_data.get('mood')} | {briefing_data.get('headline')}")
            
            return briefing_data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 파싱 실패: {str(e)}")
            logger.error(f"응답: {response_text[:200]}")
            return None
        except Exception as e:
            logger.error(f"❌ Claude API 실패: {str(e)}")
            return None
    
    def save_category_briefing(self, db, briefing_data: dict, articles: list):
        """카테고리 브리핑을 Briefing 테이블에 저장 (첫 기사 기준)"""
        
        if not briefing_data or not articles:
            return
        
        try:
            # 첫 번째 기사를 기준으로 저장 (여러 기사의 종합이므로)
            article = articles[0]
            
            new_briefing = Briefing(
                article_id=article.id,
                ai_summary=briefing_data.get("headline", ""),
                positive_points=briefing_data.get("trends", []),
                negative_points=[briefing_data.get("investor_sentiment", "")],
                related_stocks=briefing_data.get("related_stocks", []),
                related_sectors=[briefing_data.get("category", "")]
            )
            
            db.add(new_briefing)
            db.commit()
            logger.info(f"   💾 저장 완료\n")
            
        except Exception as e:
            db.rollback()
            logger.error(f"   저장 오류: {str(e)}\n")
    
    def process_categories(self):
        """모든 카테고리별 종합 분석 (신규 기사만)"""
        db = SessionLocal()
        
        try:
            logger.info("\n" + "="*60)
            logger.info("📊 카테고리별 종합 분석 시작 (신규 기사만)")
            logger.info("="*60 + "\n")
            
            # ✅ Briefing이 없는 기사만 카테고리별로 그룹화
            categorized_articles = self.get_articles_by_category(db)
            
            logger.info(f"\n분석할 카테고리: {len(categorized_articles)}개\n")
            
            if len(categorized_articles) == 0:
                logger.info("⏭️  분석할 신규 기사가 없습니다 (모두 분석됨)")
                return
            
            for category, articles in categorized_articles.items():
                if not articles:
                    continue
                
                logger.info(f"📂 {category} ({len(articles)}개 신규 기사 분석)")
                
                # 카테고리별 종합 분석
                briefing_data = self.generate_category_briefing(category, articles)
                
                if briefing_data:
                    self.save_category_briefing(db, briefing_data, articles)
                else:
                    logger.error(f"   ⚠️  분석 실패\n")
            
            logger.info("="*60)
            logger.info("✨ 모든 카테고리 분석 완료!")
            logger.info("="*60 + "\n")
            
        except Exception as e:
            db.rollback()
            logger.error(f"처리 중 오류: {str(e)}")
        finally:
            db.close()


if __name__ == "__main__":
    generator = BriefingGenerator()
    generator.process_categories()