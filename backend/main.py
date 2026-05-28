from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import os
import asyncio

from database import get_db, init_db, Article, Briefing, User, UserInterest, Stock, SessionLocal
from crawler import NewsCrawler
from briefing_generator import BriefingGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 초기화
app = FastAPI(title="Vivepick Backend", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Pydantic 모델 ============

class BriefingResponse(BaseModel):
    """브리핑 응답 모델"""
    id: int
    title: str
    main_story: str
    positive_points: list
    negative_points: list
    related_stocks: list
    related_sectors: list
    mood: str
    time_slot: str
    published_at: datetime
    
    class Config:
        from_attributes = True


class UserInterestsRequest(BaseModel):
    """사용자 관심 저장 요청"""
    interested_stocks: list = []
    interested_sectors: list = []
    interested_markets: list = []


class UserInterestsResponse(BaseModel):
    """사용자 관심 응답"""
    interested_stocks: list
    interested_sectors: list
    interested_markets: list


# ============ API 엔드포인트 ============

@app.on_event("startup")
async def startup_event():
    """앱 시작 시 실행"""
    logger.info("🚀 Vivepick 백엔드 시작")
    try:
        init_db()
        logger.info("✅ 데이터베이스 초기화 성공")
    except Exception as e:
        logger.warning(f"⚠️ DB 초기화 실패 (개발 모드): {e}")
    start_scheduler()


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "ok", "timestamp": datetime.utcnow()}


# ============ 크롤링 테스트 ============

@app.get("/trigger-crawl")
async def trigger_crawl():
    """백그라운드 크롤링 실행"""
    try:
        asyncio.create_task(asyncio.to_thread(run_crawl_and_generate))
        logger.info("🧪 테스트 크롤링 시작 (백그라운드)")
        return {
            "status": "crawling_started",
            "message": "백그라운드에서 크롤링 시작됨. 1-2분 후 /briefings에서 데이터 확인",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"❌ 크롤링 시작 실패: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "message": "크롤링 시작 실패"
        }


# ============ 브리핑 조회 ============

