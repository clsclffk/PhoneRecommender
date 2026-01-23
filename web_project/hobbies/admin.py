from django.contrib import admin
from .models import HobbyKeywords, HobbyTrends

# Register your models here.
@admin.register(HobbyKeywords)
class HobbyKeywordsAdmin(admin.ModelAdmin):
    list_display = ('hobby_name', 'created_at', 'updated_at')
    search_fields = ('hobby_name',)
    list_filter = ('hobby_name',)

@admin.register(HobbyTrends)
class HobbyTrendsAdmin(admin.ModelAdmin):
    list_display = ('trends_id', 'get_hobby_name', 'gender', 'age_group', 'date', 'count')
    search_fields = ('hobby_id__hobby_name',)
    list_filter = ('gender', 'age_group', 'date')

    def get_hobby_name(self, obj):
        return obj.hobby_id.hobby_name  # FK를 따라가서 hobby_name을 가져옴
    get_hobby_name.short_description = 'Hobby Name'