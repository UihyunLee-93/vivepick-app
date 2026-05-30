import requests
from database import SessionLocal, Article
from datetime import datetime
import logging
import time
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsCrawler:
    """네이버 뉴스 API - 카테고리 기반 + 투자 관련성 필터링"""
    
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
        
        self.categories = {
            "AI · 기술": [
                "생성형AI",
                "AI칩",
                "NVIDIA",
                "반도체",
                "클라우드"
            ],
            "금융": [
                "금리인상",
                "금융시장",
                "한은",
                "국채",
                "환율"
            ],
            "에너지": [
                "유가",
                "태양광",
                "배터리",
                "원유",
                "전기요금"
            ],
            "모빌리티": [
                "전기차",
                "자율주행",
                "현대차",
                "자동차주",
                "기아주가"
            ],
            "바이오": [
                "신약승인",
                "임상시험",
                "제약주",
                "바이오",
                "셀트리온"
            ],
            "소비 · 라이프": [
                "소비심리",
                "경기둔화",
                "소비지수",
                "부동산",
                "주택"
            ],
            "산업 · 제조": [
                "조선주",
                "철강주",
                "포스코",
                "한화",
                "방산주",
                "HD현대",
                "두산에너빌"
            ],
            "글로벌": [
                "미국주식",
                "연방준비제도",
                "글로벌기업",
                "나스닥",
                "S&P500"
            ],
            "크립토": [
                "비트코인",
                "블록체인",
                "암호화폐",
                "가상자산",
                "코인ETF"
            ],
            "콘텐츠 · 엔터": [
                "웹툰",
                "게임주",
                "넷플릭스",
                "카카오",
                "하이브주가"
            ]
        }
        
        self.exclude_keywords = [
            "공무원", "시장", "구청", "후보", "선거", "정당",
            "정책자금", "대출", "착수금",
            "포상", "기념식", "행사", "봉사",
            "교육", "장학금", "학교",
            "대회", "스포츠",
            "공고", "채용공고",
            "분양", "입찰", "계약건",
            "세미나", "발표회"
        ]
        
        self.required_keywords = [
            "주가", "수익", "실적", "주식", "종목",
            "상승", "하락", "급등", "급락",
            "기업", "시장", "수급", "지수",
            "투자", "수익률", "리스크",
            "상장", "공모", "증자",
            "컨센서스", "목표가", "리포트"
        ]
    
    def is_investment_relevant(self, title: str, content: str) -> bool:
        """투자 관련성 판단"""
        text = (title + " " + content).lower()
        
        for keyword in self.exclude_keywords:
            if keyword in text:
                return False
        
        for keyword in self.required_keywords:
            if keyword in text:
                return True
        
        return False
    
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
                    collected = 0
                    filtered = 0
                    
                    for item in data.get('items', []):
                        try:
                            title = item.get('title', '')
                            link = item.get('link', '')
                            desc = item.get('description', '')
                            
                            title = title.replace('<b>', '').replace('</b>', '')
                            desc = desc.replace('<b>', '').replace('</b>', '')
                            
                            if not (title and link):
                                continue
                            
                            if not self.is_investment_relevant(title, desc):
                                filtered += 1
                                logger.debug(f"      ⊘ 필터 제외: {title[:40]}")
                                continue
                            
                            articles.append({
                                'title': title,
                                'url': link,
                                'content': desc if len(desc) > 10 else title,
                                'source': '네이버뉴스',
                                'category': category,
                                'published_at': datetime.utcnow()
                            })
                            
                            logger.info(f"      ✅ {title[:50]}")
                            collected += 1
                        
                        except:
                            continue
                    
                    logger.info(f"   수집: {collected}개, 필터제외: {filtered}개")
                
                elif response.status_code == 401:
                    logger.error("   ❌ API 키 오류")
                    return articles
                
                time.sleep(0.5)
                
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
                    
                    source_name = f"{article_data['source']} - {article_data.get('category', '')}"
                    
                    new_article = Article(
                        title=article_data['title'][:500],
                        source_url=article_data['url'],
                        original_content=article_data['content'][:2000],
                        source_name=source_name,
                        crawled_at=article_data.get('published_at', datetime.utcnow())
                    )
                    
                    db.add(new_article)
                    db.flush()
                    saved_count += 1
                    
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
        logger.info("🔄 투자 관련성 필터링 크롤링 시작")
        logger.info("="*60)
        
        if not self.client_id:
            logger.warning("⚠️  네이버 API 키 없음")
            return
        
        logger.info("✅ 네이버 API 키 감지됨\n")
        
        all_articles = []
        
        for category, keywords in self.categories.items():
            category_articles = self.crawl_category_news(category, keywords)
            all_articles.extend(category_articles)
        
        elapsed = time.time() - start_time
        logger.info(f"\n📊 총 수집: {len(all_articles)}개 ({elapsed:.1f}초)")
        
        if len(all_articles) == 0:
            logger.warning("⚠️  수집된 기사가 없습니다")
            logger.info("="*60 + "\n")
            return
        
        self.save_to_db(all_articles)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ 완료 ({elapsed:.1f}초)")
        logger.info("="*60 + "\n")


if __name__ == "__main__":
    crawler = NewsCrawler()
    crawler.run_crawl()