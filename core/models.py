from django.db import models


class Advertiser(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name


class Campaign(models.Model):
    name = models.CharField(max_length=255)
    advertiser = models.ForeignKey(Advertiser, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['advertiser']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
        ]

    def __str__(self):
        return self.name


class AdGroup(models.Model):
    name = models.CharField(max_length=255)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['campaign']),
        ]

    def __str__(self):
        return self.name


class PerformanceReport(models.Model):
    date = models.DateField()
    adgroup = models.ForeignKey(AdGroup, on_delete=models.CASCADE)
    clicks = models.IntegerField()
    impressions = models.IntegerField()
    cost = models.FloatField()

    class Meta:
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['adgroup']),
        ]

    def __str__(self):
        return f"{self.adgroup.name} - {self.date}"


class CSVUpload(models.Model):
    file = models.FileField(upload_to='csv_uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name