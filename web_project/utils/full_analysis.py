from utils.full_analysis_function import get_keyword_percentage, calc_keyword_sentiment_score, calc_overall_sentiment_ratio, get_keyword_trend_with_ratios, get_top_comments
from crawled_data.models import TbprocessedYoutube
from analysis.models import AnalysisResults
from utils.llm_api import summarize_sentences_with_llm
from utils.rag_analysis.pipeline import extract_keywords_with_llm, search_related_sentences
import pandas as pd
import time

def run_analysis_step1(hobby_entry, sorted_selected_keywords):
    sorted_selected_keywords = sorted(sorted_selected_keywords)

    print("[STEP 1] 키워드 빈도 + 트렌드 분석 시작")

    # 데이터 로드
    samsung_sentences = TbprocessedYoutube.objects.filter(brand='samsung').values_list('sentence', flat=True)
    apple_sentences = TbprocessedYoutube.objects.filter(brand='apple').values_list('sentence', flat=True)

    # 빈도 비율 계산
    samsung_freq_ratio = get_keyword_percentage(samsung_sentences, sorted_selected_keywords)
    apple_freq_ratio = get_keyword_percentage(apple_sentences, sorted_selected_keywords)

    # 월별 트렌드
    keyword_monthly_trend = {
        "samsung": get_keyword_trend_with_ratios(sorted_selected_keywords, brand="samsung"),
        "apple": get_keyword_trend_with_ratios(sorted_selected_keywords, brand="apple")
    }

    # 결과 저장
    AnalysisResults.objects.create(
        hobby_id=hobby_entry,
        selected_keywords=sorted_selected_keywords,
        freq_ratio_samsung=samsung_freq_ratio,
        freq_ratio_apple=apple_freq_ratio,
        keyword_monthly_trend=keyword_monthly_trend
    )

    print("[STEP 1] 저장 완료")

def run_analysis_step2(hobby_entry, sorted_selected_keywords):
    sorted_selected_keywords = sorted(sorted_selected_keywords)

    print("[STEP 2] 감성 분석 + 대표 문장 요약 시작")

    # 데이터 로드 (가능하면 캐싱 or 이전에 로딩된 df 넘기기)
    df = pd.DataFrame.from_records(
        TbprocessedYoutube.objects.all().values(
            'sentence',
            'brand',
            'sentiment_label',
            'sentiment_score',
            'like_count',
            'comment_publish_date'
        )
    )

    # 감성 점수, 비율 계산
    samsung_sentiment_score = calc_keyword_sentiment_score(df=df, brand="samsung", keywords=sorted_selected_keywords)
    apple_sentiment_score = calc_keyword_sentiment_score(df=df, brand="apple", keywords=sorted_selected_keywords)

    samsung_sentiment_ratio = calc_overall_sentiment_ratio(df, brand="samsung")
    apple_sentiment_ratio = calc_overall_sentiment_ratio(df, brand="apple")

    # 대표 문장 + LLM 요약
    top_comments = get_top_comments(df, sorted_selected_keywords)
    sentiment_top_sentences = summarize_sentences_with_llm(top_comments)

    # 기존 분석 결과 가져오기 & 업데이트
    analysis_result = AnalysisResults.objects.filter(
        hobby_id=hobby_entry,
        selected_keywords=sorted_selected_keywords
    ).order_by('-created_at').first()

    if analysis_result:
        analysis_result.sentiment_samsung_score = samsung_sentiment_score
        analysis_result.sentiment_apple_score = apple_sentiment_score
        analysis_result.sentiment_samsung_ratio = samsung_sentiment_ratio
        analysis_result.sentiment_apple_ratio = apple_sentiment_ratio
        analysis_result.sentiment_top_sentences = sentiment_top_sentences
        analysis_result.save()

    print("[STEP 2] 저장 완료")

def run_analysis_step3(hobby_entry, sorted_selected_keywords):
    sorted_selected_keywords = sorted(sorted_selected_keywords)

    print("[STEP 3] 연관어 분석 + 요약 시작")

    # RAG 연관 문장 검색
    related_sentences_samsung = search_related_sentences(hobby_entry.hobby_name, brand="samsung")
    related_sentences_apple = search_related_sentences(hobby_entry.hobby_name, brand="apple")

    # 키워드 추출
    extracted_keywords_samsung = extract_keywords_with_llm(related_sentences_samsung, top_k=20)
    extracted_keywords_apple = extract_keywords_with_llm(related_sentences_apple, top_k=20)

    related_words_samsung = {
        "brand": "samsung",
        "center": hobby_entry.hobby_name,
        "related_words": extracted_keywords_samsung
    }

    related_words_apple = {
        "brand": "apple",
        "center": hobby_entry.hobby_name,
        "related_words": extracted_keywords_apple
    }

    # 기존 분석 결과 가져오기 & 업데이트
    analysis_result = AnalysisResults.objects.filter(
        hobby_id=hobby_entry,
        selected_keywords=sorted_selected_keywords
    ).order_by('-created_at').first()

    if analysis_result:
        analysis_result.related_words_samsung = related_words_samsung
        analysis_result.related_words_apple = related_words_apple
        analysis_result.save()

    print("[STEP 3] 저장 완료")
