from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime
from airflow.models import Variable
from youtube_api_function import send_failure_email, send_success_email

parquet_file_path = Variable.get(f"parquet_file_path")
hdfs_dir = Variable.get("hdfs_dir")

# DAG 정의
with DAG('upload_to_hdfs_task', 
         default_args={
             'owner': 'airflow',
             'start_date': datetime(2025, 2, 4),
             'retries': 1,
            #  'email_on_failure': True, 
            #  'email_on_retry': False,
            #  'email': ['comboy8231@gmail.com'],
            #  'on_failure_callback': send_failure_email,  
            #  'on_success_callback': send_success_email,  
         }, 
         schedule_interval=None) as dag: 
    
    # HDFS 업로드 Task
    # parquet_file_path : /home/lab13/airflow/dags/youtube_i16_1.parquet
    upload_to_hdfs = BashOperator(
        task_id='upload_to_hdfs_task',
        bash_command=f'''
        hdfs dfs -put -f /home/lab13/airflow/youtube_data/*.parquet /youtube_data
        '''
    )
    upload_to_hdfs
