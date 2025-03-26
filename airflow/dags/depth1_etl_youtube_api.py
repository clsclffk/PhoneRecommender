# tmp2.py
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.models.baseoperator import chain
from datetime import datetime
from airflow.models import Variable
from airflow.utils.dates import days_ago
from youtube_api_function import search_videos, get_all_comments, save_comments_to_parquet, send_failure_email, send_success_email
import logging

youtube_search_queries = Variable.get("youtube_search_query", deserialize_json=True)
youtube_published_afters = Variable.get("youtube_published_after", deserialize_json=True)
parquet_filenames = Variable.get("parquet_filename", deserialize_json=True)
youtube_api_keys = Variable.get("youtube_api_key", deserialize_json=True)

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 2, 4),
    'retries': 1,
#    'email_on_failure': True,
#    'email_on_retry': False,
#    'email': ['comboy8231@gmail.com'],
#    'on_failure_callback': send_failure_email,
#    'on_success_callback': send_success_email
}

# 비디오 검색
def video_search_task(search_query, published_after, api_key, **kwargs):
    video_data, _ = search_videos(search_query, published_after, api_key)
    logging.error(search_query)
    logging.error(video_data)
    kwargs['ti'].xcom_push(key=f'video_data_{search_query.replace(" ", "_")}', value=video_data)
    logging.info(f"API Key: {api_key}")

# 댓글 수집
def comment_collection_task(search_query, api_key, **kwargs):
    video_data = kwargs['ti'].xcom_pull(key=f'video_data_{search_query.replace(" ", "_")}', task_ids=f'video_search_task_{search_query.replace(" ", "_")}')
    logging.error(search_query)
    logging.error(video_data)
    all_comments = {}
    for video in video_data:
        video_id = video['video_id']
        comments = get_all_comments(video_id, api_key)
        all_comments[video_id] = {
            'title': video['title'],
            'published_at': video['published_at'],
            'channel_title': video['channel_title'],
            'comments': comments
        }
    kwargs['ti'].xcom_push(key=f'all_comments_{search_query.replace(" ", "_")}', value=all_comments)

# 댓글 parquet 저장
def save_comments_task(search_query, parquet_filename, **kwargs):
    all_comments = kwargs['ti'].xcom_pull(key=f'all_comments_{search_query.replace(" ", "_")}', task_ids=f'comment_collection_task_{search_query.replace(" ", "_")}')
    save_comments_to_parquet(all_comments, filename=parquet_filename)

# DAG 정의
# 매달 1일에 실행하도록 일단 설정!
with DAG('youtube_comments_dag', default_args=default_args, schedule_interval=None) as dag:

    rm_data = BashOperator(
            task_id = 'rm_youtube_data',
            bash_command = f'''
            cd ~/airflow/youtube_data &&
            rm -f *.parquet
            '''
            )
    save_comment_tasks = []
    for i, search_query in enumerate(youtube_search_queries):
        published_after = youtube_published_afters[i]
        parquet_filename = parquet_filenames[i]
        api_key = youtube_api_keys[i]

        # 비디오 검색 Task
        video_search = PythonOperator(
            task_id=f'video_search_task_{search_query.replace(" ", "_")}',
            python_callable=video_search_task,
            op_args=[search_query, published_after, api_key],
            provide_context=True
        )

        # 댓글 수집 Task
        comment_collection = PythonOperator(
            task_id=f'comment_collection_task_{search_query.replace(" ", "_")}',
            python_callable=comment_collection_task,
            op_args=[search_query, api_key],
            provide_context=True
        )

        # 댓글 저장 Task
        save_comments = PythonOperator(
            task_id=f'save_comments_task_{search_query.replace(" ", "_")}',
            python_callable=save_comments_task,
            op_args=[search_query, parquet_filename],
            provide_context=True
        )

        # Task 순서
        video_search >> comment_collection >> save_comments

        save_comment_tasks.append(save_comments)

    chain(rm_data, * save_comment_tasks)
