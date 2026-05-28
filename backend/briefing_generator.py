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
    """VibePick 스타일 감정형 AI 브리핑 생성"""
    
    def __init__(self):
        self.model = "claude-opus-4-6"  # ⭐ Opus (더 나은 품질)
        self.max_tokens = 500  # 짧음!
    
    def generate_briefing(self, article_title: str, article_content: str) -> dict:
        """
        VibePick 감정형 브리핑 생성
        
        반환:
        {
            "mood": "긍정적|중립|부정적",
            "headline": "한 줄 핵심",
            "today_points": ["포인트1 이모지", "포인트2 이모지", "포인트3 이모지"],
            "related_stocks": ["종목1", "종목2"],
            "investor_feeling": "투자자 심리"
        }
        """
        
        prompt = f"""당신은 주식 시장의 감정을 읽는 브리핑 전문가입니다.
뉴스를 읽고 "지금 시장의 기분"을 한눈에 표현하세요.

[뉴스 제목]
{article_title}

[뉴스 내용]
{article_content[:1200]}

## 분석 규칙:
1. **분위기**: 긍정적(↗) / 중립(→) / 부정적(↘) 중 정확히 1개
2. **한 줄 헤드라인**: 20자 이내 (뉴스 제목처럼 임팩트 있게)
3. **오늘 포인트**: 정확히 3개 (각 15자 이내 + 감정 이모지)
   - 이모지: 🚀 📈 💪 ⚡ 💥 📉 ⚠️ 🔥 등
4. **관련 종목**: 2-3개만 (한국 상장사, 진짜 관련사만)
5. **투자 심리**: 한 문장 (투자자가 느낄 심리)

## 출력 형식 (JSON만, 설명 없음):
{{
    "mood": "긍정적",
    "headline": "최대 20자 헤드라인",
    "today_points": [
        "최대 15자 포인트 이모지",
        "최대 15자 포인트 이모지",
        "최대 15자 포인트 이모지"
    ],
    "related_stocks": ["삼성전자", "SK하이닉스"],
    "investor_feeling": "장기 수익성 개선, 단기 변동성 주의"
}}

## 예시:
뉴스: "삼성전자 AI 칩 수요로 영업이익 49% 증가"
{{
    "mood": "긍정적",
    "headline": "AI 칩 수요 폭발 🚀",
    "today_points": [
        "메모리 공급 부족 📈",
        "기술주 강세 지속 💪",
        "삼성 경쟁력 확보 ⚡"
    ],
    "related_stocks": ["삼성전자", "SK하이닉스"],
    "investor_feeling": "생성형AI 수혜 장기 지속, 변동성 주의"
}}

## 주의 사항:
- 반드시 JSON만 응답 (마크다운 제외)
- 한국어만, 절대 영문 섞지 마
- 종목은 한국 상장사만 (확실할 때만 포함)
- 길이 제한 엄격히 (headline 20자, point 15자 max)
- 감정 이모지 필수 (분위기 전달 핵심)
- 투자 심리는 균형잡혀야 함 (긍정만 아님)

응답: JSON만"""
        
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
            
            # JSON 파싱 (마크다운 블록 제거)
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
        """
        DB의 브리핑 없는 기사들을 VibePick 브리핑으로 변환
        """
        db = SessionLocal()
        
        try:
            # 브리핑이 없는 기사 찾기
            articles_without_briefing = db.query(Article).filter(
                ~Article.id.in_(
                    db.query(Briefing.article_id)
                )
            ).limit(limit).all()
            
            logger.info(f"\n🎯 VibePick 감정형 브리핑 생성")
            logger.info(f"처리할 기사: {len(articles_without_briefing)}개\n")
            
            if not articles_without_briefing:
                logger.info("🎉 처리할 기사가 없습니다 (모두 완료됨)")
                return
            
            for idx, article in enumerate(articles_without_briefing, 1):
                logger.info(f"[{idx}/{len(articles_without_briefing)}] {article.title[:50]}")
                
                # 브리핑 생성
                briefing_data = self.generate_briefing(
                    article.title,
                    article.original_content
                )
                
                if briefing_data:
                    try:
                        # DB에 저장
                        new_briefing = Briefing(
                            article_id=article.id,
                            ai_summary=briefing_data.get("headline", ""),  # 한 줄 요약
                            positive_points=briefing_data.get("today_points", []),  # 오늘 포인트들
                            negative_points=[briefing_data.get("investor_feeling", "")],  # 투자심리
                            related_stocks=briefing_data.get("related_stocks", []),
                            related_sectors=[]  # 나중에 추가 가능
                        )
                        
                        db.add(new_briefing)
                        db.commit()
                        logger.info(f"   💾 저장 완료\n")
                    except Exception as e:
                        db.rollback()
                        logger.error(f"   저장 오류: {str(e)}\n")
                else:
                    logger.error(f"   ⚠️  브리핑 생성 실패\n")
            
            logger.info("✨ 모든 기사 처리 완료!")
            
        except Exception as e:
            db.rollback()
            logger.error(f"처리 중 오류: {str(e)}")
        finally:
            db.close()


if __name__ == "__main__":
    # 테스트: 브리핑 생성
    generator = BriefingGenerator()
    
    # 기사가 있으면 처리
    generator.process_articles(limit=10)