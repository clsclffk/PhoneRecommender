from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from airflow.utils.task_group import TaskGroup
from tasks.danawa_tasks import (
    create_danawa_crawling_task,
    create_danawa_to_hdfs_task,
    create_danawa_processing_task,
    create_danawa_cleanup_task,
    create_danawa_advanced_processing_task
)
from tasks.youtube_tasks import (
    create_youtube_collection_task,
    create_youtube_to_hdfs_task,
    create_youtube_processing_task,
    create_youtube_cleanup_task,
    create_youtube_advanced_processing_task
)


def log_pipeline_start():
    """파이프라인 시작 로그"""
    print("=" * 50)
    print("전체 데이터 파이프라인 시작")
    print("=" * 50)


def log_pipeline_end():
    """파이프라인 종료 로그"""
    print("=" * 50)
    print("전체 데이터 파이프라인 완료")
    print("=" * 50)


# DAG 기본 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 2, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

# 메인 오케스트레이터 DAG
with DAG(
    dag_id='main_data_pipeline',
    default_args=default_args,
    description='전체 데이터 수집 및 처리 파이프라인 오케스트레이터',
    schedule_interval='0 3 * * *',  # 매일 새벽 3시
    catchup=False,
    tags=['main', 'orchestrator']
) as dag:
    
    # 시작 로그
    start_log = PythonOperator(
        task_id='pipeline_start',
        python_callable=log_pipeline_start
    )
    
    # 다나와 파이프라인 트리거
    with TaskGroup(group_id='danawa_pipeline_group') as danawa_group:
        d_crawl = create_danawa_crawling_task(dag)
        d_hdfs = create_danawa_to_hdfs_task(dag)
        d_process = create_danawa_processing_task(dag)
        d_advanced = create_danawa_advanced_processing_task(dag)  
        d_cleanup = create_danawa_cleanup_task(dag)
        
        # 그룹 내 의존성 설정
        d_crawl >> d_hdfs >> d_process >> d_advanced >> d_cleanup 
    
    # 유튜브 파이프라인 트리거
    with TaskGroup(group_id='youtube_pipeline_group') as youtube_group:
        y_collect = create_youtube_collection_task(dag)
        y_hdfs = create_youtube_to_hdfs_task(dag)
        y_process = create_youtube_processing_task(dag)
        y_advanced = create_youtube_advanced_processing_task(dag) 
        y_cleanup = create_youtube_cleanup_task(dag)
        
        # 그룹 내 의존성 설정
        y_collect >> y_hdfs >> y_process >> y_advanced >> y_cleanup
    
    # 종료 로그
    end_log = PythonOperator(
        task_id='pipeline_end',
        python_callable=log_pipeline_end
    )
    
    # Task 의존성
    # 다나와와 유튜브는 동시 실행
    start_log >> [danawa_group, youtube_group] >> end_log