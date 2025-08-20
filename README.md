# Social Media Analytics Pipeline

A robust data engineering pipeline that fetches, transforms, and analyzes social media data from multiple platforms, computing engagement metrics and insights.

## 🎯 Project Overview

This project implements a comprehensive social media analytics pipeline that:

- **Collects data** from Twitter, Facebook, and YouTube APIs
- **Normalizes data** from multiple platforms into a unified schema
- **Computes analytics** including daily engagement metrics, top posts, and moving averages
- **Automates execution** using Apache Airflow for daily runs
- **Stores results** in multiple formats (JSON, CSV, SQLite/PostgreSQL)

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Data Storage  │    │   Analytics     │
│                 │    │                 │    │                 │
│ • Twitter API   │───▶│ • SQLite/PostgreSQL │───▶│ • Daily Metrics │
│ • Facebook API  │    │ • JSON Files    │    │ • Top Posts     │
│ • YouTube API   │    │ • CSV Files     │    │ • Moving Averages│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Collectors    │    │   Processors    │    │   Airflow DAG   │
│                 │    │                 │    │                 │
│ • BaseCollector │    │ • DataProcessor │    │ • Daily Schedule│
│ • Twitter       │    │ • Analytics     │    │ • Error Handling│
│ • Facebook      │    │ • Validation    │    │ • Notifications │
│ • YouTube       │    │ • Insights      │    └─────────────────┘
└─────────────────┘    └─────────────────┘
```

## 🚀 Features

### Data Collection
- **Multi-platform support**: Twitter, Facebook, YouTube
- **Flexible queries**: Search by keywords, hashtags, or user accounts
- **Rate limiting**: Respectful API usage with retry mechanisms
- **Error handling**: Robust error handling and logging

### Data Processing
- **Unified schema**: Normalized data model across all platforms
- **Engagement metrics**: Likes, comments, shares, and calculated engagement scores
- **Data validation**: Pydantic models for data integrity
- **Missing data handling**: Graceful handling of incomplete data

### Analytics
- **Daily metrics**: Per-platform engagement statistics
- **Top posts**: Overall and platform-specific top performers
- **Moving averages**: 7-day and 30-day engagement trends
- **Platform comparison**: Cross-platform performance analysis
- **Anomaly detection**: Statistical outlier identification

### Automation
- **Airflow DAG**: Daily scheduled execution
- **Quality checks**: Data validation and pipeline monitoring
- **Notifications**: Success/failure alerts
- **Error recovery**: Automatic retry mechanisms

## 📋 Requirements

### System Requirements
- Python 3.8+
- 4GB RAM minimum
- 10GB disk space

### API Requirements
- **Twitter**: Developer account with API v2 access
- **Facebook**: App with Graph API permissions
- **YouTube**: Google Cloud project with YouTube Data API v3

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd social_media_analytics
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
# Copy the example environment file
cp env_example.txt .env

# Edit .env with your API credentials
nano .env  # or use your preferred editor
```

### 5. Set Up API Credentials

#### Twitter API Setup
1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Create a new app
3. Generate API keys and tokens
4. Add to your `.env` file

#### Facebook API Setup
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app
3. Generate access tokens
4. Add to your `.env` file

