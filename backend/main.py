from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import engine, Base, get_db, Article, Briefing
from crawler import NewsCrawler
from briefing_generator import BriefingGenerator
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
import asyncio
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DB 초기화
Base.metadata.create_all(bind=engine)

app = FastAPI(title="VibePick API")

# 스케줄러 (startup에서 초기화)
scheduler = None

def crawl_and_generate():
    """크롤링 + 카테고리별 브리핑 생성"""
    logger.info("\n" + "="*50)
    logger.info("⏰ 자동 스케줄 실행 시작")
    logger.info("="*50)
    
    try:
        # 크롤링
        crawler = NewsCrawler()
        crawler.run_crawl()
        
        # ✅ 카테고리별 종합 분석 브리핑 생성
        generator = BriefingGenerator()
        generator.process_categories()
        
        logger.info("✅ 크롤링 + 분석 완료")
        
    except Exception as e:
        logger.error(f"❌ 실행 중 오류: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """앱 시작 시"""
    global scheduler
    
    logger.info("\n🚀 VibePick 백엔드 시작")
    
    # DB 테이블 생성
    Base.metadata.create_all(bind=engine)
    logger.info("✅ 데이터베이스 테이블 생성 완료")
    
    # 스케줄러 초기화 및 시작
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        crawl_and_generate,
        CronTrigger(hour="9,13,17", minute="0", timezone="Asia/Seoul")
    )
    scheduler.start()
    logger.info("✅ 스케줄러 시작 (09:00, 13:00, 17:00 KST에 자동 실행)")

@app.on_event("shutdown")
async def shutdown_event():
    """앱 종료 시"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("✅ 스케줄러 종료")

# ============================================
# ✅ 브리핑 엔드포인트 (카테고리별 종합 분석)
# ============================================

@app.get("/briefings")
async def get_briefings(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sectors: list = Query(None),
    stocks: list = Query(None),
    db: Session = Depends(get_db)
):
    """
    브리핑 목록 조회 (카테고리별 종합 분석)
    
    - **limit**: 최대 조회 개수 (기본값: 20)
    - **offset**: 시작 위치 (기본값: 0)
    - **sectors**: 카테고리 필터 (예: ["AI · 기술", "금융"])
    - **stocks**: 종목 필터 (예: ["삼성전자", "SK하이닉스"])
    """
    
    try:
        query = db.query(Briefing).join(Article)
        
        # 카테고리 필터링
        if sectors:
            query = query.filter(Briefing.related_sectors.overlap(sectors))
        
        # 종목 필터링
        if stocks:
            query = query.filter(Briefing.related_stocks.overlap(stocks))
        
        # 데이터 조회
        briefings = query.order_by(
            Briefing.generated_at.desc()
        ).offset(offset).limit(limit).all()
        
        response = []
        for idx, b in enumerate(briefings, 1):
            try:
                # source_name에서 category 추출
                category = b.article.source_name.split(" - ")[-1] if " - " in b.article.source_name else ""
                
                briefing_data = {
                    "id": b.id,
                    "category": category,  # ✅ 카테고리 (종합 분석 대상)
                    "title": b.ai_summary,  # ✅ 카테고리의 흐름 헤드라인
                    "originalTitle": b.article.title,  # 원본 기사 제목 (참고용)
                    "summary": b.ai_summary,  # 카테고리 분석 내용
                    "positive_points": b.positive_points or [],  # 트렌드 3개
                    "negative_points": b.negative_points or [],  # 투자자 심리
                    "related_stocks": b.related_stocks or [],
                    "related_sectors": b.related_sectors or [],
                    "published_at": b.article.crawled_at.isoformat() if b.article.crawled_at else None
                }
                
                response.append(briefing_data)
                
            except Exception as e:
                logger.error(f"[{idx}] 데이터 변환 오류: {str(e)}")
                continue
        
        logger.info(f"✅ 브리핑 조회: {len(response)}개 (카테고리별 종합)")
        return response
        
    except Exception as e:
        logger.error(f"❌ 브리핑 조회 실패: {str(e)}")
        return {"error": str(e)}, 500

@app.get("/briefings/{briefing_id}")
async def get_briefing_detail(briefing_id: int, db: Session = Depends(get_db)):
    """특정 브리핑 상세 조회"""
    try:
        briefing = db.query(Briefing).filter(Briefing.id == briefing_id).first()
        
        if not briefing:
            return {"error": "브리핑을 찾을 수 없습니다"}, 404
        
        category = briefing.article.source_name.split(" - ")[-1] if " - " in briefing.article.source_name else ""
        
        return {
            "id": briefing.id,
            "category": category,
            "title": briefing.ai_summary,
            "originalTitle": briefing.article.title,
            "summary": briefing.ai_summary,
            "positive_points": briefing.positive_points or [],  # 트렌드
            "negative_points": briefing.negative_points or [],  # 투자자 심리
            "related_stocks": briefing.related_stocks or [],
            "related_sectors": briefing.related_sectors or [],
            "published_at": briefing.article.crawled_at.isoformat() if briefing.article.crawled_at else None
        }
        
    except Exception as e:
        logger.error(f"❌ 브리핑 상세 조회 실패: {str(e)}")
        return {"error": str(e)}, 500

# ============================================
# 테스트/디버깅 엔드포인트
# ============================================

@app.get("/")
async def root():
    """API 상태 확인"""
    return {
        "status": "VibePick 백엔드 정상 작동",
        "type": "카테고리별 종합 분석 브리핑",
        "endpoints": [
            "/briefings - 브리핑 목록 (카테고리별)",
            "/briefings/{id} - 브리핑 상세",
            "/trigger-crawl - 수동 크롤링 실행",
            "/docs - API 문서"
        ]
    }

@app.get("/trigger-crawl")
async def trigger_crawl():
    """
    수동 크롤링 + 브리핑 생성 실행 (테스트용)
    
    크롤링 후 자동으로 카테고리별 종합 분석 수행
    """
    logger.info("\n🧪 테스트 크롤링 + 카테고리 분석 시작 (백그라운드)")
    
    # 백그라운드에서 실행
    asyncio.create_task(asyncio.to_thread(crawl_and_generate))
    
    return {
        "status": "크롤링 + 분석 시작됨",
        "message": "백그라운드에서 실행 중입니다",
        "process": "1) 뉴스 크롤링 2) 카테고리별 종합 분석",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "type": "category_briefing"
    }

# ============================================
# 통계 엔드포인트
# ============================================

@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """기본 통계"""
    try:
        total_articles = db.query(Article).count()
        total_briefings = db.query(Briefing).count()
        
        # 카테고리별 브리핑 수
        category_stats = db.query(
            Briefing.related_sectors,
            func.count(Briefing.id).label('count')
        ).group_by(Briefing.related_sectors).all()
        
        return {
            "total_articles": total_articles,
            "total_briefings": total_briefings,
            "briefing_coverage": f"{(total_briefings/max(total_articles, 1)*100):.1f}%",
            "briefing_type": "카테고리별 종합 분석",
            "categories_analyzed": len(category_stats),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"통계 조회 실패: {str(e)}")
        return {"error": str(e)}, 500

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development"
    )