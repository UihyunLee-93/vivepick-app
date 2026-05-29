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
        
        logger.info(f"분석 대상 기사: {len(unanalyzed_articles)}개")
        
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
            
            # 최소 2개 이상 기사일 때만 트렌드 분석
            if len(cat_articles) >= 2:
                result[cat] = cat_articles[:10]
            else:
                logger.info(f"⏭️  {cat}: 기사 {len(cat_articles)}개 (2개 미만, 분析 스킵)")
        
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

        # 공통 초보자 친화 규칙
        beginner_rules = """
### 🔑 초보자 친화 규칙 (반드시 준수):
- 전문용어는 반드시 괄호로 쉽게 설명
  예) 수급(주식을 사려는 사람 vs 팔려는 사람의 비율)
  예) 금리인상(돈 빌리는 비용이 올라가는 것)
  예) 외국인 순매수(외국 투자자들이 우리 주식을 더 많이 사고 있다는 뜻)
- 인과관계를 "A가 일어나서 → B가 되고 있어요" 형식으로 명확하게
  예) "미국이 금리를 올리면서 → 달러 강세 → 원화 약세 → 수출주에 유리한 환경"
- 숫자보다 체감 표현 활용
  예) "3.2% 상승" → "꽤 크게 올랐어요"
  예) "거래대금 2조" → "오늘 유독 많은 사람들이 이 주식을 거래했어요"
- 뉴스 배경 한 줄 설명 (왜 이게 중요한지 맥락 제공)
  예) "OPEC+는 전 세계 석유 생산량을 결정하는 모임이에요. 여기서 감산 결정이 나오면 유가가 올라요"
  예) "엔비디아는 AI 학습에 필요한 칩을 독점적으로 만드는 회사예요"
- 바이브(분위기)를 생생하게 전달
  예) "지금 시장은 살짝 겁먹은 분위기예요"
  예) "투자자들이 '이거 진짜 되는 거야?' 하면서 반신반의 중"
  예) "오늘 이 섹터는 확실히 주인공이에요"
"""

        # ============ 주말 프롬프트 ============
        if weekend:
            if weekend_type == "saturday":
                tone_instruction = "이번 주 시장 총정리 + 다음 주 월요일 주목 포인트 관점"
                action_guide = """
- 이번 주 해당 카테고리의 주요 흐름을 한 줄로 정리
- 다음 주 월요일 장에서 주목할 변수 제시
- '오늘 장', '장 시작' 같은 표현 절대 사용 금지
- '이번 주', '다음 주', '월요일' 중심 표현 사용
- 왜 이번 주 이 카테고리가 움직였는지 배경 설명 포함
"""
                slot_examples = """
{
    "category": "AI · 기술",
    "time_slot": "morning",
    "headline": "이번 주 반도체 강세, 월요일도 주목 📈",
    "main_story": "이번 주 엔비디아(AI 칩을 독점 생산하는 미국 회사)가 대규모 투자 계획을 발표하면서 → 국내 반도체주도 덩달아 올랐어요. 삼성전자·SK하이닉스는 엔비디아에 메모리 칩을 납품하는 회사라 직접적인 수혜를 받거든요. 다음 주 월요일엔 엔비디아 실적 발표가 있어서 결과에 따라 분위기가 확 바뀔 수 있어요.",
    "watch_points": [
        "월요일 엔비디아 실적 발표 — 예상보다 좋으면 반도체주 추가 상승 가능",
        "주말 사이 미국 AI 관련 뉴스 체크",
        "삼성전자·SK하이닉스 월요일 오전장 수급(사는 사람 많은지) 확인"
    ],
    "related_stocks": ["삼성전자", "SK하이닉스", "한미반도체"],
    "mood": "positive",
    "investor_sentiment": "이번 주 강세 흐름 이어받아 월요일 좋게 출발할 가능성이 높아요. 단, 엔비디아 실적이 기대보다 낮으면 차익실현(이익 챙기고 파는 것) 물량이 쏟아질 수 있으니 주의하세요."
}"""
            else:  # sunday
                tone_instruction = "주말 글로벌 이슈 정리 + 내일(월요일) 체크포인트 관점"
                action_guide = """
- 주말 사이 글로벌 이슈 중심으로 정리
- 내일 월요일 장 시작 전 확인해야 할 것들 제시
- '오늘 장' 표현 금지, '내일', '월요일 장' 표현 사용
- 투자자가 일요일 밤에 읽는다는 걸 고려해 준비성 강조
- 처음 투자하는 사람도 이해할 수 있게 배경 설명 포함
"""
                slot_examples = """
{
    "category": "글로벌",
    "time_slot": "morning",
    "headline": "미국 고용 호조, 월요일 코스피 변수 🌏",
    "main_story": "주말 사이 미국에서 일자리가 예상보다 많이 늘었다는 소식이 나왔어요. 언뜻 좋은 뉴스 같지만 → 고용이 좋으면 미국이 금리(돈 빌리는 비용)를 더 올릴 수 있다는 뜻이라 → 달러가 강해지고 → 원화가 약해져요. 원화 약세는 외국인 투자자들이 한국 주식을 팔게 만드는 요인이에요. 내일 월요일 코스피(한국 주식시장)는 약간 눌리며 시작할 가능성이 있어요.",
    "watch_points": [
        "월요일 환율(달러/원) — 1,380원 넘으면 외국인 매도 압력 커질 수 있어요",
        "미국 선물 시장 동향 — 밤사이 어떻게 움직였는지 확인",
        "중국 증시 개장 반응 체크"
    ],
    "related_stocks": ["삼성전자", "현대차", "POSCO홀딩스"],
    "mood": "neutral",
    "investor_sentiment": "달러 강세로 외국인들이 한국 주식을 팔 수 있어요. 월요일 장 초반 환율이 안정되는지가 핵심이에요. 겁먹을 필요는 없고, 월요일 오전 흐름 보고 대응해도 늦지 않아요."
}"""

            prompt = f"""당신은 주식 초보자도 이해할 수 있게 설명해주는 친근한 시장 분석가예요.
오늘은 {'토요일' if weekend_type == 'saturday' else '일요일'}로 국내 주식시장 휴장일이에요.
마치 친한 친구가 카카오톡으로 설명해주듯이 편하고 자연스럽게 써주세요.

[카테고리] {category}
[오늘] {'토요일 - 이번 주 정리 + 다음 주 프리뷰' if weekend_type == 'saturday' else '일요일 - 글로벌 이슈 + 월요일 준비'}
[관점] {tone_instruction}

[최근 기사 {len(articles)}개]
{articles_summary}

## 작성 가이드:
{action_guide}

{beginner_rules}

## 좋은 예시:
{slot_examples}

## 핵심 규칙:
- 장이 없는 날이므로 '오늘 장', '오전장', '장 시작' 표현 절대 금지
- {'이번 주 흐름 요약 + 다음 주 월요일 주목 포인트' if weekend_type == 'saturday' else '주말 글로벌 이슈 + 내일 월요일 체크리스트'} 중심
- headline은 30자 이내, 이모지 1개
- watch_points는 2~4개, 각각 왜 봐야 하는지 한 줄 이유 포함
- main_story는 3문장, 인과관계 흐름으로

## JSON 응답:
{{
    "category": "{category}",
    "time_slot": "{slot}",
    "headline": "30자 이내 (이모지 1개)",
    "main_story": "3문장 (배경 → 현재 상황 → 변수)",
    "watch_points": ["포인트1 — 이유", "포인트2 — 이유", "포인트3 — 이유"],
    "related_stocks": ["종목1", "종목2", "종목3"],
    "mood": "positive|neutral|negative",
    "investor_sentiment": "2-3문장 (초보자도 이해할 수 있게)"
}}

JSON만 응답하세요 (설명 없음)
"""

        # ============ 평일 프롬프트 ============
        else:
            time_context = {
                "morning": {
                    "desc": "출근길에 읽는 '오늘 뭘 봐야 하나?' 관점",
                    "tone": "아침(morning): '오늘 이거 챙겨야 해요!' 식의 액션 중심. 2문장으로 짧고 임팩트 있게",
                    "story_guide": "배경(왜 이슈인지) → 오늘 주목 포인트"
                },
                "noon": {
                    "desc": "점심시간에 읽는 '지금 뭐가 일어나고 있나?' 관점",
                    "tone": "점심(noon): '지금 이렇게 흘러가고 있어요' 식의 현황 설명. 3문장으로 상황 묘사",
                    "story_guide": "현재 상황 → 왜 이렇게 됐는지 → 오후 변수"
                },
                "night": {
                    "desc": "퇴근길에 읽는 '내일은 어떨까?' 전망 관점",
                    "tone": "저녁(night): '내일 이거 나올 수 있어요' 식의 예측/전망. 3문장으로 오늘 정리 + 내일 전망",
                    "story_guide": "오늘 흐름 정리 → 변수 → 내일 전망"
                }
            }
            ctx = time_context.get(slot, time_context["morning"])

            prompt = f"""당신은 주식 초보자도 이해할 수 있게 설명해주는 친근한 시장 분석가예요.
마치 친한 친구가 카카오톡으로 설명해주듯이 편하고 자연스럽게 써주세요.

[카테고리] {category}
[시간대] {slot} — {ctx['desc']}

[최근 기사 {len(articles)}개]
{articles_summary}

## 톤 & 스타일:
- {ctx['tone']}
- main_story 흐름: {ctx['story_guide']}

{beginner_rules}

## ✅ 좋은 예시:

#### 아침
{{
    "category": "AI · 기술",
    "time_slot": "morning",
    "headline": "AI 칩 수요 폭발, 반도체주 오늘 주목 📈",
    "main_story": "챗GPT 같은 AI 서비스가 늘어나면서 → AI 학습에 필요한 칩(반도체) 주문이 폭발적으로 늘고 있어요. 삼성전자·SK하이닉스는 그 칩을 만드는 회사라 오늘 오전장 흐름이 기대돼요.",
    "watch_points": [
        "삼성전자 오전 수급(사는 사람 많은지) 확인 — 외국인이 사면 강세 신호",
        "SK하이닉스 거래량 변화 — 평소보다 많으면 관심 집중된 것",
        "미국 선물 시장 분위기 — 밤사이 나스닥이 올랐으면 긍정적 출발 가능"
    ],
    "related_stocks": ["삼성전자", "SK하이닉스", "한미반도체"],
    "mood": "positive",
    "investor_sentiment": "AI 열풍이 계속되면서 반도체주에 매수(사려는) 심리가 강해요. 오전장에 기관(대형 투자회사)과 외국인이 같이 사면 더 강하게 올라갈 수 있어요."
}}

#### 점심
{{
    "category": "금융",
    "time_slot": "noon",
    "headline": "금리인상 신호에 금융주 약세 중 🤔",
    "main_story": "오전에 한국은행이 금리(돈 빌리는 비용)를 더 올릴 수 있다는 신호를 줬어요 → 금리가 오르면 은행 수익은 늘지만 대출받은 사람들이 힘들어져서 경기가 안 좋아질 수 있다는 우려 → 금융주가 약세예요. 오후 2시 미국 경제지표 발표가 분위기를 바꿀 수 있어요.",
    "watch_points": [
        "오후 2시 미국 경제지표 — 좋게 나오면 금융주 반등 가능",
        "KB금융·신한지주 매도 강도 — 계속 팔리면 오후도 약세",
        "달러/원 환율 변화 — 환율 오르면 외국인 추가 매도 가능"
    ],
    "related_stocks": ["KB금융", "신한지주", "하나금융"],
    "mood": "negative",
    "investor_sentiment": "금리인상 우려로 지금 투자자들이 금융주를 팔고 있어요. 오후 미국 지표가 예상보다 좋게 나오면 분위기가 반전될 수 있으니 조금 더 지켜봐도 괜찮아요."
}}

#### 저녁
{{
    "category": "에너지",
    "time_slot": "night",
    "headline": "유가 약세, 내일 OPEC+ 결과가 변수 📺",
    "main_story": "오늘 국제유가(원유 가격)가 내리면서 에너지 관련 주식들도 약세로 마감했어요. OPEC+(전 세계 주요 산유국들의 모임 — 여기서 석유 생산량을 결정해요)가 내일 회의를 여는데, 감산(생산 줄이기) 결정이 나오면 유가가 다시 오를 수 있어요.",
    "watch_points": [
        "내일 OPEC+ 회의 결과 — 감산 결정 나오면 에너지주 반등 신호",
        "밤사이 WTI(미국산 원유) 가격 변화",
        "S-Oil·SK이노베이션 내일 오전 반응"
    ],
    "related_stocks": ["S-Oil", "SK이노베이션", "한국전력"],
    "mood": "neutral",
    "investor_sentiment": "오늘은 약세였지만 내일 OPEC+ 회의 결과에 따라 분위기가 완전히 바뀔 수 있어요. 지금 당장 팔기보다 내일 회의 결과 확인 후 대응하는 게 나을 것 같아요."
}}

## 핵심 규칙:
- 딱딱한 보고서 톤 절대 금지
- 나쁜 소식을 긍정으로 포장 금지 (있는 그대로)
- headline은 30자 이내, 이모지 1개
- watch_points는 2~4개, 각각 "포인트 — 왜 봐야 하는지 이유" 형식
- 전문용어 나올 때마다 괄호로 설명

## JSON 응답:
{{
    "category": "{category}",
    "time_slot": "{slot}",
    "headline": "30자 이내 (이모지 1개)",
    "main_story": "{ctx['story_guide']} 흐름으로",
    "watch_points": ["포인트1 — 이유", "포인트2 — 이유", "포인트3 — 이유"],
    "related_stocks": ["종목1", "종목2", "종목3"],
    "mood": "positive|neutral|negative",
    "investor_sentiment": "2-3문장 (초보자도 이해할 수 있게)"
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