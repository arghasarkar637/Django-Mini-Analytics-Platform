from django.contrib import admin
from .models import Advertiser, Campaign, AdGroup, PerformanceReport, CSVUpload
import csv
from io import TextIOWrapper # binary file convert to text
from datetime import datetime


@admin.register(Advertiser)
class AdvertiserAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_at']
    search_fields = ['name']

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'advertiser', 'start_date', 'end_date']
    list_filter = ['advertiser', 'start_date']
    search_fields = ['name']

@admin.register(AdGroup)
class AdGroupAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'campaign']
    list_filter = ['campaign']
    search_fields = ['name']

@admin.register(PerformanceReport)
class PerformanceReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'adgroup', 'clicks', 'impressions', 'cost']
    list_filter = ['date', 'adgroup']
    search_fields = ['adgroup__name']


from django.contrib import admin
from django.db import transaction
from io import TextIOWrapper
import csv

from .models import CSVUpload, Advertiser, Campaign, AdGroup, PerformanceReport


@admin.register(CSVUpload)
class CSVUploadAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        # This function will run when saved from the admin panel.
        
        # At first Django will save the uploaded file normally.
        super().save_model(request, obj, form, change)

        # Take uploaded file name and convert to lowercase
        file_name = obj.file.name.lower()

        # obj.file.file = actual binary file
        # TextIOWrapper converts binary file → readable text file
        csv_file = TextIOWrapper(obj.file.file, encoding='utf-8')

        # Converts each CSV row into dictionary format
        reader = csv.DictReader(csv_file)

        inserted = 0
        failed = 0
        errors = []

        # If any error happens, all DB operations rollback together
        with transaction.atomic():

            # Advertiser Upload
            if "advertiser" in file_name:

                advertisers_to_create = []

                for row in reader:
                    try:
                        # Get advertiser name from CSV row
                        name = row.get("name")

                        # Validation check
                        if not name:
                            raise Exception("Name is required")

                        # Create Advertiser object and store in list
                        advertisers_to_create.append(
                            Advertiser(name=name)
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
            elif "campaign" in file_name:

                # Create advertiser lookup dictionary
                advertiser_map = {
                    a.name: a for a in Advertiser.objects.all()
                }

                campaigns_to_create = []

                for row in reader:
                    try:
                        # Find advertiser using advertiser_name
                        advertiser = advertiser_map.get(
                            row.get("advertiser_name")
                        )

                        if not advertiser:
                            raise Exception("Advertiser not found")

                        start_date = row.get("start_date")
                        end_date = row.get("end_date")

                        # Validation check
                        if start_date > end_date:
                            raise Exception(
                                "Start date cannot be after end date"
                            )

                        # Create Campaign object and store in list
                        campaigns_to_create.append(
                            Campaign(
                                name=row.get("name"),
                                advertiser=advertiser,
                                start_date=start_date,
                                end_date=end_date
                            )
                        )

                        inserted += 1

                    except Exception as e:
                        failed += 1

                        errors.append({
                            "row": row,
                            "error": str(e)
                        })

                # Insert all campaigns in one query
                Campaign.objects.bulk_create(
                    campaigns_to_create
                )

            # AdGroup Upload
            elif "adgroup" in file_name:

                # Create campaign lookup dictionary
                campaign_map = {
                    c.name: c for c in Campaign.objects.all()
                }

                adgroups_to_create = []

                for row in reader:
                    try:
                        # Find campaign using campaign_name
                        campaign = campaign_map.get(
                            row.get("campaign_name")
                        )

                        if not campaign:
                            raise Exception("Campaign not found")

                        # Create AdGroup object and store in list
                        adgroups_to_create.append(
                            AdGroup(
                                name=row.get("name"),
                                campaign=campaign
                            )
                        )

                        inserted += 1

                    except Exception as e:
                        failed += 1

                        errors.append({
                            "row": row,
                            "error": str(e)
                        })

                # Insert all adgroups in one query
                AdGroup.objects.bulk_create(
                    adgroups_to_create
                )

            # Performance Upload
            elif "performance" in file_name:
                adgroup_map = {a.name: a for a in AdGroup.objects.all()}
                performance_to_create = []

                for row in reader:
                    try:
                        adgroup = adgroup_map.get(row.get("adgroup_name"))
                        if not adgroup:
                            raise Exception("AdGroup not found")

                        perf_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
                        clicks = int(row["clicks"])
                        impressions = int(row["impressions"])
                        cost = float(row["cost"])

                        if clicks < 0:
                            raise Exception("Clicks cannot be negative")
                        if impressions < 0:
                            raise Exception("Impressions cannot be negative")
                        if cost < 0:
                            raise Exception("Cost cannot be negative")

                        campaign = adgroup.campaign
                        if not (campaign.start_date <= perf_date <= campaign.end_date):
                            raise Exception("Performance date must be within campaign date range")

                        performance_to_create.append(
                            PerformanceReport(
                                date=perf_date,
                                adgroup=adgroup,
                                clicks=clicks,
                                impressions=impressions,
                                cost=cost
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
                print("Invalid file type uploaded")

        # Print upload summary in terminal
        print("===== ADMIN BULK UPLOAD SUMMARY =====")
        print(f"Inserted: {inserted}")
        print(f"Failed: {failed}")
        print("Errors:", errors)