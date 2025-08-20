"""
Data processor for social media analytics
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog
from models import Post, DailyMetrics, TopPost, MovingAverage, AnalyticsSummary, Platform

logger = structlog.get_logger()

class DataProcessor:
    """Data processor for social media analytics"""
    
    def __init__(self):
        self.logger = logger.bind(component='data_processor')
    
    def process_posts(self, posts: List[Post]) -> pd.DataFrame:
        """Convert posts to pandas DataFrame for analysis"""
        try:
            if not posts:
                self.logger.warning("No posts to process")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame([post.dict() for post in posts])
            
            # Convert datetime columns
            df['post_date'] = pd.to_datetime(df['post_date'])
            df['collected_at'] = pd.to_datetime(df['collected_at'])
            
            # Add date column for grouping
            df['date'] = df['post_date'].dt.date.astype(str)
            
            # Ensure engagement metrics are numeric
            numeric_columns = ['likes', 'comments', 'shares']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Calculate engagement score
            df['engagement_score'] = df['likes'] + df['comments'] + df['shares']
            
            self.logger.info(f"Processed {len(df)} posts")
            return df
            
        except Exception as e:
            self.logger.error(f"Error processing posts: {e}")
            return pd.DataFrame()
    
    def compute_daily_metrics(self, df: pd.DataFrame) -> List[DailyMetrics]:
        """Compute daily engagement metrics per platform"""
        try:
            if df.empty:
                return []
            
            daily_metrics = []
            
            # Group by date and platform
            grouped = df.groupby(['date', 'platform'])
            
            for (date, platform), group in grouped:
                total_posts = len(group)
                total_likes = group['likes'].sum()
                total_comments = group['comments'].sum()
                total_shares = group['shares'].sum()
                total_engagement = group['engagement_score'].sum()
                avg_engagement = total_engagement / total_posts if total_posts > 0 else 0
                
                metrics = DailyMetrics(
                    date=date,
                    platform=platform,
                    total_posts=total_posts,
                    total_likes=total_likes,
                    total_comments=total_comments,
                    total_shares=total_shares,
                    total_engagement=total_engagement,
                    avg_engagement_per_post=round(avg_engagement, 2)
                )
                
                daily_metrics.append(metrics)
            
            self.logger.info(f"Computed daily metrics for {len(daily_metrics)} date-platform combinations")
            return daily_metrics
            
        except Exception as e:
            self.logger.error(f"Error computing daily metrics: {e}")
            return []
    
    def get_top_posts(self, df: pd.DataFrame, top_n: int = 5) -> List[TopPost]:
        """Get top posts by engagement score"""
        try:
            if df.empty:
                return []
            
            # Sort by engagement score and get top N
            top_posts_df = df.nlargest(top_n, 'engagement_score')
            
            top_posts = []
            for _, row in top_posts_df.iterrows():
                post = TopPost(
                    post_id=row['post_id'],
                    platform=row['platform'],
                    content=row['content'][:200] + "..." if len(row['content']) > 200 else row['content'],
                    engagement_score=int(row['engagement_score']),
                    likes=int(row['likes']),
                    comments=int(row['comments']),
                    shares=int(row['shares']),
                    post_date=row['post_date'],
                    author_name=row['author_name']
                )
                top_posts.append(post)
            
            self.logger.info(f"Identified top {len(top_posts)} posts by engagement")
            return top_posts
            
        except Exception as e:
            self.logger.error(f"Error getting top posts: {e}")
            return []
    
    def get_top_posts_per_platform(self, df: pd.DataFrame, top_n: int = 3) -> Dict[str, List[TopPost]]:
        """Get top posts per platform"""
        try:
            if df.empty:
                return {}
            
            top_posts_per_platform = {}
            
            for platform in df['platform'].unique():
                platform_df = df[df['platform'] == platform]
                top_posts_df = platform_df.nlargest(top_n, 'engagement_score')
                
                top_posts = []
                for _, row in top_posts_df.iterrows():
                    post = TopPost(
                        post_id=row['post_id'],
                        platform=row['platform'],
                        content=row['content'][:200] + "..." if len(row['content']) > 200 else row['content'],
                        engagement_score=int(row['engagement_score']),
                        likes=int(row['likes']),
                        comments=int(row['comments']),
                        shares=int(row['shares']),
                        post_date=row['post_date'],
                        author_name=row['author_name']
                    )
                    top_posts.append(post)
                
                top_posts_per_platform[platform] = top_posts
            
            self.logger.info(f"Identified top {top_n} posts per platform for {len(top_posts_per_platform)} platforms")
            return top_posts_per_platform
            
        except Exception as e:
            self.logger.error(f"Error getting top posts per platform: {e}")
            return {}
    
    def compute_moving_averages(self, df: pd.DataFrame, window_7d: int = 7, window_30d: int = 30) -> List[MovingAverage]:
        """Compute moving averages of engagement metrics"""
        try:
            if df.empty:
                return []
            
            moving_averages = []
            
            # Ensure date is datetime for proper sorting
            df_sorted = df.copy()
            df_sorted['post_date'] = pd.to_datetime(df_sorted['post_date'])
            df_sorted = df_sorted.sort_values('post_date')
            
            for platform in df_sorted['platform'].unique():
                platform_df = df_sorted[df_sorted['platform'] == platform]
                
                # Group by date and sum engagement
                daily_engagement = platform_df.groupby(platform_df['post_date'].dt.date)['engagement_score'].sum().reset_index()
                daily_engagement.columns = ['date', 'engagement']
                daily_engagement['date'] = pd.to_datetime(daily_engagement['date'])
                daily_engagement = daily_engagement.sort_values('date')
                
                # Compute moving averages
                if len(daily_engagement) >= window_7d:
                    moving_avg_7d = daily_engagement['engagement'].rolling(window=window_7d, min_periods=1).mean()
                else:
                    moving_avg_7d = daily_engagement['engagement'].mean()
                
                if len(daily_engagement) >= window_30d:
                    moving_avg_30d = daily_engagement['engagement'].rolling(window=window_30d, min_periods=1).mean()
                else:
                    moving_avg_30d = daily_engagement['engagement'].mean()
                
                # Get the latest moving average values
                latest_date = daily_engagement['date'].max()
                latest_7d_avg = moving_avg_7d.iloc[-1] if len(moving_avg_7d) > 0 else 0
                latest_30d_avg = moving_avg_30d.iloc[-1] if len(moving_avg_30d) > 0 else 0
                
                moving_avg = MovingAverage(
                    platform=platform,
                    date=latest_date.strftime('%Y-%m-%d'),
                    moving_avg_7d=round(latest_7d_avg, 2),
                    moving_avg_30d=round(latest_30d_avg, 2)
                )
                
                moving_averages.append(moving_avg)
            
            self.logger.info(f"Computed moving averages for {len(moving_averages)} platforms")
            return moving_averages
            
        except Exception as e:
            self.logger.error(f"Error computing moving averages: {e}")
            return []
    
    def generate_analytics_summary(self, posts: List[Post]) -> AnalyticsSummary:
        """Generate complete analytics summary"""
        try:
            self.logger.info("Generating analytics summary")
            
            # Process posts
            df = self.process_posts(posts)
            
            if df.empty:
                self.logger.warning("No data available for analytics summary")
                return AnalyticsSummary(
                    date=datetime.now().strftime('%Y-%m-%d'),
                    daily_metrics=[],
                    top_posts_overall=[],
                    top_posts_per_platform={},
                    moving_averages=[]
                )
            
            # Compute all metrics
            daily_metrics = self.compute_daily_metrics(df)
            top_posts_overall = self.get_top_posts(df, top_n=5)
            top_posts_per_platform = self.get_top_posts_per_platform(df, top_n=3)
            moving_averages = self.compute_moving_averages(df)
            
            # Create summary
            summary = AnalyticsSummary(
                date=datetime.now().strftime('%Y-%m-%d'),
                daily_metrics=daily_metrics,
                top_posts_overall=top_posts_overall,
                top_posts_per_platform=top_posts_per_platform,
                moving_averages=moving_averages
            )
            
            self.logger.info("Analytics summary generated successfully")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating analytics summary: {e}")
            raise
    
    def get_platform_comparison(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Compare performance across platforms"""
        try:
            if df.empty:
                return {}
            
            platform_stats = {}
            
            for platform in df['platform'].unique():
                platform_df = df[df['platform'] == platform]
                
                stats = {
                    'total_posts': len(platform_df),
                    'total_engagement': int(platform_df['engagement_score'].sum()),
                    'avg_engagement_per_post': round(platform_df['engagement_score'].mean(), 2),
                    'avg_likes_per_post': round(platform_df['likes'].mean(), 2),
                    'avg_comments_per_post': round(platform_df['comments'].mean(), 2),
                    'avg_shares_per_post': round(platform_df['shares'].mean(), 2),
                    'top_engagement_post': int(platform_df['engagement_score'].max()),
                    'engagement_distribution': {
                        'low': len(platform_df[platform_df['engagement_score'] < 10]),
                        'medium': len(platform_df[(platform_df['engagement_score'] >= 10) & (platform_df['engagement_score'] < 100)]),
                        'high': len(platform_df[platform_df['engagement_score'] >= 100])
                    }
                }
                
                platform_stats[platform] = stats
            
            return platform_stats
            
        except Exception as e:
            self.logger.error(f"Error computing platform comparison: {e}")
            return {}
    
    def detect_anomalies(self, df: pd.DataFrame, threshold: float = 2.0) -> List[Dict[str, Any]]:
        """Detect anomalous posts based on engagement patterns"""
        try:
            if df.empty:
                return []
            
            anomalies = []
            
            # Calculate z-score for engagement scores
            engagement_scores = df['engagement_score'].values
            mean_engagement = np.mean(engagement_scores)
            std_engagement = np.std(engagement_scores)
            
            if std_engagement > 0:
                z_scores = np.abs((engagement_scores - mean_engagement) / std_engagement)
                anomaly_indices = np.where(z_scores > threshold)[0]
                
                for idx in anomaly_indices:
                    row = df.iloc[idx]
                    anomaly = {
                        'post_id': row['post_id'],
                        'platform': row['platform'],
                        'engagement_score': int(row['engagement_score']),
                        'z_score': round(z_scores[idx], 2),
                        'content_preview': row['content'][:100] + "..." if len(row['content']) > 100 else row['content'],
                        'author_name': row['author_name'],
                        'post_date': row['post_date'].strftime('%Y-%m-%d %H:%M:%S')
                    }
                    anomalies.append(anomaly)
            
            self.logger.info(f"Detected {len(anomalies)} anomalous posts")
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {e}")
            return []
