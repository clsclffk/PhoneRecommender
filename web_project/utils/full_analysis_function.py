from collections import Counter
from collections import defaultdict
from django.db.models import Q
import pandas as pd
from crawled_data.models import TbprocessedYoutube, TbcrawledDanawa  

def get_keyword_percentage(sentences, keyword_list):
    """
    문장 리스트에서 키워드 리스트의 빈도 백분율을 계산하는 함수
    """
    keyword_counts = Counter()

    # 키워드 카운트
    for sentence in sentences:
        for keyword in keyword_list:
            if keyword in sentence:
                keyword_counts[keyword] += 1

    # 전체 키워드 등장 횟수 합계
    total_count = sum(keyword_counts.values())

    # 등장한 키워드가 없을 경우 모두 0%
    if total_count == 0:
        return {key: 0 for key in keyword_list}
    
    # 백분율 계산 (소수점 2자리로 반올림)
    return {key: round((keyword_counts[key] / total_count) * 100, 2) for key in keyword_list}

# 키워드별 감성 점수 반환
def calc_keyword_sentiment_score(df, brand, keywords):
    brand_df = df[df['brand'] == brand]
    if brand_df.empty:
        return {}

    result = {}
    
    for keyword in keywords:
        keyword_df = brand_df[brand_df['sentence'].str.contains(keyword)]
        if keyword_df.empty:
            continue

        avg_pos = keyword_df[keyword_df['sentiment_label'] == '1']['sentiment_score'].mean()
        avg_neg = keyword_df[keyword_df['sentiment_label'] == '0']['sentiment_score'].mean()

        # NaN 처리 → 0으로 대체
        avg_pos = 0 if pd.isna(avg_pos) else avg_pos
        avg_neg = 0 if pd.isna(avg_neg) else avg_neg

        result[keyword] = {
            'pos': round(avg_pos or 0, 4),
            'neg': round(avg_neg or 0, 4)
        }
    return result

# 브랜드 전체 긍부정 비율 반환
def calc_overall_sentiment_ratio(df, brand):
    brand_df = df[df['brand'] == brand]
    if brand_df.empty:
        return {}

    pos_count = len(brand_df[brand_df['sentiment_label'] == '1'])
    neg_count = len(brand_df[brand_df['sentiment_label'] == '0'])
    total = pos_count + neg_count

    if total == 0:
        return {}

    return {
        'pos': round(pos_count / total, 4),
        'neg': round(neg_count / total, 4)
    }

