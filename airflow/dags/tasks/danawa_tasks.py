from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import timedelta


def create_danawa_crawling_task(dag):
    """다나와 크롤링 Task 생성"""
    from utils.danawa_crawler import crawl_danawa
    
    return PythonOperator(
        task_id='crawl_danawa',
        python_callable=crawl_danawa,
        dag=dag,
        retries=2,
        retry_delay=timedelta(minutes=3)
    )


def create_danawa_to_hdfs_task(dag):
    """다나와 데이터를 HDFS에 적재하는 Task 생성"""
    return BashOperator(
        task_id='upload_danawa_to_hdfs',
        bash_command='''
        hdfs dfs -rm -r /danawa_data/* &&
        hdfs dfs -put -f /home/lab13/airflow/data/danawa/*.parquet /danawa_data
        ''',
        dag=dag
    )


def create_danawa_processing_task(dag):
    """HDFS 데이터를 Spark로 처리하여 MySQL에 적재하는 Task 생성"""
    from utils.spark_processor import process_danawa_data
    
    return PythonOperator(
        task_id='process_danawa_data',
        python_callable=process_danawa_data,
        dag=dag,
        retries=1,
        retry_delay=timedelta(minutes=2)
    )


def create_danawa_cleanup_task(dag):
    """다나와 데이터 폴더 정리 Task 생성"""
    return BashOperator(
        task_id='cleanup_danawa_data',
        bash_command='rm -f /home/lab13/airflow/data/danawa/*.parquet',
        dag=dag
    )