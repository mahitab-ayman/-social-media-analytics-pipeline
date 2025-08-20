"""
Base collector class for social media platforms
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import structlog
from models import Post, Platform

logger = structlog.get_logger()

class BaseCollector(ABC):
    """Abstract base class for social media data collectors"""
    
    def __init__(self, platform: Platform, config: Dict[str, Any]):
        self.platform = platform
        self.config = config
        self.logger = logger.bind(platform=platform.value)
        
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the platform API"""
        pass
    
    @abstractmethod
    def collect_posts(self, 
                     query: Optional[str] = None,
                     user_id: Optional[str] = None,
                     limit: int = 100,
                     since_date: Optional[datetime] = None) -> List[Post]:
        """Collect posts from the platform"""
        pass
    
    @abstractmethod
    def get_user_posts(self, user_id: str, limit: int = 100) -> List[Post]:
        """Get posts from a specific user"""
        pass
    
    @abstractmethod
    def get_trending_posts(self, limit: int = 100) -> List[Post]:
        """Get trending posts from the platform"""
        pass
    
    def normalize_post(self, raw_post: Dict[str, Any]) -> Post:
        """Normalize raw post data to unified Post model"""
        try:
            return Post(
                post_id=str(raw_post.get('id', '')),
                platform=self.platform,
                content=raw_post.get('text', raw_post.get('content', '')),
                author_id=str(raw_post.get('author_id', '')),
                author_name=raw_post.get('author_name', raw_post.get('username', '')),
                likes=int(raw_post.get('likes', raw_post.get('favorite_count', 0))),
                comments=int(raw_post.get('comments', raw_post.get('reply_count', 0))),
                shares=int(raw_post.get('shares', raw_post.get('retweet_count', 0))),
                post_date=self._parse_date(raw_post.get('created_at', raw_post.get('date', ''))),
                url=raw_post.get('url', ''),
                media_urls=raw_post.get('media_urls', []),
                hashtags=raw_post.get('hashtags', []),
                mentions=raw_post.get('mentions', [])
            )
        except Exception as e:
            self.logger.error(f"Error normalizing post: {e}", raw_post=raw_post)
            raise
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object"""
        try:
            # Try common date formats
            formats = [
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # If all formats fail, return current time
            self.logger.warning(f"Could not parse date: {date_str}, using current time")
            return datetime.utcnow()
            
        except Exception as e:
            self.logger.error(f"Error parsing date {date_str}: {e}")
            return datetime.utcnow()
    
    def _handle_rate_limit(self, response: Dict[str, Any]) -> None:
        """Handle API rate limiting"""
        if 'rate_limit_remaining' in response:
            remaining = response['rate_limit_remaining']
            if remaining <= 5:
                self.logger.warning(f"Rate limit low: {remaining} requests remaining")
        
        if 'rate_limit_reset' in response:
            reset_time = response['rate_limit_reset']
            self.logger.info(f"Rate limit resets at: {reset_time}")
    
    def _retry_request(self, func, *args, max_retries: int = 3, **kwargs):
        """Retry API request with exponential backoff"""
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                
                wait_time = (2 ** attempt) * self.config.get('RETRY_DELAY', 5)
                self.logger.warning(f"Request failed, retrying in {wait_time}s: {e}")
                import time
                time.sleep(wait_time)
    
    def validate_credentials(self) -> bool:
        """Validate that required credentials are present"""
        required_fields = self.get_required_credentials()
        missing_fields = [field for field in required_fields if not self.config.get(field)]
        
        if missing_fields:
            self.logger.error(f"Missing required credentials: {missing_fields}")
            return False
        
        return True
    
    @abstractmethod
    def get_required_credentials(self) -> List[str]:
        """Get list of required credential field names"""
        pass
