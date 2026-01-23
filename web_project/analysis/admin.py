from django.contrib import admin
from .models import AnalysisResults

# Register your models here.

@admin.register(AnalysisResults)
class AnalysisResultsAdmin(admin.ModelAdmin):
    list_display = ('analysis_id', 'get_hobby_name', 'selected_keywords', 'created_at', 'updated_at')
    search_fields = ('hobby__id__hobby_name',)
    list_filter = ('hobby_id',)

    def get_hobby_name(self, obj):
        return obj.hobby_id.hobby_name
    get_hobby_name.short_description = 'Hobby Name'

    def display_selected_keywords(self, obj):
        return ", ".join(obj.selected_keywords)
    display_selected_keywords.short_description = 'Selected Keywords'