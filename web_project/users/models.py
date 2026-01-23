from django.db import models
from hobbies.models import HobbyKeywords

# Create your models here.

class TbUsers(models.Model):
    """사용자 정보"""
    user_id = models.AutoField(primary_key=True)
    nickname = models.CharField(max_length=50)
    
    AGE_GROUP_CHOICES = [
        ('10s', '10대'), ('20s', '20대'), ('30s', '30대'),
        ('40s', '40대'), ('50s', '50대'), ('60s', '60대')
    ]
    age_group = models.CharField(max_length=10, choices=AGE_GROUP_CHOICES)
    
    GENDER_CHOICES = [('M', '남성'), ('F', '여성')]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'tb_users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'