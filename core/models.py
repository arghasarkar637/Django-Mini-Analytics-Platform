from django.db import models
from django.core.exceptions import ValidationError

class Advertiser(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class Campaign(models.Model):
    name = models.CharField(max_length=255)
    advertiser = models.ForeignKey(Advertiser, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()

    def clean(self):
        if self.start_date > self.end_date:
            raise ValidationError("Start date cannot be after end date")
        
    def save(self, *args, **kwargs):
        self.full_clean()   # clean() call
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class AdGroup(models.Model):
    name = models.CharField(max_length=255)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
class PerformanceReport(models.Model):
    date = models.DateField()
    adgroup = models.ForeignKey(AdGroup, on_delete=models.CASCADE)
    clicks = models.IntegerField()
    impressions = models.IntegerField()
    cost = models.FloatField()

    def clean(self):
        # 1. non-negative check
        if self.clicks < 0:
            raise ValidationError("Clicks cannot be negative")

        if self.impressions < 0:
            raise ValidationError("Impressions cannot be negative")

        if self.cost < 0:
            raise ValidationError("Cost cannot be negative")

        # 2. campaign date range check
        campaign = self.adgroup.campaign
        if not (campaign.start_date <= self.date <= campaign.end_date):
            raise ValidationError("Performance date must be within campaign date range")
        

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.adgroup.name} - {self.date}"
    


class CSVUpload(models.Model):
    file = models.FileField(upload_to='csv_uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name