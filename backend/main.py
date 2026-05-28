from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from database import engine, Base, get_db, Article, Briefing
from crawler import NewsCrawler
from briefing_generator import BriefingGenerator
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
import asyncio
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DB 초기화
Base.metadata.create_all(bind=engine)

app = FastAPI(title="VibePick API")

# 스케줄러 설정
scheduler = BackgroundScheduler()

def crawl_and_generate():
    """크롤링 + 브리핑 생성"""
    logger.info("\n" + "="*50)
    logger.info("⏰ 자동 스케줄 실행 시작")
    logger.info("="*50)
    
    # 크롤링
    crawler = NewsCrawler()
    crawler.run_crawl()
    
    # 브리핑 생성
    generator = BriefingGenerator()
    generator.process_articles(limit=10)

# 스케줄 등록 (09:00, 13:00, 17:00 KST)
scheduler.add_job(
    crawl_and_generate,
    CronTrigger(hour="9,13,17", minute="0", timezone="Asia/Seoul")
)

@app.on_event("startup")
async def startup_event():
    """앱 시작 시"""
    logger.info("\n🚀 Vivepick 백엔드 시작")
    
    # DB 테이블 생성
    Base.metadata.create_all(bind=engine)
    logger.info("✅ 데이터베이스 테이블 생성 완료")
    logger.info("✅ 데이터베이스 초기화 성공")
    
    # 스케줄러 시작
    scheduler.start()
    logger.info("✅ 스케줄러 시작 (09:00, 13:00, 17:00 KST에 자동 실행)")

@app.on_event("shutdown")
async def shutdown_event():
    """앱 종료 시"""
    scheduler.shutdown()

# ============================================
# ✅ 수정된 브리핑 엔드포인트
# ============================================

class BriefingResponseSchema:
    """API 응답 스키마"""
    pass

@app.get("/briefings")
async def get_briefings(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sectors: list = Query(None),
    stocks: list = Query(None),
    db: Session = Depends(get_db)
):
    """
    브리핑 목록 조회
    
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
                # ✅ source_name에서 category 추출
                category = b.article.source_name.split(" - ")[-1] if " - " in b.article.source_name else ""
                
                briefing_data = {
                    "id": b.id,
                    "category": category,  # ✅ 카테고리 추가
                    "title": b.ai_summary,  # ✅ AI 분석 헤드라인을 제목으로!
                    "originalTitle": b.article.title,  # 원본 기사 제목 (참고용)
                    "summary": b.ai_summary,  # AI 분석 내용
                    "positive_points": b.positive_points or [],  # 오늘 포인트들
                    "negative_points": b.negative_points or [],  # 투자 심리
                    "related_stocks": b.related_stocks or [],
                    "related_sectors": b.related_sectors or [],
                    "mood": "neutral",  # 기본값
                    "published_at": b.article.crawled_at.isoformat() if b.article.crawled_at else None
                }
                
                # mood 추출 (summary에서)
                summary_lower = (b.ai_summary or "").lower()
                if "📈" in summary_lower or "🚀" in summary_lower or "긍정" in summary_lower:
                    briefing_data["mood"] = "positive"
                elif "📉" in summary_lower or "⚠️" in summary_lower or "부정" in summary_lower:
                    briefing_data["mood"] = "negative"
                else:
                    briefing_data["mood"] = "neutral"
                
                response.append(briefing_data)
                
            except Exception as e:
                logger.error(f"[{idx}] 데이터 변환 오류: {str(e)}")
                continue
        
        logger.info(f"✅ 브리핑 조회: {len(response)}개")
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
            "positive_points": briefing.positive_points or [],
            "negative_points": briefing.negative_points or [],
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
        "endpoints": [
            "/briefings - 브리핑 목록",
            "/briefings/{id} - 브리핑 상세",
            "/trigger-crawl - 수동 크롤링 실행",
            "/docs - API 문서"
        ]
    }

@app.get("/trigger-crawl")
async def trigger_crawl():
    """수동 크롤링 실행 (테스트용)"""
    logger.info("\n🧪 테스트 크롤링 시작 (백그라운드)")
    
    # 백그라운드에서 실행
    asyncio.create_task(asyncio.to_thread(crawl_and_generate))
    
    return {"status": "크롤링 시작됨", "message": "백그라운드에서 실행 중입니다"}

@app.get("/health")
async def health_check():
    """헬스체크"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)