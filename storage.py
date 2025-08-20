"""
Data storage module for social media analytics
"""
import json
import csv
import sqlite3
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
from models import Post, AnalyticsSummary, DailyMetrics, TopPost, MovingAverage

logger = structlog.get_logger()

class DataStorage:
    """Data storage handler for social media analytics"""
    
    def __init__(self, output_dir: str = "./output", database_url: str = "sqlite:///social_media_analytics.db"):
        self.output_dir = output_dir
        self.database_url = database_url
        self.logger = logger.bind(component='data_storage')
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize database if SQLite
        if database_url.startswith('sqlite'):
            self._init_sqlite_database()
    
    def _init_sqlite_database(self):
        """Initialize SQLite database with required tables"""
        try:
            db_path = self.database_url.replace('sqlite:///', '')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create posts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    post_id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    content TEXT,
                    author_id TEXT,
                    author_name TEXT,
                    likes INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    engagement_score INTEGER DEFAULT 0,
                    post_date TEXT,
                    collected_at TEXT,
                    url TEXT,
                    media_urls TEXT,
                    hashtags TEXT,
                    mentions TEXT
                )
            ''')
            
            # Create daily_metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    total_posts INTEGER DEFAULT 0,
                    total_likes INTEGER DEFAULT 0,
                    total_comments INTEGER DEFAULT 0,
                    total_shares INTEGER DEFAULT 0,
                    total_engagement INTEGER DEFAULT 0,
                    avg_engagement_per_post REAL DEFAULT 0,
                    UNIQUE(date, platform)
                )
            ''')
            
            # Create analytics_summaries table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analytics_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    summary_data TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info("SQLite database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing SQLite database: {e}")
    
    def save_posts_json(self, posts: List[Post], filename: Optional[str] = None) -> str:
        """Save posts to JSON file"""
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"posts_{timestamp}.json"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # Convert posts to dictionaries
            posts_data = [post.dict() for post in posts]
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(posts_data, f, indent=2, default=str)
            
            self.logger.info(f"Saved {len(posts)} posts to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error saving posts to JSON: {e}")
            raise
    
    def save_posts_csv(self, posts: List[Post], filename: Optional[str] = None) -> str:
        """Save posts to CSV file"""
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"posts_{timestamp}.csv"
            
            filepath = os.path.join(self.output_dir, filename)
            
            if not posts:
                self.logger.warning("No posts to save")
                return filepath
            
            # Get fieldnames from first post
            fieldnames = list(posts[0].dict().keys())
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for post in posts:
                    # Convert datetime objects to strings for CSV
                    post_dict = post.dict()
                    for key, value in post_dict.items():
                        if isinstance(value, datetime):
                            post_dict[key] = value.isoformat()
                        elif isinstance(value, list):
                            post_dict[key] = ', '.join(map(str, value))
                    
                    writer.writerow(post_dict)
            
            self.logger.info(f"Saved {len(posts)} posts to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error saving posts to CSV: {e}")
            raise
    
    def save_analytics_summary(self, summary: AnalyticsSummary, format: str = 'json') -> str:
        """Save analytics summary to file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if format.lower() == 'json':
                filename = f"analytics_summary_{timestamp}.json"
                filepath = os.path.join(self.output_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(summary.dict(), f, indent=2, default=str)
                    
            elif format.lower() == 'csv':
                filename = f"analytics_summary_{timestamp}.csv"
                filepath = os.path.join(self.output_dir, filename)
                
                # Save daily metrics to CSV
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    if summary.daily_metrics:
                        fieldnames = list(summary.daily_metrics[0].dict().keys())
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        
                        for metric in summary.daily_metrics:
                            writer.writerow(metric.dict())
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Saved analytics summary to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error saving analytics summary: {e}")
            raise
    
    def save_to_database(self, posts: List[Post], summary: Optional[AnalyticsSummary] = None):
        """Save data to database"""
        try:
            if self.database_url.startswith('sqlite'):
                self._save_to_sqlite(posts, summary)
            else:
                self.logger.warning(f"Database type not supported: {self.database_url}")
                
        except Exception as e:
            self.logger.error(f"Error saving to database: {e}")
            raise
    
    def _save_to_sqlite(self, posts: List[Post], summary: Optional[AnalyticsSummary] = None):
        """Save data to SQLite database"""
        try:
            db_path = self.database_url.replace('sqlite:///', '')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Save posts
            for post in posts:
                cursor.execute('''
                    INSERT OR REPLACE INTO posts 
                    (post_id, platform, content, author_id, author_name, likes, comments, 
                     shares, engagement_score, post_date, collected_at, url, media_urls, 
                     hashtags, mentions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    post.post_id,
                    post.platform.value,
                    post.content,
                    post.author_id,
                    post.author_name,
                    post.likes,
                    post.comments,
                    post.shares,
                    post.engagement_score,
                    post.post_date.isoformat(),
                    post.collected_at.isoformat(),
                    post.url,
                    ','.join(post.media_urls) if post.media_urls else None,
                    ','.join(post.hashtags) if post.hashtags else None,
                    ','.join(post.mentions) if post.mentions else None
                ))
            
            # Save daily metrics if summary provided
            if summary and summary.daily_metrics:
                for metric in summary.daily_metrics:
                    cursor.execute('''
                        INSERT OR REPLACE INTO daily_metrics 
                        (date, platform, total_posts, total_likes, total_comments, 
                         total_shares, total_engagement, avg_engagement_per_post)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        metric.date,
                        metric.platform.value,
                        metric.total_posts,
                        metric.total_likes,
                        metric.total_comments,
                        metric.total_shares,
                        metric.total_engagement,
                        metric.avg_engagement_per_post
                    ))
            
            # Save analytics summary
            if summary:
                cursor.execute('''
                    INSERT INTO analytics_summaries (date, summary_data)
                    VALUES (?, ?)
                ''', (
                    summary.date,
                    json.dumps(summary.dict(), default=str)
                ))
            
            conn.commit()
            conn.close()
            self.logger.info(f"Saved {len(posts)} posts to SQLite database")
            
        except Exception as e:
            self.logger.error(f"Error saving to SQLite: {e}")
            raise
    
    def load_posts_from_json(self, filepath: str) -> List[Post]:
        """Load posts from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            posts = []
            for post_data in data:
                # Convert string dates back to datetime
                if 'post_date' in post_data and isinstance(post_data['post_date'], str):
                    post_data['post_date'] = datetime.fromisoformat(post_data['post_date'].replace('Z', '+00:00'))
                if 'collected_at' in post_data and isinstance(post_data['collected_at'], str):
                    post_data['collected_at'] = datetime.fromisoformat(post_data['collected_at'].replace('Z', '+00:00'))
                
                # Convert string lists back to lists
                if 'media_urls' in post_data and isinstance(post_data['media_urls'], str):
                    post_data['media_urls'] = post_data['media_urls'].split(',') if post_data['media_urls'] else []
                if 'hashtags' in post_data and isinstance(post_data['hashtags'], str):
                    post_data['hashtags'] = post_data['hashtags'].split(',') if post_data['hashtags'] else []
                if 'mentions' in post_data and isinstance(post_data['mentions'], str):
                    post_data['mentions'] = post_data['mentions'].split(',') if post_data['mentions'] else []
                
                post = Post(**post_data)
                posts.append(post)
            
            self.logger.info(f"Loaded {len(posts)} posts from {filepath}")
            return posts
            
        except Exception as e:
            self.logger.error(f"Error loading posts from JSON: {e}")
            raise
    
    def load_posts_from_database(self, limit: Optional[int] = None, platform: Optional[str] = None) -> List[Post]:
        """Load posts from database"""
        try:
            if not self.database_url.startswith('sqlite'):
                self.logger.warning(f"Database type not supported: {self.database_url}")
                return []
            
            db_path = self.database_url.replace('sqlite:///', '')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Build query
            query = "SELECT * FROM posts"
            params = []
            
            if platform:
                query += " WHERE platform = ?"
                params.append(platform)
            
            query += " ORDER BY post_date DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert rows to Post objects
            posts = []
            for row in rows:
                post_data = {
                    'post_id': row[0],
                    'platform': row[1],
                    'content': row[2],
                    'author_id': row[3],
                    'author_name': row[4],
                    'likes': row[5],
                    'comments': row[6],
                    'shares': row[7],
                    'engagement_score': row[8],
                    'post_date': datetime.fromisoformat(row[9]),
                    'collected_at': datetime.fromisoformat(row[10]),
                    'url': row[11],
                    'media_urls': row[12].split(',') if row[12] else [],
                    'hashtags': row[13].split(',') if row[13] else [],
                    'mentions': row[14].split(',') if row[14] else []
                }
                
                post = Post(**post_data)
                posts.append(post)
            
            conn.close()
            self.logger.info(f"Loaded {len(posts)} posts from database")
            return posts
            
        except Exception as e:
            self.logger.error(f"Error loading posts from database: {e}")
            raise
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            stats = {
                'output_directory': self.output_dir,
                'database_url': self.database_url,
                'files_in_output': len(os.listdir(self.output_dir)) if os.path.exists(self.output_dir) else 0
            }
            
            if self.database_url.startswith('sqlite'):
                db_path = self.database_url.replace('sqlite:///', '')
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Get post count
                    cursor.execute("SELECT COUNT(*) FROM posts")
                    stats['total_posts_in_db'] = cursor.fetchone()[0]
                    
                    # Get platform distribution
                    cursor.execute("SELECT platform, COUNT(*) FROM posts GROUP BY platform")
                    stats['posts_by_platform'] = dict(cursor.fetchall())
                    
                    conn.close()
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting storage stats: {e}")
            return {}
