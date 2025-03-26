from django.core.management.base import BaseCommand
from django.db import connection
from crawled_data.models import TbcrawledDanawa, TbprocessedDanawa
import pandas as pd
import time
import requests
from konlpy.tag import Okt
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TextClassificationPipeline
from tqdm import tqdm
from utils.data_preprocessing import clean_data, clean_text, normalize, split_sentences
from utils.brand_classification import has_brand_keyword

def truncate_table():
    with connection.cursor() as cursor:
        cursor.execute('TRUNCATE TABLE tbProcessed_Danawa')

class Command(BaseCommand):
   
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('[다나와 처리 시작]'))

         # 1. 불용어 로드
        url = "https://raw.githubusercontent.com/yoonkt200/FastCampusDataset/master/korean_stopwords.txt"
        response = requests.get(url)
        external_stopwords = response.text.splitlines()

        # 데이터 로드
        raw_data = TbcrawledDanawa.objects.all().values('scoring', 'review_content', 'item')
        df = pd.DataFrame(list(raw_data))   

        # 전처리
        df = df.dropna(subset=['review_content']) 
        df = df[df['review_content'].str.strip() != '']
        df['clean_review'] = df['review_content'].apply(lambda x: clean_text(x, stopwords=external_stopwords))
        df['normalized_review'] = df['clean_review'].apply(normalize)
        df['split_sentences'] = df['normalized_review'].apply(split_sentences)
        df = df.explode('split_sentences').reset_index(drop=True)
        df = df.rename(columns={'split_sentences': 'sentence'})

        # 관련없는 문장 제거
        df = df[df["sentence"].apply(has_brand_keyword)].reset_index(drop=True)
        
        # 감성 분석
        tokenizer = AutoTokenizer.from_pretrained("Copycats/koelectra-base-v3-generalized-sentiment-analysis")
        model = AutoModelForSequenceClassification.from_pretrained("Copycats/koelectra-base-v3-generalized-sentiment-analysis")
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        sentiment_classifier = TextClassificationPipeline(
            tokenizer=tokenizer, model=model, device=0 if torch.cuda.is_available() else -1
        )

        # 감성 분석 실행
        def process_in_batches(reviews, batch_size=32):
            results = []
            for i in tqdm(range(0, len(reviews), batch_size)):
                batch = reviews[i:i+batch_size]
                preds = sentiment_classifier(batch, truncation=True, max_length=512)
                results.extend(preds)
            return results

        reviews = df['sentence'].tolist()
        predictions = process_in_batches(reviews)

        df['sentiment_label'] = [int(pred['label']) for pred in predictions]
        df['sentiment_score'] = [float(pred['score']) for pred in predictions]

        # 명사 추출
        okt = Okt()
        df['noun'] = df['sentence'].apply(lambda x: " ".join(okt.nouns(x)))

        # 브랜드 기준으로 구분 (S24 → 삼성, 아이폰16 → 애플)
        df['brand'] = df['item'].apply(lambda x: 'samsung' if x == 'S24' else 'apple' if x == '아이폰16' else None)

        # 기존 데이터 삭제
        truncate_table()

        objects = []
        for _, row in df.iterrows():
            obj = TbprocessedDanawa(
                review_content = row['review_content'],
                sentence = row['sentence'],
                brand = row['brand'],
                sentiment_label = row['sentiment_label'],
                sentiment_score = row['sentiment_score'],
                noun = row['noun'],
                scoring = row['scoring']  # 평점도 같이 저장
            )
            objects.append(obj)

        # DB에 저장
        TbprocessedDanawa.objects.bulk_create(objects, batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f"{len(objects)}개 리뷰가 Tbprocessed_Danawa에 저장 완료"))