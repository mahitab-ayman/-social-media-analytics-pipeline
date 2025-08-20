"""
Twitter data collector using Twitter API v2
"""
import tweepy
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import structlog
from .base_collector import BaseCollector
from models import Post, Platform

logger = structlog.get_logger()

class TwitterCollector(BaseCollector):
    """Twitter data collector implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(Platform.TWITTER, config)
        self.client = None
        self.api_v1 = None
        
    def get_required_credentials(self) -> List[str]:
        """Get required Twitter API credentials"""
        return [
            'TWITTER_API_KEY',
            'TWITTER_API_SECRET', 
            'TWITTER_BEARER_TOKEN'
        ]
    
    def authenticate(self) -> bool:
        """Authenticate with Twitter API"""
        try:
            if not self.validate_credentials():
                return False
            
            # Create API v2 client (recommended)
            self.client = tweepy.Client(
                bearer_token=self.config['TWITTER_BEARER_TOKEN'],
                consumer_key=self.config['TWITTER_API_KEY'],
                consumer_secret=self.config['TWITTER_API_SECRET'],
                access_token=self.config.get('TWITTER_ACCESS_TOKEN'),
                access_token_secret=self.config.get('TWITTER_ACCESS_TOKEN_SECRET'),
                wait_on_rate_limit=True
            )
            
            # Create API v1 client for additional endpoints
            auth = tweepy.OAuthHandler(
                self.config['TWITTER_API_KEY'],
                self.config['TWITTER_API_SECRET']
            )
            if self.config.get('TWITTER_ACCESS_TOKEN') and self.config.get('TWITTER_ACCESS_TOKEN_SECRET'):
                auth.set_access_token(
                    self.config['TWITTER_ACCESS_TOKEN'],
                    self.config['TWITTER_ACCESS_TOKEN_SECRET']
                )
            
            self.api_v1 = tweepy.API(auth, wait_on_rate_limit=True)
            
            # Test authentication
            me = self.client.get_me()
            self.logger.info(f"Successfully authenticated as: {me.data.username}")
            return True
            
        except Exception as e:
            self.logger.error(f"Twitter authentication failed: {e}")
            return False
    
    def collect_posts(self, 
                     query: Optional[str] = None,
                     user_id: Optional[str] = None,
                     limit: int = 100,
                     since_date: Optional[datetime] = None) -> List[Post]:
        """Collect tweets based on query or user"""
        if not self.client:
            if not self.authenticate():
                return []
        
        posts = []
        
        try:
            if query:
                posts.extend(self._search_tweets(query, limit, since_date))
            elif user_id:
                posts.extend(self._get_user_tweets(user_id, limit))
            else:
                # Get trending tweets
                posts.extend(self._get_trending_tweets(limit))
                
        except Exception as e:
            self.logger.error(f"Error collecting Twitter posts: {e}")
        
        return posts
    
    def get_user_posts(self, user_id: str, limit: int = 100) -> List[Post]:
        """Get tweets from a specific user"""
        return self.collect_posts(user_id=user_id, limit=limit)
    
    def get_trending_posts(self, limit: int = 100) -> List[Post]:
        """Get trending tweets"""
        return self.collect_posts(limit=limit)
    
    def _search_tweets(self, query: str, limit: int, since_date: Optional[datetime] = None) -> List[Post]:
        """Search tweets using query"""
        posts = []
        
        try:
            # Build search parameters
            search_params = {
                'query': query,
                'max_results': min(limit, 100),  # Twitter API v2 max is 100 per request
                'tweet_fields': 'created_at,public_metrics,author_id,entities',
                'user_fields': 'username,name',
                'expansions': 'author_id',
                'media_fields': 'url,preview_image_url'
            }
            
            if since_date:
                search_params['start_time'] = since_date.isoformat() + 'Z'
            
            # Execute search
            response = self.client.search_recent_tweets(**search_params)
            
            if response.data:
                # Create user lookup for author names
                user_lookup = {}
                if response.includes and 'users' in response.includes:
                    for user in response.includes['users']:
                        user_lookup[user.id] = user.username
                
                for tweet in response.data:
                    post = self._convert_tweet_to_post(tweet, user_lookup)
                    if post:
                        posts.append(post)
            
            # Handle pagination if needed
            while len(posts) < limit and response.meta.get('next_token'):
                search_params['next_token'] = response.meta['next_token']
                response = self.client.search_recent_tweets(**search_params)
                
                if response.data:
                    for tweet in response.data:
                        post = self._convert_tweet_to_post(tweet, user_lookup)
                        if post and len(posts) < limit:
                            posts.append(post)
                else:
                    break
                    
        except Exception as e:
            self.logger.error(f"Error searching tweets: {e}")
        
        return posts
    
    def _get_user_tweets(self, user_id: str, limit: int) -> List[Post]:
        """Get tweets from a specific user"""
        posts = []
        
        try:
            # Get user tweets
            response = self.client.get_users_tweets(
                id=user_id,
                max_results=min(limit, 100),
                tweet_fields='created_at,public_metrics,author_id,entities',
                user_fields='username,name',
                expansions='author_id'
            )
            
            if response.data:
                user_lookup = {}
                if response.includes and 'users' in response.includes:
                    for user in response.includes['users']:
                        user_lookup[user.id] = user.username
                
                for tweet in response.data:
                    post = self._convert_tweet_to_post(tweet, user_lookup)
                    if post:
                        posts.append(post)
                        
        except Exception as e:
            self.logger.error(f"Error getting user tweets: {e}")
        
        return posts
    
    def _get_trending_tweets(self, limit: int) -> List[Post]:
        """Get trending tweets (using popular hashtags)"""
        # For trending, we'll search for popular hashtags
        trending_hashtags = ['#tech', '#news', '#politics', '#sports', '#entertainment']
        posts = []
        
        for hashtag in trending_hashtags:
            if len(posts) >= limit:
                break
            posts.extend(self._search_tweets(hashtag, limit - len(posts)))
        
        return posts[:limit]
    
    def _convert_tweet_to_post(self, tweet, user_lookup: Dict[str, str]) -> Optional[Post]:
        """Convert Twitter tweet to Post model"""
        try:
            # Extract hashtags and mentions
            hashtags = []
            mentions = []
            
            if hasattr(tweet, 'entities') and tweet.entities:
                if 'hashtags' in tweet.entities:
                    hashtags = [tag['tag'] for tag in tweet.entities['hashtags']]
                if 'mentions' in tweet.entities:
                    mentions = [mention['username'] for mention in tweet.entities['mentions']]
            
            # Get metrics
            metrics = getattr(tweet, 'public_metrics', {})
            
            # Get author name
            author_name = user_lookup.get(tweet.author_id, 'Unknown')
            
            return Post(
                post_id=str(tweet.id),
                platform=Platform.TWITTER,
                content=tweet.text,
                author_id=str(tweet.author_id),
                author_name=author_name,
                likes=metrics.get('like_count', 0),
                comments=metrics.get('reply_count', 0),
                shares=metrics.get('retweet_count', 0),
                post_date=tweet.created_at,
                hashtags=hashtags,
                mentions=mentions
            )
            
        except Exception as e:
            self.logger.error(f"Error converting tweet to post: {e}")
            return None
