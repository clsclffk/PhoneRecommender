from celery import shared_task
import pandas as pd
import json
from analysis.models import TbAnalysisResults
from hobbies.models import TbHobbies
from crawled_data.models import TbProcessedYoutube
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
# 성능 병목 로깅
from utils.timer_decorator import timer

def _flatten_sentences(queryset_sentences):
    """TbProcessedYoutube.sentences (텍스트)를 문장 리스트로 변환"""
    out = []
    for text in queryset_sentences:
        if not text:
            continue
        for line in (text if isinstance(text, str) else str(text)).split('\n'):
            s = line.strip()
            if s:
                out.append(s)
    return out


@shared_task
@timer 
def run_analysis_step1_task(analysis_id):
    print("[TASK] Step 1 데이터 분석 시작")
    try:
        analysis_result = TbAnalysisResults.objects.get(analysis_id=analysis_id)
        hobby_entry = analysis_result.hobby
        hobby = hobby_entry.hobby_name
        sorted_keywords = analysis_result.keywords or []

        # 데이터 로드: sentences 필드를 문장 리스트로 펼침
        qs_samsung = TbProcessedYoutube.objects.filter(brand='samsung').values_list('sentences', flat=True)
        qs_apple = TbProcessedYoutube.objects.filter(brand='apple').values_list('sentences', flat=True)
        samsung_sentences = _flatten_sentences(qs_samsung)
        apple_sentences = _flatten_sentences(qs_apple)

        samsung_freq_ratio = get_keyword_percentage(samsung_sentences, sorted_keywords)
        apple_freq_ratio = get_keyword_percentage(apple_sentences, sorted_keywords)

        monthly_trends = {
            "samsung": get_keyword_trend_with_ratios(sorted_keywords, brand="samsung"),
            "apple": get_keyword_trend_with_ratios(sorted_keywords, brand="apple")
        }

        analysis_result.freq_ratios = {"samsung": samsung_freq_ratio, "apple": apple_freq_ratio}
        analysis_result.monthly_trends = monthly_trends
        analysis_result.save(update_fields=['freq_ratios', 'monthly_trends'])

        print("[DONE] Step 1 데이터 분석 저장 완료")

    except Exception as e:
        print(f"[ERROR] Step 1 데이터 분석 실패: {e}")

@shared_task
@timer 
def generate_summary_page_1_1(analysis_id):
    print("[TASK] summary_page_1_1 작업 시작")

    try:
        with transaction.atomic():
            analysis_result = TbAnalysisResults.objects.get(analysis_id=analysis_id)
            hobby_entry = analysis_result.hobby
            hobby = hobby_entry.hobby_name
            sorted_keywords = analysis_result.keywords or []
            freq = analysis_result.freq_ratios or {}
            apple_ratio = freq.get('apple', {})
            samsung_ratio = freq.get('samsung', {})

            summary = generate_summary_for_page_1_1(
                hobby,
                sorted_keywords,
                apple_ratio,
                samsung_ratio
            )

            summaries = {}
            if analysis_result.summaries:
                try:
                    summaries = json.loads(analysis_result.summaries)
                except (TypeError, json.JSONDecodeError):
                    pass
            summaries['summary_page_1_1'] = summary
            analysis_result.summaries = json.dumps(summaries, ensure_ascii=False)
            analysis_result.save(update_fields=['summaries'])

            print("[DONE] summary_page_1_1 저장 완료")

    except Exception as e:
        print(f"[ERROR] summary_page_1_1 Task 실패: {e}")

@shared_task
@timer 
def generate_summary_page_1_2(analysis_id):
    print("[TASK] summary_page_1_2 작업 시작")

    try:
        analysis_result = TbAnalysisResults.objects.get(analysis_id=analysis_id)
        hobby_entry = analysis_result.hobby
        hobby = hobby_entry.hobby_name
        sorted_keywords = analysis_result.keywords or []
        keyword_monthly_trend = analysis_result.monthly_trends or {}

        summary = generate_summary_for_page_1_2(
            hobby,
            sorted_keywords,
            keyword_monthly_trend
        )

        summaries = {}
        if analysis_result.summaries:
            try:
                summaries = json.loads(analysis_result.summaries)
            except (TypeError, json.JSONDecodeError):
                pass
        summaries['summary_page_1_2'] = summary
        analysis_result.summaries = json.dumps(summaries, ensure_ascii=False)
        analysis_result.save(update_fields=['summaries'])

        print("[DONE] summary_page_1_2 저장 완료")

    except Exception as e:
        print(f"[ERROR] summary_page_1_2 Task 실패: {e}")

