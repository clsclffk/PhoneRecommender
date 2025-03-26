# tmp1.py
import os
import time
import json
import pandas as pd
from googleapiclient.discovery import build
from airflow.models import Variable
from airflow.utils.email import send_email

# API_KEY = Variable.get("youtube_api_key")

# API
# def get_youtube_service(api_key):
#     return build('youtube', 'v3', developerKey=api_key)

# youtube_service = get_youtube_service(API_KEY)

# 비디오
def search_videos(search_query, published_after, api_key):
    youtube_service = build('youtube', 'v3', developerKey=api_key)
    request = youtube_service.search().list(
        q=search_query,
        part='snippet',
        type='video',
        maxResults=50,
        order='viewCount',
        publishedAfter=published_after
    )
    response = request.execute()
    video_data = [
        {
            'video_id': item['id']['videoId'],
            'title': item['snippet']['title'],
            'published_at': item['snippet']['publishedAt'],
            'channel_title': item['snippet']['channelTitle']
        }
        for item in response['items']
    ]
    # 보겸 TV 제외
    video_data = [video for video in video_data if video['channel_title'] != '보겸TV']

    return video_data, response.get('nextPageToken')

# 댓글
def get_all_comments(video_id, api_key):
    youtube_service = build('youtube', 'v3', developerKey=api_key)
    comments = []
    next_page_token = None
    while True:
        request = youtube_service.commentThreads().list(
            part='snippet',
            videoId=video_id,
            textFormat='plainText',
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            like_count = item['snippet']['topLevelComment']['snippet']['likeCount']
            published_at = item['snippet']['topLevelComment']['snippet']['publishedAt']
            comments.append({'comment': comment, 'like_count': like_count, 'published_at': published_at})

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
        time.sleep(1)

    return comments

# Parquet로 저장
def save_comments_to_parquet(all_comments, filename='youtube_comments.parquet'):
    data = []
    for video_id, video_info in all_comments.items():
        title = video_info['title']
        published_at = video_info['published_at']
        channel_title = video_info['channel_title']
        comments = video_info['comments']

        for comment in comments:
            data.append({
                'video_id': video_id,
                'title': title,
                'publish_date': published_at,
                'channel_name': channel_title,
                'comment': comment['comment'],
                'like_count': comment['like_count'],
                'comment_publish_date': comment['published_at']
            })

    df = pd.DataFrame(data)
    df.fillna('', inplace=True)
    df.to_parquet(filename, engine='pyarrow', index=False)
    print(f'저장 완료: {filename}')

# 이메일 알림
def send_failure_email(context):
    subject = f"DAG {context['dag'].dag_id} 실행 실패!"
    message = f"DAG 실패: {context['exception']}"
    send_email(to='comboy8231@gmail.com', subject=subject, html_content=message)

def send_success_email(context):
    subject = f"DAG {context['dag'].dag_id} 실행 성공!"
    message = "DAG이 성공적으로 실행되었습니다."
    send_email(to='comboy8231@gmail.com', subject=subject, html_content=message)

