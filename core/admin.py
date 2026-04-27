from django.contrib import admin
from .models import Advertiser, Campaign, AdGroup, PerformanceReport, CSVUpload
import csv
from io import TextIOWrapper # binary file convert to text


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

    def save_model(self, request, obj, form, change): # This function will run when saved from the admin panel.
        super().save_model(request, obj, form, change) # At fist django will default save

        file = obj.file.name # take uploaded file
        csv_file = TextIOWrapper(obj.file.file, encoding='utf-8')  # file.file = actual binary file
        reader = csv.DictReader(csv_file) # It is converting each row into a dictionary.

        # for row in reader:
        #     print(row)   # read each row and print terminal

        # 🎉 Advertiser Upload
        if "advertiser" in file:
            for row in reader:
                Advertiser.objects.get_or_create(
                    # id=row['advertiser_id'],
                    name=row['name'] # existing obj return
                )


        # 🔵 Campaign Upload
        elif "campaign" in file:
            for row in reader:
                try:
                    advertiser = Advertiser.objects.get(name=row['advertiser_name'])

                    Campaign.objects.create(
                        # id=int(row['id']),
                        name=row['name'],
                        advertiser=advertiser,
                        start_date=row['start_date'],
                        end_date=row['end_date']
                    )

                except Advertiser.DoesNotExist:
                    print(f"❌ Advertiser not found for row {row}")

                except Exception as e:
                    print(f"❌ Error in row {row} → {e}")

        # ♥️ AdGroup Upload
        elif "adgroup" in file:
            for row in reader:
                adgroup_name = row.get('name') or row.get('adgroup_name')

                try:
                    campaign = Campaign.objects.get(name=row['campaign_name'])

                    AdGroup.objects.create(
                        name=adgroup_name,
                        campaign=campaign
                    )

                except Campaign.DoesNotExist:
                    print(f"❌ Campaign not found for adgroup {adgroup_name}")

                except Exception as e:
                    print(f"❌ Error in row {row} → {e}")



        # 💙 Performance Upload
        elif "performance" in file:
            inserted = 0
            failed = 0

            for row in reader:
                try:
                    adgroup = AdGroup.objects.get(name=row['adgroup_name'])

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
                    print(f"❌ Error in row {row} → {e}")

            print(f"✅ Inserted: {inserted}, ❌ Failed: {failed}")