def get_keyword_trend_with_ratios(selected_keywords, brand='samsung'):
    """
    선택한 키워드 기준으로 월별 키워드 비율 및 감성 비율만 반환하는 함수

    {
        '2025-01': {
            '카메라': {
                'ratio': 0.6,        # 전체 키워드 언급량 중 '카메라' 비율
                'pos_ratio': 0.7,    # '카메라' 언급 중 긍정 비율
                'neg_ratio': 0.3     # '카메라' 언급 중 부정 비율
            },
            ...
        },
        ...
    }

    1. ratio (키워드 비율)
       → 특정 키워드가 월별 전체 키워드 언급량에서 차지하는 비율
       → 계산식:
           ratio = (해당 키워드 언급량) / (선택한 키워드 전체 언급량 합계)
    
    2. pos_ratio (긍정 비율)
       → 특정 키워드에 대한 전체 언급 중 긍정 비율
       → 계산식:
           pos_ratio = (해당 키워드의 긍정 언급 수) / (해당 키워드 전체 언급 수)
    
    3. neg_ratio (부정 비율)
       → 특정 키워드에 대한 전체 언급 중 부정 비율
       → 계산식:
           neg_ratio = (해당 키워드의 부정 언급 수) / (해당 키워드 전체 언급 수)

    """

    # 댓글 필터링
    qs = TbprocessedYoutube.objects.filter(
        brand=brand,
        sentence__iregex=r'(' + '|'.join(selected_keywords) + ')'
    ).values('sentence', 'comment_publish_date', 'sentiment_label')

    if not qs.exists():
        return {}

    # DataFrame 변환
    df = pd.DataFrame.from_records(qs)

    # 날짜 전처리
    df['month'] = pd.to_datetime(df['comment_publish_date']).dt.to_period('M').astype(str)

    # 초기화
    trend_result = defaultdict(lambda: defaultdict(lambda: {
        "count": 0,
        "pos": 0,
        "neg": 0
    }))

    # 각 문장에서 키워드 카운트 & 감성 집계
    for _, row in df.iterrows():
        month = row['month']
        sentence = row['sentence']
        sentiment = row['sentiment_label']

        for keyword in selected_keywords:
            if keyword in sentence:
                trend_result[month][keyword]['count'] += 1
                if sentiment == '1':
                    trend_result[month][keyword]['pos'] += 1
                elif sentiment == '0':
                    trend_result[month][keyword]['neg'] += 1

    # 비율 계산 (0 ~ 1 사이 비율)
    final_result = {}

    for month, keyword_data in trend_result.items():
        # 월별 전체 키워드 언급 총합
        month_total_count = sum([data['count'] for data in keyword_data.values()])
        if month_total_count == 0:
            continue

        final_result[month] = {}

        for keyword, data in keyword_data.items():
            count = data['count']
            pos = data['pos']
            neg = data['neg']

            ratio = round(count / month_total_count, 4) if month_total_count != 0 else 0
            pos_ratio = round(pos / count, 4) if count != 0 else 0
            neg_ratio = round(neg / count, 4) if count != 0 else 0

            final_result[month][keyword] = {
                "ratio": ratio,
                "pos_ratio": pos_ratio,
                "neg_ratio": neg_ratio
            }

    return final_result

def get_top_comments(df, selected_keywords):
    """
    브랜드별 긍정/부정 대표 문장 추출
    - 좋아요 수가 가장 높은 문장 또는 감성 점수가 가장 높은 문장 기준
    - 브랜드별 + 키워드별 + 긍정/부정 대표 문장 추출
    결과 예시:
    {
        "samsung": {
            "카메라": {
                "pos": "카메라가 선명하고 배터리가 오래 간다.",
                "neg": "카메라가 저조도에서 흐릿해요."
            },
            "배터리": {...}
        },
        "apple": {
            "카메라": {...},
            "배터리": {...}
        }
    }
    """

    # 브랜드 필터링
    df = df[df['brand'].isin(['samsung', 'apple'])]

    result = {
        "samsung": {},
        "apple": {}
    }

    for keyword in selected_keywords:
        for brand in ['samsung', 'apple']:
            result[brand][keyword] = {}

            for label in ['1', '0']:  # 1: 긍정, 0: 부정
                subset = df[
                    (df['brand'] == brand) &
                    (df['sentiment_label'] == label) &
                    (df['sentence'].str.contains(keyword))
                ]

                sentiment_type = 'pos' if label == '1' else 'neg'

                if subset.empty:
                    print(f"[INFO] {brand} - {keyword} - {'긍정' if label == '1' else '부정'} 문장 없음")
                    result[brand][keyword][sentiment_type] = "데이터 없음"  
                    continue

                subset_sorted = subset.sort_values(
                    by=['sentiment_score', 'like_count'],
                    ascending=[False, False]
                )

                selected_sentence = subset_sorted.iloc[0]['sentence']
                result[brand][keyword][sentiment_type] = selected_sentence

    return result

# 다나와 평균 평점 계산
def get_danawa_avg_scores():
    raw_data = TbcrawledDanawa.objects.all().values('scoring', 'item')
    df = pd.DataFrame(list(raw_data))

    df['brand'] = df['item'].apply(lambda x: 'samsung' if x == 'S24' else 'apple' if x == '아이폰16' else None)
    df['scoring'] = df['scoring'].astype(str).str.replace('점', '', regex=False)
    df['scoring'] = pd.to_numeric(df['scoring'], errors='coerce')

    avg_scores = df.groupby('brand')['scoring'].mean().round(2).to_dict()
    return avg_scores