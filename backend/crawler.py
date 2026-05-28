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
    """금융 뉴스 크롤링 (강화된 버전 - 차단 우회)"""
    
    def __init__(self):
        self.session = self._create_session()
        self.timeout = 10
    
    def _create_session(self):
        """재시도 로직이 있는 세션 생성"""
        session = requests.Session()
        
        # ✅ User-Agent 강화 (봇 감지 우회)
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        })
        
        # ✅ 재시도 로직 (3회 재시도, 백오프 전략)
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
    
    # ============ 크롤링 소스 1: FN뉴스 RSS ============
    
    def crawl_fn_news_rss(self) -> list:
        """FN뉴스 RSS"""
        articles = []
        
        rss_feeds = [
            "https://www.fnnews.com/rss/headline.xml",
            "https://www.fnnews.com/rss/business.xml",
        ]
        
        for feed_url in rss_feeds:
            try:
                logger.info(f"   크롤링: {feed_url}")
                response = self.session.get(feed_url, timeout=self.timeout)
                response.encoding = 'utf-8'
                
                logger.info(f"   상태코드: {response.status_code}")
                
                if response.status_code != 200:
                    logger.warning(f"   ⚠️  HTTP {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                items = soup.find_all('item')
                
                logger.info(f"   발견: {len(items)}개 항목")
                
                if not items:
                    logger.warning(f"   ⚠️  item 태그 없음")
                    continue
                
                for item in items[:20]:
                    try:
                        title_tag = item.find('title')
                        link_tag = item.find('link')
                        desc_tag = item.find('description')
                        
                        title = (title_tag.text or '').strip() if title_tag else ''
                        link = (link_tag.text or '').strip() if link_tag else ''
                        desc = (desc_tag.text or '').strip() if desc_tag else ''
                        
                        # ❌ 영문 제목 필터링
                        if not (title and link and self._has_korean(title)):
                            continue
                        
                        articles.append({
                            'title': title,
                            'url': link,
                            'content': desc if len(desc) > 30 else title,
                            'source': 'FN뉴스',
                            'published_at': datetime.utcnow()
                        })
                    except Exception as e:
                        logger.debug(f"   항목 오류: {str(e)}")
                        continue
                
                fn_count = len([a for a in articles if a['source'] == 'FN뉴스'])
                logger.info(f"   수집: {fn_count}개")
                
            except requests.Timeout:
                logger.warning(f"   ⏱️  타임아웃")
            except requests.ConnectionError as e:
                logger.error(f"   ❌ 연결 오류: {str(e)}")
            except Exception as e:
                logger.error(f"   ❌ 오류: {str(e)}")
        
        return articles
    
    # ============ 크롤링 소스 2: 네이버 금융 ============
    
    def crawl_naver_finance(self) -> list:
        """네이버 금융"""
        articles = []
        
        try:
            url = "https://finance.naver.com/news/mainnews.naver"
            logger.info(f"   크롤링: {url}")
            
            response = self.session.get(url, timeout=self.timeout)
            response.encoding = 'utf-8'
            
            logger.info(f"   상태코드: {response.status_code}")
            
            if response.status_code != 200:
                logger.warning(f"   ⚠️  HTTP {response.status_code}")
                return articles
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # ✅ 여러 선택자 시도 (구조 변경 대응)
            news_items = soup.select("div.newsList > ul > li")
            if not news_items:
                news_items = soup.select("li.newItem")
            if not news_items:
                news_items = soup.select("tr")[:30]
            
            logger.info(f"   발견: {len(news_items)}개 항목")
            
            for item in news_items[:25]:
                try:
                    title_elem = item.select_one("a.nclicks")
                    if not title_elem:
                        title_elem = item.select_one("a")
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    news_url = title_elem.get('href', '')
                    
                    if not (title and self._has_korean(title) and news_url):
                        continue
                    
                    articles.append({
                        'title': title,
                        'url': news_url,
                        'content': title,
                        'source': '네이버금융',
                        'published_at': datetime.utcnow()
                    })
                    
                except Exception as e:
                    logger.debug(f"   항목 오류: {str(e)}")
                    continue
            
            logger.info(f"   수집: {len(articles)}개")
                
        except requests.Timeout:
            logger.warning(f"   ⏱️  타임아웃")
        except requests.ConnectionError as e:
            logger.error(f"   ❌ 연결 오류: {str(e)}")
        except Exception as e:
            logger.error(f"   ❌ 오류: {str(e)}")
        
        return articles
    
    # ============ 크롤링 소스 3: 이코노미스트 ============
    
    def crawl_economist_rss(self) -> list:
        """이코노미스트"""
        articles = []
        
        try:
            # ✅ 도메인 변경 대응
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
                    
                    for item in items[:15]:
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
                                'content': desc if len(desc) > 30 else title,
                                'source': '이코노미스트',
                                'published_at': datetime.utcnow()
                            })
                        except:
                            continue
                    
                    if articles:
                        logger.info(f"   수집: {len(articles)}개")
                        break  # 성공하면 다음 URL 시도 안 함
                
                except requests.Timeout:
                    logger.debug(f"   ⏱️  타임아웃")
                    continue
                except Exception as e:
                    logger.debug(f"   ❌ 오류: {str(e)}")
                    continue
        
        except Exception as e:
            logger.error(f"   ❌ 전체 오류: {str(e)}")
        
        return articles
    
    # ============ 헬퍼 함수 ============
    
    def _has_korean(self, text: str) -> bool:
        """한글 포함 여부"""
        for char in text:
            if ord(char) >= 0xAC00 and ord(char) <= 0xD7A3:
                return True
        return False
    
    def _validate_article(self, article_data: dict) -> bool:
        """데이터 검증"""
        if not article_data.get('title') or len(article_data['title']) < 5:
            return False
        if not article_data.get('url') or len(article_data.get('url', '')) < 10:
            return False
        if len(article_data.get('content', '')) < 10:
            return False
        return True
    
    def save_to_db(self, articles: list):
        """DB 저장"""
        db = SessionLocal()
        saved_count = 0
        duplicate_count = 0
        
        try:
            for article_data in articles:
                if not self._validate_article(article_data):
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
                    
                except Exception as e:
                    logger.error(f"   저장 오류: {str(e)}")
                    db.rollback()
            
            db.commit()
            logger.info(f"✅ 저장: {saved_count}개, 중복: {duplicate_count}개")
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ DB 오류: {str(e)}")
        finally:
            db.close()
    
    def run_crawl(self):
        """전체 크롤링"""
        start_time = time.time()
        
        logger.info("\n" + "="*60)
        logger.info("🔄 크롤링 시작 (강화된 버전)")
        logger.info("="*60)
        
        all_articles = []
        
        try:
            # Step 1
            logger.info("\n📡 Step 1: FN뉴스 RSS")
            all_articles.extend(self.crawl_fn_news_rss())
            
            # Step 2
            logger.info("\n📡 Step 2: 네이버금융")
            all_articles.extend(self.crawl_naver_finance())
            
            # Step 3
            logger.info("\n📡 Step 3: 이코노미스트")
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