#!/usr/bin/env python3
"""
Demo script for Social Media Analytics Pipeline
This script demonstrates the pipeline functionality using sample data
"""

import os
import sys
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_sample_data():
    """Create sample social media data for demonstration"""
    from models import Post, Platform
    
    sample_posts = []
    
    # Create sample posts across different platforms
    platforms = [Platform.TWITTER, Platform.FACEBOOK, Platform.YOUTUBE]
    
    for platform in platforms:
        for i in range(1, 11):
            post = Post(
                post_id=f"{platform.value}_{i}",
                platform=platform,
                content=f"This is a sample {platform.value} post #{i} about data engineering and social media analytics. "
                        f"It demonstrates the capabilities of our pipeline in processing and analyzing social media data. "
                        f"#dataengineering #analytics #socialmedia",
                author_id=f"{platform.value}_user_{i}",
                author_name=f"{platform.value.title()}User{i}",
                likes=i * 25,
                comments=i * 5,
                shares=i * 3,
                post_date=datetime.utcnow() - timedelta(hours=i),
                hashtags=['dataengineering', 'analytics', 'socialmedia'],
                mentions=[]
            )
            sample_posts.append(post)
    
    return sample_posts

def run_demo():
    """Run the complete demo"""
    print(" Social Media Analytics Pipeline - Demo")
    print("=" * 60)
    
    try:
        # Create sample data
        print(" Creating sample social media data...")
        posts = create_sample_data()
        print(f" Created {len(posts)} sample posts across 3 platforms")
        
        # Initialize processor
        print("\n Initializing data processor...")
        from processor import DataProcessor
        processor = DataProcessor()
        
        # Process data
        print(" Processing and analyzing data...")
        df = processor.process_posts(posts)
        print(f" Processed {len(df)} posts into DataFrame")
        
        # Generate analytics
        print(" Generating analytics summary...")
        summary = processor.generate_analytics_summary(posts)
        print(f" Generated analytics summary for {summary.date}")
        
        # Display results
        print("\n Analytics Results:")
        print("-" * 40)
        
        # Daily metrics
        print(f" Daily Metrics: {len(summary.daily_metrics)} combinations")
        for metric in summary.daily_metrics[:3]:
            print(f"  {metric.date} - {metric.platform}: {metric.total_posts} posts, "
                  f"{metric.total_engagement} total engagement")
        
        # Top posts
        print(f"\n Top Posts Overall: {len(summary.top_posts_overall)} posts")
        for i, post in enumerate(summary.top_posts_overall[:3], 1):
            print(f"  {i}. {post.platform} - {post.engagement_score} engagement")
        
        # Platform comparison
        print(f"\n Platform Comparison:")
        comparison = processor.get_platform_comparison(df)
        for platform, stats in comparison.items():
            print(f"  {platform}: {stats['total_posts']} posts, "
                  f"avg engagement: {stats['avg_engagement_per_post']:.2f}")
        
        # Moving averages
        print(f"\n Moving Averages: {len(summary.moving_averages)} platforms")
        for avg in summary.moving_averages:
            print(f"  {avg.platform}: 7-day avg: {avg.moving_avg_7d:.2f}, "
                  f"30-day avg: {avg.moving_avg_30d:.2f}")
        
        # Anomaly detection
        print(f"\n Anomaly Detection:")
        anomalies = processor.detect_anomalies(df, threshold=2.0)
        print(f"  Detected {len(anomalies)} anomalous posts")
        
        # Test storage
        print(f"\n Testing data storage...")
        from storage import DataStorage
        storage = DataStorage(output_dir="./demo_output")
        
        # Save to files
        json_file = storage.save_posts_json(posts, "demo_posts.json")
        csv_file = storage.save_posts_csv(posts, "demo_posts.csv")
        summary_file = storage.save_analytics_summary(summary, 'json')
        
        print(f" Saved posts to: {json_file}")
        print(f" Saved posts to: {csv_file}")
        print(f" Saved summary to: {summary_file}")
        
        # Save to database
        storage.save_to_database(posts, summary)
        print(" Saved data to SQLite database")
        
        # Get storage stats
        stats = storage.get_storage_stats()
        print(f" Storage stats: {stats}")
        
        print("\n Demo completed successfully!")
        print(f"\n Check the 'demo_output' directory for generated files")
        print(f" Review the analytics results above")
        print(f" This demonstrates the complete pipeline workflow")
        
        return True
        
    except Exception as e:
        print(f"\n Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main demo function"""
    success = run_demo()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
