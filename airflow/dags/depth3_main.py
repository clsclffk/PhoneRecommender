from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime, timedelta
from airflow.utils.email import send_email


# ✅ 이메일 알림 설정
def send_failure_email(context):
    subject = f"DAG {context['dag'].dag_id} 실행 실패!"
    message = f"DAG 실패: {context['exception']}"
    send_email(to='comboy8231@gmail.com', subject=subject, html_content=message)

def send_success_email(context):
    subject = f"DAG {context['dag'].dag_id} 실행 성공!"
    message = "DAG이 성공적으로 실행되었습니다."
    send_email(to='comboy8231@gmail.com', subject=subject, html_content=message)


# ✅ 기본 설정
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 2, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': True, 
    'email_on_retry': False,   
    'email': ['comboy8231@gmail.com'], 
    'on_failure_callback': send_failure_email, 
    'on_success_callback': send_success_email   
}

# ✅ Main DAG (Danawa + YouTube 병렬 실행)
main_dag = DAG(
    'depth3_main',
    default_args=default_args,
    schedule_interval='@monthly',
    catchup=False
)

# ✅ Danawa DAG 실행
start_danawa_dag = TriggerDagRunOperator(
    task_id='start_danawa_dag',
    trigger_dag_id='depth2_danawa',  
    wait_for_completion=False,  # 즉시 실행 후 종료
    dag=main_dag
)

# ✅ YouTube DAG 실행
start_youtube_dag = TriggerDagRunOperator(
    task_id='start_youtube_dag',
    trigger_dag_id='depth2_youtube',  
    wait_for_completion=False,  # 즉시 실행 후 종료
    dag=main_dag
)

# ✅ Danawa와 YouTube 병렬 실행
start_danawa_dag >> start_youtube_dag
