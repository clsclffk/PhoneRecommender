from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.models import Variable
from datetime import datetime, timedelta

# DAG 정의
with DAG(
    dag_id='danawa_to_hdfs',
    default_args={
        'owner': 'airflow',
        'depends_on_past' : False,
        'start_date': datetime(2025, 2, 1),
        'retries': 1,
        'retry_delay': timedelta(minutes=5)
    },
    schedule_interval=None,
    catchup=False
) as dag:

    # HDFS 업로드 Task
    danawa_to_hdfs = BashOperator(
        task_id='danawa_to_hdfs',
        bash_command=f'''
        hdfs dfs -rm -r /danawa_data/* &&
        cd ~/airflow/danawa_data &&
        hdfs dfs -put -f /home/lab13/airflow/danawa_data/*.parquet /danawa_data
        ''',
    )
    danawa_to_hdfs
