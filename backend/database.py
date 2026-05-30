import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Text, DateTime, Boolean, Integer, ARRAY, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid

load_dotenv()

# 데이터베이스 연결
DATABASE_URL = os.getenv("SUPABASE_DB_URL")
if not DATABASE_URL:
    print("⚠️ DATABASE_URL not found, skipping DB init")
    DATABASE_URL = "postgresql://localhost/dummy"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,   # 끊어진 커넥션 자동 감지 후 재연결
    pool_recycle=300,     # 5분마다 커넥션 재생성 (Supabase idle 타임아웃 대응)
    pool_size=5,
    max_overflow=10
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# ============ ORM 모델 ============

class Article(Base):
    """기사 테이블"""
    __tablename__ = "articles"
    
    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    source_url = Column(String(2048), unique=True, nullable=False, index=True)
    original_content = Column(Text, nullable=False)
    source_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    crawled_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    briefings = relationship("Briefing", back_populates="article", cascade="all, delete-orphan")


class Briefing(Base):
    """AI 브리핑 테이블"""
    __tablename__ = "briefings"
    
    id = Column(BigInteger, primary_key=True, index=True)
    article_id = Column(BigInteger, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    ai_summary = Column(Text, nullable=False)
    main_story = Column(Text, nullable=True)
    positive_points = Column(ARRAY(String), nullable=False, default=[])
    negative_points = Column(ARRAY(String), nullable=False, default=[])
    related_stocks = Column(ARRAY(String), nullable=False, default=[], index=True)
    related_sectors = Column(ARRAY(String), nullable=False, default=[], index=True)
    mood = Column(String(20), nullable=True)
    time_slot = Column(String(20), nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    article = relationship("Article", back_populates="briefings")


class Stock(Base):
    """주식 정보 테이블"""
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), unique=True, nullable=False, index=True)
    name_ko = Column(String(100), nullable=False)
    name_en = Column(String(100))
    sector = Column(String(50), index=True)
    market = Column(String(20))  # KOSPI, KOSDAQ, NASDAQ
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    """사용자 테이블"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_premium = Column(Boolean, default=False)
    
    # 관계
    interests = relationship("UserInterest", back_populates="user", uselist=False, cascade="all, delete-orphan")
    views = relationship("UserView", back_populates="user", cascade="all, delete-orphan")


class UserInterest(Base):
    """사용자 관심 태그"""
    __tablename__ = "user_interests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    interested_stocks = Column(ARRAY(String), default=[])
    interested_sectors = Column(ARRAY(String), default=[])
    interested_markets = Column(ARRAY(String), default=[])
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    user = relationship("User", back_populates="interests")


class UserView(Base):
    """사용자 조회 이력"""
    __tablename__ = "user_views"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    briefing_id = Column(BigInteger, ForeignKey("briefings.id"), nullable=False)
    viewed_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    user = relationship("User", back_populates="views")


# 데이터베이스 초기화
def init_db():
    """테이블 생성"""
    Base.metadata.create_all(bind=engine)
    print("✅ 데이터베이스 테이블 생성 완료")


# DB 세션 가져오기
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()