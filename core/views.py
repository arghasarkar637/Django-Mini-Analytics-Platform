import csv
import json  # direct JSON payload handle 
from io import TextIOWrapper

from django.db import transaction
from django.db.models import Sum, F, FloatField, ExpressionWrapper
from django.db.models.functions import Cast
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Advertiser, Campaign, AdGroup, PerformanceReport
from .serializers import CSVUploadSerializer
from .validation import (
    validate_advertiser_row,
    validate_campaign_row,
    validate_adgroup_row,
    validate_performance_row,
)

from rest_framework.generics import RetrieveUpdateDestroyAPIView
from .serializers import (
    AdvertiserSerializer,
    CampaignSerializer,
    AdGroupSerializer,
    PerformanceReportSerializer
)

# F : Field reference.
# ExpressionWrapper : complex calculation wrap
# Cast : type convert (int → float)


class CSVIngestAPIView(APIView):

    # shared helper for final response
    def _build_response(self, inserted, failed, errors):
        return Response({
            "total_rows": inserted + failed,
            "inserted": inserted,
            "failed": failed,
            "errors": errors
        }, status=status.HTTP_200_OK)

    # NEW: shared processor for both CSV rows and JSON rows
    def _process_records(self, model_name, rows):
        inserted = 0
        failed = 0
        errors = []


        try:
            with transaction.atomic():  # If any error happens, all DB operations rollback together

                # Advertiser Upload
                if model_name == "advertiser":

                    advertisers_to_create = []

                    for row in rows:
                        try:
                            cleaned = validate_advertiser_row(row)

                            advertisers_to_create.append(
                                Advertiser(name=cleaned["name"])
                            )
                            inserted += 1

                        except Exception as e:
                            failed += 1
                            errors.append({
                                "row": row,
                                "error": str(e)
                            })

                    # Insert all advertisers in one query (fast)
                    Advertiser.objects.bulk_create(
                        advertisers_to_create,
                        ignore_conflicts=True  # skip duplicate unique values
                    )

                # Campaign Upload
                elif model_name == "campaign":

                    advertiser_map = {
                        adv.name: adv
                        for adv in Advertiser.objects.all()
                    }

                    campaigns_to_create = []

                    for row in rows:
                        try:
                            cleaned = validate_campaign_row(row, advertiser_map)

                            campaigns_to_create.append(
                                Campaign(
                                    name=cleaned["name"],
                                    advertiser=cleaned["advertiser"],
                                    start_date=cleaned["start_date"],
                                    end_date=cleaned["end_date"]
                                )
                            )

                            inserted += 1

                        except Exception as e:
                            failed += 1
                            errors.append({
                                "row": row,
                                "error": str(e)
                            })

                    Campaign.objects.bulk_create(campaigns_to_create)

                # AdGroup Upload
                elif model_name == "adgroup":

                    campaign_map = {
                        camp.name: camp
                        for camp in Campaign.objects.all()
                    }

                    adgroups_to_create = []

                    for row in rows:
                        try:
                            cleaned = validate_adgroup_row(row, campaign_map)

                            adgroups_to_create.append(
                                AdGroup(
                                    name=cleaned["name"],
                                    campaign=cleaned["campaign"]
                                )
                            )
                            inserted += 1

                        except Exception as e:
                            failed += 1
                            errors.append({
                                "row": row,
                                "error": str(e)
                            })

                    AdGroup.objects.bulk_create(adgroups_to_create)

                # Performance Upload
                elif model_name == "performance":

                    adgroup_map = {
                        adg.name: adg
                        for adg in AdGroup.objects.all()
                    }

                    performance_to_create = []

                    for row in rows:
                        try:
                            cleaned = validate_performance_row(row, adgroup_map)

                            performance_to_create.append(
                                PerformanceReport(
                                    date=cleaned["date"],
                                    adgroup=cleaned["adgroup"],
                                    clicks=cleaned["clicks"],
                                    impressions=cleaned["impressions"],
                                    cost=cleaned["cost"]
                                )
                            )

                            inserted += 1

                        except Exception as e:
                            failed += 1
                            errors.append({
                                "row": row,
                                "error": str(e)
                            })

                    PerformanceReport.objects.bulk_create(performance_to_create)

                else:
                    return Response(
                        {"error": "Invalid model type"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return self._build_response(inserted, failed, errors)

    # NEW: CSV path
    def _handle_csv_upload(self, file):
        file_name = file.name.lower()

        reader = csv.DictReader(
            TextIOWrapper(file, encoding='utf-8')
        )

        # Convert DictReader to list so we can reuse the same processor
        rows = list(reader)

        if "advertiser" in file_name:
            return self._process_records("advertiser", rows)

        elif "campaign" in file_name:
            return self._process_records("campaign", rows)

        elif "adgroup" in file_name:
            return self._process_records("adgroup", rows)

        elif "performance" in file_name:
            return self._process_records("performance", rows)

        return Response(
            {"error": "Invalid file type"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # NEW: direct JSON path
    def _handle_json_upload(self, request):
        model_name = request.data.get("model")
        payload = request.data.get("data")

        if not model_name or payload is None:
            return Response(
                {
                    "error": "Send either a CSV file or JSON with model and data"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # If data comes as string from form-data / Postman, parse it
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                return Response(
                    {"error": "data must be valid JSON"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Allow single object or list of objects
        if isinstance(payload, dict):
            rows = [payload]
        elif isinstance(payload, list):
            rows = payload
        else:
            return Response(
                {"error": "data must be an object or a list of objects"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return self._process_records(model_name.lower(), rows)

    def post(self, request):
        # CSV file path
        file = request.FILES.get('file')

        if file:
            serializer = CSVUploadSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

            return self._handle_csv_upload(serializer.validated_data["file"])

        return self._handle_json_upload(request)


class AnalyticsAPIView(APIView):

    def get(self, request):
        qs = PerformanceReport.objects.select_related(  # select_related : performance optimization, Avoid N + 1 query
            "adgroup__campaign__advertiser"
        )

        #  Filters
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        advertiser = request.GET.get("advertiser")
        campaign = request.GET.get("campaign")
        adgroup = request.GET.get("adgroup")

        if start_date and end_date:
            qs = qs.filter(date__range=[start_date, end_date])  # ?start_date=2024-05-01&end_date=2024-08-01

        if advertiser:
            qs = qs.filter(adgroup__campaign__advertiser__name=advertiser)  # ?advertiser=Google_1|Meta_28

        if campaign:
            qs = qs.filter(adgroup__campaign__name=campaign)  # ?campaign=Campaign_20 | Campaign_8

        if adgroup:
            qs = qs.filter(adgroup__name=adgroup)  # ?adgroup=AdGroup_60

        #  group_by
        group_by = request.GET.get("group_by")  # advertiser/campaign/adgroup/date

        group_fields = []  # Group by : It controls how data is grouped and aggregated.

        if group_by == "advertiser":
            group_fields = ["adgroup__campaign__advertiser__name"]

        elif group_by == "campaign":
            group_fields = ["adgroup__campaign__name"]

        elif group_by == "adgroup":
            group_fields = ["adgroup__name"]

        elif group_by == "date":
            group_fields = ["date"]

        else:
            # default → overall
            group_fields = []

        #  Aggregation. Annotate : Adding an extra calculated field to each row/group
        qs = qs.values(*group_fields).annotate(  # aggregation / calculation
            total_clicks=Sum("clicks"),
            total_impressions=Sum("impressions"),
            total_cost=Sum("cost"),
        )

        # CTR = clicks / impressions
        qs = qs.annotate(
            ctr=ExpressionWrapper(
                Cast(F("total_clicks"), FloatField()) /
                Cast(F("total_impressions"), FloatField()),
                output_field=FloatField()
            )
        )

        #  CPC = cost / clicks
        qs = qs.annotate(
            cpc=ExpressionWrapper(
                Cast(F("total_cost"), FloatField()) /
                Cast(F("total_clicks"), FloatField()),
                output_field=FloatField()
            )
        )

        return Response(qs)
    

class AdvertiserDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Advertiser.objects.all()
    serializer_class = AdvertiserSerializer


class CampaignDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer


class AdGroupDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = AdGroup.objects.all()
    serializer_class = AdGroupSerializer


class PerformanceReportDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = PerformanceReport.objects.all()
    serializer_class = PerformanceReportSerializer


# {
#   "model": "performance",
#   "data": {
#     "date": "2024-01-10",
#     "adgroup_name": "AdGroup A",
#     "clicks": 100,
#     "impressions": 5000,
#     "cost": 250.5
#   }
# }