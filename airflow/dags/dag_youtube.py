from airflow import DAG
from datetime import datetime, timedelta
from tasks.youtube_tasks import (
    create_youtube_cleanup_task,
    create_youtube_collection_task,
    create_youtube_to_hdfs_task,
    create_youtube_processing_task
)


# DAG 기본 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 2, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

# 유튜브 DAG 정의
with DAG(
    dag_id='youtube_pipeline',
    default_args=default_args,
    description='유튜브 댓글 수집 및 적재 파이프라인',
    schedule_interval='0 * * * *',  # 매시간 정각에 실행
    catchup=False,
    tags=['youtube', 'api', 'etl']
) as dag:
    
    # Task 생성
    cleanup_task = create_youtube_cleanup_task(dag)
    collect_task = create_youtube_collection_task(dag)
    hdfs_task = create_youtube_to_hdfs_task(dag)
    process_task = create_youtube_processing_task(dag)
    
    # Task 의존성 설정
    # 기존 데이터 삭제 → API 수집 → HDFS 적재 → Spark 처리 → MySQL 적재
    cleanup_task >> collect_task >> hdfs_task >> process_task