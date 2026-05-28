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
        """✅ Briefing이 없는 최신 기사만 그룹화 (1개 이상이면 분석)"""
        
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
        
        # 4️⃣ 각 카테고리별 1개 이상이면 분석 (최대 10개)
        result = {}
        for cat, cat_articles in categorized.items():
            if len(cat_articles) >= 1:  # 1개 이상이면 분석!
                result[cat] = cat_articles[:10]  # 최대 10개
            else:
                logger.info(f"⏭️  {cat}: 기사 0개 (분석 스킵)")
        
        logger.info(f"📂 카테고리별 기사 그룹화: {len(result)}개 카테고리 (1개 이상 보유)")
        for cat, arts in result.items():
            logger.info(f"   {cat}: {len(arts)}개 (신규)")
        
        return result
    
    def generate_category_briefing(self, category: str, articles: list) -> dict:
        """카테고리별 종합 분석 브리핑 생성 (현실적인 감정 분석)"""
        
        # 기사들을 요약 문자열로
        articles_summary = "\n".join([
            f"- {article.title}: {article.original_content[:300]}"
            for article in articles
        ])
        
        prompt = f"""당신은 중립적인 시장 분석가입니다.
뉴스의 긍정/부정을 객관적으로 판단하세요.

[카테고리] {category}

[최근 기사 {len(articles)}개]
{articles_summary}

## 📊 분석 원칙:

### ❌ 절대 금지 (당신이 자주 하는 실수):
1. 모든 뉴스를 긍정적으로 해석하기
2. 부정적 뉴스를 "기회"로 포장하기
3. "장기적으로 긍정"이라며 현재의 부정 무시
4. 투자자 입장에서 낙관적으로 왜곡
5. **은행이 금리인상하면 "수익성 개선"이라 긍정으로 표현 (❌ 이건 기업입장에선 부담)**

### ✅ 부정적 신호 (절대 긍정으로 왜곡하지 마세요):
- **금리인상** → 부정적 (기업·소비자 차입비용 증가)
- **경기둔화** → 부정적 (성장율 하락)
- **실업률 증가** → 부정적 (고용 악화)
- **손실 발표** → 부정적 (실적 악화)
- **경쟁 심화** → 부정적 (가격 하락, 마진 압박)
- **규제강화** → 부정적 (비용 증가)
- **구조조정** → 부정적 (일자리 감소)
- **매출/이익 감소** → 부정적 (사업 위축)

### ✅ 긍정 신호 (숫자로 확인되어야 함):
- 매출/이익 **증가** (% 수치 명시)
- 신제품 **출시 성공** (판매량 증가)
- **M&A 완료** (전략적 강화)
- **시장점유율 확대**
- **기술혁신 완성** (실제 적용)

### ✅ 중립 신호:
- 인사이동 (영향 불확실)
- 실적 발표 (예상 범위 내)
- 정책 분석 (방향 불명확)

### 2️⃣ 핵심 흐름 (20자 이내, 이모지 1개)
❌ 모든 기사에 🚀를 붙이지 마세요!

```
✅ 좋은 예시:
- 긍정적: "AI칩 수요 폭발, 공급 경쟁 🚀" (부정확한 부분 없음)
- 부정적: "금리인상 확정, 기업 부담 ⚠️" (현실적)
- 중립: "실적 발표, 시장 반응 주목 →" (결과 미정)
```

### 3️⃣ 트렌드 분석 (정확히 3개)
**기사에서 반복되는 부정적 신호도 포함하세요!**

```
예시 (금융 - 금리인상 기사 많을 때):
1. "금리 인상 신호 강해짐"
2. "대출 수요 축소 우려"
3. "기업 차입금 비용 증가"

예시 (에너지 - 유가 약세 기사):
1. "국제유가 하락 추세"
2. "정제 마진 축소 중"
3. "공급 과잉 신호 확산"
```

### 4️⃣ 관련 주요 종목 (3-5개)
기사에 언급된 기업들

### 5️⃣ 투자자 심리 (2-3문장)
**현실 그대로 표현하세요!**

```
❌ 나쁜 예시:
"금리인상이지만 강한 매수심리 유지. AI 혁신에 희망"
→ 너무 긍정적으로만 표현

✅ 좋은 예시:
"금리인상 신호에 신중한 관망 중. 대출 비용 증가 우려.
기대와 우려가 섞여있는 상황. 선별 투자 중"
→ 현실적이고 균형잡힌 표현

✅ 부정적 기사 분석:
"유가 약세로 에너지주 약함. 공급과잉 신호에 투자 주춤.
장기 회복까지 관망 필요"
→ 부정적이지만 정직함
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

## ✅ 현실적인 예시:

### AI · 기술 (호실적 기사 많을 때)
{{
    "category": "AI · 기술",
    "mood": "긍정적",
    "headline": "AI칩 수요 폭발, 공급경쟁 심화 🚀",
    "trends": [
        "AI칩 수요 사상 최고",
        "공급사 투자경쟁 심화",
        "가격 인상여력 확대"
    ],
    "related_stocks": ["삼성전자", "SK하이닉스", "엔비디아"],
    "investor_sentiment": "AI 성장스토리 매수심리 강함. 밸류에이션 우려로 변동성 커짐. 기술주 양극화 진행중"
}}

### 금융 (금리인상 기사 많을 때) - 명백히 부정적!
{{
    "category": "금융",
    "mood": "부정적",
    "headline": "금리인상 확정, 차입비용 증가 ⚠️",
    "trends": [
        "금리인상 신호 강화중",
        "기업 차입비용 증가",
        "대출수요 축소 우려"
    ],
    "related_stocks": ["은행주", "금융지주"],
    "investor_sentiment": "금리인상 신호에 신중한 관망. 기업·가계 부담 증가 우려. 금융주도 변동성 확대 예상"
}}

### 에너지 (유가약세 기사 많을 때) - 명백히 부정적!
{{
    "category": "에너지",
    "mood": "부정적",
    "headline": "유가약세, 수익성 악화 📉",
    "trends": [
        "국제유가 지속 하락",
        "정제 마진 축소중",
        "공급 과잉 우려"
    ],
    "related_stocks": ["S-Oil", "SK이노베이션"],
    "investor_sentiment": "유가약세로 에너지주 약함. 정제마진 축소에 수익성 악화. 회복까지 관망 필요"
}}

## 🎯 핵심 규칙 (절대 위반하지 마세요):
1. ❌ 금리인상 뉴스를 "은행 수익성 개선"으로 긍정 해석 금지
2. ❌ 경기 부진을 "저점 도달 = 회복 기회"로 왜곡 금지
3. ❌ 손실 기사를 "일시적"이라며 무시 금지
4. ✅ 부정적 신호는 부정적으로 표현하세요
5. ✅ 기사의 표면 내용 그대로 판단하세요
6. ✅ 투자자 입장에서 "현재" 영향을 평가하세요

JSON만 응답 (설명 없음)
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
        """모든 카테고리별 종합 분석 (신규 기사만, 1개 이상, 현실적 감정)"""
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