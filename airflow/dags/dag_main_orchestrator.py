from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta


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
    schedule_interval='0 * * * *',  # 매시간 정각에 실행
    catchup=False,
    tags=['main', 'orchestrator']
) as dag:
    
    # 시작 로그
    start_log = PythonOperator(
        task_id='pipeline_start',
        python_callable=log_pipeline_start
    )
    
    # 다나와 파이프라인 트리거
    trigger_danawa = TriggerDagRunOperator(
        task_id='trigger_danawa_pipeline',
        trigger_dag_id='danawa_pipeline',
        wait_for_completion=True,
        poke_interval=30
    )
    
    # 유튜브 파이프라인 트리거
    trigger_youtube = TriggerDagRunOperator(
        task_id='trigger_youtube_pipeline',
        trigger_dag_id='youtube_pipeline',
        wait_for_completion=True,
        poke_interval=30
    )
    
    # 종료 로그
    end_log = PythonOperator(
        task_id='pipeline_end',
        python_callable=log_pipeline_end
    )
    
    # Task 의존성
    # 다나와와 유튜브는 동시 실행
    start_log >> [trigger_danawa, trigger_youtube] >> end_log