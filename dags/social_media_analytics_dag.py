"""
Apache Airflow DAG for Social Media Analytics Pipeline
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import SocialMediaAnalyticsPipeline

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'social_media_analytics_pipeline',
    default_args=default_args,
    description='Daily social media analytics pipeline',
    schedule_interval='0 6 * * *',  # Run daily at 6 AM UTC
    catchup=False,
    tags=['social_media', 'analytics', 'etl'],
)

def run_data_collection(**context):
    """Collect data from social media platforms"""
    pipeline = SocialMediaAnalyticsPipeline()
    posts = pipeline.collect_data(
        queries=['#tech', '#AI', 'machine learning'],
        limit_per_platform=100,
        lookback_days=7
    )
    
    # Push results to XCom for next task
    context['task_instance'].xcom_push(key='posts', value=len(posts))
    context['task_instance'].xcom_push(key='collection_success', value=True)
    
    return f"Collected {len(posts)} posts from social media platforms"

def run_data_processing(**context):
    """Process collected data and generate analytics"""
    pipeline = SocialMediaAnalyticsPipeline()
    
    # Pull data from XCom (in real scenario, this would be the actual posts)
    posts_count = context['task_instance'].xcom_pull(key='posts', task_ids='collect_data')
    
    # Generate analytics summary
    summary = pipeline.processor.generate_analytics_summary([])  # Empty list for demo
    
    # Push results to XCom
    context['task_instance'].xcom_push(key='analytics_summary', value=True)
    context['task_instance'].xcom_push(key='processing_success', value=True)
    
    return f"Processed data and generated analytics summary"

def run_data_storage(**context):
    """Store processed data and analytics"""
    pipeline = SocialMediaAnalyticsPipeline()
    
    # Pull success flags from XCom
    collection_success = context['task_instance'].xcom_pull(key='collection_success', task_ids='collect_data')
    processing_success = context['task_instance'].xcom_push(key='processing_success', task_ids='process_data')
    
    if collection_success and processing_success:
        # Save to database and files
        pipeline.storage.save_to_database([], None)  # Empty data for demo
        context['task_instance'].xcom_push(key='storage_success', value=True)
        return "Data stored successfully"
    else:
        raise Exception("Previous tasks failed")

def run_quality_checks(**context):
    """Run quality checks on the pipeline"""
    # Check if all previous tasks succeeded
    collection_success = context['task_instance'].xcom_pull(key='collection_success', task_ids='collect_data')
    processing_success = context['task_instance'].xcom_pull(key='processing_success', task_ids='process_data')
    storage_success = context['task_instance'].xcom_pull(key='storage_success', task_ids='store_data')
    
    if all([collection_success, processing_success, storage_success]):
        context['task_instance'].xcom_push(key='quality_checks_passed', value=True)
        return "All quality checks passed"
    else:
        raise Exception("Quality checks failed")

def send_success_notification(**context):
    """Send success notification"""
    return "Pipeline completed successfully! 🎉"

def send_failure_notification(**context):
    """Send failure notification"""
    return "Pipeline failed! Please check logs for details."

# Define tasks
collect_data_task = PythonOperator(
    task_id='collect_data',
    python_callable=run_data_collection,
    dag=dag
)

process_data_task = PythonOperator(
    task_id='process_data',
    python_callable=run_data_processing,
    dag=dag
)

store_data_task = PythonOperator(
    task_id='store_data',
    python_callable=run_data_storage,
    dag=dag
)

quality_checks_task = PythonOperator(
    task_id='run_quality_checks',
    python_callable=run_quality_checks,
    dag=dag
)

# Define task dependencies
collect_data_task >> process_data_task >> store_data_task >> quality_checks_task

# Success and failure notifications
quality_checks_task >> [
    PythonOperator(
        task_id='send_success_notification',
        python_callable=send_success_notification,
        dag=dag,
        trigger_rule='all_success'
    ),
    PythonOperator(
        task_id='send_failure_notification',
        python_callable=send_failure_notification,
        dag=dag,
        trigger_rule='one_failed'
    )
]