#### YouTube API Setup
1. Go to [Google Cloud Console](https://console.developers.google.com/)
2. Create a new project
3. Enable YouTube Data API v3
4. Generate API key
5. Add to your `.env` file

## 🚀 Usage

### Basic Pipeline Execution

```python
from pipeline import SocialMediaAnalyticsPipeline

# Initialize pipeline
pipeline = SocialMediaAnalyticsPipeline()

# Run with custom queries
results = pipeline.run_pipeline(
    queries=['#tech', '#AI', 'machine learning'],
    save_to_db=True,
    save_to_files=True
)

print(f"Pipeline completed: {results['success']}")
print(f"Posts collected: {results['posts_collected']}")
```

### Custom Data Collection

```python
# Collect from specific users
user_ids = {
    'twitter': '123456789',
    'facebook': '987654321',
    'youtube': 'UC123456789'
}

posts = pipeline.collect_data(
    user_ids=user_ids,
    limit_per_platform=50
)
```

### Analytics Generation

```python
from processor import DataProcessor

processor = DataProcessor()

# Generate analytics summary
summary = processor.generate_analytics_summary(posts)

# Get platform comparison
comparison = processor.get_platform_comparison(df)

# Detect anomalies
anomalies = processor.detect_anomalies(df, threshold=2.0)
```

### Airflow Automation

1. **Install Airflow**:
```bash
pip install apache-airflow
```

2. **Set Airflow home**:
```bash
export AIRFLOW_HOME=./airflow
airflow db init
```

3. **Copy DAG**:
```bash
cp dags/social_media_analytics_dag.py $AIRFLOW_HOME/dags/
```

4. **Start Airflow**:
```bash
airflow webserver --port 8080
airflow scheduler
```

## 📊 Data Models

### Post Model
```python
class Post(BaseModel):
    post_id: str
    platform: Platform
    content: str
    author_id: str
    author_name: str
    likes: int
    comments: int
    shares: int
    post_date: datetime
    engagement_score: int  # Computed field
```

### Analytics Summary
```python
class AnalyticsSummary(BaseModel):
    date: str
    daily_metrics: List[DailyMetrics]
    top_posts_overall: List[TopPost]
    top_posts_per_platform: Dict[str, List[TopPost]]
    moving_averages: List[MovingAverage]
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///social_media_analytics.db` |
| `POSTS_LIMIT` | Maximum posts per platform | `1000` |
| `LOOKBACK_DAYS` | Days to look back for data | `7` |
| `OUTPUT_FORMAT` | Output file format | `json` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Pipeline Settings

```python
# In config.py
BATCH_SIZE = 100          # Posts per batch
MAX_RETRIES = 3           # API retry attempts
RETRY_DELAY = 5           # Seconds between retries
```

## 📁 Project Structure

```
social_media_analytics/
├── collectors/                 # Data collection modules
│   ├── __init__.py
│   ├── base_collector.py      # Abstract base class
│   ├── twitter_collector.py   # Twitter API collector
│   ├── facebook_collector.py  # Facebook API collector
│   └── youtube_collector.py   # YouTube API collector
├── dags/                      # Airflow DAGs
│   └── social_media_analytics_dag.py
├── models.py                  # Data models and schemas
├── processor.py               # Data processing and analytics
├── storage.py                 # Data storage handlers
├── pipeline.py                # Main pipeline orchestrator
├── config.py                  # Configuration management
├── requirements.txt           # Python dependencies
├── env_example.txt           # Environment variables template
└── README.md                 # This file
```

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### Test Coverage
```bash
pip install pytest-cov
pytest --cov=. tests/
```

## 📈 Monitoring and Logging

### Logging Configuration
- **Structured logging** with structlog
- **JSON format** for easy parsing
- **Multiple log levels** (DEBUG, INFO, WARNING, ERROR)
- **File and console output**

### Pipeline Monitoring
- **Success/failure tracking**
- **Execution time monitoring**
- **Data quality metrics**
- **Error rate tracking**

## 🔒 Security Considerations

- **API keys** stored in environment variables
- **No hardcoded credentials** in source code
- **Rate limiting** to respect API quotas
- **Error logging** without sensitive data exposure

## 🚨 Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify API credentials in `.env` file
   - Check API permissions and quotas
   - Ensure tokens haven't expired

2. **Rate Limiting**
   - Reduce `POSTS_LIMIT` in configuration
   - Increase `RETRY_DELAY` between requests
   - Check API rate limit documentation

3. **Data Quality Issues**
   - Verify data models match API responses
   - Check for missing required fields
   - Review error logs for specific issues

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run pipeline with debug logging
pipeline = SocialMediaAnalyticsPipeline()
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Twitter API** for social media data access
- **Facebook Graph API** for platform integration
- **YouTube Data API** for video analytics
- **Apache Airflow** for workflow automation
- **Pydantic** for data validation

## 📞 Support

For questions and support:
- Create an issue in the repository
- Check the troubleshooting section
- Review the configuration documentation

---

**Note**: This pipeline requires valid API credentials from the respective social media platforms. Make sure to comply with each platform's terms of service and rate limiting policies.
