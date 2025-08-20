"""
Main pipeline orchestrator for social media analytics
"""
import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog
import time

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from models import Post, Platform
from collectors import TwitterCollector, FacebookCollector, YouTubeCollector
from processor import DataProcessor
from storage import DataStorage

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

class SocialMediaAnalyticsPipeline:
    """Main pipeline for social media analytics"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = logger.bind(component='pipeline')
        
        # Initialize components
        self.collectors = {}
        self.processor = DataProcessor()
        self.storage = DataStorage(
            output_dir=self.config.OUTPUT_DIR,
            database_url=self.config.DATABASE_URL
        )
        
        # Initialize collectors based on available credentials
        self._initialize_collectors()
    
    def _initialize_collectors(self):
        """Initialize available social media collectors"""
        try:
            # Twitter collector
            if all([
                self.config.TWITTER_API_KEY,
                self.config.TWITTER_API_SECRET,
                self.config.TWITTER_BEARER_TOKEN
            ]):
                self.collectors[Platform.TWITTER] = TwitterCollector({
                    'TWITTER_API_KEY': self.config.TWITTER_API_KEY,
                    'TWITTER_API_SECRET': self.config.TWITTER_API_SECRET,
                    'TWITTER_ACCESS_TOKEN': self.config.TWITTER_ACCESS_TOKEN,
                    'TWITTER_ACCESS_TOKEN_SECRET': self.config.TWITTER_ACCESS_TOKEN_SECRET,
                    'TWITTER_BEARER_TOKEN': self.config.TWITTER_BEARER_TOKEN,
                    'RETRY_DELAY': self.config.RETRY_DELAY
                })
                self.logger.info("Twitter collector initialized")
            
            # Facebook collector
            if all([
                self.config.FACEBOOK_APP_ID,
                self.config.FACEBOOK_APP_SECRET,
                self.config.FACEBOOK_ACCESS_TOKEN
            ]):
                self.collectors[Platform.FACEBOOK] = FacebookCollector({
                    'FACEBOOK_APP_ID': self.config.FACEBOOK_APP_ID,
                    'FACEBOOK_APP_SECRET': self.config.FACEBOOK_APP_SECRET,
                    'FACEBOOK_ACCESS_TOKEN': self.config.FACEBOOK_ACCESS_TOKEN,
                    'RETRY_DELAY': self.config.RETRY_DELAY
                })
                self.logger.info("Facebook collector initialized")
            
            # YouTube collector
            if self.config.YOUTUBE_API_KEY:
                self.collectors[Platform.YOUTUBE] = YouTubeCollector({
                    'YOUTUBE_API_KEY': self.config.YOUTUBE_API_KEY,
                    'RETRY_DELAY': self.config.RETRY_DELAY
                })
                self.logger.info("YouTube collector initialized")
            
            if not self.collectors:
                self.logger.error("No collectors initialized. Check your API credentials.")
            else:
                self.logger.info(f"Initialized {len(self.collectors)} collectors: {list(self.collectors.keys())}")
                
        except Exception as e:
            self.logger.error(f"Error initializing collectors: {e}")
    
    def collect_data(self, 
                    queries: Optional[List[str]] = None,
                    user_ids: Optional[Dict[str, str]] = None,
                    limit_per_platform: int = 100,
                    lookback_days: int = 7) -> List[Post]:
        """Collect data from all available platforms"""
        all_posts = []
        
        try:
            since_date = datetime.utcnow() - timedelta(days=lookback_days)
            
            for platform, collector in self.collectors.items():
                try:
                    self.logger.info(f"Collecting data from {platform.value}")
                    
                    # Authenticate collector
                    if not collector.authenticate():
                        self.logger.warning(f"Failed to authenticate {platform.value} collector")
                        continue
                    
                    platform_posts = []
                    
                    # Collect trending posts
                    if not queries and not user_ids:
                        platform_posts = collector.get_trending_posts(limit_per_platform)
                        self.logger.info(f"Collected {len(platform_posts)} trending posts from {platform.value}")
                    
                    # Collect posts by query
                    elif queries:
                        for query in queries:
                            query_posts = collector.collect_posts(
                                query=query,
                                limit=limit_per_platform // len(queries),
                                since_date=since_date
                            )
                            platform_posts.extend(query_posts)
                            self.logger.info(f"Collected {len(query_posts)} posts for query '{query}' from {platform.value}")
                    
                    # Collect posts by user
                    elif user_ids and platform.value in user_ids:
                        user_id = user_ids[platform.value]
                        platform_posts = collector.get_user_posts(user_id, limit_per_platform)
                        self.logger.info(f"Collected {len(platform_posts)} posts from user {user_id} on {platform.value}")
                    
                    all_posts.extend(platform_posts)
                    
                    # Rate limiting - be respectful to APIs
                    if len(self.collectors) > 1:
                        time.sleep(2)
                        
                except Exception as e:
                    self.logger.error(f"Error collecting data from {platform.value}: {e}")
                    continue
            
            self.logger.info(f"Total posts collected: {len(all_posts)}")
            return all_posts
            
        except Exception as e:
            self.logger.error(f"Error in data collection: {e}")
            return all_posts
    
    def run_pipeline(self, 
                    queries: Optional[List[str]] = None,
                    user_ids: Optional[Dict[str, str]] = None,
                    save_to_db: bool = True,
                    save_to_files: bool = True) -> Dict[str, Any]:
        """Run the complete analytics pipeline"""
        try:
            self.logger.info("Starting social media analytics pipeline")
            start_time = time.time()
            
            # Step 1: Collect data
            self.logger.info("Step 1: Collecting data from social media platforms")
            posts = self.collect_data(queries, user_ids)
            
            if not posts:
                self.logger.warning("No posts collected. Pipeline cannot continue.")
                return {
                    'success': False,
                    'error': 'No posts collected',
                    'posts_count': 0
                }
            
            # Step 2: Process and analyze data
            self.logger.info("Step 2: Processing and analyzing data")
            analytics_summary = self.processor.generate_analytics_summary(posts)
            
            # Step 3: Save results
            self.logger.info("Step 3: Saving results")
            saved_files = []
            
            if save_to_files:
                # Save posts to JSON
                json_file = self.storage.save_posts_json(posts)
                saved_files.append(json_file)
                
                # Save posts to CSV
                csv_file = self.storage.save_posts_csv(posts)
                saved_files.append(csv_file)
                
                # Save analytics summary
                summary_json = self.storage.save_analytics_summary(analytics_summary, 'json')
                saved_files.append(summary_json)
                
                summary_csv = self.storage.save_analytics_summary(analytics_summary, 'csv')
                saved_files.append(summary_csv)
            
            if save_to_db:
                self.storage.save_to_database(posts, analytics_summary)
            
            # Step 4: Generate additional insights
            self.logger.info("Step 4: Generating additional insights")
            df = self.processor.process_posts(posts)
            
            platform_comparison = self.processor.get_platform_comparison(df)
            anomalies = self.processor.detect_anomalies(df)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Prepare results
            results = {
                'success': True,
                'execution_time_seconds': round(execution_time, 2),
                'posts_collected': len(posts),
                'platforms_analyzed': list(df['platform'].unique()),
                'analytics_summary': analytics_summary.dict(),
                'platform_comparison': platform_comparison,
                'anomalies_detected': len(anomalies),
                'saved_files': saved_files,
                'saved_to_database': save_to_db
            }
            
            self.logger.info(f"Pipeline completed successfully in {execution_time:.2f} seconds")
            return results
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time_seconds': time.time() - start_time if 'start_time' in locals() else 0
            }
    
    def run_daily_pipeline(self) -> Dict[str, Any]:
        """Run daily scheduled pipeline"""
        try:
            self.logger.info("Running daily scheduled pipeline")
            
            # Default queries for daily collection
            daily_queries = [
                '#tech', '#news', '#politics', '#sports', '#entertainment',
                'artificial intelligence', 'machine learning', 'data science'
            ]
            
            results = self.run_pipeline(
                queries=daily_queries,
                save_to_db=True,
                save_to_files=True
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Daily pipeline failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status and statistics"""
        try:
            status = {
                'collectors_available': len(self.collectors),
                'collectors_platforms': [p.value for p in self.collectors.keys()],
                'storage_stats': self.storage.get_storage_stats(),
                'config_validation': self.config.validate_config()
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting pipeline status: {e}")
            return {'error': str(e)}


def main():
    """Main function to run the pipeline"""
    try:
        # Initialize pipeline
        pipeline = SocialMediaAnalyticsPipeline()
        
        # Check pipeline status
        status = pipeline.get_pipeline_status()
        print(f"Pipeline Status: {status}")
        
        if not status['collectors_available']:
            print("No collectors available. Please check your API credentials.")
            return
        
        # Run pipeline with sample queries
        print("\nRunning pipeline with sample queries...")
        results = pipeline.run_pipeline(
            queries=['#tech', '#AI', 'machine learning'],
            save_to_db=True,
            save_to_files=True
        )
        
        if results['success']:
            print(f"\nPipeline completed successfully!")
            print(f"Posts collected: {results['posts_count']}")
            print(f"Execution time: {results['execution_time_seconds']} seconds")
            print(f"Files saved: {len(results['saved_files'])}")
        else:
            print(f"\nPipeline failed: {results.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"Error running pipeline: {e}")
        logger.error(f"Main function error: {e}")


if __name__ == "__main__":
    main()
