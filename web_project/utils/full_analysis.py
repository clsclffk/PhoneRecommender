from utils.full_analysis_function import get_keyword_percentage, calc_keyword_sentiment_score, calc_overall_sentiment_ratio, get_keyword_trend_with_ratios, get_top_comments
from crawled_data.models import TbProcessedYoutube
from analysis.models import TbAnalysisResults
from utils.llm_api import summarize_sentences_with_llm
from utils.rag_analysis.pipeline import extract_keywords_with_llm, search_related_sentences
import pandas as pd
import time

def run_analysis_step1(hobby_entry, sorted_selected_keywords):
    sorted_selected_keywords = sorted(sorted_selected_keywords)

    print("[STEP 1] 키워드 빈도 + 트렌드 분석 시작")

    # 데이터 로드: sentences 필드를 문장 리스트로 펼침
    def _flatten(queryset):
        out = []
        for text in queryset:
            if not text:
                continue
            for line in (text if isinstance(text, str) else str(text)).split('\n'):
                s = line.strip()
                if s:
                    out.append(s)
        return out
    qs_s = TbProcessedYoutube.objects.filter(brand='samsung').values_list('sentences', flat=True)
    qs_a = TbProcessedYoutube.objects.filter(brand='apple').values_list('sentences', flat=True)
    samsung_sentences = _flatten(qs_s)
    apple_sentences = _flatten(qs_a)

    # 빈도 비율 계산
    samsung_freq_ratio = get_keyword_percentage(samsung_sentences, sorted_selected_keywords)
    apple_freq_ratio = get_keyword_percentage(apple_sentences, sorted_selected_keywords)

    # 월별 트렌드
    keyword_monthly_trend = {
        "samsung": get_keyword_trend_with_ratios(sorted_selected_keywords, brand="samsung"),
        "apple": get_keyword_trend_with_ratios(sorted_selected_keywords, brand="apple")
    }

    TbAnalysisResults.objects.create(
        hobby=hobby_entry,
        keywords=sorted_selected_keywords,
        age_group='20s',
        gender='M',
        freq_ratios={'samsung': samsung_freq_ratio, 'apple': apple_freq_ratio},
        monthly_trends=keyword_monthly_trend
    )

    print("[STEP 1] 저장 완료")

def run_analysis_step2(hobby_entry, sorted_selected_keywords):
    sorted_selected_keywords = sorted(sorted_selected_keywords)

    print("[STEP 2] 감성 분석 + 대표 문장 요약 시작")

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
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=['sentence', 'brand', 'sentiment_label', 'sentiment_score', 'like_count', 'comment_publish_date'])

    # 감성 점수, 비율 계산
    samsung_sentiment_score = calc_keyword_sentiment_score(df=df, brand="samsung", keywords=sorted_selected_keywords)
    apple_sentiment_score = calc_keyword_sentiment_score(df=df, brand="apple", keywords=sorted_selected_keywords)

    samsung_sentiment_ratio = calc_overall_sentiment_ratio(df, brand="samsung")
    apple_sentiment_ratio = calc_overall_sentiment_ratio(df, brand="apple")

    # 대표 문장 + LLM 요약
    top_comments = get_top_comments(df, sorted_selected_keywords)
    sentiment_top_sentences = summarize_sentences_with_llm(top_comments)

    analysis_result = TbAnalysisResults.objects.filter(
        hobby=hobby_entry,
        keywords=sorted_selected_keywords
    ).order_by('-updated_at').first()

    if analysis_result:
        import json
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

    analysis_result = TbAnalysisResults.objects.filter(
        hobby=hobby_entry,
        keywords=sorted_selected_keywords
    ).order_by('-updated_at').first()

    if analysis_result:
        import json
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

    print("[STEP 3] 저장 완료")
