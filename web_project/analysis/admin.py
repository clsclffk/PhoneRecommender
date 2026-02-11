from django.contrib import admin
from .models import TbAnalysisResults

# Register your models here.

@admin.register(TbAnalysisResults)
class TbAnalysisResultsAdmin(admin.ModelAdmin):
    list_display = ('analysis_id', 'get_hobby_name', 'display_keywords', 'updated_at')
    search_fields = ('hobby__hobby_name',)
    list_filter = ('hobby',)

    def get_hobby_name(self, obj):
        return obj.hobby.hobby_name if obj.hobby else '-'
    get_hobby_name.short_description = 'Hobby Name'

    def display_keywords(self, obj):
        return ", ".join(obj.keywords) if obj.keywords else '-'
    display_keywords.short_description = 'Keywords'