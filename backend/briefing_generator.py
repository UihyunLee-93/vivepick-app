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
    """VibePick 재미있는 시장 분위기 브리핑"""
    
    def __init__(self):
        self.model = "claude-opus-4-6"
        self.max_tokens = 1000
    
    def get_articles_by_category(self, db) -> dict:
        """Briefing이 없는 최신 기사를 키워드로 분류"""
        
        analyzed_article_ids = db.query(Briefing.article_id).distinct().all()
        analyzed_ids = {row[0] for row in analyzed_article_ids}
        
        logger.info(f"이미 분석된 기사: {len(analyzed_ids)}개")
        
        unanalyzed_articles = db.query(Article).filter(
            Article.id.notin_(analyzed_ids) if analyzed_ids else True
        ).order_by(
            Article.crawled_at.desc()
        ).limit(100).all()
        
        logger.info(f"분석 대상 기사: {len(unanalyzed_articles)}개")
        
        # ✅ 카테고리별 키워드 정의
        category_keywords = {
            "AI · 기술": ["ai", "칩", "반도체", "클라우드", "기술", "nvidia", "엔비디아", "sk하이닉스", "삼성전자", "생성형"],
            "금융": ["금리", "금융", "한은", "환율", "국채", "금융시장", "kb금융", "신한", "하나금융"],
            "에너지": ["유가", "배터리", "태양광", "전기요금", "원유", "에너지", "sk이노베이션", "한전"],
            "모빌리티": ["자동차", "전기차", "현대차", "기아", "모빌리티", "포드", "테슬라"],
            "바이오": ["바이오", "신약", "제약", "셀트리온", "삼성바이오"],
            "소비 · 라이프": ["소비", "라이프", "아모레", "호텔", "식품", "유통"],
            "산업 · 제조": ["산업", "제조", "건설", "해양", "현대중공업", "두산"],
            "글로벌": ["미국", "중국", "일본", "유럽", "국제", "해외"],
            "크립토": ["비트코인", "암호화폐", "이더리움", "디지털자산"],
            "콘텐츠 · 엔터": ["콘텐츠", "엔터", "방송", "영화", "음악", "게임", "하이브", "jyp", "sm"]
        }
        
        categorized = defaultdict(list)
        for article in unanalyzed_articles:
            category = "기타"
            
            # title + original_content에서 키워드 검색
            text = (article.title + " " + article.original_content).lower()
            
            for cat, keywords in category_keywords.items():
                if any(kw.lower() in text for kw in keywords):
                    category = cat
                    break
            
            categorized[category].append(article)
        
        result = {}
        for cat, cat_articles in categorized.items():
            if cat == "기타":  # ✅ 기타는 제외
                logger.info(f"⏭️  기타: {len(cat_articles)}개 (분석 스킵)")
                continue
            
            if len(cat_articles) >= 1:
                result[cat] = cat_articles[:10]
            else:
                logger.info(f"⏭️  {cat}: 기사 0개 (분석 스킵)")
        
        logger.info(f"📂 카테고리별 기사 그룹화: {len(result)}개 카테고리")
        for cat, arts in result.items():
            logger.info(f"   {cat}: {len(arts)}개 (신규)")
        
        return result
    
    def generate_category_briefing(self, category: str, articles: list, slot: str = "morning") -> dict:
        """카테고리별 재미있는 브리핑 생성 (시간대별로 다른 톤)"""
        
        articles_summary = "\n".join([
            f"- {article.title}: {article.original_content[:300]}"
            for article in articles
        ])
        
        time_context = {
            "morning": "출근길에 읽을 수 있는 '오늘 뭘 봐야 하나?' 관점",
            "noon": "점심시간에 읽을 수 있는 '지금 뭐가 일어나고 있나?' 관점",
            "night": "퇴근길에 읽을 수 있는 '내일은 어떨까?' 전망 관점"
        }
        
        tone_instruction = time_context.get(slot, "객관적인 시장 흐름")
        
        prompt = f"""당신은 재미있고 통찰력 있는 시장 분석가입니다.
마치 친구한테 설명해주듯이, 자연스럽고 재미있게 브리핑하세요.

[카테고리] {category}
[시간대] {slot} ({tone_instruction})

[최근 기사 {len(articles)}개]
{articles_summary}

## 📊 당신의 역할:

### 톤 & 스타일:
- **출근길(morning)**: "오늘 이거 챙겨야 해요!" 식의 액션 제시
- **점심(noon)**: "지금 이렇게 흘러가고 있어요" 식의 현황 설명
- **퇴근(night)**: "내일 이거 나올 수 있어요" 식의 예측/전망

### ✅ 좋은 예시:

#### 아침 (출근길 - 행동성)
{{
    "category": "AI · 기술",
    "time_slot": "morning",
    "headline": "AI칩 수요 폭발, 반도체주는 '사이드 시트' 📈",
    "main_story": "엔비디아 투자 소식 + 국내 반도체 수급 개선 = 오늘 반도체주 주목. 삼성전자·SK하이닉스 오전장 흐름 체크 필수",
    "watch_points": [
        "삼성전자 오전장 강도 확인",
        "SK하이닉스 수급 변화",
        "해외 선물 영향도 체크"
    ],
    "related_stocks": ["삼성전자", "SK하이닉스", "엔비디아"],
    "mood": "positive",
    "investor_sentiment": "AI 수요 강세에 반도체 복구 기대. 오전장에 매수 심리 강할 듯"
}}

#### 점심 (장중 - 현황)
{{
    "category": "금융",
    "time_slot": "noon",
    "headline": "금리인상 신호에 금융주 약세... 오후는 어떨까? 🤔",
    "main_story": "오전장 기준 금융주가 약세 이어가는 중. 한은 발언 이후 시장 심리 꺾인 상태. 오후 해외 지표가 변수",
    "watch_points": [
        "오후 미국 경제지표 발표 (2시 예정)",
        "금융주 매도 강도 지속 여부",
        "환율 변화 추적"
    ],
    "related_stocks": ["KB금융", "신한지주", "하나금융"],
    "mood": "negative",
    "investor_sentiment": "금리인상 공포에 매도 심리. 오후 미국 지표가 해결책 될 수도"
}}

#### 저녁 (마감 후 - 전망)
{{
    "category": "에너지",
    "time_slot": "night",
    "headline": "유가 약세 지속, 내일 OPEC+ 회의가 변수 📺",
    "main_story": "오늘 유가 하락으로 에너지주 약세. 내일 OPEC+ 회의 결과에 따라 반전 가능. 밤사이 선물 추이 주목",
    "watch_points": [
        "밤사이 WTI유가 변화",
        "내일 OPEC+ 회의 결과",
        "한국 유가 연동성"
    ],
    "related_stocks": ["S-Oil", "SK이노베이션", "한국전력"],
    "mood": "neutral",
    "investor_sentiment": "유가 약세로 관망 중이지만, 내일 OPEC+ 회의에서 회복 신호 나올 가능성"
}}

## 🎯 핵심 규칙:

### ❌ 절대 금지:
1. 딱딱한 "보고서" 톤
2. 금리인상을 긍정으로 포장
3. 행동성 없는 설명만
4. 시간대 관계없이 같은 내용

### ✅ 반드시 포함:
1. **시간대에 맞는 톤** (아침/점심/저녁 다름)
2. **Watch Points** (구체적 행동 또는 관찰 포인트)
3. **변수 제시** (뭐가 바뀔 수 있나?)
4. **자연스러운 문체** (친구 조언 같은 느낌)

## 📋 JSON 응답:
{{
    "category": "{category}",
    "time_slot": "{slot}",
    "headline": "20자 이내 (이모지 1개)",
    "main_story": "2-3문장 (상황 설명 + 변수)",
    "watch_points": ["포인트1", "포인트2", "포인트3"],
    "related_stocks": ["종목1", "종목2", "종목3"],
    "mood": "positive|neutral|negative",
    "investor_sentiment": "2-3문장"
}}

JSON만 응답하세요 (설명 없음)
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
    
    def save_category_briefing(self, db, briefing_data: dict, articles: list, slot: str = "morning"):
        """카테고리 브리핑을 DB에 저장 (mood 정규화 + time_slot)"""
        
        if not briefing_data or not articles:
            return
        
        try:
            article = articles[0]
            
            # ✅ mood 값 정규화 (다양한 형식 대응)
            mood_raw = briefing_data.get("mood", "neutral")
            
            mood_map = {
                "긍정적": "positive",
                "중립": "neutral",
                "부정적": "negative",
                "positive": "positive",
                "neutral": "neutral",
                "negative": "negative"
            }
            
            # 정확한 매칭 먼저 시도
            mood_en = mood_map.get(mood_raw)
            
            # 없으면 소문자로 통일해서 시도
            if not mood_en:
                mood_lower = str(mood_raw).lower().strip()
                mood_en = mood_map.get(mood_lower, "neutral")
            
            # 그래도 없으면 기본값
            if not mood_en:
                mood_en = "neutral"
            
            logger.info(f"   mood 변환: '{mood_raw}' → '{mood_en}'")
            
            new_briefing = Briefing(
                article_id=article.id,
                ai_summary=briefing_data.get("headline", ""),
                main_story=briefing_data.get("main_story", ""),
                positive_points=briefing_data.get("watch_points", []),
                negative_points=[briefing_data.get("investor_sentiment", "")],
                related_stocks=briefing_data.get("related_stocks", []),
                related_sectors=[briefing_data.get("category", "")],
                mood=mood_en,
                time_slot=slot  # ✅ time_slot 저장
            )
            
            db.add(new_briefing)
            db.commit()
            logger.info(f"   💾 저장 완료 (분위기: {mood_en}, 시간대: {slot})\n")
            
        except Exception as e:
            db.rollback()
            logger.error(f"   저장 오류: {str(e)}\n")
    
    def process_categories(self, slot: str = "morning"):
        """카테고리별 재미있는 분석 (시간대별)"""
        db = SessionLocal()
        
        try:
            logger.info("\n" + "="*60)
            logger.info(f"📊 {slot.upper()} 브리핑 생성 시작")
            logger.info("="*60 + "\n")
            
            categorized_articles = self.get_articles_by_category(db)
            
            logger.info(f"\n분석할 카테고리: {len(categorized_articles)}개\n")
            
            if len(categorized_articles) == 0:
                logger.info("⏭️  분석할 신규 기사가 없습니다")
                return
            
            for category, articles in categorized_articles.items():
                if not articles:
                    continue
                
                logger.info(f"📂 {category} ({len(articles)}개 신규 기사)")
                
                briefing_data = self.generate_category_briefing(category, articles, slot=slot)
                
                if briefing_data:
                    self.save_category_briefing(db, briefing_data, articles, slot=slot)  # ✅ slot 파라미터 전달
                else:
                    logger.error(f"   ⚠️  분석 실패\n")
            
            logger.info("="*60)
            logger.info("✨ 브리핑 생성 완료!")
            logger.info("="*60 + "\n")
            
        except Exception as e:
            db.rollback()
            logger.error(f"처리 중 오류: {str(e)}")
        finally:
            db.close()


if __name__ == "__main__":
    generator = BriefingGenerator()
    generator.process_categories(slot="morning")