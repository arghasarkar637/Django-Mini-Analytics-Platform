from rest_framework import serializers
from .models import Advertiser, Campaign, AdGroup, PerformanceReport


class CSVUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.lower().endswith(".csv"):
            raise serializers.ValidationError("Only CSV files are allowed.")
        return value


class AdvertiserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advertiser
        fields = "__all__"


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = "__all__"


class AdGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdGroup
        fields = "__all__"


class PerformanceReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceReport
        fields = "__all__"