def _build_step2_dataframe():
    """TbProcessedYoutube에서 sentence 단위 DataFrame 생성 (sentences 필드 한 줄 = 한 문장)"""
    rows = []
    for r in TbProcessedYoutube.objects.all().values(
        'sentences', 'brand', 'sentiment_label', 'sentiment_score', 'like_count', 'commented_at'
    ):
        text = r.get('sentences') or ''
        for line in (text if isinstance(text, str) else str(text)).split('\n'):
            s = line.strip()
            if not s:
                continue
            rows.append({
                'sentence': s,
                'brand': r['brand'],
                'sentiment_label': r['sentiment_label'],
                'sentiment_score': r['sentiment_score'],
                'like_count': r['like_count'],
                'comment_publish_date': r['commented_at'],
            })
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=['sentence', 'brand', 'sentiment_label', 'sentiment_score', 'like_count', 'comment_publish_date'])


@shared_task
@timer 
def run_analysis_step2_task(analysis_id):
    print("[TASK] Step 2 데이터 분석 시작")

    try:
        analysis_result = TbAnalysisResults.objects.get(analysis_id=analysis_id)
        hobby_entry = analysis_result.hobby
        hobby_name = hobby_entry.hobby_name
        sorted_keywords = analysis_result.keywords or []

        df = _build_step2_dataframe()

        # 감성 점수 계산
        samsung_sentiment_score = calc_keyword_sentiment_score(df, brand="samsung", keywords=sorted_keywords)
        apple_sentiment_score = calc_keyword_sentiment_score(df, brand="apple", keywords=sorted_keywords)

        # 긍/부정 비율 계산
        samsung_sentiment_ratio = calc_overall_sentiment_ratio(df, brand="samsung")
        apple_sentiment_ratio = calc_overall_sentiment_ratio(df, brand="apple")

        # 대표 문장 뽑기 → LLM 요약 (함수 내부에서 LLM 호출)
        top_comments = get_top_comments(df, sorted_keywords)
        sentiment_top_sentences = summarize_sentences_with_llm(top_comments)

        summaries = {}
        if analysis_result.summaries:
            try:
                summaries = json.loads(analysis_result.summaries)
            except (TypeError, json.JSONDecodeError):
                pass
        summaries['sentiment_samsung_score'] = samsung_sentiment_score
        summaries['sentiment_apple_score'] = apple_sentiment_score
        summaries['sentiment_samsung_ratio'] = samsung_sentiment_ratio
        summaries['sentiment_apple_ratio'] = apple_sentiment_ratio
        summaries['sentiment_top_sentences'] = sentiment_top_sentences
        analysis_result.summaries = json.dumps(summaries, ensure_ascii=False)
        analysis_result.save(update_fields=['summaries'])

        print("[DONE] Step 2 데이터 분석 저장 완료")

    except Exception as e:
        print(f"[ERROR] Step 2 데이터 분석 실패: {e}")

@shared_task
@timer 
def generate_summary_page_2_1(analysis_id):
    print("[TASK] summary_page_2_1 작업 시작")

    try:
        analysis_result = TbAnalysisResults.objects.get(analysis_id=analysis_id)
        hobby_entry = analysis_result.hobby
        hobby = hobby_entry.hobby_name
        sorted_keywords = analysis_result.keywords or []
        summaries = {}
        if analysis_result.summaries:
            try:
                summaries = json.loads(analysis_result.summaries)
            except (TypeError, json.JSONDecodeError):
                pass
        keyword_monthly_trend = analysis_result.monthly_trends or {}

        summary = generate_summary_for_page_2_1(
            hobby,
            sorted_keywords,
            summaries.get('sentiment_apple_score'),
            summaries.get('sentiment_samsung_score'),
            summaries.get('sentiment_apple_ratio'),
            summaries.get('sentiment_samsung_ratio'),
            keyword_monthly_trend
        )

        summaries['summary_page_2_1'] = summary
        analysis_result.summaries = json.dumps(summaries, ensure_ascii=False)
        analysis_result.save(update_fields=['summaries'])

        print("[DONE] summary_page_2_1 저장 완료")

    except Exception as e:
        print(f"[ERROR] summary_page_2_1 Task 실패: {e}")

