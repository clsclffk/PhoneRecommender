from django.contrib import admin
from .models import PhoneRecommendations

# Register your models here.

@admin.register(PhoneRecommendations)
class PhoneRecommendationsAdmin(admin.ModelAdmin):
    list_display = ('get_hobby_name', 'selected_keywords', 'display_recommendation_phones', 'created_at')
    search_fields = ('hobby_id__hobby_name',)
    list_filter = ('hobby_id', )

    def get_hobby_name(self, obj):
        return obj.hobby_id.hobby_name  # FK를 따라가서 hobby_name 가져오기
    get_hobby_name.short_description = 'Hobby Name'  

    def display_recommendation_phones(self, obj):
        # recommendations에서 phone_name 리스트 추출
        return ', '.join([rec.get('phone_name', '-') for rec in obj.recommendations]) if obj.recommendations else '-'
    display_recommendation_phones.short_description = '추천 스마트폰'

