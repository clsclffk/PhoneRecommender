from django.contrib import admin
from .models import Users

# Register your models here.
@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = (
        'nickname', 
        'get_hobby_name', 
        'gender', 
        'age_group', 
        'selected_keywords', 
        'created_at'
    )
    search_fields = ('nickname', 'hobby_id__hobby_name')
    list_filter = ('gender', 'age_group', 'created_at')

    def get_hobby_name(self, obj):
        return obj.hobby_id.hobby_name  # FK 따라가서 hobby_name 출력
    get_hobby_name.short_description = 'Hobby Name'