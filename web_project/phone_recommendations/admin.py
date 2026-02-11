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
        rec = obj.recommendations
        if isinstance(rec, dict) and 'recommendations' in rec:
            text = rec.get('recommendations', '') or ''
            return (text[:80] + '...') if len(text) > 80 else text
        if isinstance(rec, list):
            return ', '.join([r.get('phone_name', '-') for r in rec]) if rec else '-'
        return '-'
    display_recommendation_phones.short_description = '추천 스마트폰'

