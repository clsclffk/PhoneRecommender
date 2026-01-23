from django.core.management.base import BaseCommand
from django.db import connection
from crawled_data.models import TbcrawledYoutube, TbprocessedYoutube  
from utils.data_preprocessing import (
    clean_data, clean_text, normalize, split_sentences
)
from utils.sentiment_modeling import sentiment_classifier
from utils.brand_classification import predict_brand, has_brand_keyword
import pandas as pd
import time
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TextClassificationPipeline

# 감성 분석 모델 정의
MODEL_NAME = "Copycats/koelectra-base-v3-generalized-sentiment-analysis"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

# GPU/CPU 설정
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# 감성 분석 파이프라인
sentiment_classifier = TextClassificationPipeline(
    tokenizer=tokenizer, 
    model=model, 
    device=0 if torch.cuda.is_available() else -1
)

def truncate_table():
        with connection.cursor() as cursor:
            cursor.execute('TRUNCATE TABLE tbProcessed_Youtube')

class Command(BaseCommand):
    help = 'YouTube 데이터를 전처리하고 감성 분석 및 브랜드 분류 후 tbProcessed_Youtube 테이블에 적재'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('YouTube 데이터 처리 시작'))
        start_time = time.time()

        # 모델 필드명 전부 가져오기
        field_names = [f.name for f in TbcrawledYoutube._meta.get_fields()]
        self.stdout.write(self.style.WARNING(f"모든 필드: {field_names}"))

        # 데이터 로드
        youtube_data = TbcrawledYoutube.objects.all().values(*field_names)
        df = pd.DataFrame(list(youtube_data))
        self.stdout.write(self.style.WARNING(f"원본 적재 데이터 수: {df.shape[0]}개"))
        
        # 전처리
        df = clean_data(df)
        self.stdout.write(self.style.WARNING(f"[디버깅] clean_data 이후 행 개수: {df.shape[0]}개"))
        my_stopwords = {
            "근데", "진짜", "진쨔", "진짜루", "진짜로", "진쨔루"
        }
        df["cleaned_comment"] = df["comment"].apply(lambda x: clean_text(x, stopwords=my_stopwords))
        # cleaned_comment 추가 후 row 개수와 샘플 확인
        self.stdout.write(self.style.WARNING(f"[디버깅] clean_text 적용 후 행 개수: {df.shape[0]}개"))
        self.stdout.write(self.style.WARNING(f"[디버깅] clean_text 샘플:\n{df[['comment', 'cleaned_comment']].head(5)}"))

        df["normalized_comment"] = df["cleaned_comment"].apply(normalize)
        # normalized_comment 추가 후 row 개수와 샘플 확인
        self.stdout.write(self.style.WARNING(f"[디버깅] normalize 적용 후 행 개수: {df.shape[0]}개"))

        df['split_sentences'] = df['normalized_comment'].apply(split_sentences)
        df_split = df.explode("split_sentences").reset_index(drop=True)
        df_split = df_split.rename(columns={"split_sentences": "sentence"})
        empty_sentence = df_split[df_split['sentence'].astype(str).str.strip() == '']
        self.stdout.write(self.style.WARNING(f"[경고] explode 후 빈 sentence row 수: {empty_sentence.shape[0]}개"))
        self.stdout.write(self.style.WARNING(f"[문장 분리 후] {df_split.shape[0]}개"))

        # 브랜드 분류
        df_split = df_split[df_split["sentence"].apply(has_brand_keyword)].reset_index(drop=True)
        df_split['predicted_brand'] = df_split['sentence'].apply(predict_brand)
        self.stdout.write(self.style.WARNING(f"[브랜드 필터 후] {df_split.shape[0]}개"))

        # 감성 분석 배치 처리
        batch_sentences = df_split['sentence'].tolist()

        results = sentiment_classifier(
            batch_sentences,
            truncation=True,
            max_length=512
        )

        # 결과 추가
        df_split['sentiment_label'] = [int(r['label']) for r in results]
        df_split['sentiment_score'] = [float(r['score']) for r in results]

        end_time = time.time()  
        elasped_time = end_time - start_time

        self.stdout.write(self.style.SUCCESS(f"총 소요 시간: {elasped_time:.2f}초"))

        # 기존 삭제하고 다시 저장
        truncate_table()

        objects = []
        for _, row in df_split.iterrows():
            obj = TbprocessedYoutube(
                video_id = row['video_id'],
                comment = row['comment'],
                sentence = row['sentence'],
                like_count = row['like_count'],
                brand=row['predicted_brand'],  # samsung / apple
                sentiment_label=row['sentiment_label'],  # 1/0
                sentiment_score=row['sentiment_score'],  # float 확률
                comment_publish_date=row['comment_publish_date']
            )
            objects.append(obj)

        # 1000개씩 쪼개서 넣기 (성능 최적화)
        TbprocessedYoutube.objects.bulk_create(objects, batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f"{len(df_split)}개의 댓글이 tbProcessedYoutube에 저장 완료"))



