from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import csv
from io import TextIOWrapper
from .models import Advertiser, Campaign, AdGroup, PerformanceReport
from django.db.models import Sum, F, FloatField, ExpressionWrapper 
from django.db.models.functions import Cast
# F : Field reference. 
# ExpressionWrapper : omplex calculation wrap
# Cast : type convert (int → float)


class CSVIngestAPIView(APIView):
    def post(self, request):
        file = request.FILES.get('file')

        if not file:
            return Response({"error": "No file uploaded"}, status=400)

        file_name = file.name.lower()

        reader = csv.DictReader(TextIOWrapper(file, encoding='utf-8'))

        inserted = 0
        failed = 0
        errors = []

        for row in reader:
            try:

                # 🔵 Advertiser
                if "advertiser" in file_name:
                    Advertiser.objects.get_or_create(
                        name=row['name']
                    )

                # 🔵 Campaign
                elif "campaign" in file_name:
                    advertiser = Advertiser.objects.get(name=row['advertiser_name'])

                    Campaign.objects.create(
                        name=row['name'],
                        advertiser=advertiser,
                        start_date=row['start_date'],
                        end_date=row['end_date']
                    )

                # 🔵 AdGroup
                elif "adgroup" in file_name:
                    for row in reader:
                        try:
                            campaign = Campaign.objects.filter(name=row['campaign_name']).first()
                            if not campaign:
                                raise Exception("Campaign not found")

                            AdGroup.objects.create(
                                name=row['name'],
                                campaign=campaign
                            )
                            inserted += 1

                        except Exception as e:
                            failed += 1
                            errors.append({
                                "row": row,
                                "error": str(e)
                            })


                # 🔵 Performance
                elif "performance" in file_name:
                    adgroup = AdGroup.objects.filter(name=row['adgroup_name']).first()
                    if not adgroup:
                        raise Exception("AdGroup not found")

                    PerformanceReport.objects.create(
                        date=row['date'],
                        adgroup=adgroup,
                        clicks=int(row['clicks']),
                        impressions=int(row['impressions']),
                        cost=float(row['cost'])
                    )

                inserted += 1

            except Exception as e:
                failed += 1
                errors.append({
                    "row": row,
                    "error": str(e)
                })

        return Response({
            "inserted": inserted,
            "failed": failed,
            "errors": errors
        }, status=status.HTTP_200_OK)
    

class AnalyticsAPIView(APIView):

    def get(self, request):
        qs = PerformanceReport.objects.select_related(  # select_related : performance optimization, Avoid N + 1 query
            "adgroup__campaign__advertiser"
        )

        # 🔵 Filters
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        advertiser = request.GET.get("advertiser")
        campaign = request.GET.get("campaign")
        adgroup = request.GET.get("adgroup")

        if start_date and end_date:
            qs = qs.filter(date__range=[start_date, end_date]) # ?start_date=2024-05-01&end_date=2024-08-01

        if advertiser:
            qs = qs.filter(adgroup__campaign__advertiser__name=advertiser) # ?advertiser=Google_1|Meta_28

        if campaign:
            qs = qs.filter(adgroup__campaign__name=campaign) # ?campaign=Campaign_20 | Campaign_8

        if adgroup:
            qs = qs.filter(adgroup__name=adgroup) # ?adgroup=AdGroup_60

        # 🔵 group_by
        group_by = request.GET.get("group_by")  # advertiser/campaign/adgroup/date

        group_fields = []

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

        # 🔵 Aggregation
        qs = qs.values(*group_fields).annotate(
            total_clicks=Sum("clicks"),
            total_impressions=Sum("impressions"),
            total_cost=Sum("cost"),
        )

        # 🔵 CTR = clicks / impressions
        qs = qs.annotate(
            ctr=ExpressionWrapper(
                Cast(F("total_clicks"), FloatField()) /
                Cast(F("total_impressions"), FloatField()),
                output_field=FloatField()
            )
        )

        # 🔵 CPC = cost / clicks
        qs = qs.annotate(
            cpc=ExpressionWrapper(
                Cast(F("total_cost"), FloatField()) /
                Cast(F("total_clicks"), FloatField()),
                output_field=FloatField()
            )
        )

        return Response(qs)
