import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from database import SessionLocal, Article
from datetime import datetime
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsCrawler:
    """금융 뉴스 크롤링 (validation 완화)"""
    
    def __init__(self):
        self.session = self._create_session()
        self.timeout = 10
    
    def _create_session(self):
        """재시도 로직이 있는 세션 생성"""
        session = requests.Session()
        
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9",
            "Connection": "keep-alive",
        })
        
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    # ============ 크롤링 소스 ============
    
    def crawl_fn_news_rss(self) -> list:
        """FN뉴스 RSS"""
        articles = []
        
        # FN뉴스는 현재 404 (주소 변경됨)
        # 스킵하고 다른 소스 사용
        logger.info("   ⏭️  FN뉴스 404 (주소 변경됨, 스킵)")
        return articles
    
    def crawl_naver_finance(self) -> list:
        """네이버 금융"""
        articles = []
        
        # Railway에서 네이버 접근 불가 (404)
        # 스킵
        logger.info("   ⏭️  네이버 404 (Railway IP 차단, 스킵)")
        return articles
    
    def crawl_economist_rss(self) -> list:
        """이코노미스트 (유일하게 작동하는 소스)"""
        articles = []
        
        urls = [
            "https://www.economist.co.kr/feed",
            "https://economist.co.kr/feed",
        ]
        
        for url in urls:
            try:
                logger.info(f"   크롤링: {url}")
                response = self.session.get(url, timeout=self.timeout)
                response.encoding = 'utf-8'
                
                logger.info(f"   상태코드: {response.status_code}")
                
                if response.status_code != 200:
                    logger.debug(f"   ⚠️  HTTP {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                items = soup.find_all('item')
                
                logger.info(f"   발견: {len(items)}개 항목")
                
                if not items:
                    logger.debug(f"   ⚠️  item 태그 없음")
                    continue
                
                for item in items[:20]:
                    try:
                        title_tag = item.find('title')
                        link_tag = item.find('link')
                        desc_tag = item.find('description')
                        
                        title = (title_tag.text or '').strip() if title_tag else ''
                        link = (link_tag.text or '').strip() if link_tag else ''
                        desc = (desc_tag.text or '').strip() if desc_tag else ''
                        
                        if not (title and link and self._has_korean(title)):
                            continue
                        
                        articles.append({
                            'title': title,
                            'url': link,
                            'content': desc if len(desc) > 10 else title,  # ✅ 완화: 본문 없으면 제목
                            'source': '이코노미스트',
                            'published_at': datetime.utcnow()
                        })
                    except Exception as e:
                        logger.debug(f"   항목 오류: {str(e)}")
                        continue
                
                if articles:
                    logger.info(f"   수집: {len(articles)}개")
                    return articles  # 성공하면 반환
            
            except Exception as e:
                logger.debug(f"   오류: {str(e)}")
                continue
        
        return articles
    
    # ============ 헬퍼 함수 ============
    
    def _has_korean(self, text: str) -> bool:
        """한글 포함 여부"""
        for char in text:
            if ord(char) >= 0xAC00 and ord(char) <= 0xD7A3:
                return True
        return False
    
    def _validate_article(self, article_data: dict) -> bool:
        """✅ 완화된 validation"""
        
        # 제목: 3자 이상 (완화)
        if not article_data.get('title') or len(article_data['title']) < 3:
            logger.debug(f"   검증 실패: 제목 짧음 ({len(article_data.get('title', ''))}자)")
            return False
        
        # URL: 필수만 (길이 제한 제거)
        if not article_data.get('url'):
            logger.debug(f"   검증 실패: URL 없음")
            return False
        
        # 본문: 없으면 제목 사용
        content = article_data.get('content', '')
        if not content or len(content) < 1:
            # ✅ 본문 없으면 제목으로 채우기
            article_data['content'] = article_data['title']
        
        return True
    
    def save_to_db(self, articles: list):
        """DB 저장"""
        db = SessionLocal()
        saved_count = 0
        duplicate_count = 0
        validation_fail = 0
        
        try:
            for article_data in articles:
                if not self._validate_article(article_data):
                    validation_fail += 1
                    continue
                
                existing = db.query(Article).filter(
                    Article.source_url == article_data['url']
                ).first()
                
                if existing:
                    duplicate_count += 1
                    continue
                
                try:
                    new_article = Article(
                        title=article_data['title'][:500],
                        source_url=article_data['url'],
                        original_content=article_data['content'][:2000],
                        source_name=article_data['source'],
                        crawled_at=article_data.get('published_at', datetime.utcnow())
                    )
                    
                    db.add(new_article)
                    saved_count += 1
                    logger.info(f"   ✅ {article_data['title'][:50]}")
                    
                except Exception as e:
                    logger.error(f"   저장 오류: {str(e)}")
                    db.rollback()
            
            db.commit()
            logger.info(f"\n✅ 저장 완료: {saved_count}개")
            logger.info(f"   중복: {duplicate_count}개")
            logger.info(f"   검증 실패: {validation_fail}개")
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ DB 오류: {str(e)}")
        finally:
            db.close()
    
    def run_crawl(self):
        """전체 크롤링"""
        start_time = time.time()
        
        logger.info("\n" + "="*60)
        logger.info("🔄 크롤링 시작")
        logger.info("="*60)
        
        all_articles = []
        
        try:
            # 현재 작동하는 소스만 사용
            logger.info("\n📡 Step 1: FN뉴스 RSS")
            all_articles.extend(self.crawl_fn_news_rss())
            
            logger.info("\n📡 Step 2: 네이버금융")
            all_articles.extend(self.crawl_naver_finance())
            
            logger.info("\n📡 Step 3: 이코노미스트 (유일 작동 소스)")
            all_articles.extend(self.crawl_economist_rss())
            
        except Exception as e:
            logger.error(f"❌ 크롤링 중 오류: {str(e)}")
        
        elapsed = time.time() - start_time
        
        logger.info(f"\n📊 수집 완료: {len(all_articles)}개 ({elapsed:.1f}초)")
        
        if len(all_articles) == 0:
            logger.warning("⚠️  기사 0개")
            logger.info("="*60 + "\n")
            return
        
        logger.info("💾 DB 저장 중...")
        self.save_to_db(all_articles)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ 완료 ({elapsed:.1f}초)")
        logger.info("="*60 + "\n")


if __name__ == "__main__":
    crawler = NewsCrawler()
    crawler.run_crawl()