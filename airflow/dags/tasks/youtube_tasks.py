from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import timedelta

def create_youtube_collection_task(dag):
    """유튜브 댓글 수집 Task 생성"""
    from utils.youtube_api import collect_youtube_comments
    
    return PythonOperator(
        task_id='collect_youtube_comments',
        python_callable=collect_youtube_comments,
        dag=dag,
        retries=2,
        retry_delay=timedelta(minutes=3)
    )

def create_youtube_to_hdfs_task(dag):
    """유튜브 데이터를 HDFS에 날짜별 파티션({{ ds }})으로 적재하는 Task 생성"""
    return BashOperator(
        task_id='upload_youtube_to_hdfs',
        bash_command='''
        # 1. 해당 날짜의 파티션 폴더 생성
        hdfs dfs -mkdir -p /youtube_data/{{ ds }} &&
        
        # 2. 해당 날짜 폴더에 기존 데이터가 있다면 삭제 (멱등성 확보)
        hdfs dfs -rm -f /youtube_data/{{ ds }}/*.parquet &&
        
        # 3. 로컬의 수집 데이터를 HDFS의 날짜별 파티션 폴더로 이동
        hdfs dfs -put -f /home/lab13/airflow/data/youtube/*.parquet /youtube_data/{{ ds }}
        ''',
        dag=dag
    )

def create_youtube_processing_task(dag):
    """HDFS 데이터를 Spark로 처리하여 MySQL에 적재하는 Task 생성"""
    from utils.spark_processor import process_youtube_data
    
    return PythonOperator(
        task_id='process_youtube_data',
        python_callable=process_youtube_data,
        provide_context=True,
        dag=dag,
        retries=1,
        retry_delay=timedelta(minutes=2)
    )

def create_youtube_advanced_processing_task(dag):
    """유튜브 가공 테이블 생성 (감성 분석 및 tb_processed_youtube 적재)"""
    return BashOperator(
        task_id='process_youtube_advanced',
        bash_command='cd /home/lab13/projects/PhoneRecommender/web_project && /home/lab13/venv/bin/python manage.py process_youtube_data',
        dag=dag,
        retries=1,
        retry_delay=timedelta(minutes=2)
    )

def create_youtube_cleanup_task(dag):
    """유튜브 데이터 폴더 정리 Task 생성"""
    return BashOperator(
        task_id='cleanup_youtube_data',
        bash_command='rm -f /home/lab13/airflow/data/youtube/*.parquet',
        dag=dag
    )