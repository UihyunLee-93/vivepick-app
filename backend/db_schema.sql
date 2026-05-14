-- 1. 기사 테이블
CREATE TABLE articles (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    source_url VARCHAR(2048) UNIQUE NOT NULL,
    original_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    crawled_at TIMESTAMP DEFAULT NOW(),
    source_name VARCHAR(100)
);

-- 2. AI 브리핑 테이블
CREATE TABLE briefings (
    id BIGSERIAL PRIMARY KEY,
    article_id BIGINT REFERENCES articles(id) ON DELETE CASCADE,
    ai_summary TEXT NOT NULL,
    positive_points TEXT[] NOT NULL,
    negative_points TEXT[] NOT NULL,
    related_stocks TEXT[] NOT NULL,
    related_sectors TEXT[] NOT NULL,
    generated_at TIMESTAMP DEFAULT NOW()
);

-- 3. 주식 정보 테이블
CREATE TABLE stocks (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) UNIQUE NOT NULL,
    name_ko VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    sector VARCHAR(50),
    market VARCHAR(20), -- KOSPI, KOSDAQ, NASDAQ
    created_at TIMESTAMP DEFAULT NOW()
);

-- 4. 사용자 테이블
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_premium BOOLEAN DEFAULT FALSE
);

-- 5. 사용자 관심 태그 테이블
CREATE TABLE user_interests (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    interested_stocks TEXT[] NOT NULL DEFAULT '{}',
    interested_sectors TEXT[] NOT NULL DEFAULT '{}',
    interested_markets TEXT[] NOT NULL DEFAULT '{}',
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 6. 사용자 조회 이력 테이블 (분석용)
CREATE TABLE user_views (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    briefing_id BIGINT REFERENCES briefings(id),
    viewed_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_articles_crawled_at ON articles(crawled_at DESC);
CREATE INDEX idx_briefings_article_id ON briefings(article_id);
CREATE INDEX idx_briefings_stocks ON briefings USING GIN(related_stocks);
CREATE INDEX idx_briefings_sectors ON briefings USING GIN(related_sectors);
CREATE INDEX idx_user_interests ON user_interests(user_id);
CREATE INDEX idx_stocks_sector ON stocks(sector);
