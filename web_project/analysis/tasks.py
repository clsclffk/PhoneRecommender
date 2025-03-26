from celery import shared_task
import pandas as pd
from analysis.models import AnalysisResults
from hobbies.models import HobbyKeywords
from crawled_data.models import TbprocessedYoutube
from phone_recommendations.models import PhoneRecommendations
from utils.full_analysis_function import get_keyword_percentage, calc_keyword_sentiment_score, calc_overall_sentiment_ratio, get_keyword_trend_with_ratios, get_top_comments
from utils.llm_api import summarize_sentences_with_llm
from utils.rag_analysis.pipeline import extract_keywords_with_llm, search_related_sentences
from django.db import transaction
import time
from datetime import datetime
from utils.rag_phone_recommend.pipeline import search_phone_recommendations, generate_recommendation_text, save_recommendations_to_db

# 페이지별 요약 생성 함수 임포트
from utils.llm_api import (
    generate_summary_for_page_1_1,
    generate_summary_for_page_1_2,
    generate_summary_for_page_2_1,
    generate_summary_for_page_2_2,
    generate_summary_for_page_3
)

@shared_task
def run_analysis_step1_task(analysis_id):
    print("[TASK] Step 1 데이터 분석 시작")
    try:
        # AnalysisResults 객체 불러오기
        analysis_result = AnalysisResults.objects.get(analysis_id=analysis_id)

        hobby_entry = analysis_result.hobby_id
        hobby = hobby_entry.hobby_name
        sorted_keywords = analysis_result.selected_keywords

        # 데이터 로드
        samsung_sentences = TbprocessedYoutube.objects.filter(brand='samsung').values_list('sentence', flat=True)
        apple_sentences = TbprocessedYoutube.objects.filter(brand='apple').values_list('sentence', flat=True)

        # 분석 수행
        samsung_freq_ratio = get_keyword_percentage(samsung_sentences, sorted_keywords)
        apple_freq_ratio = get_keyword_percentage(apple_sentences, sorted_keywords)

        keyword_monthly_trend = {
            "samsung": get_keyword_trend_with_ratios(sorted_keywords, brand="samsung"),
            "apple": get_keyword_trend_with_ratios(sorted_keywords, brand="apple")
        }

        # 저장
        print(f"[DEBUG] Step 1 저장 직전 - freq_ratio_apple={apple_freq_ratio}")
        print(f"[DEBUG] Step 1 저장 직전 - freq_ratio_samsung={samsung_freq_ratio}")

        analysis_result.freq_ratio_samsung = samsung_freq_ratio
        analysis_result.freq_ratio_apple = apple_freq_ratio
        analysis_result.keyword_monthly_trend = keyword_monthly_trend
        analysis_result.save(update_fields=['freq_ratio_samsung',
                                            'freq_ratio_apple',
                                            'keyword_monthly_trend'])

        print("[DONE] Step 1 데이터 분석 저장 완료")

    except Exception as e:
        print(f"[ERROR] Step 1 데이터 분석 실패: {e}")

@shared_task
def generate_summary_page_1_1(analysis_id):
    print("[TASK] summary_page_1_1 작업 시작")

    try:
        with transaction.atomic():
            # AnalysisResults를 analysis_id로 조회
            analysis_result = AnalysisResults.objects.get(analysis_id=analysis_id)

            # 관련 데이터 추출
            hobby_entry = analysis_result.hobby_id  
            hobby = hobby_entry.hobby_name
            sorted_keywords = analysis_result.selected_keywords  

            # 여기에 로그 추가!!! (핵심 데이터 상태 체크)
            print(f"[DEBUG] analysis_id={analysis_id}")
            print(f"[DEBUG] hobby={hobby}")
            print(f"[DEBUG] sorted_keywords={sorted_keywords}")
            print(f"[DEBUG] freq_ratio_apple={analysis_result.freq_ratio_apple}")
            print(f"[DEBUG] freq_ratio_samsung={analysis_result.freq_ratio_samsung}")

            # summary 생성 함수 호출
            summary = generate_summary_for_page_1_1(
                hobby,
                sorted_keywords,
                analysis_result.freq_ratio_apple,
                analysis_result.freq_ratio_samsung
            )

            print(f"[DEBUG] 생성된 summary={summary}")

            # 결과 저장
            analysis_result.summary_page_1_1 = summary
            analysis_result.save(update_fields=['summary_page_1_1'])  # 변경된 필드만 저장

            print("[DONE] summary_page_1_1 저장 완료")
            print(f"[DEBUG] 저장 후 summary_page_1_1={analysis_result.summary_page_1_1}")

    except Exception as e:
        print(f"[ERROR] summary_page_1_1 Task 실패: {e}")

