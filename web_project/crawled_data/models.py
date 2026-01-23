from django.db import models

# Create your models here.
class TbRawDanawa(models.Model):
    """다나와 원본 데이터"""
    id = models.AutoField(primary_key=True)
    item_name = models.CharField(max_length=200)
    content = models.TextField()
    rating = models.IntegerField()
    purchased_at = models.DateTimeField()
    collected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'tb_raw_danawa'
        verbose_name = 'Raw Danawa Data'
        verbose_name_plural = 'Raw Danawa Data'

class TbProcessedDanawa(models.Model):
    """다나와 가공 데이터"""
    id = models.AutoField(primary_key=True)
    brand_id = models.IntegerField()  # 1: 삼성, 2: 애플
    cleaned_content = models.TextField()
    nouns = models.CharField(max_length=500, blank=True, null=True)
    sentiment_label = models.CharField(max_length=10)  # positive/negative
    sentiment_score = models.FloatField()
    rating = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'tb_processed_danawa'
        verbose_name = 'Processed Danawa Data'
        verbose_name_plural = 'Processed Danawa Data'

class TbRawYoutube(models.Model):
    """유튜브 원본 데이터"""
    id = models.AutoField(primary_key=True)
    video_id = models.CharField(max_length=255)
    content = models.TextField()
    like_count = models.IntegerField(default=0)
    commented_at = models.DateTimeField()
    collected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'tb_raw_youtube'
        verbose_name = 'Raw Youtube Data'
        verbose_name_plural = 'Raw Youtube Data'

class TbProcessedYoutube(models.Model):
    """유튜브 가공 데이터"""
    id = models.AutoField(primary_key=True)
    brand = models.CharField(max_length=20)  # samsung/apple
    sentences = models.TextField()  # 문장 분리된 텍스트
    sentiment_label = models.CharField(max_length=10)  # positive/negative
    sentiment_score = models.FloatField()
    like_count = models.IntegerField(default=0)
    commented_at = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'tb_processed_youtube'
        verbose_name = 'Processed Youtube Data'
        verbose_name_plural = 'Processed Youtube Data'
