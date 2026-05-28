import requests
from bs4 import BeautifulSoup
from database import SessionLocal, Article
from datetime import datetime
import logging
import xml.etree.ElementTree as ET
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsCrawler:
    """개선된 금융 뉴스 크롤링 (스케줄 안정성 중심)"""
    
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.timeout = 5  # ✅ 단축 (10초 → 5초)
        self.max_retries = 2
    
    # ============ 크롤링 소스 1: FN뉴스 RSS (가장 신뢰도 높음) ============
    
    def crawl_fn_news_rss(self) -> list:
        """FN뉴스 RSS (한글, 빠름, 신뢰도 높음)"""
        articles = []
        
        rss_feeds = [
            "https://www.fnnews.com/rss/headline.xml",
            "https://www.fnnews.com/rss/business.xml",
        ]
        
        for feed_url in rss_feeds:
            try:
                logger.info(f"📰 {feed_url} 크롤링 중...")
                response = self.session.get(feed_url, timeout=self.timeout, headers=self.headers)
                response.encoding = 'utf-8'
                
                root = ET.fromstring(response.content)
                items = root.findall('.//item')
                
                for item in items[:15]:  # 한 피드당 15개만
                    try:
                        title_elem = item.find('title')
                        link_elem = item.find('link')
                        desc_elem = item.find('description')
                        
                        title = (title_elem.text or '').strip() if title_elem is not None else ''
                        link = (link_elem.text or '').strip() if link_elem is not None else ''
                        desc = (desc_elem.text or '').strip() if desc_elem is not None else ''
                        
                        # ✅ 한글 포함 확인
                        if not (title and link and self._has_korean(title)):
                            continue
                        
                        articles.append({
                            'title': title,
                            'url': link,
                            'content': desc if len(desc) > 30 else title,  # desc가 짧으면 title 사용
                            'source': 'FN뉴스',
                            'published_at': datetime.utcnow()
                        })
                    except Exception as e:
                        logger.debug(f"   항목 파싱 오류: {str(e)}")
                        continue
                
                logger.info(f"   ✅ {len([a for a in articles if a['source'] == 'FN뉴스'])}개 수집")
                
            except requests.Timeout:
                logger.warning(f"   ⏱️  타임아웃: {feed_url}")
            except Exception as e:
                logger.error(f"   ❌ 크롤링 실패: {str(e)}")
        
        return articles
    
    # ============ 크롤링 소스 2: 네이버 금융 헤드라인 (제목만, 빠름) ============
    
    def crawl_naver_finance(self) -> list:
        """
        네이버 금융 뉴스 (제목만 가져옴 - 상세 크롤링 제거)
        
        ✅ 개선 사항:
        - 상세 페이지 요청 제거 (45분 → 2분)
        - 제목을 본문으로 사용 (임시)
        - 타임아웃 짧음 (5초)
        """
        articles = []
        
        try:
            logger.info(f"📰 네이버금융 크롤링 중...")
            url = "https://finance.naver.com/news/mainnews.naver"
            response = self.session.get(url, timeout=self.timeout, headers=self.headers)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            news_items = soup.select("div.newsList > ul > li")
            
            logger.info(f"   발견: {len(news_items)}개 항목")
            
            for item in news_items[:20]:  # 20개만
                try:
                    title_elem = item.select_one("a.nclicks")
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    news_url = title_elem.get('href', '')
                    
                    # ✅ 한글 제목만
                    if not (title and self._has_korean(title) and news_url):
                        continue
                    
                    # ✅ 상세 크롤링 안 함! (제목을 본문으로)
                    articles.append({
                        'title': title,
                        'url': news_url,
                        'content': title,  # 임시: 제목을 본문으로 사용
                        'source': '네이버금융',
                        'published_at': datetime.utcnow()
                    })
                    
                except Exception as e:
                    logger.debug(f"   항목 처리 오류: {str(e)}")
                    continue
            
            logger.info(f"   ✅ {len(articles)}개 수집")
                
        except requests.Timeout:
            logger.warning(f"   ⏱️  타임아웃")
        except Exception as e:
            logger.error(f"   ❌ 크롤링 실패: {str(e)}")
        
        return articles
    
    # ============ 크롤링 소스 3: 이코노미스트 RSS ============
    
    def crawl_economist_rss(self) -> list:
        """이코노미스트 경제 뉴스 RSS"""
        articles = []
        
        try:
            logger.info(f"📰 이코노미스트 크롤링 중...")
            rss_url = "https://www.economist.co.kr/feed"
            response = self.session.get(rss_url, timeout=self.timeout, headers=self.headers)
            response.encoding = 'utf-8'
            
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            
            for item in items[:10]:
                try:
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    desc_elem = item.find('description')
                    
                    title = (title_elem.text or '').strip() if title_elem is not None else ''
                    link = (link_elem.text or '').strip() if link_elem is not None else ''
                    desc = (desc_elem.text or '').strip() if desc_elem is not None else ''
                    
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
            
            logger.info(f"   ✅ {len(articles)}개 수집")
        
        except requests.Timeout:
            logger.warning(f"   ⏱️  타임아웃")
        except Exception as e:
            logger.warning(f"   ⚠️  크롤링 실패: {str(e)}")
        
        return articles
    
    # ============ 헬퍼 함수 ============
    
    def _has_korean(self, text: str) -> bool:
        """한글 포함 여부 확인"""
        for char in text:
            if ord(char) >= 0xAC00 and ord(char) <= 0xD7A3:
                return True
        return False
    
    def _validate_article(self, article_data: dict) -> bool:
        """기사 데이터 검증"""
        
        # 제목 검증
        if not article_data.get('title'):
            return False
        if len(article_data['title']) < 5:
            logger.debug(f"   제목 너무 짧음: {article_data['title']}")
            return False
        
        # URL 검증
        if not article_data.get('url') or len(article_data.get('url', '')) < 10:
            logger.debug(f"   URL 없음: {article_data['title'][:30]}")
            return False
        
        # 본문 검증
        if len(article_data.get('content', '')) < 10:
            logger.debug(f"   본문 너무 짧음: {article_data['title'][:30]}")
            return False
        
        return True
    
    def save_to_db(self, articles: list):
        """
        크롤링한 기사를 DB에 저장
        
        ✅ 개선 사항:
        - 데이터 검증 강화
        - 예외처리 및 로깅
        - 트랜잭션 관리
        """
        db = SessionLocal()
        saved_count = 0
        skipped_count = 0
        duplicate_count = 0
        
        try:
            for article_data in articles:
                # ✅ 1단계: 데이터 검증
                if not self._validate_article(article_data):
                    skipped_count += 1
                    continue
                
                # ✅ 2단계: 중복 확인
                existing = db.query(Article).filter(
                    Article.source_url == article_data['url']
                ).first()
                
                if existing:
                    duplicate_count += 1
                    continue
                
                # ✅ 3단계: DB 저장
                try:
                    new_article = Article(
                        title=article_data['title'][:500],
                        source_url=article_data['url'],
                        original_content=article_data['content'][:2000],  # 길이 제한
                        source_name=article_data['source'],
                        crawled_at=article_data.get('published_at', datetime.utcnow())
                    )
                    
                    db.add(new_article)
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"   저장 오류: {str(e)}")
                    db.rollback()
                    continue
            
            # ✅ 4단계: 커밋
            db.commit()
            logger.info(f"\n✅ 저장 완료")
            logger.info(f"   성공: {saved_count}개")
            logger.info(f"   중복: {duplicate_count}개")
            logger.info(f"   검증 실패: {skipped_count}개")
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ DB 커밋 실패: {str(e)}")
        finally:
            db.close()
    
    def run_crawl(self):
        """
        전체 크롤링 실행
        
        ✅ 목표: 5분 이내에 완료
        ✅ 스케줄 안전성 우선
        """
        import time
        start_time = time.time()
        
        logger.info("\n" + "="*60)
        logger.info("🔄 뉴스 크롤링 시작 (스케줄 기반)")
        logger.info("="*60 + "\n")
        
        all_articles = []
        
        # 1. FN뉴스 RSS
        logger.info("📡 Step 1: FN뉴스 RSS")
        all_articles.extend(self.crawl_fn_news_rss())
        
        # 2. 네이버 금융
        logger.info("📡 Step 2: 네이버금융")
        all_articles.extend(self.crawl_naver_finance())
        
        # 3. 이코노미스트
        logger.info("📡 Step 3: 이코노미스트")
        all_articles.extend(self.crawl_economist_rss())
        
        # 4. 결과
        elapsed = time.time() - start_time
        logger.info(f"\n📊 수집 완료")
        logger.info(f"   총 기사: {len(all_articles)}개")
        logger.info(f"   소요 시간: {elapsed:.1f}초\n")
        
        if len(all_articles) == 0:
            logger.warning("⚠️ 수집된 기사가 없습니다")
            return
        
        # 5. DB 저장
        logger.info("💾 DB 저장 중...")
        self.save_to_db(all_articles)
        
        # 6. 최종 요약
        elapsed = time.time() - start_time
        logger.info("\n" + "="*60)
        logger.info(f"✅ 크롤링 완료")
        logger.info(f"   전체 소요 시간: {elapsed:.1f}초")
        
        if elapsed > 300:
            logger.warning(f"   ⚠️ 5분 초과 (스케줄 지연 주의)")
        else:
            logger.info(f"   ✅ 스케줄 안전 (여유 시간 있음)")
        
        logger.info("="*60 + "\n")


if __name__ == "__main__":
    crawler = NewsCrawler()
    crawler.run_crawl()