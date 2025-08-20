"""
Configuration file for Social Media Analytics Pipeline
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the social media analytics pipeline"""
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///social_media_analytics.db')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'social_media_analytics')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
    
    # Twitter API Configuration
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
    TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
    TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
    TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
    
    # Facebook API Configuration
    FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID')
    FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET')
    FACEBOOK_ACCESS_TOKEN = os.getenv('FACEBOOK_ACCESS_TOKEN')
    
    # YouTube API Configuration
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
    YOUTUBE_CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID')
    YOUTUBE_CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET')
    
    # Pipeline Configuration
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '100'))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY = int(os.getenv('RETRY_DELAY', '5'))
    
    # Data Collection Settings
    POSTS_LIMIT = int(os.getenv('POSTS_LIMIT', '1000'))
    LOOKBACK_DAYS = int(os.getenv('LOOKBACK_DAYS', '7'))
    
    # Output Configuration
    OUTPUT_FORMAT = os.getenv('OUTPUT_FORMAT', 'json')  # json, csv, database
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', './output')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', './logs/pipeline.log')
    
    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """Get database configuration as dictionary"""
        if cls.DATABASE_URL.startswith('postgresql'):
            return {
                'host': cls.POSTGRES_HOST,
                'port': cls.POSTGRES_PORT,
                'database': cls.POSTGRES_DB,
                'user': cls.POSTGRES_USER,
                'password': cls.POSTGRES_PASSWORD
            }
        return {'database': cls.DATABASE_URL}
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is present"""
        required_twitter = [
            cls.TWITTER_API_KEY, 
            cls.TWITTER_API_SECRET,
            cls.TWITTER_BEARER_TOKEN
        ]
        
        required_facebook = [
            cls.FACEBOOK_APP_ID,
            cls.FACEBOOK_APP_SECRET,
            cls.FACEBOOK_ACCESS_TOKEN
        ]
        
        required_youtube = [
            cls.YOUTUBE_API_KEY
        ]
        
        # At least two platforms should be configured
        configured_platforms = 0
        if all(required_twitter):
            configured_platforms += 1
        if all(required_facebook):
            configured_platforms += 1
        if all(required_youtube):
            configured_platforms += 1
            
        if configured_platforms < 2:
            print("Warning: At least 2 social media platforms must be configured")
            return False
            
        return True
