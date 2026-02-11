from django.contrib import admin
from .models import TbHobbies, TbHobbyRequests

# Register your models here.
@admin.register(TbHobbies)
class TbHobbiesAdmin(admin.ModelAdmin):
    list_display = ('hobby_id', 'hobby_name')
    search_fields = ('hobby_name',)
    list_filter = ('hobby_name',)


@admin.register(TbHobbyRequests)
class TbHobbyRequestsAdmin(admin.ModelAdmin):
    list_display = ('request_id', 'get_hobby_name', 'user', 'analysis_id', 'keyword', 'status')
    search_fields = ('keyword', 'hobby__hobby_name')
    list_filter = ('status',)

    def get_hobby_name(self, obj):
        return obj.hobby.hobby_name if obj.hobby else '-'
    get_hobby_name.short_description = 'Hobby Name'