@shared_task
def generate_summary_page_1_2(analysis_id):

    """Page 1-2 요약 Celery 비동기 Task"""
    print("[TASK] summary_page_1_2 작업 시작")

    try:
        # AnalysisResults를 analysis_id로 조회
        analysis_result = AnalysisResults.objects.get(analysis_id=analysis_id)

        # 관련 데이터 추출
        hobby_entry = analysis_result.hobby_id  # FK라서 객체 바로 가져올 수 있음
        hobby = hobby_entry.hobby_name
        sorted_keywords = analysis_result.selected_keywords
        keyword_monthly_trend = analysis_result.keyword_monthly_trend
        
        # 요약 생성 함수 호출
        summary = generate_summary_for_page_1_2(
            hobby,
            sorted_keywords,
            keyword_monthly_trend
        )

        # 결과 저장
        analysis_result.summary_page_1_2 = summary
        analysis_result.save(update_fields=['summary_page_1_2'])

        print("[DONE] summary_page_1_2 저장 완료")

    except Exception as e:
        print(f"[ERROR] summary_page_1_2 Task 실패: {e}")

@shared_task
def run_analysis_step2_task(analysis_id):
    print("[TASK] Step 2 데이터 분석 시작")

    try:
        # AnalysisResults 가져오기
        analysis_result = AnalysisResults.objects.get(analysis_id=analysis_id)
        #analysis_result.refresh_from_db() 
        # 관련 정보 로드
        hobby_entry = analysis_result.hobby_id
        hobby_name = hobby_entry.hobby_name
        sorted_keywords = analysis_result.selected_keywords

        # 데이터 로드 (한 번만 불러와서 필터링)
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

        # 감성 점수 계산
        samsung_sentiment_score = calc_keyword_sentiment_score(df, brand="samsung", keywords=sorted_keywords)
        apple_sentiment_score = calc_keyword_sentiment_score(df, brand="apple", keywords=sorted_keywords)

        # 긍/부정 비율 계산
        samsung_sentiment_ratio = calc_overall_sentiment_ratio(df, brand="samsung")
        apple_sentiment_ratio = calc_overall_sentiment_ratio(df, brand="apple")

        # 대표 문장 뽑기 → LLM 요약 (함수 내부에서 LLM 호출)
        top_comments = get_top_comments(df, sorted_keywords)
        sentiment_top_sentences = summarize_sentences_with_llm(top_comments)

        # 값 저장
        print(f"[DEBUG] 저장 직전 summary_page_1_1={analysis_result.summary_page_1_1}")
        analysis_result.sentiment_samsung_score = samsung_sentiment_score
        analysis_result.sentiment_apple_score = apple_sentiment_score
        analysis_result.sentiment_samsung_ratio = samsung_sentiment_ratio
        analysis_result.sentiment_apple_ratio = apple_sentiment_ratio
        analysis_result.sentiment_top_sentences = sentiment_top_sentences
        print(f"[DEBUG] 저장 직전 summary_page_1_1={analysis_result.summary_page_1_1}")
        analysis_result.save(update_fields=[
            'sentiment_samsung_score',
            'sentiment_apple_score',
            'sentiment_samsung_ratio',
            'sentiment_apple_ratio',
            'sentiment_top_sentences'
        ])

        print("[DONE] Step 2 데이터 분석 저장 완료")

    except Exception as e:
        print(f"[ERROR] Step 2 데이터 분석 실패: {e}")

@shared_task
def generate_summary_page_2_1(analysis_id):
    print("[TASK] summary_page_2_1 작업 시작")

    try:
        # AnalysisResults를 analysis_id로 조회
        analysis_result = AnalysisResults.objects.get(analysis_id=analysis_id)

        # 관련 데이터 추출
        hobby_entry = analysis_result.hobby_id  # FK라서 객체 바로 가져올 수 있음
        hobby = hobby_entry.hobby_name
        sorted_keywords = analysis_result.selected_keywords
        keyword_monthly_trend = analysis_result.keyword_monthly_trend

        # 요약 생성 함수 호출
        summary = generate_summary_for_page_2_1(
            hobby,
            sorted_keywords,
            analysis_result.sentiment_apple_score,
            analysis_result.sentiment_samsung_score,
            analysis_result.sentiment_apple_ratio,
            analysis_result.sentiment_samsung_ratio,
            analysis_result.keyword_monthly_trend
        )

        # 저장
        analysis_result.summary_page_2_1 = summary
        analysis_result.save(update_fields=['summary_page_2_1'])

        print("[DONE] summary_page_2_1 저장 완료")

    except Exception as e:
        print(f"[ERROR] summary_page_2_1 Task 실패: {e}")

