import os
import json
import logging
from anthropic import Anthropic
from database import SessionLocal, Article, Briefing
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = Anthropic()


class BriefingGenerator:
    """VibePick 감정형 브리핑 - 현실적인 감정 분석 (개선판)"""
    
    def __init__(self):
        self.model = "claude-opus-4-6"
        self.max_tokens = 500
    
    def generate_briefing(self, article_title: str, article_content: str) -> dict:
        """현실적인 감정형 브리핑 생성 (부정적 뉴스 강화)"""
        
        prompt = f"""당신은 투자자의 심리를 읽는 시장 브리핑 전문가입니다.
뉴스를 읽고 "지금 투자자들이 어떻게 느낄지" 정직하게 표현하세요.
**절대** 모든 뉴스를 긍정적으로만 쓰지 마세요!

[뉴스 제목]
{article_title}

[뉴스 내용]
{article_content[:1200]}

## 🎯 분석 규칙:

### 1️⃣ 분위기 판단 (정직하게!)
- **부정적 뉴스** (우선순위 높음):
  * 금리인상 / 금리 인상 기대 → 부정적 (대출 부담↑)
  * 경기둔화 / 경기 악화 / 경기 둔화 신호 → 부정적
  * 규제 / 규제 강화 / 수사 / 적발 → 부정적
  * 부실 / 부도 / 손실 / 악화 → 부정적
  * 하락 / 하향 / 조정 / 낙폭 → 부정적
  * 구조조정 / 감원 / 폐지 → 부정적

- **긍정적 뉴스** (명확할 때만):
  * 기술 혁신 / AI 성장 / 신기술 도입 → 긍정적
  * 호실적 / 매출 증가 / 이익 성장 (30% 이상) → 긍정적
  * 투자 유입 / 펀딩 성공 → 긍정적
  * 상승 / 강세 / 랠리 → 긍정적
  * 신제품 출시 (성공 가능성 높을 때) → 긍정적

- **중립 뉴스** (판단 어려울 때):
  * 정책 분석 / 평가 / 전망 → 중립
  * 실적 발표 (평범한 수준) → 중립
  * 인사 / 임원 교체 → 중립
  * 제휴 / 협약 (효과 미미) → 중립

### 2️⃣ 한 줄 헤드라인 (15자 이내, 이모지 필수 1개만)
- **부정적**: "금리인상 임박, 차입금 부담 📉" (14자)
- **긍정적**: "AI 수요 폭발 🚀" (9자)
- **중립**: "실적 발표, 평범한 수준" (11자)

**중요: 이모지는 필수 1개만! 너무 많으면 게임처럼 보임**
- 긍정: 🚀 📈 💪 ⚡ (둘 중 1개만)
- 부정: 📉 ⚠️ 💔 🔴 (둘 중 1개만)
- 중립: → ◀ ▶ 📊 (둘 중 1개만)

### 3️⃣ 오늘 포인트 (정확히 3개, 각 15자 이내)
```
예시 (부정적 뉴스):
["금리 비용 증가 위험", "대출 상환 부담 확대", "변동성 높아질 우려"]

예시 (긍정적 뉴스):
["주요 기업 발주 재개", "공급 부족 지속", "가격 인상 여력"]

예시 (중립 뉴스):
["분기 실적 발표", "시장 반응 주목", "향후 전망 중요"]
```

### 4️⃣ 관련 종목 (2-3개만, 실제 상장사)
```
부정적: ["은행주", "금융사"]
긍정적: ["삼성전자", "SK하이닉스"]
중립: ["실적 관련사", "정책 대상 기업"]
```

### 5️⃣ 투자 심리 (1문장, 투자자 관점)
```
부정적: "금리 인상 여파로 매도 압박 가능"
긍정적: "AI 성장 이야기로 매수 관심 확대"
중립: "실적 발표 후 방향성 결정 예상"
```

## 📋 JSON 응답 형식 (반드시 JSON만):
{{
    "mood": "긍정적|중립|부정적",
    "headline": "15자 이내 (이모지 1개)",
    "today_points": ["15자 이내", "15자 이내", "15자 이내"],
    "related_stocks": ["종목1", "종목2"],
    "investor_feeling": "투자자 심리 1문장"
}}

## ❌ 피해야 할 예시:
```json
{{
    "mood": "긍정적",
    "headline": "모든 좋은 뉴스다!! 🚀🚀📈💪⚡",  // ❌ 너무 많은 이모지
    "today_points": ["포인트1", "포인트2"],  // ❌ 2개만 있음 (3개 필요)
    "related_stocks": [],  // ❌ 종목 없음
    "investor_feeling": ""  // ❌ 빔
}}
```

## ✅ 좋은 예시:

### 부정적 뉴스: "한은 기준금리 7월 인상 시사"
{{
    "mood": "부정적",
    "headline": "금리인상 임박, 차입금 부담 📉",
    "today_points": ["금리 비용 증가 위험", "대출 상환 부담 확대", "변동성 높아질 우려"],
    "related_stocks": ["은행주", "금융사"],
    "investor_feeling": "금리 인상 여파로 매도 압박 가능, 신중한 진입 필요"
}}

### 긍정적 뉴스: "삼성전자 AI칩 매출 급증, 영업이익 49% 증가"
{{
    "mood": "긍정적",
    "headline": "AI 수요 폭발 🚀",
    "today_points": ["AI칩 공급 부족 영속", "가격 인상 여력 있어", "경쟁사보다 우위 확보"],
    "related_stocks": ["삼성전자", "SK하이닉스"],
    "investor_feeling": "AI 붐 장기화 기대, 반도체 종목 강세 지속 가능"
}}

### 중립 뉴스: "분기 실적 공개, 시장 평가"
{{
    "mood": "중립",
    "headline": "분기 실적, 시장 반응 주목 →",
    "today_points": ["실적 발표 시장 영향", "투자자 평가 분기점", "향후 가이던스 중요"],
    "related_stocks": ["실적 관련사", "대형주"],
    "investor_feeling": "실적 수준에 따라 단기 방향성 결정될 가능성"
}}

## 🎯 절대 지켜야 할 것:
- JSON만 응답 (마크다운, 설명 없음)
- 부정적 뉴스도 정직하게 표시
- 이모지는 정확히 1개만
- 포인트는 정확히 3개
- 종목은 2-3개 (실제 존재하는 회사만)
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
            
            logger.info(f"✅ 브리핑 생성: {article_title[:40]}")
            logger.info(f"   분위기: {briefing_data.get('mood')} | 헤드: {briefing_data.get('headline')}")
            
            return briefing_data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 파싱 실패: {str(e)}")
            logger.error(f"응답: {response_text[:200]}")
            return None
        except Exception as e:
            logger.error(f"❌ Claude API 실패: {str(e)}")
            return None
    
    def process_articles(self, limit: int = None):
        """DB 기사를 VibePick 브리핑으로 변환"""
        db = SessionLocal()
        
        try:
            articles_without_briefing = db.query(Article).filter(
                ~Article.id.in_(
                    db.query(Briefing.article_id)
                )
            ).limit(limit).all()
            
            logger.info(f"\n🎯 VibePick 감정형 브리핑 생성 (개선판: 부정적 뉴스 강화)")
            logger.info(f"처리할 기사: {len(articles_without_briefing)}개\n")
            
            if not articles_without_briefing:
                logger.info("🎉 처리할 기사가 없습니다 (모두 완료됨)")
                return
            
            for idx, article in enumerate(articles_without_briefing, 1):
                logger.info(f"[{idx}/{len(articles_without_briefing)}] {article.title[:50]}")
                
                briefing_data = self.generate_briefing(
                    article.title,
                    article.original_content
                )
                
                if briefing_data:
                    try:
                        new_briefing = Briefing(
                            article_id=article.id,
                            ai_summary=briefing_data.get("headline", ""),
                            positive_points=briefing_data.get("today_points", []),
                            negative_points=[briefing_data.get("investor_feeling", "")],
                            related_stocks=briefing_data.get("related_stocks", []),
                            related_sectors=[]
                        )
                        
                        db.add(new_briefing)
                        db.commit()
                        logger.info(f"   💾 저장 완료 ({briefing_data.get('mood')})\n")
                    except Exception as e:
                        db.rollback()
                        logger.error(f"   저장 오류: {str(e)}\n")
                else:
                    logger.error(f"   ⚠️  생성 실패\n")
            
            logger.info("✨ 모든 기사 처리 완료!")
            
        except Exception as e:
            db.rollback()
            logger.error(f"처리 중 오류: {str(e)}")
        finally:
            db.close()


if __name__ == "__main__":
    generator = BriefingGenerator()
    generator.process_articles(limit=10)