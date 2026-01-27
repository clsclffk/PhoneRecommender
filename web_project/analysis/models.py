from django.db import models
import hashlib


class TbAnalysisResults(models.Model):
    analysis_id = models.AutoField(primary_key=True)
    hobby = models.ForeignKey('hobbies.TbHobbies', on_delete=models.CASCADE)
    
    # 반정규화 컬럼
    age_group = models.CharField(max_length=10)
    gender = models.CharField(max_length=1)
    
    # 키워드
    keywords = models.JSONField()  # 원본
    keywords_hash = models.CharField(max_length=64, db_index=True)  # 해시
    
    # 분석 결과
    freq_ratios = models.JSONField(blank=True, null=True)
    monthly_trends = models.JSONField(blank=True, null=True)
    summaries = models.TextField(blank=True, null=True)
    related_words = models.CharField(max_length=500, blank=True, null=True)
    wordcloud_data = models.TextField(blank=True, null=True)
    recommendations = models.TextField(blank=True, null=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tb_analysis_results'
        indexes = [
            models.Index(
                fields=['keywords_hash', 'hobby', 'age_group', 'gender'],
                name='idx_analysis_full'
            ),
        ]
    
    def save(self, *args, **kwargs):
        if isinstance(self.keywords, list):
            sorted_kw = sorted(self.keywords)
            kw_str = '|'.join(sorted_kw)
            self.keywords_hash = hashlib.sha256(kw_str.encode()).hexdigest()
        super().save(*args, **kwargs)