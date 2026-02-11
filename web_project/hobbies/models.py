from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now

# Create your models here.
class TbHobbies(models.Model):
    """취미 마스터 테이블"""
    hobby_id = models.AutoField(primary_key=True)
    hobby_name = models.CharField(max_length=50, unique=True)

    class Meta:
        managed = True
        db_table = 'tb_hobbies'
        verbose_name = 'Hobby'
        verbose_name_plural = 'Hobbies'

class TbHobbyRequests(models.Model):
    """사용자별 취미 요청 기록"""
    request_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('users.TbUsers', on_delete=models.CASCADE, db_column='user_id')
    analysis_id = models.IntegerField()  # tb_analysis_results와 연결
    hobby = models.ForeignKey(TbHobbies, on_delete=models.CASCADE, db_column='hobby_id')
    keyword = models.CharField(max_length=100)  # 단일 키워드 (JSON 아님)
    status = models.CharField(max_length=20, default='pending')

    class Meta:
        managed = True
        db_table = 'tb_hobby_requests'
        verbose_name = 'Hobby Request'
        verbose_name_plural = 'Hobby Requests'