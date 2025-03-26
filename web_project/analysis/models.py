from django.db import models
from hobbies.models import HobbyKeywords

class AnalysisResults(models.Model):
    analysis_id = models.AutoField(primary_key=True)

    # 취미와 키워드 조합 기준
    hobby_id = models.ForeignKey(
        HobbyKeywords,
        on_delete=models.CASCADE,
        db_column='hobby_id'
    )
    selected_keywords = models.JSONField()  # 사용자가 선택한 기능 키워드 리스트

    # 키워드 빈도 비율 (브랜드 기준)
    freq_ratio_samsung = models.JSONField(null=True, blank=True)  # 삼성 기준 키워드 비율
    freq_ratio_apple = models.JSONField(null=True, blank=True)    # 애플 기준 키워드 비율

    # 관련 단어 네트워크 (브랜드 기준)
    related_words_samsung = models.JSONField(null=True, blank=True)  # 삼성 관련 단어 네트워크
    related_words_apple = models.JSONField(null=True, blank=True)    # 애플 관련 단어 네트워크

    # 키워드별 감성 점수 (긍/부정 비율)
    sentiment_samsung_score = models.JSONField(null=True, blank=True)  # 삼성 키워드별 감성 점수
    sentiment_apple_score = models.JSONField(null=True, blank=True)    # 애플 키워드별 감성 점수

    # 브랜드별 전체 긍/부정 댓글 비율
    sentiment_samsung_ratio = models.JSONField(null=True, blank=True)  # 삼성 긍/부정 비율
    sentiment_apple_ratio = models.JSONField(null=True, blank=True)    # 애플 긍/부정 비율

    # 브랜드별 대표 문장 (긍정/부정)
    sentiment_top_sentences = models.JSONField(default=dict, blank=True, null=True)  # 브랜드별 키워드별 긍정/부정 대표 문장

    # 키워드별 월별 언급량 및 감성 비율
    keyword_monthly_trend = models.JSONField(default=dict, blank=True, null=True)  # 월별 트렌드 정보

    # LLM이 생성한 분석 요약
    # 페이지 1 요약 → 2개로 분리
    summary_page_1_1 = models.TextField(blank=True, null=True)  # 키워드 빈도
    summary_page_1_2 = models.TextField(blank=True, null=True)  # 월별 트렌드

    # 페이지 2 요약
    summary_page_2_1 = models.TextField(blank=True, null=True)  # 감성 분석
    summary_page_2_2 = models.TextField(blank=True, null=True) # 대표 문장

    # 페이지 3 요약
    summary_page_3 = models.TextField(blank=True, null=True)

    # 생성/수정 시간
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'analysis_results'
        # unique_together 고려 사항
        unique_together = (('hobby_id', 'selected_keywords'),)
        verbose_name = 'Analysis result'
        verbose_name_plural = 'Analysis results'

    def __str__(self):
        return f"Analysis for Hobby {self.hobby_id.hobby_name} | Keywords {self.selected_keywords}"
