import os
import json
import logging
from anthropic import Anthropic
from database import SessionLocal, Article, Briefing
from datetime import datetime, timedelta
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = Anthropic()


class BriefingGenerator:
    """VibePick 재미있는 시장 분위기 브리핑"""
    
    def __init__(self):
        self.model = "claude-opus-4-6"
        self.max_tokens = 1000
    
    def is_weekend(self) -> bool:
        """KST 기준 주말 여부 확인"""
        kst_now = datetime.utcnow() + timedelta(hours=9)
        return kst_now.weekday() >= 5

    def get_weekend_type(self) -> str:
        """토요일인지 일요일인지 반환"""
        kst_now = datetime.utcnow() + timedelta(hours=9)
        return "saturday" if kst_now.weekday() == 5 else "sunday"

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
        
        logger.info(f"분析 대상 기사: {len(unanalyzed_articles)}개")
        
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
            text = (article.title + " " + article.original_content).lower()
            
            for cat, keywords in category_keywords.items():
                if any(kw.lower() in text for kw in keywords):
                    category = cat
                    break
            
            categorized[category].append(article)
        
        result = {}
        for cat, cat_articles in categorized.items():
            if cat == "기타":
                logger.info(f"⏭️  기타: {len(cat_articles)}개 (분析 스킵)")
                continue
            
            if len(cat_articles) >= 1:
                result[cat] = cat_articles[:10]
            else:
                logger.info(f"⏭️  {cat}: 기사 0개 (분析 스킵)")
        
        logger.info(f"📂 카테고리별 기사 그룹화: {len(result)}개 카테고리")
        for cat, arts in result.items():
            logger.info(f"   {cat}: {len(arts)}개 (신규)")
        
        return result
    
    def generate_category_briefing(self, category: str, articles: list, slot: str = "morning", weekend: bool = False, weekend_type: str = "saturday") -> dict:
        """카테고리별 브리핑 생성 (평일/주말, 시간대별 톤 분리)"""
        
        articles_summary = "\n".join([
            f"- {article.title}: {article.original_content[:300]}"
            for article in articles
        ])

        # ============ 주말 프롬프트 ============
        if weekend:
            if weekend_type == "saturday":
                tone_instruction = "이번 주 시장 총정리 + 다음 주 월요일 주목 포인트 관점"
                action_guide = """
- 이번 주 해당 카테고리의 주요 흐름을 한 줄로 정리
- 다음 주 월요일 장에서 주목할 변수 제시
- '오늘 장', '장 시작' 같은 표현 절대 사용 금지
- '이번 주', '다음 주', '월요일' 중심 표현 사용
"""
                slot_examples = """
{
    "category": "AI · 기술",
    "time_slot": "morning",
    "headline": "이번 주 반도체 강세, 월요일도 주목 📈",
    "main_story": "이번 주 엔비디아 투자 확대 소식에 국내 반도체주도 강세로 마감. 삼성전자·SK하이닉스는 엔비디아에 메모리를 납품하는 회사라 직접 수혜를 받아요. 다음 주 엔비디아 실적 발표 결과에 따라 월요일 분위기가 확 바뀔 수 있어요.",
    "watch_points": [
        "월요일 엔비디아 실적 발표 — 예상 상회 시 추가 상승 가능",
        "주말 사이 해외 AI 관련 뉴스",
        "삼성전자·SK하이닉스 월요일 수급 변화"
    ],
    "related_stocks": ["삼성전자", "SK하이닉스", "한미반도체"],
    "mood": "positive",
    "investor_sentiment": "이번 주 강세 이어받아 월요일 좋게 출발할 가능성이 높아요. 단, 엔비디아 실적이 기대 하회 시 차익실현 물량 주의."
}"""
            else:  # sunday
                tone_instruction = "주말 글로벌 이슈 정리 + 내일(월요일) 체크포인트 관점"
                action_guide = """
- 주말 사이 글로벌 이슈 중심으로 정리
- 내일 월요일 장 시작 전 확인해야 할 것들 제시
- '오늘 장' 표현 금지, '내일', '월요일 장' 표현 사용
- 투자자가 일요일 밤에 읽는다는 걸 고려해 준비성 강조
"""
                slot_examples = """
{
    "category": "글로벌",
    "time_slot": "morning",
    "headline": "미국 고용 호조, 월요일 코스피 변수 🌏",
    "main_story": "주말 사이 미국 고용지표가 예상을 웃돌며 달러 강세. 달러 강세는 원화 약세로 이어져 외국인 매도 압력이 높아질 수 있어요. 내일 월요일 코스피는 환율 영향 받으며 약보합 출발 가능성이 있어요.",
    "watch_points": [
        "월요일 달러/원 환율 — 1,380원 넘으면 외국인 매도 압력 커질 수 있어요",
        "미국 선물 시장 밤사이 동향",
        "중국 증시 개장 반응"
    ],
    "related_stocks": ["삼성전자", "현대차", "POSCO홀딩스"],
    "mood": "neutral",
    "investor_sentiment": "달러 강세로 외국인 매도 우려. 월요일 장 초반 환율 안정 여부가 관건이에요."
}"""

            prompt = f"""당신은 재미있고 통찰력 있는 시장 분析가입니다.
마치 친구한테 설명해주듯이, 자연스럽고 재미있게 브리핑하세요.
오늘은 {'토요일' if weekend_type == 'saturday' else '일요일'}로 국내 주식시장 휴장일입니다.

[카테고리] {category}
[오늘] {'토요일 - 이번 주 정리 + 다음 주 프리뷰' if weekend_type == 'saturday' else '일요일 - 글로벌 이슈 + 월요일 준비'}
[관점] {tone_instruction}

[최근 기사 {len(articles)}개]
{articles_summary}

## 작성 가이드:
{action_guide}

## 좋은 예시:
{slot_examples}

## 핵심 규칙:
- 장이 없는 날이므로 '오늘 장', '오전장', '장 시작' 표현 절대 금지
- {'이번 주 흐름 요약 + 다음 주 월요일 주목 포인트' if weekend_type == 'saturday' else '주말 글로벌 이슈 + 내일 월요일 체크리스트'} 중심
- 딱딱한 보고서 톤 금지, 자연스러운 문체
- headline은 20자 이내, 이모지 1개
- watch_points는 2~4개

## JSON 응답:
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

        # ============ 평일 프롬프트 (원래 버전) ============
        else:
            time_context = {
                "morning": "출근길에 읽을 수 있는 '오늘 뭘 봐야 하나?' 관점",
                "noon": "점심시간에 읽을 수 있는 '지금 뭐가 일어나고 있나?' 관점",
                "night": "퇴근길에 읽을 수 있는 '내일은 어떨까?' 전망 관점"
            }
            tone_instruction = time_context.get(slot, "객관적인 시장 흐름")

            prompt = f"""당신은 재미있고 통찰력 있는 시장 분析가입니다.
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
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text.strip()
            
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            briefing_data = json.loads(response_text)
            
            logger.info(f"✅ {category} 분析 완료")
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
        """카테고리 브리핑을 DB에 저장"""
        
        if not briefing_data or not articles:
            return
        
        try:
            article = articles[0]
            
            mood_raw = briefing_data.get("mood", "neutral")
            mood_map = {
                "긍정적": "positive",
                "중립": "neutral",
                "부정적": "negative",
                "positive": "positive",
                "neutral": "neutral",
                "negative": "negative"
            }
            
            mood_en = mood_map.get(mood_raw)
            if not mood_en:
                mood_en = mood_map.get(str(mood_raw).lower().strip(), "neutral")
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
                time_slot=slot
            )
            
            db.add(new_briefing)
            db.commit()
            logger.info(f"   💾 저장 완료 (분위기: {mood_en}, 시간대: {slot})\n")
            
        except Exception as e:
            db.rollback()
            logger.error(f"   저장 오류: {str(e)}\n")
    
    def process_categories(self, slot: str = "morning"):
        """카테고리별 브리핑 생성 (평일/주말 자동 감지)"""
        db = SessionLocal()
        
        try:
            weekend = self.is_weekend()
            weekend_type = self.get_weekend_type() if weekend else None

            logger.info("\n" + "="*60)
            if weekend:
                logger.info(f"📊 {slot.upper()} 브리핑 생성 시작 ({'토요일' if weekend_type == 'saturday' else '일요일'} - 주말 모드)")
            else:
                logger.info(f"📊 {slot.upper()} 브리핑 생성 시작 (평일 모드)")
            logger.info("="*60 + "\n")
            
            categorized_articles = self.get_articles_by_category(db)
            
            logger.info(f"\n분析할 카테고리: {len(categorized_articles)}개\n")
            
            if len(categorized_articles) == 0:
                logger.info("⏭️  분析할 신규 기사가 없습니다")
                return
            
            for category, articles in categorized_articles.items():
                if not articles:
                    continue
                
                logger.info(f"📂 {category} ({len(articles)}개 신규 기사)")
                
                briefing_data = self.generate_category_briefing(
                    category, articles,
                    slot=slot,
                    weekend=weekend,
                    weekend_type=weekend_type
                )
                
                if briefing_data:
                    self.save_category_briefing(db, briefing_data, articles, slot=slot)
                else:
                    logger.error(f"   ⚠️  분析 실패\n")
            
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