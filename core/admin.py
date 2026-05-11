from django.contrib import admin
from .models import Advertiser, Campaign, AdGroup, PerformanceReport, CSVUpload
import csv
from io import TextIOWrapper  # binary file convert to text
from django.db import transaction

from .validation import (
    validate_advertiser_row,
    validate_campaign_row,
    validate_adgroup_row,
    validate_performance_row,
)


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
                        cleaned = validate_advertiser_row(row)

                        # Create Advertiser object and store in list
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
            elif "campaign" in file_name:

                # Create advertiser lookup dictionary
                advertiser_map = {
                    a.name: a for a in Advertiser.objects.all()
                }

                campaigns_to_create = []

                for row in reader:
                    try:
                        cleaned = validate_campaign_row(row, advertiser_map)

                        # Create Campaign object and store in list
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
                        cleaned = validate_adgroup_row(row, campaign_map)

                        # Create AdGroup object and store in list
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

                PerformanceReport.objects.bulk_create(
                    performance_to_create
                )

            else:
                print("Invalid file type uploaded")

        # Print upload summary in terminal
        print("===== ADMIN BULK UPLOAD SUMMARY =====")
        print(f"Inserted: {inserted}")
        print(f"Failed: {failed}")
        print("Errors:", errors)