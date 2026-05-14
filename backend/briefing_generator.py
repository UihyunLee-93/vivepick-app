import os
import json
import logging
from anthropic import Anthropic
from database import SessionLocal, Article, Briefing, Stock
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = Anthropic()


class BriefingGenerator:
    """Claude API를 사용한 AI 브리핑 생성"""
    
    def __init__(self):
        self.model = "claude-3-5-haiku-20241022"  # 비용 최적화를 위해 Haiku 사용
        self.max_tokens = 800
    
    def generate_briefing(self, article_title: str, article_content: str) -> Dict:
        """
        기사 데이터를 받아 AI 브리핑 생성
        
        반환 형식:
        {
            "summary": "3줄 요약",
            "positive_points": ["좋은점 1", "좋은점 2"],
            "negative_points": ["나쁜점 1", "나쁜점 2"],
            "related_stocks": ["삼성전자", "SK하이닉스"],
            "related_sectors": ["반도체", "2차전지"]
        }
        """
        
        prompt = f"""
당신은 금융 뉴스 분석 전문가입니다. 다음 뉴스 기사를 분석하고 JSON 형식으로 응답하세요.

[기사 제목]
{article_title}

[기사 내용]
{article_content[:2000]}

다음 형식으로 **반드시 JSON만** 응답하세요 (다른 텍스트 없음):

{{
    "summary": "3줄 이내로 핵심 내용을 요약",
    "positive_points": ["투자자 관점에서의 긍정적 요소 1", "긍정적 요소 2"],
    "negative_points": ["투자자 관점에서의 부정적 요소 1", "부정적 요소 2"],
    "related_stocks": ["관련 상장사 1", "관련 상장사 2"],
    "related_sectors": ["관련 섹터 1", "관련 섹터 2"]
}}

주의사항:
- 한국 주식시장 관점 (코스피/코스닥)
- 실제 상장사만 포함
- 각 항목 2-3개 요소만 포함
- 요약은 객관적이고 중립적으로
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
            
            # JSON 파싱 (마크다운 코드블록 제거)
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            briefing_data = json.loads(response_text)
            
            logger.info(f"✅ 브리핑 생성: {article_title[:50]}")
            return briefing_data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 파싱 실패: {str(e)}")
            logger.error(f"응답: {response_text}")
            return None
        except Exception as e:
            logger.error(f"❌ Claude API 호출 실패: {str(e)}")
            return None
    
    def process_articles(self, limit: int = None):
        """
        DB의 브리핑이 없는 기사들을 처리
        
        Args:
            limit: 처리할 기사 개수 (None이면 모두 처리)
        """
        db = SessionLocal()
        
        try:
            # 브리핑이 없는 기사 찾기
            articles_without_briefing = db.query(Article).filter(
                ~Article.id.in_(
                    db.query(Briefing.article_id)
                )
            ).limit(limit).all()
            
            logger.info(f"\n📊 처리할 기사: {len(articles_without_briefing)}개\n")
            
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
                    # DB에 저장
                    new_briefing = Briefing(
                        article_id=article.id,
                        ai_summary=briefing_data.get("summary", ""),
                        positive_points=briefing_data.get("positive_points", []),
                        negative_points=briefing_data.get("negative_points", []),
                        related_stocks=briefing_data.get("related_stocks", []),
                        related_sectors=briefing_data.get("related_sectors", [])
                    )
                    
                    db.add(new_briefing)
                    db.commit()
                    logger.info(f"   💾 브리핑 저장 완료\n")
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
    generator.process_articles(limit=5)  # 테스트용 5개만 처리
