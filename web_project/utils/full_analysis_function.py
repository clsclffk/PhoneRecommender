from collections import Counter
from collections import defaultdict
from django.db.models import Q
import pandas as pd
import hashlib
from crawled_data.models import TbProcessedYoutube, TbRawDanawa


# 해시 생성 헬퍼 함수 (추가)
def generate_keywords_hash(keywords):
    """키워드 리스트를 해시로 변환"""
    sorted_keywords = sorted(keywords)
    keyword_string = '|'.join(sorted_keywords)
    return hashlib.sha256(keyword_string.encode()).hexdigest()


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
    TbProcessedYoutube: sentences(TextField), commented_at 사용
    """
    qs = TbProcessedYoutube.objects.filter(brand=brand).values(
        'sentences', 'commented_at', 'sentiment_label'
    )
    rows = []
    for r in qs:
        text = r.get('sentences') or ''
        for line in (text if isinstance(text, str) else str(text)).split('\n'):
            s = line.strip()
            if not s:
                continue
            if any(kw in s for kw in selected_keywords):
                rows.append({
                    'sentence': s,
                    'comment_publish_date': r['commented_at'],
                    'sentiment_label': r['sentiment_label']
                })
    if not rows:
        return {}

    df = pd.DataFrame.from_records(rows)
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

    # 비율 계산
    final_result = {}

    for month, keyword_data in trend_result.items():
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
    """
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
                    result[brand][keyword][sentiment_type] = "데이터 없음"  
                    continue

                subset_sorted = subset.sort_values(
                    by=['sentiment_score', 'like_count'],
                    ascending=[False, False]
                )

                selected_sentence = subset_sorted.iloc[0]['sentence']
                result[brand][keyword][sentiment_type] = selected_sentence

    return result


# 다나와 평균 평점 계산 (TbRawDanawa: item_name, rating)
def get_danawa_avg_scores():
    raw_data = TbRawDanawa.objects.all().values('item_name', 'rating')
    df = pd.DataFrame(list(raw_data))
    if df.empty:
        return {'samsung': 0, 'apple': 0}

    df['brand'] = df['item_name'].apply(
        lambda x: 'samsung' if x and 'S24' in str(x) else 'apple' if x and '아이폰' in str(x) else None
    )
    df = df[df['brand'].notna()]
    if df.empty:
        return {'samsung': 0, 'apple': 0}
    avg_scores = df.groupby('brand')['rating'].mean().round(2).to_dict()
    return avg_scores