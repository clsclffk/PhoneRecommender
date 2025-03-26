from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now

# Create your models here.
class HobbyKeywords(models.Model):
    hobby_id = models.AutoField(primary_key=True)
    hobby_name = models.CharField(max_length=50, unique=True)
    keyword_list = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = True
        db_table = 'hobby_keywords'
        verbose_name = 'Hobby Keyword'
        verbose_name_plural = 'Hobby Keywords'

    def __str__(self):
        return f"{self.hobby_name}"
   
class HobbyTrends(models.Model):
    trends_id = models.AutoField(primary_key=True)
    hobby_id = models.ForeignKey(HobbyKeywords, on_delete=models.CASCADE, db_column='hobby_id') 
    gender = models.CharField(max_length=1, choices=[('M', '남성'), ('F', '여성')])
    age_group = models.CharField(max_length=10, choices=[
        ('10s', '10대'), ('20s', '20대'),
        ('30s', '30대'), ('40s', '40대'),
        ('50s', '50대'), ('60s', '60대')
    ])
    selected_keywords = models.JSONField(default=list)
    count = models.IntegerField(default=0)
    date = models.DateField(auto_now_add=True)  

    class Meta:
        managed = True
        db_table = 'hobby_trends'
        # unique_together = (('hobby_id', 'gender', 'age_group', 'date'),)
        verbose_name = 'Hobby Trend'
        verbose_name_plural = 'Hobby Trends'
        
    def __str__(self):
        return f"{self.hobby_id.hobby_name} ({self.gender}, {self.age_group}): {self.count}"


