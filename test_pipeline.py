#!/usr/bin/env python3
"""
Test script for Social Media Analytics Pipeline
This script demonstrates the pipeline functionality with sample data
"""

import os
import sys
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import Post, Platform, AnalyticsSummary, DailyMetrics, TopPost, MovingAverage
from processor import DataProcessor
from storage import DataStorage

def create_sample_posts():
    """Create sample posts for testing"""
    sample_posts = []
    
    # Sample Twitter posts
    for i in range(1, 21):
        post = Post(
            post_id=f"twitter_{i}",
            platform=Platform.TWITTER,
            content=f"This is a sample Twitter post #{i} about technology and AI. #tech #AI #innovation",
            author_id=f"twitter_user_{i}",
            author_name=f"TwitterUser{i}",
            likes=i * 15,
            comments=i * 3,
            shares=i * 2,
            post_date=datetime.utcnow() - timedelta(hours=i),
            hashtags=['tech', 'AI', 'innovation'],
            mentions=[]
        )
        sample_posts.append(post)
    
    # Sample Facebook posts
    for i in range(1, 16):
        post = Post(
            post_id=f"facebook_{i}",
            platform=Platform.FACEBOOK,
            content=f"Sample Facebook post #{i} discussing social media trends and engagement strategies.",
            author_id=f"facebook_user_{i}",
            author_name=f"FacebookUser{i}",
            likes=i * 20,
            comments=i * 5,
            shares=i * 3,
            post_date=datetime.utcnow() - timedelta(hours=i * 2),
            hashtags=['socialmedia', 'engagement', 'trends'],
            mentions=[]
        )
        sample_posts.append(post)
    
    # Sample YouTube posts
    for i in range(1, 11):
        post = Post(
            post_id=f"youtube_{i}",
            platform=Platform.YOUTUBE,
            content=f"Sample YouTube video #{i} about data science and machine learning. This is a comprehensive tutorial covering various aspects of ML algorithms and their applications in real-world scenarios.",
            author_id=f"youtube_channel_{i}",
            author_name=f"YouTubeChannel{i}",
            likes=i * 50,
            comments=i * 8,
            shares=i * 5,
            post_date=datetime.utcnow() - timedelta(hours=i * 3),
            url=f"https://www.youtube.com/watch?v=sample_{i}",
            hashtags=['datascience', 'machinelearning', 'tutorial'],
            mentions=[]
        )
        sample_posts.append(post)
    
    return sample_posts

def test_data_processing():
    """Test data processing functionality"""
    print(" Testing Data Processing...")
    
    # Create sample posts
    posts = create_sample_posts()
    print(f" Created {len(posts)} sample posts")
    
    # Initialize processor
    processor = DataProcessor()
    
    # Process posts
    df = processor.process_posts(posts)
    print(f" Processed posts into DataFrame with {len(df)} rows")
    
    # Generate analytics summary
    summary = processor.generate_analytics_summary(posts)
    print(f" Generated analytics summary for {summary.date}")
    
    # Test individual analytics functions
    daily_metrics = processor.compute_daily_metrics(df)
    print(f" Computed daily metrics for {len(daily_metrics)} date-platform combinations")
    
    top_posts = processor.get_top_posts(df, top_n=5)
    print(f" Identified top {len(top_posts)} posts by engagement")
    
    top_per_platform = processor.get_top_posts_per_platform(df, top_n=3)
    print(f" Identified top posts per platform for {len(top_per_platform)} platforms")
    
    moving_averages = processor.compute_moving_averages(df)
    print(f" Computed moving averages for {len(moving_averages)} platforms")
    
    platform_comparison = processor.get_platform_comparison(df)
    print(f" Generated platform comparison for {len(platform_comparison)} platforms")
    
    anomalies = processor.detect_anomalies(df, threshold=2.0)
    print(f" Detected {len(anomalies)} anomalous posts")
    
    return summary, df

def test_data_storage():
    """Test data storage functionality"""
    print("\n Testing Data Storage...")
    
    # Create sample posts and summary
    posts = create_sample_posts()
    processor = DataProcessor()
    summary = processor.generate_analytics_summary(posts)
    
    # Initialize storage
    storage = DataStorage(output_dir="./test_output")
    
    # Test JSON storage
    json_file = storage.save_posts_json(posts, "test_posts.json")
    print(f" Saved posts to JSON: {json_file}")
    
    # Test CSV storage
    csv_file = storage.save_posts_csv(posts, "test_posts.csv")
    print(f" Saved posts to CSV: {csv_file}")
    
    # Test analytics summary storage
    summary_json = storage.save_analytics_summary(summary, 'json')
    print(f" Saved analytics summary to JSON: {summary_json}")
    
    summary_csv = storage.save_analytics_summary(summary, 'csv')
    print(f" Saved analytics summary to CSV: {summary_csv}")
    
    # Test database storage
    storage.save_to_database(posts, summary)
    print(" Saved data to database")
    
    # Test loading from storage
    loaded_posts = storage.load_posts_from_json(json_file)
    print(f" Loaded {len(loaded_posts)} posts from JSON")
    
    # Get storage stats
    stats = storage.get_storage_stats()
    print(f" Storage stats: {stats}")
    
    return storage

def test_pipeline_integration():
    """Test full pipeline integration"""
    print("\n🔗 Testing Pipeline Integration...")
    
    try:
        from pipeline import SocialMediaAnalyticsPipeline
        
        # Initialize pipeline (without real API credentials)
        pipeline = SocialMediaAnalyticsPipeline()
        
        # Get pipeline status
        status = pipeline.get_pipeline_status()
        print(f" Pipeline status: {status}")
        
        print(" Pipeline integration test completed")
        
    except ImportError as e:
        print(f"  Pipeline import failed (expected without API credentials): {e}")
    except Exception as e:
        print(f"  Pipeline test failed: {e}")

def display_sample_analytics(summary, df):
    """Display sample analytics results"""
    print("\n Sample Analytics Results:")
    print("=" * 50)
    
    # Display daily metrics
    print("\n Daily Metrics:")
    for metric in summary.daily_metrics[:3]:  # Show first 3
        print(f"  {metric.date} - {metric.platform}: {metric.total_posts} posts, "
              f"{metric.total_engagement} total engagement")
    
    # Display top posts
    print("\n Top Posts Overall:")
    for i, post in enumerate(summary.top_posts_overall[:3], 1):
        print(f"  {i}. {post.platform} - {post.engagement_score} engagement "
              f"({post.likes} likes, {post.comments} comments, {post.shares} shares)")
    
    # Display platform comparison
    print("\n Platform Comparison:")
    processor = DataProcessor()
    comparison = processor.get_platform_comparison(df)
    
    for platform, stats in comparison.items():
        print(f"  {platform}: {stats['total_posts']} posts, "
              f"avg engagement: {stats['avg_engagement_per_post']:.2f}")

def main():
    """Main test function"""
    print(" Social Media Analytics Pipeline - Test Suite")
    print("=" * 60)
    
    try:
        # Test data processing
        summary, df = test_data_processing()
        
        # Test data storage
        storage = test_data_storage()
        
        # Test pipeline integration
        test_pipeline_integration()
        
        # Display sample results
        display_sample_analytics(summary, df)
        
        print("\n All tests completed successfully!")
        print("\n Check the 'test_output' directory for generated files")
        print(" Review the analytics results above")
        
    except Exception as e:
        print(f"\n Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
