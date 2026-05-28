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
    """VibePick 감정형 브리핑 - 현실적인 감정 분석"""
    
    def __init__(self):
        self.model = "claude-opus-4-6"
        self.max_tokens = 500
    
    def generate_briefing(self, article_title: str, article_content: str) -> dict:
        """현실적인 감정형 브리핑 생성"""
        
        prompt = f"""당신은 투자자의 심리를 읽는 시장 브리핑 전문가입니다.
뉴스를 읽고 "지금 투자자들이 어떻게 느낄지" 정직하게 표현하세요.
절대 모든 뉴스를 긍정적으로만 쓰지 마세요!

[뉴스 제목]
{article_title}

[뉴스 내용]
{article_content[:1200]}

## 분석 규칙:
1. **분위기**: 긍정적(↗) / 중립(→) / 부정적(↘) 중 정직하게 1개만 선택
   - 금리인상 뉴스 → 부정적
   - 기업 부실 → 부정적  
   - 기술 혁신 → 긍정적
   - 경기 악화 신호 → 부정적
   - 중립적 뉴스 → 중립

2. **한 줄 헤드라인**: 20자 이내 (정직하고 임팩트 있게)
   - ✅ 좋은 예: "금리인상 임박, 차입금 부담 ↗" (18자)
   - ✅ 좋은 예: "AI 수요 폭발, 반도체 강세 🚀" (17자)
   - ❌ 나쁜 예: "내용 설명" (너무 길거나 와닝 없음)
   - 긍정/부정 이모지 필수: 🚀 📈 🔴 📉 ↗ ↘ ⚠️

3. **오늘 포인트**: 정확히 3개 (각 15자 이내 + 현실적 이모지)
   - 긍정 이모지: 🚀 📈 💪 ⚡ 
   - 중립 이모지: → ◀ ▶ 📊
   - 부정 이모지: 📉 ⚠️ 💔 🔴

4. **관련 종목**: 2-3개만 (실제 관련사)

5. **투자 심리**: 한 문장 (투자자가 실제로 느낄 심리)
   - 금리 인상 → "단기 변동성 높을듯"
   - 실적 부진 → "이익 개선까지 관망"
   - 규제 리스크 → "매도 압박 가능"
   - 호실적 → "가격 재평가 기대"

## 출력 형식 (JSON만):
{{
    "mood": "긍정적|중립|부정적",
    "headline": "최대 20자 (필수 이모지)",
    "today_points": [
        "최대 15자 이모지",
        "최대 15자 이모지",
        "최대 15자 이모지"
    ],
    "related_stocks": ["종목1", "종목2"],
    "investor_feeling": "투자자 심리 한 문장"
}}

## 예시 (올바른 감정 분석):

뉴스: "한은 기준금리 7월 인상 시사"
{{
    "mood": "부정적",
    "headline": "금리인상 임박, 차입금 부담 📉",
    "today_points": [
        "금리 비용 증가 위험 ⚠️",
        "채권 투자수익률 상승 →",
        "변동성 높아질 우려 🔴"
    ],
    "related_stocks": ["은행주", "금융사"],
    "investor_feeling": "금리 인상 여파로 매도 압박 가능, 신중한 진입 필요"
}}

뉴스: "삼성전자 AI칩 매출 급증, 영업이익 49% 증가"
{{
    "mood": "긍정적",
    "headline": "AI 수요 급증, 반도체 강세 🚀",
    "today_points": [
        "AI칩 공급 부족 영속 📈",
        "가격 인상 여력 있어 💪",
        "경쟁사보다 우위 확보 ⚡"
    ],
    "related_stocks": ["삼성전자", "SK하이닉스"],
    "investor_feeling": "AI 붐 장기화 기대, 반도체 종목 강세 지속 가능"
}}

뉴스: "경기둔화 신호 속 소비심리 악화"
{{
    "mood": "부정적",
    "headline": "경기 둔화, 소비 위축 우려",
    "today_points": [
        "경기 악화 신호 강해짐 📉",
        "소비주 약세 예상 ⚠️",
        "경기민감주 매도 압박 💔"
    ],
    "related_stocks": ["유통주", "소비재주"],
    "investor_feeling": "경기 부양 정책 기다리며 관망, 약세 장기화 우려"
}}

## 주의:
- 모든 뉴스를 긍정적으로 쓰면 안 됨!
- 부정적 뉴스는 정직하게 부정적으로
- 투자자의 실제 심리를 반영
- JSON만 응답 (마크다운 제외)"""
        
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
            
            logger.info(f"\n🎯 VibePick 감정형 브리핑 생성 (현실적 분석)")
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
                            ai_summary=briefing_data.get("headline", ""),  # ✅ AI 헤드라인을 ai_summary로
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