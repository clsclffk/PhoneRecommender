from django.db import models

# Create your models here.
class TbcrawledDanawa(models.Model):
    scoring = models.TextField(blank=True, null=True)
    market = models.TextField(blank=True, null=True)
    purchasing_date = models.TextField(blank=True, null=True)
    review_title = models.TextField(blank=True, null=True)
    review_content = models.TextField(blank=True, null=True)
    item = models.TextField(blank=True, null=True)
    inserted_at = models.DateTimeField()
    class Meta:
        managed = False
        db_table = 'tbCrawled_Danawa'

class TbprocessedDanawa(models.Model):
    processed_id = models.AutoField(primary_key=True)
    brand = models.CharField(max_length=20, blank=True, null=True)  # 삼성 / 애플
    review_content = models.TextField(blank=True, null=True)        # 원본 리뷰
    clean_review = models.TextField(blank=True, null=True)          # 정제된 리뷰
    sentence = models.TextField(blank=True, null=True)              # 문장 분리된 단위
    noun = models.TextField(blank=True, null=True)                 # 명사 추출 결과
    sentiment_label = models.CharField(max_length=10, blank=True, null=True)  # 1(긍정)/0(부정)
    sentiment_score = models.FloatField(blank=True, null=True)      # 확률 점수
    scoring = models.TextField(blank=True, null=True)               # 평점 (예: "80점")

    class Meta:
        managed = True
        db_table = 'tbProcessed_Danawa'

class TbcrawledYoutube(models.Model):
    video_id = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    publish_date = models.DateField(blank=True, null=True)
    channel_name = models.CharField(max_length=255)
    comment = models.TextField()
    like_count = models.IntegerField(blank=True, null=True)
    comment_publish_date = models.DateField(blank=True, null=True)
    inserted_at = models.DateTimeField()
    class Meta:
        managed = False
        db_table = 'tbCrawled_Youtube'

class TbprocessedYoutube(models.Model):
    processed_id = models.AutoField(primary_key=True)
    video_id = models.CharField(max_length=255)
    comment = models.TextField()  # 원본 댓글
    sentence = models.TextField()  # 문장으로 분리된 부분
    like_count = models.IntegerField(blank=True, null=True)
    brand = models.CharField(max_length=50)  # 브랜드 분류 결과
    sentiment_label = models.CharField(max_length=10)  # 긍정/부정 등
    sentiment_score = models.FloatField(blank=True, null=True)  # 점수
    comment_publish_date = models.DateField(blank=True, null=True)

    class Meta:
        managed = True 
        db_table = 'tbProcessed_Youtube'
