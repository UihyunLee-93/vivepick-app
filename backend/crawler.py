import requests
from database import SessionLocal, Article
from datetime import datetime
import logging
import time
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsCrawler:
    """네이버 뉴스 API - 카테고리 기반 크롤링"""
    
    def __init__(self):
        self.client_id = os.getenv("NAVER_CLIENT_ID")
        self.client_secret = os.getenv("NAVER_CLIENT_SECRET")
        
        if not self.client_id or not self.client_secret:
            logger.warning("⚠️  네이버 API 키가 없습니다")
            self.client_id = None
            self.client_secret = None
        
        self.headers = {
            "X-Naver-Client-Id": self.client_id or "",
            "X-Naver-Client-Secret": self.client_secret or ""
        }
        
        # ✅ 카테고리별 검색어 (VibePick 카테고리와 매칭)
        self.categories = {
            "AI · 기술": [
                "생성형AI",
                "AI칩",
                "GPT",
                "머신러닝",
                "클라우드"
            ],
            "금융": [
                "금리",
                "환율",
                "주식시장",
                "부동산",
                "은행"
            ],
            "에너지": [
                "유가",
                "태양광",
                "풍력",
                "석유",
                "전기요금"
            ],
            "모빌리티": [
                "전기차",
                "자율주행",
                "수소차",
                "배터리",
                "완성차"
            ],
            "바이오": [
                "신약",
                "임상시험",
                "제약",
                "바이오",
                "헬스케어"
            ],
            "소비 · 라이프": [
                "소비심리",
                "패션",
                "음식",
                "여행",
                "쇼핑"
            ],
            "산업 · 제조": [
                "반도체",
                "자동화",
                "제조업",
                "조선",
                "철강"
            ],
            "글로벌": [
                "미국주식",
                "환율",
                "국제정세",
                "글로벌기업",
                "해외투자"
            ],
            "크립토": [
                "비트코인",
                "이더리움",
                "암호화폐",
                "블록체인",
                "NFT"
            ],
            "콘텐츠 · 엔터": [
                "영화",
                "드라마",
                "음악",
                "웹툰",
                "게임"
            ]
        }
    
    def crawl_category_news(self, category: str, keywords: list) -> list:
        """카테고리별 뉴스 크롤링"""
        articles = []
        
        if not self.client_id:
            logger.error("❌ 네이버 API 키 없음")
            return articles
        
        logger.info(f"\n📂 카테고리: {category}")
        
        for keyword in keywords:
            try:
                logger.info(f"   검색어: {keyword}")
                
                url = "https://openapi.naver.com/v1/search/news.json"
                params = {
                    "query": keyword,
                    "display": 10,
                    "start": 1,
                    "sort": "date"
                }
                
                response = requests.get(
                    url, 
                    headers=self.headers, 
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for item in data.get('items', []):
                        try:
                            title = item.get('title', '')
                            link = item.get('link', '')
                            desc = item.get('description', '')
                            
                            title = title.replace('<b>', '').replace('</b>', '')
                            desc = desc.replace('<b>', '').replace('</b>', '')
                            
                            if not (title and link):
                                continue
                            
                            articles.append({
                                'title': title,
                                'url': link,
                                'content': desc if len(desc) > 10 else title,
                                'source': '네이버뉴스',
                                'category': category,  # ✅ 카테고리 추가
                                'published_at': datetime.utcnow()
                            })
                            
                            logger.info(f"      ✅ {title[:50]}")
                        
                        except:
                            continue
                    
                    logger.info(f"   수집: {len(articles)}개")
                
                elif response.status_code == 401:
                    logger.error("   ❌ API 키 오류")
                    return articles
                
                time.sleep(0.5)  # API 제한 회피
                
            except Exception as e:
                logger.error(f"   ❌ {keyword} 오류: {str(e)}")
                continue
        
        return articles
    
    def save_to_db(self, articles: list):
        """DB 저장"""
        db = SessionLocal()
        saved_count = 0
        duplicate_count = 0
        
        logger.info(f"\n💾 DB 저장 시작: {len(articles)}개 기사")
        
        try:
            for idx, article_data in enumerate(articles, 1):
                try:
                    if not article_data.get('url'):
                        continue
                    
                    existing = db.query(Article).filter(
                        Article.source_url == article_data['url']
                    ).first()
                    
                    if existing:
                        duplicate_count += 1
                        continue
                    
                    new_article = Article(
                        title=article_data['title'][:500],
                        source_url=article_data['url'],
                        original_content=article_data['content'][:2000],
                        source_name=f"{article_data['source']} - {article_data.get('category', '')}",
                        crawled_at=article_data.get('published_at', datetime.utcnow())
                    )
                    
                    db.add(new_article)
                    db.flush()
                    saved_count += 1
                    
                    logger.info(f"   [{idx}] ✅ [{article_data.get('category')}] {article_data['title'][:40]}")
                    
                except Exception as e:
                    logger.error(f"   [{idx}] 저장 실패: {str(e)}")
                    db.rollback()
                    continue
            
            db.commit()
            logger.info(f"\n✅ DB 저장 완료: 저장 {saved_count}개, 중복 {duplicate_count}개\n")
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ DB 오류: {str(e)}")
        finally:
            db.close()
    
    def run_crawl(self):
        """전체 크롤링 실행"""
        start_time = time.time()
        
        logger.info("\n" + "="*60)
        logger.info("🔄 카테고리 기반 뉴스 크롤링 시작")
        logger.info("="*60)
        
        if not self.client_id:
            logger.warning("⚠️  네이버 API 키 없음")
            return
        
        logger.info("✅ 네이버 API 키 감지됨\n")
        
        all_articles = []
        
        # ✅ 각 카테고리별로 크롤링
        for category, keywords in self.categories.items():
            category_articles = self.crawl_category_news(category, keywords)
            all_articles.extend(category_articles)
        
        elapsed = time.time() - start_time
        logger.info(f"\n📊 총 수집: {len(all_articles)}개 ({elapsed:.1f}초)")
        
        if len(all_articles) == 0:
            logger.warning("⚠️  수집된 기사가 없습니다")
            logger.info("="*60 + "\n")
            return
        
        # DB 저장
        self.save_to_db(all_articles)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ 완료 ({elapsed:.1f}초)")
        logger.info("="*60 + "\n")


if __name__ == "__main__":
    crawler = NewsCrawler()
    crawler.run_crawl()