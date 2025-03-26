from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime, timedelta
from airflow.utils.email import send_email


# 이메일 알림 : 성공 & 실패 알림
# def send_failure_email(context):
#     subject = f"DAG {context['dag'].dag_id} 실행 실패!"
#     message = f"DAG 실패: {context['exception']}"
#     send_email(to='comboy8231@gmail.com', subject=subject, html_content=message)

# def send_success_email(context):
#     subject = f"DAG {context['dag'].dag_id} 실행 성공!"
#     message = "DAG이 성공적으로 실행되었습니다."
#     send_email(to='comboy8231@gmail.com', subject=subject, html_content=message)

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 2, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    # 'email_on_failure': True, 
    # 'email_on_retry': False,   
    # 'email': ['comboy8231@gmail.com'], 
    # 'on_failure_callback': send_failure_email, 
    # 'on_success_callback': send_success_email   
}

# main_dag_danawa = DAG(
#     'depth2_danawa',
#     default_args=default_args,
#     schedule_interval='@monthly',
#     catchup=False
# )

main_dag_youtube = DAG(
    'depth2_youtube',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
)

# # DAG 1 실행 (HDFS 업로드)
# depth2_etl_danawa_to_hdfs = TriggerDagRunOperator(
#     task_id='depth2_etl_danawa_to_hdfs',
#     trigger_dag_id='danawa_to_hdfs',  # 실행할 DAG ID
#     dag=main_dag_danawa
# )

# # DAG 2 실행 (PySpark 데이터 처리)
# depth2_etl_danawa_preprocessing = TriggerDagRunOperator(
#     task_id='depth2_etl_danawa_preprocessing',
#     trigger_dag_id='danawa_preprocessing',  # 실행할 DAG ID
#     wait_for_completion=False,
#     dag=main_dag_danawa
# )

# DAG 1 실행 (유튜브 API로 가져오기)
depth2_etl_youtube_api = TriggerDagRunOperator(
    task_id='depth2_etl_youtube_api',
    trigger_dag_id='youtube_comments_dag',  # 실행할 DAG ID
    wait_for_completion=True,  # 완료될 때까지 기다림
    dag=main_dag_youtube
)

# DAG 2 실행 (HDFS에 업로드)
depth2_etl_load_to_hdfs = TriggerDagRunOperator(
    task_id='depth2_etl_load_to_hdfs',
    trigger_dag_id='upload_to_hdfs_task',  # 실행할 DAG ID
    wait_for_completion=True,  # 완료될 때까지 기다림
    dag=main_dag_youtube
)

# DAG 3 실행 (전처리)
depth2_etl_youtube_preprocessing = TriggerDagRunOperator(
    task_id='depth2_etl_youtube_preprocessing',
    trigger_dag_id='youtube_preprocessing',  # 실행할 DAG ID
    wait_for_completion=True,  # 완료될 때까지 기다림
    dag=main_dag_youtube
)


# DAG 실행 순서 설정
depth2_etl_youtube_api >> depth2_etl_load_to_hdfs >> depth2_etl_youtube_preprocessing
