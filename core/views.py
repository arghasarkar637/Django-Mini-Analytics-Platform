from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import csv
from io import TextIOWrapper
from .models import Advertiser, Campaign, AdGroup, PerformanceReport

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