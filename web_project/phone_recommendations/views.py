from django.shortcuts import render
from django.views import View
from phone_recommendations.models import PhoneRecommendations
from hobbies.models import HobbyKeywords
from web_project.utils.rag_phone_recommend.pipeline import (
    search_phone_recommendations,
    generate_recommendation_text
)

# Create your views here.
