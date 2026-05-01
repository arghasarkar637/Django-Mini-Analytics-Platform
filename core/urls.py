from django.urls import path
from .views import CSVIngestAPIView, AnalyticsAPIView

urlpatterns = [
    path('ingest/', CSVIngestAPIView.as_view()),
    path("analytics/", AnalyticsAPIView.as_view()),

]