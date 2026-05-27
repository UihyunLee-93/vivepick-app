import requests
from bs4 import BeautifulSoup
from database import SessionLocal, Article
from datetime import datetime
import os
from typing import List, Dict
import logging
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsCrawler:
    """금융 뉴스 크롤링"""
    
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    # ============ 뉴스 소스 1: XML ElementTree로 RSS 크롤링 ============
    
    def crawl_financial_news_rss(self) -> List[Dict]:
        """ElementTree로 RSS 파싱 (외부 라이브러리 불필요)"""
        articles = []
        
        rss_feeds = [
            "https://www.fnnews.com/rss/headline.xml",
            "https://feeds.bloomberg.com/markets/news.rss",
            "https://feeds2.cnbc.com/cnbc-intl/",
        ]
        
        for feed_url in rss_feeds:
            try:
                response = self.session.get(feed_url, timeout=10, headers=self.headers)
                response.encoding = 'utf-8'
                
                # XML ElementTree 사용 (Python 내장)
                root = ET.fromstring(response.content)
                
                # RSS 네임스페이스
                ns = {'': 'http://www.rss.org/2.0/'}
                
                # item 태그 찾기
                items = root.findall('.//item')
                
                for item in items[:10]:
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    desc_elem = item.find('description')
                    
                    if title_elem is not None and link_elem is not None:
                        title = title_elem.text or ''
                        link = link_elem.text or ''
                        desc = desc_elem.text if desc_elem is not None else ''
                        
                        if title and link:  # title과 link 모두 있을 때만
                            articles.append({
                                'title': title.strip(),
                                'url': link.strip(),
                                'content': desc.strip() if desc else '',
                                'source': feed_url.split('/')[-2],
                                'published_at': datetime.utcnow()
                            })
                
                logger.info(f"✅ RSS 크롤링 성공: {feed_url} ({len([a for a in articles if feed_url.split('/')[-2] in a['source']])}개)")
                
            except Exception as e:
                logger.error(f"RSS 크롤링 실패 ({feed_url}): {str(e)}")
        
        return articles
    
    # ============ 뉴스 소스 2: Finnhub (주식 API) ============
    
    def crawl_finnhub_news(self) -> List[Dict]:
        """Finnhub API로 금융 뉴스 수집"""
        articles = []
        api_key = os.getenv("FINNHUB_API_KEY")
        
        if not api_key:
            logger.warning("FINNHUB_API_KEY 없음 - Finnhub 크롤링 스킵")
            return articles
        
        try:
            url = "https://finnhub.io/api/v1/news"
            params = {
                "category": "finance",
                "token": api_key,
                "minId": 0
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'data' in data:
                for item in data['data'][:20]:
                    articles.append({
                        'title': item.get('headline', ''),
                        'url': item.get('url', ''),
                        'content': item.get('summary', ''),
                        'source': item.get('source', 'Finnhub'),
                        'published_at': datetime.fromtimestamp(item.get('datetime', datetime.utcnow().timestamp()))
                    })
                
                logger.info(f"✅ Finnhub 크롤링 성공: {len(articles)}개 기사")
        except Exception as e:
            logger.error(f"Finnhub 크롤링 실패: {str(e)}")
        
        return articles
    
    # ============ 뉴스 소스 3: Naver 금융 ============
    
    def crawl_naver_finance(self) -> List[Dict]:
        """네이버 금융 뉴스 수집"""
        articles = []
        
        try:
            url = "https://finance.naver.com/news/mainnews.naver"
            response = self.session.get(url, timeout=10, headers=self.headers)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            news_items = soup.select("div.newsList > ul > li")
            
            logger.info(f"📰 네이버 뉴스 항목 찾음: {len(news_items)}개")
            
            for item in news_items[:30]:
                try:
                    title_elem = item.select_one("a.nclicks")
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        news_url = title_elem.get('href', '')
                        
                        if news_url:
                            try:
                                detail_response = self.session.get(
                                    news_url, 
                                    timeout=10, 
                                    headers=self.headers
                                )
                                detail_response.encoding = 'utf-8'
                                detail_soup = BeautifulSoup(detail_response.content, 'html.parser')
                                
                                content_elem = detail_soup.select_one("div#dic_area")
                                content = content_elem.get_text(strip=True) if content_elem else ""
                                
                                articles.append({
                                    'title': title,
                                    'url': news_url,
                                    'content': content[:1000],
                                    'source': 'Naver Finance',
                                    'published_at': datetime.utcnow()
                                })
                            except Exception as e:
                                logger.debug(f"⚠️ 네이버 상세 크롤링 실패: {str(e)}")
                                continue
                except Exception as e:
                    logger.debug(f"⚠️ 네이버 항목 처리 실패: {str(e)}")
                    continue
            
            if articles:
                logger.info(f"✅ 네이버 금융 크롤링 성공: {len(articles)}개 기사")
            else:
                logger.warning("⚠️ 네이버 금융 크롤링: 기사 없음")
                
        except Exception as e:
            logger.error(f"네이버 금융 크롤링 실패: {str(e)}")
        
        return articles
    
    def save_to_db(self, articles: List[Dict]):
        """크롤링한 기사를 DB에 저장"""
        db = SessionLocal()
        saved_count = 0
        
        try:
            for article_data in articles:
                # URL이 비어있으면 스킵
                if not article_data.get('url'):
                    logger.warning(f"⏭️  URL 없음: {article_data['title'][:50]}")
                    continue
                
                # 중복 확인
                existing = db.query(Article).filter(
                    Article.source_url == article_data['url']
                ).first()
                
                if existing:
                    logger.info(f"⏭️  이미 존재: {article_data['title'][:50]}")
                    continue
                
                # 새 기사 저장
                new_article = Article(
                    title=article_data['title'],
                    source_url=article_data['url'],
                    original_content=article_data['content'],
                    source_name=article_data['source'],
                    crawled_at=article_data.get('published_at', datetime.utcnow())
                )
                
                db.add(new_article)
                saved_count += 1
                logger.info(f"✅ 저장: {article_data['title'][:50]}")
            
            db.commit()
            logger.info(f"\n✨ 총 {saved_count}개 기사 저장 완료\n")
            
        except Exception as e:
            db.rollback()
            logger.error(f"DB 저장 실패: {str(e)}")
        finally:
            db.close()
    
    def run_crawl(self):
        """전체 크롤링 실행"""
        logger.info("🔄 뉴스 크롤링 시작...\n")
        
        all_articles = []
        
        logger.info("📡 RSS 피드 크롤링 중...")
        all_articles.extend(self.crawl_financial_news_rss())
        
        logger.info("📡 Finnhub API 크롤링 중...")
        all_articles.extend(self.crawl_finnhub_news())
        
        logger.info("📡 네이버 금융 크롤링 중...")
        all_articles.extend(self.crawl_naver_finance())
        
        logger.info(f"📰 총 {len(all_articles)}개 기사 수집\n")
        
        if len(all_articles) == 0:
            logger.warning("⚠️ 수집된 기사가 없습니다. 나중에 다시 시도하세요.")
        
        self.save_to_db(all_articles)


if __name__ == "__main__":
    crawler = NewsCrawler()
    crawler.run_crawl()