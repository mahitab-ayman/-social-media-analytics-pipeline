"""
YouTube data collector using YouTube Data API v3
"""
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import structlog
from .base_collector import BaseCollector
from models import Post, Platform

logger = structlog.get_logger()

class YouTubeCollector(BaseCollector):
    """YouTube data collector implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(Platform.YOUTUBE, config)
        self.youtube = None
        self.api_key = None
        
    def get_required_credentials(self) -> List[str]:
        """Get required YouTube API credentials"""
        return ['YOUTUBE_API_KEY']
    
    def authenticate(self) -> bool:
        """Authenticate with YouTube Data API"""
        try:
            if not self.validate_credentials():
                return False
            
            self.api_key = self.config['YOUTUBE_API_KEY']
            
            # Create YouTube API client
            self.youtube = build('youtube', 'v3', developerKey=self.api_key)
            
            # Test authentication by making a simple request
            test_response = self.youtube.search().list(
                part='snippet',
                q='test',
                maxResults=1
            ).execute()
            
            self.logger.info("Successfully authenticated with YouTube Data API")
            return True
            
        except Exception as e:
            self.logger.error(f"YouTube authentication failed: {e}")
            return False
    
    def collect_posts(self, 
                     query: Optional[str] = None,
                     user_id: Optional[str] = None,
                     limit: int = 100,
                     since_date: Optional[datetime] = None) -> List[Post]:
        """Collect YouTube videos based on query or channel"""
        if not self.youtube:
            if not self.authenticate():
                return []
        
        posts = []
        
        try:
            if query:
                posts.extend(self._search_videos(query, limit, since_date))
            elif user_id:
                posts.extend(self._get_channel_videos(user_id, limit))
            else:
                # Get trending videos
                posts.extend(self._get_trending_videos(limit))
                
        except Exception as e:
            self.logger.error(f"Error collecting YouTube videos: {e}")
        
        return posts
    
    def get_user_posts(self, user_id: str, limit: int = 100) -> List[Post]:
        """Get videos from a specific channel"""
        return self.collect_posts(user_id=user_id, limit=limit)
    
    def get_trending_posts(self, limit: int = 100) -> List[Post]:
        """Get trending videos"""
        return self.collect_posts(limit=limit)
    
    def _search_videos(self, query: str, limit: int, since_date: Optional[datetime] = None) -> List[Post]:
        """Search YouTube videos using query"""
        posts = []
        
        try:
            # Build search parameters
            search_params = {
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'order': 'relevance',
                'maxResults': min(limit, 50)  # YouTube API max is 50 per request
            }
            
            if since_date:
                # YouTube uses RFC 3339 format
                search_params['publishedAfter'] = since_date.isoformat() + 'Z'
            
            # Execute search
            response = self.youtube.search().list(**search_params).execute()
            
            if 'items' in response:
                video_ids = [item['id']['videoId'] for item in response['items']]
                
                # Get detailed video information including statistics
                video_details = self._get_video_details(video_ids)
                
                for item in response['items']:
                    video_id = item['id']['videoId']
                    if video_id in video_details:
                        post = self._convert_video_to_post(item, video_details[video_id])
                        if post:
                            posts.append(post)
            
            # Handle pagination if needed
            while len(posts) < limit and 'nextPageToken' in response:
                search_params['pageToken'] = response['nextPageToken']
                response = self.youtube.search().list(**search_params).execute()
                
                if 'items' in response:
                    video_ids = [item['id']['videoId'] for item in response['items']]
                    video_details = self._get_video_details(video_ids)
                    
                    for item in response['items']:
                        video_id = item['id']['videoId']
                        if video_id in video_details and len(posts) < limit:
                            post = self._convert_video_to_post(item, video_details[video_id])
                            if post:
                                posts.append(post)
                else:
                    break
                    
        except HttpError as e:
            self.logger.error(f"YouTube API error: {e}")
        except Exception as e:
            self.logger.error(f"Error searching YouTube videos: {e}")
        
        return posts
    
    def _get_channel_videos(self, channel_id: str, limit: int) -> List[Post]:
        """Get videos from a specific channel"""
        posts = []
        
        try:
            # Get channel's uploads playlist
            channel_response = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            ).execute()
            
            if 'items' in channel_response and channel_response['items']:
                uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                
                # Get videos from uploads playlist
                playlist_response = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=uploads_playlist_id,
                    maxResults=min(limit, 50)
                ).execute()
                
                if 'items' in playlist_response:
                    video_ids = [item['snippet']['resourceId']['videoId'] for item in playlist_response['items']]
                    video_details = self._get_video_details(video_ids)
                    
                    for item in playlist_response['items']:
                        video_id = item['snippet']['resourceId']['videoId']
                        if video_id in video_details:
                            post = self._convert_video_to_post(item['snippet'], video_details[video_id])
                            if post:
                                posts.append(post)
                                
        except HttpError as e:
            self.logger.error(f"YouTube API error: {e}")
        except Exception as e:
            self.logger.error(f"Error getting channel videos: {e}")
        
        return posts
    
    def _get_trending_videos(self, limit: int) -> List[Post]:
        """Get trending videos"""
        posts = []
        
        try:
            # Get trending videos
            response = self.youtube.videos().list(
                part='snippet,statistics',
                chart='mostPopular',
                regionCode='US',
                maxResults=min(limit, 50)
            ).execute()
            
            if 'items' in response:
                for item in response['items']:
                    post = self._convert_video_to_post(item['snippet'], item['statistics'])
                    if post:
                        posts.append(post)
                        
        except HttpError as e:
            self.logger.error(f"YouTube API error: {e}")
        except Exception as e:
            self.logger.error(f"Error getting trending videos: {e}")
        
        return posts
    
    def _get_video_details(self, video_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get detailed information for multiple videos"""
        video_details = {}
        
        try:
            # YouTube API allows up to 50 video IDs per request
            for i in range(0, len(video_ids), 50):
                batch_ids = video_ids[i:i+50]
                
                response = self.youtube.videos().list(
                    part='statistics',
                    id=','.join(batch_ids)
                ).execute()
                
                if 'items' in response:
                    for item in response['items']:
                        video_details[item['id']] = item['statistics']
                        
        except HttpError as e:
            self.logger.error(f"YouTube API error getting video details: {e}")
        except Exception as e:
            self.logger.error(f"Error getting video details: {e}")
        
        return video_details
    
    def _convert_video_to_post(self, video_snippet: Dict[str, Any], video_stats: Dict[str, Any]) -> Optional[Post]:
        """Convert YouTube video to Post model"""
        try:
            # Extract video information
            video_id = video_snippet.get('id', video_snippet.get('resourceId', {}).get('videoId', ''))
            if not video_id:
                return None
            
            title = video_snippet.get('title', '')
            description = video_snippet.get('description', '')
            content = f"{title}\n\n{description[:200]}..." if len(description) > 200 else f"{title}\n\n{description}"
            
            # Parse published date
            published_at = datetime.strptime(
                video_snippet['publishedAt'], 
                '%Y-%m-%dT%H:%M:%SZ'
            )
            
            # Get channel information
            channel_id = video_snippet['channelId']
            channel_name = video_snippet['channelTitle']
            
            # Get engagement metrics
            view_count = int(video_stats.get('viewCount', 0))
            like_count = int(video_stats.get('likeCount', 0))
            comment_count = int(video_stats.get('commentCount', 0))
            
            # YouTube doesn't have shares, so we'll use views as a proxy for reach
            # and calculate engagement as likes + comments
            shares = 0  # YouTube doesn't provide share count
            
            # Extract hashtags from description (YouTube supports hashtags in descriptions)
            hashtags = []
            words = description.split()
            for word in words:
                if word.startswith('#'):
                    hashtags.append(word[1:])  # Remove # symbol
            
            return Post(
                post_id=video_id,
                platform=Platform.YOUTUBE,
                content=content,
                author_id=channel_id,
                author_name=channel_name,
                likes=like_count,
                comments=comment_count,
                shares=shares,
                post_date=published_at,
                url=f"https://www.youtube.com/watch?v={video_id}",
                hashtags=hashtags
            )
            
        except Exception as e:
            self.logger.error(f"Error converting YouTube video to Post model: {e}")
            return None
    
    def _get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a YouTube channel"""
        try:
            response = self.youtube.channels().list(
                part='snippet,statistics',
                id=channel_id
            ).execute()
            
            if 'items' in response and response['items']:
                return response['items'][0]
            return None
            
        except HttpError as e:
            self.logger.error(f"YouTube API error getting channel info: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting channel info: {e}")
            return None
