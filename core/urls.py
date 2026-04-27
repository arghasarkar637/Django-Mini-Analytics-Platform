from django.urls import path
from .views import CSVIngestAPIView

urlpatterns = [
    path('ingest/', CSVIngestAPIView.as_view()),
]