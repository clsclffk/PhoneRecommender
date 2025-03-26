from django.db import models
from hobbies.models import HobbyKeywords

# Create your models here.

class Users(models.Model):
    user_id = models.AutoField(primary_key=True)
    hobby_id = models.ForeignKey('hobbies.HobbyKeywords', models.PROTECT, db_column='hobby_id')
    nickname = models.CharField(max_length=50)  

    AGE_GROUP_CHOICES = [
        ('10s', '10대'), 
        ('20s', '20대'), 
        ('30s', '30대'),
        ('40s', '40대'), 
        ('50s', '50대'), 
        ('60s', '60대')
    ]
    age_group = models.CharField(max_length=10, choices=AGE_GROUP_CHOICES)

    GENDER_CHOICES = [
        ('M', '남성'), 
        ('F', '여성')
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)

    # 사용자가 선택한 기능 키워드
    selected_keywords = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True) 

    class Meta:
        managed = True
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def get_gender_display(self):
        return dict(self.GENDER_CHOICES).get(self.gender, self.gender)