@shared_task
@timer 
def generate_summary_page_2_2(analysis_id):
    print("[TASK] summary_page_2_2 작업 시작")

    try:
        analysis_result = TbAnalysisResults.objects.get(analysis_id=analysis_id)
        hobby_entry = analysis_result.hobby
        hobby = hobby_entry.hobby_name
        sorted_keywords = analysis_result.keywords or []
        summaries = {}
        if analysis_result.summaries:
            try:
                summaries = json.loads(analysis_result.summaries)
            except (TypeError, json.JSONDecodeError):
                pass
        sentiment_top_sentences = summaries.get('sentiment_top_sentences') or {}

        summary = generate_summary_for_page_2_2(
            hobby,
            sorted_keywords,
            sentiment_top_sentences
        )

        summaries['summary_page_2_2'] = summary
        analysis_result.summaries = json.dumps(summaries, ensure_ascii=False)
        analysis_result.save(update_fields=['summaries'])

        print("[DONE] summary_page_2_2 저장 완료")

    except Exception as e:
        print(f"[ERROR] summary_page_2_2 Task 실패: {e}")


@shared_task
@timer 
def run_analysis_step3_task(analysis_id):
    print("[TASK] Step 3 데이터 분석 시작")

    try:
        analysis_result = TbAnalysisResults.objects.get(analysis_id=analysis_id)
        hobby_entry = analysis_result.hobby
        hobby_name = hobby_entry.hobby_name
        sorted_keywords = analysis_result.keywords or []

        related_sentences_samsung = search_related_sentences(hobby_name, brand="samsung")
        related_sentences_apple = search_related_sentences(hobby_name, brand="apple")

        extracted_keywords_samsung = extract_keywords_with_llm(related_sentences_samsung, top_k=20)
        extracted_keywords_apple = extract_keywords_with_llm(related_sentences_apple, top_k=20)

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

        summaries = {}
        if analysis_result.summaries:
            try:
                summaries = json.loads(analysis_result.summaries)
            except (TypeError, json.JSONDecodeError):
                pass
        summaries['related_words_samsung'] = related_words_samsung
        summaries['related_words_apple'] = related_words_apple
        analysis_result.summaries = json.dumps(summaries, ensure_ascii=False)
        analysis_result.save(update_fields=['summaries'])

        print("[DONE] Step 3 데이터 분석 저장 완료")

    except Exception as e:
        print(f"[ERROR] Step 3 데이터 분석 실패: {e}")

@shared_task
@timer 
def generate_summary_page_3(analysis_id):
    print("[TASK] summary_page_3 작업 시작")

    try:
        analysis_result = TbAnalysisResults.objects.get(analysis_id=analysis_id)
        hobby_entry = analysis_result.hobby
        hobby = hobby_entry.hobby_name
        sorted_keywords = analysis_result.keywords or []
        summaries = {}
        if analysis_result.summaries:
            try:
                summaries = json.loads(analysis_result.summaries)
            except (TypeError, json.JSONDecodeError):
                pass
        related_words_apple = summaries.get('related_words_apple') or {}
        related_words_samsung = summaries.get('related_words_samsung') or {}

        summary = generate_summary_for_page_3(
            hobby,
            sorted_keywords,
            related_words_apple,
            related_words_samsung
        )

        summaries['summary_page_3'] = summary
        analysis_result.summaries = json.dumps(summaries, ensure_ascii=False)
        analysis_result.save(update_fields=['summaries'])

        print("[DONE] summary_page_3 저장 완료")

    except Exception as e:
        print(f"[ERROR] summary_page_3 Task 실패: {e}")

@shared_task
@timer 
def run_analysis_step4_task(analysis_id):
    try:
        analysis_result = TbAnalysisResults.objects.get(analysis_id=analysis_id)
        hobby_entry = analysis_result.hobby
        selected_keywords = analysis_result.keywords or []

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
