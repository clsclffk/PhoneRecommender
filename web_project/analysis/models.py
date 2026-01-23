from django.db import models
from hobbies.models import HobbyKeywords

class TbAnalysisResults(models.Model):
    """분석 결과 저장 테이블"""
    analysis_id = models.AutoField(primary_key=True)
    hobby = models.ForeignKey(TbHobbies, on_delete=models.CASCADE, db_column='hobby_id')
    
    # 조회 기준 컬럼 (반정규화)
    age_group = models.CharField(max_length=10)
    gender = models.CharField(max_length=1)
    keywords = models.JSONField()  # ['카메라', '화질', '초점']
    
    # 분석 결과 데이터 (JSON)
    freq_ratios = models.JSONField(blank=True, null=True)  # 키워드 빈도 비율
    monthly_trends = models.JSONField(blank=True, null=True)  # 월별 트렌드
    summaries = models.TextField(blank=True, null=True)  # LLM 요약문
    related_words = models.CharField(max_length=500, blank=True, null=True)  # 연관어
    wordcloud_data = models.TextField(blank=True, null=True)  # 워드클라우드
    recommendations = models.TextField(blank=True, null=True)  # 추천 결과
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'tb_analysis_results'
        verbose_name = 'Analysis Result'
        verbose_name_plural = 'Analysis Results'
        
        # 인덱스
        indexes = [
            # 복합 인덱스: 조회 성능의 핵심
            models.Index(
                fields=['hobby', 'age_group', 'gender'],
                name='idx_analysis_lookup'
            ),
            # 최신 결과 조회용
            models.Index(
                fields=['-updated_at'],
                name='idx_analysis_recent'
            ),
        ]