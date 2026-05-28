import requests
from bs4 import BeautifulSoup
from database import SessionLocal, Article
from datetime import datetime
import logging
import time
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsCrawler:
    """네이버 뉴스 검색 API를 사용한 크롤링"""
    
    def __init__(self):
        # ⚠️ 환경변수에서 API 키 가져오기
        self.client_id = os.getenv("NAVER_CLIENT_ID")
        self.client_secret = os.getenv("NAVER_CLIENT_SECRET")
        
        if not self.client_id or not self.client_secret:
            logger.warning("⚠️  네이버 API 키가 없습니다")
            logger.warning("   환경변수 설정: NAVER_CLIENT_ID, NAVER_CLIENT_SECRET")
            self.client_id = None
            self.client_secret = None
        
        self.headers = {
            "X-Naver-Client-Id": self.client_id or "",
            "X-Naver-Client-Secret": self.client_secret or ""
        }
        
        # 크롤링할 키워드들 (금융/기술/주식)
        self.keywords = [
            "삼성전자 주가",
            "SK하이닉스",
            "LG에너지솔루션",
            "현대자동차",
            "셀트리온",
            "카카오",
            "네이버",
            "AI칩",
            "반도체",
            "전기차 배터리"
        ]
    
    def crawl_naver_news(self) -> list:
        """네이버 뉴스 검색 API를 사용한 크롤링"""
        articles = []
        
        if not self.client_id:
            logger.error("❌ 네이버 API 키 없음 - 더미 데이터 사용")
            return self._get_dummy_articles()
        
        try:
            for keyword in self.keywords:
                try:
                    logger.info(f"   검색어: {keyword}")
                    
                    url = "https://openapi.naver.com/v1/search/news.json"
                    params = {
                        "query": keyword,
                        "display": 10,  # 10개씩
                        "start": 1,
                        "sort": "date"  # 최신순
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
                                
                                # HTML 태그 제거
                                title = title.replace('<b>', '').replace('</b>', '')
                                desc = desc.replace('<b>', '').replace('</b>', '')
                                
                                if not (title and link and self._has_korean(title)):
                                    continue
                                
                                articles.append({
                                    'title': title,
                                    'url': link,
                                    'content': desc if len(desc) > 10 else title,
                                    'source': '네이버뉴스',
                                    'published_at': datetime.utcnow()
                                })
                                
                                logger.info(f"      ✅ {title[:50]}")
                            
                            except Exception as e:
                                logger.debug(f"      항목 오류: {str(e)}")
                                continue
                        
                        logger.info(f"   수집: {len([a for a in articles if a['source'] == '네이버뉴스'])}개")
                    
                    elif response.status_code == 401:
                        logger.error("   ❌ API 키 오류 (NAVER_CLIENT_ID, NAVER_CLIENT_SECRET 확인)")
                        return self._get_dummy_articles()
                    
                    elif response.status_code == 429:
                        logger.warning("   ⚠️  Rate limit 초과 (5초 대기)")
                        time.sleep(5)
                    
                    else:
                        logger.warning(f"   ⚠️  HTTP {response.status_code}")
                    
                    # API 요청 간격 (차단 방지)
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"   ❌ 오류: {str(e)}")
                    continue
        
        except Exception as e:
            logger.error(f"❌ 크롤링 중 오류: {str(e)}")
        
        return articles
    
    def _has_korean(self, text: str) -> bool:
        """한글 포함 여부"""
        for char in text:
            if ord(char) >= 0xAC00 and ord(char) <= 0xD7A3:
                return True
        return False
    
    def _get_dummy_articles(self) -> list:
        """API 키 없을 때 더미 데이터 반환"""
        logger.info("   📌 더미 데이터 사용 (API 키 없음)")
        return [
            {
                'title': '삼성전자, AI 칩셋 수요로 2분기 영업이익 49% 증가',
                'url': 'https://news.naver.com/dummy1',
                'content': '반도체 시장의 AI 칩셋 수요가 급증하면서 삼성전자의 2분기 영업이익이 증가했습니다.',
                'source': '네이버뉴스',
                'published_at': datetime.utcnow()
            },
            {
                'title': 'SK하이닉스, HBM 메모리 수주 50% 증가',
                'url': 'https://news.naver.com/dummy2',
                'content': 'AI 데이터센터 수요 증가로 고대역폭 메모리(HBM) 수주가 급증했습니다.',
                'source': '네이버뉴스',
                'published_at': datetime.utcnow()
            },
            {
                'title': 'LG에너지솔루션, 전기차 배터리 주문 55% 증가',
                'url': 'https://news.naver.com/dummy3',
                'content': '글로벌 자동차 업체들의 전기차 배터리 주문이 증가하고 있습니다.',
                'source': '네이버뉴스',
                'published_at': datetime.utcnow()
            },
            {
                'title': '현대차, AI 기반 자율주행 기술 개발비 2배 증가',
                'url': 'https://news.naver.com/dummy4',
                'content': '현대자동차가 AI 자율주행 기술 개발에 투자를 확대하고 있습니다.',
                'source': '네이버뉴스',
                'published_at': datetime.utcnow()
            },
            {
                'title': '셀트리온, 바이오신약 임상시험 3상 진입',
                'url': 'https://news.naver.com/dummy5',
                'content': '셀트리온이 자체 개발 신약의 3상 임상시험 진입을 공식 발표했습니다.',
                'source': '네이버뉴스',
                'published_at': datetime.utcnow()
            }
        ]
    
    def save_to_db(self, articles: list):
        """DB 저장"""
        db = SessionLocal()
        saved_count = 0
        duplicate_count = 0
        
        try:
            for article_data in articles:
                # URL 검증
                if not article_data.get('url'):
                    continue
                
                # 중복 확인
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
        """크롤링 실행"""
        start_time = time.time()
        
        logger.info("\n" + "="*60)
        logger.info("🔄 네이버 뉴스 API 크롤링 시작")
        logger.info("="*60)
        
        if self.client_id:
            logger.info("✅ 네이버 API 키 감지됨")
        else:
            logger.warning("⚠️  네이버 API 키 없음 → 더미 데이터 사용")
        
        logger.info("\n📡 네이버 뉴스 검색 중...")
        articles = self.crawl_naver_news()
        
        elapsed = time.time() - start_time
        logger.info(f"\n📊 수집 완료: {len(articles)}개 ({elapsed:.1f}초)")
        
        if len(articles) == 0:
            logger.warning("⚠️  기사 0개")
            logger.info("="*60 + "\n")
            return
        
        logger.info("💾 DB 저장 중...")
        self.save_to_db(articles)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ 완료 ({elapsed:.1f}초)")
        logger.info("="*60 + "\n")


if __name__ == "__main__":
    crawler = NaverNewsCrawler()
    crawler.run_crawl()