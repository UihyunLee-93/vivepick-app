from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import os

from database import get_db, init_db, Article, Briefing, User, UserInterest, Stock
from crawler import NewsCrawler
from briefing_generator import BriefingGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 초기화
app = FastAPI(title="Vivepick Backend", version="1.0.0")

# CORS 설정 (Swift 앱에서 호출 가능하도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Pydantic 모델 ============

class BriefingResponse(BaseModel):
    """브리핑 응답 모델"""
    id: int
    title: str
    summary: str
    positive_points: list
    negative_points: list
    related_stocks: list
    related_sectors: list
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
    #init_db()
    start_scheduler()


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "ok", "timestamp": datetime.utcnow()}


# ============ 브리핑 조회 ============

@app.get("/briefings", response_model=list[BriefingResponse])
async def get_briefings(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sectors: list = Query(None),
    stocks: list = Query(None),
    db: Session = Depends(get_db)
):
    """
    브리핑 목록 조회 (필터링 가능)
    
    Parameters:
    - limit: 조회 개수 (기본 20, 최대 100)
    - offset: 스킵할 개수
    - sectors: 섹터 필터 (예: ["반도체", "2차전지"])
    - stocks: 종목 필터 (예: ["삼성전자", "SK하이닉스"])
    """
    
    query = db.query(Briefing).join(Article)
    
    # 섹터 필터링
    if sectors:
        query = query.filter(
            Briefing.related_sectors.overlap(sectors)
        )
    
    # 종목 필터링
    if stocks:
        query = query.filter(
            Briefing.related_stocks.overlap(stocks)
        )
    
    briefings = query.order_by(
        Briefing.generated_at.desc()
    ).offset(offset).limit(limit).all()
    
    # 응답 포맷팅
    response = []
    for b in briefings:
        response.append({
            "id": b.id,
            "title": b.article.title,
            "summary": b.ai_summary,
            "positive_points": b.positive_points,
            "negative_points": b.negative_points,
            "related_stocks": b.related_stocks,
            "related_sectors": b.related_sectors,
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
        "title": briefing.article.title,
        "summary": briefing.ai_summary,
        "positive_points": briefing.positive_points,
        "negative_points": briefing.negative_points,
        "related_stocks": briefing.related_stocks,
        "related_sectors": briefing.related_sectors,
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
    
    # 사용자 확인 또는 생성
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, email=f"user_{user_id}@vivepick.app")
        db.add(user)
        db.commit()
    
    # 관심 데이터 업데이트 또는 생성
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
    db: Session = Depends(get_db)
):
    """
    사용자 맞춤형 브리핑 조회
    (사용자의 관심 태그 기반 필터링)
    """
    
    # 사용자 관심 데이터 조회
    user_interest = db.query(UserInterest).filter(
        UserInterest.user_id == user_id
    ).first()
    
    if not user_interest:
        # 관심 데이터가 없으면 최신 브리핑만 반환
        briefings = db.query(Briefing).order_by(
            Briefing.generated_at.desc()
        ).offset(offset).limit(limit).all()
    else:
        # 관심 섹터/종목 기반 필터링
        query = db.query(Briefing)
        
        if user_interest.interested_sectors or user_interest.interested_stocks:
            query = query.filter(
                (Briefing.related_sectors.overlap(user_interest.interested_sectors)) |
                (Briefing.related_stocks.overlap(user_interest.interested_stocks))
            )
        
        briefings = query.order_by(
            Briefing.generated_at.desc()
        ).offset(offset).limit(limit).all()
    
    # 응답 포맷팅
    response = []
    for b in briefings:
        response.append({
            "id": b.id,
            "title": b.article.title,
            "summary": b.ai_summary,
            "positive_points": b.positive_points,
            "negative_points": b.negative_points,
            "related_stocks": b.related_stocks,
            "related_sectors": b.related_sectors,
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
    
    return {
        "total_articles": total_articles,
        "total_briefings": total_briefings,
        "total_users": total_users,
        "briefing_coverage": f"{(total_briefings/max(total_articles, 1)*100):.1f}%"
    }


# ============ 스케줄러 ============

def run_crawl_and_generate():
    """크롤링 + 브리핑 생성 작업"""
    logger.info("\n" + "="*50)
    logger.info("⏰ 자동 스케줄 실행 시작")
    logger.info("="*50 + "\n")
    
    # 크롤링
    crawler = NewsCrawler()
    crawler.run_crawl()
    
    # 브리핑 생성
    generator = BriefingGenerator()
    generator.process_articles(limit=10)


scheduler = None

def start_scheduler():
    """백그라운드 스케줄러 시작"""
    global scheduler
    
    scheduler = BackgroundScheduler()
    
    # 하루 3회: 09:00, 13:00, 17:00
    scheduler.add_job(
        run_crawl_and_generate,
        'cron',
        hour='9,13,17',
        minute='0',
        timezone='Asia/Seoul'
    )
    
    scheduler.start()
    logger.info("✅ 스케줄러 시작 (09:00, 13:00, 17:00 KST에 자동 실행)")


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
