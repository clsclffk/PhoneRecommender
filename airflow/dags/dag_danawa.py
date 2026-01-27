from airflow import DAG
from datetime import datetime, timedelta
from tasks.danawa_tasks import (
    create_danawa_cleanup_task,
    create_danawa_crawling_task,
    create_danawa_to_hdfs_task,
    create_danawa_processing_task
)


# DAG 기본 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 2, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

# 다나와 DAG 정의
with DAG(
    dag_id='danawa_pipeline',
    default_args=default_args,
    description='다나와 리뷰 크롤링 및 적재 파이프라인',
    schedule_interval='0 3 * * *',  # 매일 새벽 3시
    catchup=False,
    tags=['danawa', 'crawler', 'etl']
) as dag:
    
    # Task 생성
    cleanup_task = create_danawa_cleanup_task(dag)
    crawl_task = create_danawa_crawling_task(dag)
    hdfs_task = create_danawa_to_hdfs_task(dag)
    process_task = create_danawa_processing_task(dag)
    
    # Task 의존성 설정
    # 기존 데이터 삭제 → 크롤링 → HDFS 적재 → Spark 처리 → MySQL 적재
    cleanup_task >> crawl_task >> hdfs_task >> process_task