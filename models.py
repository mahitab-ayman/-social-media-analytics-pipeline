"""
Data models for Social Media Analytics Pipeline
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum

class Platform(str, Enum):
    """Social media platforms"""
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"

class Post(BaseModel):
    """Unified social media post model"""
    post_id: str = Field(..., description="Unique identifier for the post")
    platform: Platform = Field(..., description="Social media platform")
    content: str = Field(..., description="Post content/text")
    author_id: str = Field(..., description="Author/User ID")
    author_name: Optional[str] = Field(None, description="Author display name")
    likes: int = Field(default=0, description="Number of likes")
    comments: int = Field(default=0, description="Number of comments")
    shares: int = Field(default=0, description="Number of shares/retweets")
    post_date: datetime = Field(..., description="Post creation date/time")
    collected_at: datetime = Field(default_factory=datetime.utcnow, description="When data was collected")
    
    # Optional fields for platform-specific data
    url: Optional[str] = Field(None, description="Post URL")
    media_urls: Optional[List[str]] = Field(None, description="Media URLs attached to post")
    hashtags: Optional[List[str]] = Field(None, description="Hashtags in the post")
    mentions: Optional[List[str]] = Field(None, description="User mentions in the post")
    
    @property
    def engagement_score(self) -> int:
        """Calculate total engagement score"""
        return self.likes + self.comments + self.shares
    
    @validator('likes', 'comments', 'shares')
    def validate_engagement_metrics(cls, v):
        """Ensure engagement metrics are non-negative"""
        if v < 0:
            raise ValueError('Engagement metrics must be non-negative')
        return v
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class DailyMetrics(BaseModel):
    """Daily engagement metrics per platform"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    platform: Platform = Field(..., description="Social media platform")
    total_posts: int = Field(..., description="Total posts for the day")
    total_likes: int = Field(..., description="Total likes for the day")
    total_comments: int = Field(..., description="Total comments for the day")
    total_shares: int = Field(..., description="Total shares for the day")
    total_engagement: int = Field(..., description="Total engagement score for the day")
    avg_engagement_per_post: float = Field(..., description="Average engagement per post")
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True

class TopPost(BaseModel):
    """Top performing post model"""
    post_id: str = Field(..., description="Post ID")
    platform: Platform = Field(..., description="Platform")
    content: str = Field(..., description="Post content (truncated)")
    engagement_score: int = Field(..., description="Total engagement score")
    likes: int = Field(..., description="Likes count")
    comments: int = Field(..., description="Comments count")
    shares: int = Field(..., description="Shares count")
    post_date: datetime = Field(..., description="Post date")
    author_name: Optional[str] = Field(None, description="Author name")
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class MovingAverage(BaseModel):
    """Moving average metrics"""
    platform: Platform = Field(..., description="Platform")
    date: str = Field(..., description="Date")
    moving_avg_7d: float = Field(..., description="7-day moving average of engagement")
    moving_avg_30d: float = Field(..., description="30-day moving average of engagement")
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True

class AnalyticsSummary(BaseModel):
    """Complete analytics summary"""
    date: str = Field(..., description="Analysis date")
    daily_metrics: List[DailyMetrics] = Field(..., description="Daily metrics per platform")
    top_posts_overall: List[TopPost] = Field(..., description="Top 5 posts across all platforms")
    top_posts_per_platform: dict = Field(..., description="Top 3 posts per platform")
    moving_averages: List[MovingAverage] = Field(..., description="Moving averages per platform")
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
