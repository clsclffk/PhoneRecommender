from django.apps import AppConfig


class AnalysisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analysis'

    def ready(self):
        import dash_apps.keyword_bar_chart
        import dash_apps.association_network_graph
        import dash_apps.sentiment_bar_chart
        import dash_apps.hobby_trends_chart
        import dash_apps.keyword_trend_chart
        import dash_apps.danawa_wordcloud