@app.get("/briefings", response_model=list[BriefingResponse])
async def get_briefings(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    time_slot: str = Query(None),
    sectors: list = Query(None),
    stocks: list = Query(None),
    mood: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    브리핑 목록 조회 (필터링 가능)
    
    Parameters:
    - limit: 조회 개수 (기본 20, 최대 100)
    - offset: 스킵할 개수
    - time_slot: 시간대 필터 (morning, noon, night)
    - sectors: 섹터 필터
    - stocks: 종목 필터
    - mood: 분위기 필터 (positive, neutral, negative)
    """
    
    query = db.query(Briefing).join(Article)
    
    if time_slot:
        query = query.filter(Briefing.time_slot == time_slot)
    
    if sectors:
        query = query.filter(Briefing.related_sectors.overlap(sectors))
    
    if stocks:
        query = query.filter(Briefing.related_stocks.overlap(stocks))
    
    if mood:
        query = query.filter(Briefing.mood == mood)
    
    briefings = query.order_by(
        Briefing.generated_at.desc()
    ).offset(offset).limit(limit).all()
    
    response = []
    for b in briefings:
        response.append({
            "id": b.id,
            "title": b.ai_summary,
            "main_story": b.main_story or "",
            "positive_points": b.positive_points,
            "negative_points": b.negative_points,
            "related_stocks": b.related_stocks,
            "related_sectors": b.related_sectors,
            "mood": b.mood or "neutral",
            "time_slot": b.time_slot or "morning",
            "published_at": b.article.crawled_at
        })
    
    return response


@app.get("/briefings/{briefing_id}", response_model=BriefingResponse)
async def get_briefing_detail(briefing_id: int, db: Session = Depends(get_db)):
    """특정 브리핑 상세 조회"""
    briefing = db.query(Briefing).filter(Briefing.id == briefing_id).first()
    
    if not briefing:
        raise HTTPException(status_code=404, detail="브리핑을 찾을 수 없습니다")
    
    return {
        "id": briefing.id,
        "title": briefing.ai_summary,
        "main_story": briefing.main_story or "",
        "positive_points": briefing.positive_points,
        "negative_points": briefing.negative_points,
        "related_stocks": briefing.related_stocks,
        "related_sectors": briefing.related_sectors,
        "mood": briefing.mood or "neutral",
        "time_slot": briefing.time_slot or "morning",
        "published_at": briefing.article.crawled_at
    }


# ============ 사용자 관심 설정 ============

@app.post("/users/{user_id}/interests", response_model=UserInterestsResponse)
async def save_user_interests(
    user_id: str,
    interests: UserInterestsRequest,
    db: Session = Depends(get_db)
):
    """사용자 관심 태그 저장"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, email=f"user_{user_id}@vivepick.app")
        db.add(user)
        db.commit()
    
    user_interest = db.query(UserInterest).filter(
        UserInterest.user_id == user_id
    ).first()
    
    if user_interest:
        user_interest.interested_stocks = interests.interested_stocks
        user_interest.interested_sectors = interests.interested_sectors
        user_interest.interested_markets = interests.interested_markets
        user_interest.updated_at = datetime.utcnow()
    else:
        user_interest = UserInterest(
            user_id=user_id,
            interested_stocks=interests.interested_stocks,
            interested_sectors=interests.interested_sectors,
            interested_markets=interests.interested_markets
        )
        db.add(user_interest)
    
    db.commit()
    
    return {
        "interested_stocks": user_interest.interested_stocks,
        "interested_sectors": user_interest.interested_sectors,
        "interested_markets": user_interest.interested_markets
    }


@app.get("/users/{user_id}/interests", response_model=UserInterestsResponse)
async def get_user_interests(user_id: str, db: Session = Depends(get_db)):
    """사용자 관심 태그 조회"""
    
    user_interest = db.query(UserInterest).filter(
        UserInterest.user_id == user_id
    ).first()
    
    if not user_interest:
        return {
            "interested_stocks": [],
            "interested_sectors": [],
            "interested_markets": []
        }
    
    return {
        "interested_stocks": user_interest.interested_stocks,
        "interested_sectors": user_interest.interested_sectors,
        "interested_markets": user_interest.interested_markets
    }


@app.get("/users/{user_id}/briefings", response_model=list[BriefingResponse])
async def get_user_personalized_briefings(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    time_slot: str = Query(None),
    db: Session = Depends(get_db)
):
    """사용자 맞춤형 브리핑 조회"""
    
    user_interest = db.query(UserInterest).filter(
        UserInterest.user_id == user_id
    ).first()
    
    query = db.query(Briefing)
    
    if time_slot:
        query = query.filter(Briefing.time_slot == time_slot)
    
    if user_interest and (user_interest.interested_sectors or user_interest.interested_stocks):
        query = query.filter(
            (Briefing.related_sectors.overlap(user_interest.interested_sectors)) |
            (Briefing.related_stocks.overlap(user_interest.interested_stocks))
        )
    
    briefings = query.order_by(
        Briefing.generated_at.desc()
    ).offset(offset).limit(limit).all()
    
    response = []
    for b in briefings:
        response.append({
            "id": b.id,
            "title": b.ai_summary,
            "main_story": b.main_story or "",
            "positive_points": b.positive_points,
            "negative_points": b.negative_points,
            "related_stocks": b.related_stocks,
            "related_sectors": b.related_sectors,
            "mood": b.mood or "neutral",
            "time_slot": b.time_slot or "morning",
            "published_at": b.article.crawled_at
        })
    
    return response


# ============ 통계 ============

@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """기본 통계"""
    total_articles = db.query(Article).count()
    total_briefings = db.query(Briefing).count()
    total_users = db.query(User).count()
    
    positive_count = db.query(Briefing).filter(Briefing.mood == "positive").count()
    neutral_count = db.query(Briefing).filter(Briefing.mood == "neutral").count()
    negative_count = db.query(Briefing).filter(Briefing.mood == "negative").count()
    
    morning_count = db.query(Briefing).filter(Briefing.time_slot == "morning").count()
    noon_count = db.query(Briefing).filter(Briefing.time_slot == "noon").count()
    night_count = db.query(Briefing).filter(Briefing.time_slot == "night").count()
    
    return {
        "total_articles": total_articles,
        "total_briefings": total_briefings,
        "total_users": total_users,
        "briefing_coverage": f"{(total_briefings/max(total_articles, 1)*100):.1f}%",
        "mood_distribution": {
            "positive": positive_count,
            "neutral": neutral_count,
            "negative": negative_count
        },
        "time_slot_distribution": {
            "morning": morning_count,
            "noon": noon_count,
            "night": night_count
        }
    }


# ============ 스케줄러 ============

def run_crawl_and_generate(slot: str = "morning"):
    """크롤링 + 브리핑 생성 작업"""
    logger.info("\n" + "="*50)
    logger.info(f"⏰ {slot.upper()} 자동 스케줄 실행")
    logger.info("="*50 + "\n")
    
    try:
        crawler = NewsCrawler()
        crawler.run_crawl()
    except Exception as e:
        logger.error(f"❌ 크롤링 실패: {str(e)}")
    
    try:
        generator = BriefingGenerator()
        generator.process_categories(slot=slot)
    except Exception as e:
        logger.error(f"❌ 브리핑 생성 실패: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


def clean_previous_day_data():
    """자동 정리 함수 - 자정마다 전날 데이터 삭제"""
    db = SessionLocal()
    try:
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        logger.info("\n" + "="*50)
        logger.info("🧹 자정 정리 시작")
        logger.info("="*50 + "\n")
        
        # briefings 정리
        briefing_count = db.query(Briefing).filter(
            Briefing.generated_at < yesterday
        ).delete()
        
        # articles 정리
        article_count = db.query(Article).filter(
            Article.crawled_at < yesterday
        ).delete()
        
        db.commit()
        
        logger.info(f"✅ 정리 완료: briefing {briefing_count}개, article {article_count}개 삭제")
        logger.info("="*50 + "\n")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 정리 실패: {str(e)}")
    finally:
        db.close()


scheduler = None

def start_scheduler():
    """백그라운드 스케줄러 시작"""
    global scheduler
    
    scheduler = BackgroundScheduler()
    
    # 하루 3회: 09:00 (아침), 13:00 (점심), 17:00 (저녁)
    scheduler.add_job(
        lambda: run_crawl_and_generate(slot="morning"),
        'cron',
        hour='9',
        minute='0',
        timezone='Asia/Seoul'
    )
    
    scheduler.add_job(
        lambda: run_crawl_and_generate(slot="noon"),
        'cron',
        hour='13',
        minute='0',
        timezone='Asia/Seoul'
    )
    
    scheduler.add_job(
        lambda: run_crawl_and_generate(slot="night"),
        'cron',
        hour='17',
        minute='0',
        timezone='Asia/Seoul'
    )
    
    # ✅ 자정마다 전날 데이터 정리
    scheduler.add_job(
        clean_previous_day_data,
        'cron',
        hour='0',
        minute='0',
        timezone='Asia/Seoul'
    )
    
    scheduler.start()
    logger.info("✅ 스케줄러 시작 (09:00/13:00/17:00 크롤링 + 00:00 정리)")


@app.on_event("shutdown")
async def shutdown_event():
    """앱 종료 시"""
    if scheduler:
        scheduler.shutdown()
    logger.info("🛑 Vivepick 백엔드 종료")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development"
    )