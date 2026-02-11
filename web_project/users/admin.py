from django.contrib import admin
from .models import TbUsers

# Register your models here.
@admin.register(TbUsers)
class TbUsersAdmin(admin.ModelAdmin):
    list_display = ('nickname', 'gender', 'age_group', 'created_at')
    search_fields = ('nickname',)
    list_filter = ('gender', 'age_group', 'created_at')