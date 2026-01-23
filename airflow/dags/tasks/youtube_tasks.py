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
    """유튜브 데이터를 HDFS에 적재하는 Task 생성"""
    return BashOperator(
        task_id='upload_youtube_to_hdfs',
        bash_command='''
        hdfs dfs -rm -r /youtube_data/* &&
        hdfs dfs -put -f /home/lab13/airflow/data/youtube/*.parquet /youtube_data
        ''',
        dag=dag
    )


def create_youtube_processing_task(dag):
    """HDFS 데이터를 Spark로 처리하여 MySQL에 적재하는 Task 생성"""
    from utils.spark_processor import process_youtube_data
    
    return PythonOperator(
        task_id='process_youtube_data',
        python_callable=process_youtube_data,
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