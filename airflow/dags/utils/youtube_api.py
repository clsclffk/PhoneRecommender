import os
import time
import pandas as pd
from googleapiclient.discovery import build
from airflow.models import Variable


class YoutubeAPICollector:
    """유튜브 API를 이용한 댓글 수집기"""
    
    def __init__(self, output_dir='/home/lab13/airflow/data/youtube'):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Airflow Variable에서 설정 가져오기
        self.search_queries = Variable.get("youtube_search_query", deserialize_json=True)
        self.published_afters = Variable.get("youtube_published_after", deserialize_json=True)
        self.parquet_filenames = Variable.get("parquet_filename", deserialize_json=True)
        self.api_keys = Variable.get("youtube_api_key", deserialize_json=True)
    
    def search_videos(self, search_query, published_after, api_key):
        """비디오 검색"""
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
        
        # 특정 채널 제외
        video_data = [video for video in video_data if video['channel_title'] != '보겸TV']
        
        return video_data
    
    def get_all_comments(self, video_id, api_key):
        """비디오의 모든 댓글 가져오기"""
        youtube_service = build('youtube', 'v3', developerKey=api_key)
        comments = []
        next_page_token = None
        
        while True:
            try:
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
                    
                    comments.append({
                        'comment': comment,
                        'like_count': like_count,
                        'published_at': published_at
                    })
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                
                time.sleep(1)
            
            except Exception as e:
                print(f"댓글 수집 중 오류 발생: {e}")
                break
        
        return comments
    
    def save_to_parquet(self, all_comments, filename):
        """댓글 데이터를 Parquet 파일로 저장"""
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
        
        output_path = os.path.join(self.output_dir, filename)
        df.to_parquet(output_path, engine='pyarrow', index=False)
        print(f'저장 완료: {output_path}')
    
    def collect_comments(self, search_query, published_after, api_key):
        """비디오 검색 후 댓글 수집"""
        print(f"\n'{search_query}' 검색 시작")
        
        # 비디오 검색
        video_data = self.search_videos(search_query, published_after, api_key)
        print(f"검색된 비디오: {len(video_data)}개")
        
        # 각 비디오의 댓글 수집
        all_comments = {}
        for video in video_data:
            video_id = video['video_id']
            print(f"  - {video['title'][:30]}... 댓글 수집 중")
            
            comments = self.get_all_comments(video_id, api_key)
            all_comments[video_id] = {
                'title': video['title'],
                'published_at': video['published_at'],
                'channel_title': video['channel_title'],
                'comments': comments
            }
        
        return all_comments
    
    def run(self):
        """전체 수집 프로세스 실행"""
        try:
            for i, search_query in enumerate(self.search_queries):
                published_after = self.published_afters[i]
                parquet_filename = self.parquet_filenames[i]
                api_key = self.api_keys[i]
                
                # 댓글 수집
                all_comments = self.collect_comments(search_query, published_after, api_key)
                
                # Parquet 저장
                self.save_to_parquet(all_comments, parquet_filename)
            
            print("\n★ 유튜브 댓글 수집 완료 ★")
        
        except Exception as e:
            print(f"수집 중 오류 발생: {e}")
            raise


def collect_youtube_comments():
    """Airflow Task에서 호출할 함수"""
    collector = YoutubeAPICollector()
    collector.run()


if __name__ == '__main__':
    collect_youtube_comments()