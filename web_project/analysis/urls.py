from django.urls import path
from .views import (
    AnalysisReportStep1View,
    AnalysisReportStep2View,
    AnalysisReportStep3View,
    AnalysisReportStep4View,
    StartAnalysisView
)

urlpatterns = [
    path('report/step1/', AnalysisReportStep1View.as_view(), name='analysis-step1'),
    path('report/step2/', AnalysisReportStep2View.as_view(), name='analysis-step2'),
    path('report/step3/', AnalysisReportStep3View.as_view(), name='analysis-step3'),
    path('report/step4/', AnalysisReportStep4View.as_view(), name='analysis-step4'),
    path('start-analysis/', StartAnalysisView.as_view(), name='start-analysis'), 
]
