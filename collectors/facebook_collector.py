"""
Facebook data collector using Facebook Graph API
"""
import facebook
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import structlog
from .base_collector import BaseCollector
from models import Post, Platform

logger = structlog.get_logger()

class FacebookCollector(BaseCollector):
    """Facebook data collector implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(Platform.FACEBOOK, config)
        self.graph = None
        self.access_token = None
        
    def get_required_credentials(self) -> List[str]:
        """Get required Facebook API credentials"""
        return [
            'FACEBOOK_APP_ID',
            'FACEBOOK_APP_SECRET',
            'FACEBOOK_ACCESS_TOKEN'
        ]
    
    def authenticate(self) -> bool:
        """Authenticate with Facebook Graph API"""
        try:
            if not self.validate_credentials():
                return False
            
            self.access_token = self.config['FACEBOOK_ACCESS_TOKEN']
            
            # Create Graph API instance
            self.graph = facebook.GraphAPI(access_token=self.access_token, version="3.1")
            
            # Test authentication by getting user info
            user_info = self.graph.get_object('me')
            self.logger.info(f"Successfully authenticated as: {user_info.get('name', 'Unknown')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Facebook authentication failed: {e}")
            return False
    
    def collect_posts(self, 
                     query: Optional[str] = None,
                     user_id: Optional[str] = None,
                     limit: int = 100,
                     since_date: Optional[datetime] = None) -> List[Post]:
        """Collect Facebook posts based on query or user"""
        if not self.graph:
            if not self.authenticate():
                return []
        
        posts = []
        
        try:
            if query:
                posts.extend(self._search_posts(query, limit, since_date))
            elif user_id:
                posts.extend(self._get_user_posts(user_id, limit))
            else:
                # Get trending posts from pages
                posts.extend(self._get_trending_posts(limit))
                
        except Exception as e:
            self.logger.error(f"Error collecting Facebook posts: {e}")
        
        return posts
    
    def get_user_posts(self, user_id: str, limit: int = 100) -> List[Post]:
        """Get posts from a specific user/page"""
        return self.collect_posts(user_id=user_id, limit=limit)
    
    def get_trending_posts(self, limit: int = 100) -> List[Post]:
        """Get trending posts from popular pages"""
        return self.collect_posts(limit=limit)
    
    def _search_posts(self, query: str, limit: int, since_date: Optional[datetime] = None) -> List[Post]:
        """Search Facebook posts using query"""
        posts = []
        
        try:
            # Facebook Graph API search for posts
            search_params = {
                'q': query,
                'type': 'post',
                'limit': min(limit, 100)
            }
            
            if since_date:
                # Facebook uses Unix timestamp
                search_params['since'] = int(since_date.timestamp())
            
            # Execute search
            response = self.graph.request('search', search_params)
            
            if 'data' in response:
                for post_data in response['data']:
                    post = self._convert_post_data_to_post(post_data)
                    if post and len(posts) < limit:
                        posts.append(post)
            
            # Handle pagination
            while len(posts) < limit and 'paging' in response and 'next' in response['paging']:
                next_url = response['paging']['next']
                response = requests.get(next_url).json()
                
                if 'data' in response:
                    for post_data in response['data']:
                        post = self._convert_post_data_to_post(post_data)
                        if post and len(posts) < limit:
                            posts.append(post)
                else:
                    break
                    
        except Exception as e:
            self.logger.error(f"Error searching Facebook posts: {e}")
        
        return posts
    
    def _get_user_posts(self, user_id: str, limit: int) -> List[Post]:
        """Get posts from a specific user/page"""
        posts = []
        
        try:
            # Get posts from user/page
            response = self.graph.get_object(
                f"{user_id}/posts",
                fields="id,message,created_time,from,likes.summary(true),comments.summary(true),shares",
                limit=min(limit, 100)
            )
            
            if 'data' in response:
                for post_data in response['data']:
                    post = self._convert_post_data_to_post(post_data)
                    if post:
                        posts.append(post)
                        
        except Exception as e:
            self.logger.error(f"Error getting user posts: {e}")
        
        return posts
    
    def _get_trending_posts(self, limit: int) -> List[Post]:
        """Get trending posts from popular pages"""
        # Popular pages to get trending posts from
        popular_pages = [
            'CNN', 'BBCNews', 'FoxNews', 'NBCNews',
            'ESPN', 'NBA', 'NFL', 'MLB',
            'Netflix', 'Disney', 'Marvel'
        ]
        
        posts = []
        
        for page_name in popular_pages:
            if len(posts) >= limit:
                break
            try:
                # Search for page
                page_search = self.graph.request('search', {'q': page_name, 'type': 'page'})
                if 'data' in page_search and page_search['data']:
                    page_id = page_search['data'][0]['id']
                    page_posts = self._get_user_posts(page_id, limit - len(posts))
                    posts.extend(page_posts)
            except Exception as e:
                self.logger.warning(f"Error getting posts from page {page_name}: {e}")
                continue
        
        return posts[:limit]
    
    def _convert_post_data_to_post(self, post_data: Dict[str, Any]) -> Optional[Post]:
        """Convert Facebook post data to Post model"""
        try:
            # Extract message content
            message = post_data.get('message', '')
            if not message:
                return None  # Skip posts without text content
            
            # Parse created time
            created_time = datetime.strptime(
                post_data['created_time'], 
                '%Y-%m-%dT%H:%M:%S%z'
            )
            
            # Get author information
            from_info = post_data.get('from', {})
            author_id = str(from_info.get('id', ''))
            author_name = from_info.get('name', 'Unknown')
            
            # Get engagement metrics
            likes_count = 0
            if 'likes' in post_data and 'summary' in post_data['likes']:
                likes_count = post_data['likes']['summary'].get('total_count', 0)
            
            comments_count = 0
            if 'comments' in post_data and 'summary' in post_data['comments']:
                comments_count = post_data['comments']['summary'].get('total_count', 0)
            
            shares_count = 0
            if 'shares' in post_data:
                shares_count = post_data['shares'].get('count', 0)
            
            # Extract hashtags and mentions from message
            hashtags = []
            mentions = []
            
            # Simple hashtag extraction (Facebook doesn't provide structured data)
            words = message.split()
            for word in words:
                if word.startswith('#'):
                    hashtags.append(word[1:])  # Remove # symbol
                elif word.startswith('@'):
                    mentions.append(word[1:])  # Remove @ symbol
            
            return Post(
                post_id=str(post_data['id']),
                platform=Platform.FACEBOOK,
                content=message,
                author_id=author_id,
                author_name=author_name,
                likes=likes_count,
                comments=comments_count,
                shares=shares_count,
                post_date=created_time,
                hashtags=hashtags,
                mentions=mentions
            )
            
        except Exception as e:
            self.logger.error(f"Error converting Facebook post to Post model: {e}")
            return None
    
    def _get_page_info(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a Facebook page"""
        try:
            return self.graph.get_object(
                page_id,
                fields="name,username,fan_count,category"
            )
        except Exception as e:
            self.logger.error(f"Error getting page info for {page_id}: {e}")
            return None
