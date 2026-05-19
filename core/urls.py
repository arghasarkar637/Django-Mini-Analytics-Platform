from django.urls import path
from .views import *

urlpatterns = [
    path("ingest/", CSVIngestAPIView.as_view(), name="ingest"),
    path("analytics/", AnalyticsAPIView.as_view(), name="analytics"),

    path("advertisers/<int:pk>/", AdvertiserDetailAPIView.as_view(), name="advertiser-detail"),
    path("campaigns/<int:pk>/", CampaignDetailAPIView.as_view(), name="campaign-detail"),
    path("adgroups/<int:pk>/", AdGroupDetailAPIView.as_view(), name="adgroup-detail"),
    path("performance/<int:pk>/", PerformanceReportDetailAPIView.as_view(), name="performance-detail"),
]