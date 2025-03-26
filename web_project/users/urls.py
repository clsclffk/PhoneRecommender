from django.urls import path
from .views import UserInfoView, HobbySelectView, RecommendHobbyView, KeywordSelectView

urlpatterns = [
    path('user-info/', UserInfoView.as_view(), name='user-info'),
    path('hobby-select/', HobbySelectView.as_view(), name='hobby-select'), 
    path('recommend-hobby/', RecommendHobbyView.as_view(), name='recommend-hobby'),  
    path('keyword-select/', KeywordSelectView.as_view(), name='keyword-select'),
]