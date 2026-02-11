from django.db import models
from hobbies.models import TbHobbies

# Create your models here.

class PhoneRecommendations(models.Model):
    recommendation_id = models.AutoField(primary_key=True)
    hobby_id = models.ForeignKey(TbHobbies, on_delete=models.CASCADE, db_column='hobby_id')
    selected_keywords = models.JSONField(default=list)
    
    # 후보 + 이유를 포함한 추천 결과 전체
    recommendations = models.JSONField()  

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'phone_recommendations'
        verbose_name = 'Phone recommendation'
        verbose_name_plural = 'Phone recommendations'

    def __str__(self):
        return f"{self.hobby_id.hobby_name} 추천 ({', '.join(self.selected_keywords)})"
