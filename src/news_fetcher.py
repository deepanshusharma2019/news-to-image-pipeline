"""
News Fetcher Module
Handles fetching news headlines from various sources including RSS feeds and APIs.
"""

import logging
import feedparser
import requests
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class NewsItem:
    """Data class for news items."""
    title: str
    summary: str
    url: str
    published: datetime
    source: str


class NewsFetcher:
    """Fetches news from multiple sources."""
    
    def __init__(self, config: Dict):
        """Initialize news fetcher with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Default RSS feeds if none configured
        self.rss_feeds = config.get('rss_feeds', [
            {'name': 'BBC News', 'url': 'http://feeds.bbci.co.uk/news/rss.xml'},
            {'name': 'CNN', 'url': 'http://rss.cnn.com/rss/edition.rss'},
            {'name': 'Reuters', 'url': 'http://feeds.reuters.com/reuters/topNews'},
            {'name': 'Associated Press', 'url': 'https://feeds.apnews.com/rss/apf-topnews'}
        ])
        
        # News API configuration (optional)
        self.news_api_key = config.get('news_api_key')
        self.keywords = config.get('keywords', ['technology', 'science', 'world'])
        
    def get_latest_headlines(self, limit: int = 10) -> List[str]:
        """Get latest headlines from all configured sources."""
        headlines = []
        
        # Fetch from RSS feeds
        for feed in self.rss_feeds:
            try:
                feed_headlines = self._fetch_rss_headlines(feed, limit // len(self.rss_feeds))
                headlines.extend(feed_headlines)
            except Exception as e:
                self.logger.error(f"Error fetching from {feed['name']}: {e}")
        
        # Fetch from News API if configured
        if self.news_api_key:
            try:
                api_headlines = self._fetch_news_api_headlines(limit // 2)
                headlines.extend(api_headlines)
            except Exception as e:
                self.logger.error(f"Error fetching from News API: {e}")
        
        # Remove duplicates and limit results
        unique_headlines = list(dict.fromkeys(headlines))[:limit]
        self.logger.info(f"Fetched {len(unique_headlines)} unique headlines")
        
        return unique_headlines
    
    def _fetch_rss_headlines(self, feed: Dict, limit: int = 5) -> List[str]:
        """Fetch headlines from RSS feed."""
        try:
            self.logger.debug(f"Fetching from RSS: {feed['name']}")
            parsed_feed = feedparser.parse(feed['url'])
            
            headlines = []
            for entry in parsed_feed.entries[:limit]:
                # Clean up the title
                title = entry.title.strip()
                if title and len(title) > 10:  # Filter out very short titles
                    headlines.append(title)
            
            return headlines
            
        except Exception as e:
            self.logger.error(f"RSS fetch error for {feed['name']}: {e}")
            return []
    
    def _fetch_news_api_headlines(self, limit: int = 5) -> List[str]:
        """Fetch headlines from News API."""
        if not self.news_api_key:
            return []
        
        try:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                'apiKey': self.news_api_key,
                'language': 'en',
                'pageSize': limit,
                'category': 'general'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            headlines = []
            
            for article in data.get('articles', []):
                title = article.get('title', '').strip()
                if title and len(title) > 10:
                    headlines.append(title)
            
            return headlines
            
        except Exception as e:
            self.logger.error(f"News API fetch error: {e}")
            return []
    
    def get_news_items(self, limit: int = 10) -> List[NewsItem]:
        """Get detailed news items with metadata."""
        items = []
        
        for feed in self.rss_feeds:
            try:
                feed_items = self._fetch_rss_items(feed, limit // len(self.rss_feeds))
                items.extend(feed_items)
            except Exception as e:
                self.logger.error(f"Error fetching detailed items from {feed['name']}: {e}")
        
        return sorted(items, key=lambda x: x.published, reverse=True)[:limit]
    
    def _fetch_rss_items(self, feed: Dict, limit: int = 5) -> List[NewsItem]:
        """Fetch detailed news items from RSS feed."""
        try:
            parsed_feed = feedparser.parse(feed['url'])
            items = []
            
            for entry in parsed_feed.entries[:limit]:
                # Parse published date
                published = datetime.now()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                
                item = NewsItem(
                    title=entry.title.strip(),
                    summary=getattr(entry, 'summary', '')[:200] + '...',
                    url=getattr(entry, 'link', ''),
                    published=published,
                    source=feed['name']
                )
                items.append(item)
            
            return items
            
        except Exception as e:
            self.logger.error(f"RSS items fetch error for {feed['name']}: {e}")
            return []
    
    def filter_by_keywords(self, headlines: List[str], keywords: List[str] = None) -> List[str]:
        """Filter headlines by keywords."""
        if not keywords:
            keywords = self.keywords
        
        filtered = []
        for headline in headlines:
            if any(keyword.lower() in headline.lower() for keyword in keywords):
                filtered.append(headline)
        
        return filtered if filtered else headlines[:3]  # Return top 3 if no matches