@shared_task
def generate_summary_page_2_2(analysis_id):
    print("[TASK] summary_page_2_2 작업 시작")

    try:
        # AnalysisResults를 analysis_id로 조회
        analysis_result = AnalysisResults.objects.get(analysis_id=analysis_id)

        # 관련 데이터 추출
        hobby_entry = analysis_result.hobby_id  # FK라서 객체 바로 가져올 수 있음
        hobby = hobby_entry.hobby_name
        sorted_keywords = analysis_result.selected_keywords

        # 요약 생성 함수 호출
        summary = generate_summary_for_page_2_2(
            hobby,
            sorted_keywords,
            analysis_result.sentiment_top_sentences
        )

        # 저장
        analysis_result.summary_page_2_2 = summary
        analysis_result.save(update_fields=['summary_page_2_2'])

        print("[DONE] summary_page_2_2 저장 완료")

    except Exception as e:
        print(f"[ERROR] summary_page_2_2 Task 실패: {e}")


@shared_task
def run_analysis_step3_task(analysis_id):
    print("[TASK] Step 3 데이터 분석 시작")

    try:
        # AnalysisResults 가져오기
        analysis_result = AnalysisResults.objects.get(analysis_id=analysis_id)
        # analysis_result.refresh_from_db() 
        # 관련 정보 로드
        hobby_entry = analysis_result.hobby_id
        hobby_name = hobby_entry.hobby_name
        sorted_keywords = analysis_result.selected_keywords

        # RAG 검색 → 각 브랜드 문장 수집
        related_sentences_samsung = search_related_sentences(hobby_name, brand="samsung")
        related_sentences_apple = search_related_sentences(hobby_name, brand="apple")

        # LLM 키워드 추출 (20개)
        extracted_keywords_samsung = extract_keywords_with_llm(related_sentences_samsung, top_k=20)
        extracted_keywords_apple = extract_keywords_with_llm(related_sentences_apple, top_k=20)

        # 포맷 맞추기 (dict 형태)
        related_words_samsung = {
            "brand": "samsung",
            "center": hobby_name,
            "related_words": extracted_keywords_samsung
        }

        related_words_apple = {
            "brand": "apple",
            "center": hobby_name,
            "related_words": extracted_keywords_apple
        }

        # 값 저장
        # analysis_result.refresh_from_db()
        analysis_result.related_words_samsung = related_words_samsung
        analysis_result.related_words_apple = related_words_apple
        analysis_result.save(update_fields=[''
        'related_words_samsung',
        'related_words_apple'])

        print("[DONE] Step 3 데이터 분석 저장 완료")

    except Exception as e:
        print(f"[ERROR] Step 3 데이터 분석 실패: {e}")

@shared_task
def generate_summary_page_3(analysis_id):
    print("[TASK] summary_page_3 작업 시작")

    try:
        # AnalysisResults를 analysis_id로 조회
        analysis_result = AnalysisResults.objects.get(analysis_id=analysis_id)

        # 관련 데이터 추출
        hobby_entry = analysis_result.hobby_id  # FK라서 객체 바로 가져올 수 있음
        hobby = hobby_entry.hobby_name
        sorted_keywords = analysis_result.selected_keywords

        summary = generate_summary_for_page_3(
            hobby,
            sorted_keywords,
            analysis_result.related_words_apple,
            analysis_result.related_words_samsung
        )

        analysis_result.summary_page_3 = summary
        analysis_result.save(update_fields=['summary_page_3'])

        print("[DONE] summary_page_3 저장 완료")

    except Exception as e:
        print(f"[ERROR] summary_page_3 Task 실패: {e}")

@shared_task
# rag로 폰 추천하고 DB에 저장하는 task
def run_analysis_step4_task(analysis_id):
    try:
        analysis_result = AnalysisResults.objects.get(analysis_id=analysis_id)
        hobby_entry = analysis_result.hobby_id
        selected_keywords = analysis_result.selected_keywords

        exists = PhoneRecommendations.objects.filter(
            hobby_id=hobby_entry,
            selected_keywords=sorted(selected_keywords)
        ).exists()

        if exists:
            print(f"[INFO] 이미 추천 있음! 분석 ID: {analysis_id}")
            return

        recommendations = search_phone_recommendations(hobby_entry.hobby_name, selected_keywords)
        generated_text = generate_recommendation_text(
            recommendations,
            hobby_entry.hobby_name,
            selected_keywords
        )

        save_recommendations_to_db(hobby_entry, sorted(selected_keywords), generated_text)

        print(f"[INFO] 추천 완료! 분석 ID: {analysis_id}")
    
    except Exception as e:
        print(f"[ERROR] Step 4 추천 생성 실패: {e}")
