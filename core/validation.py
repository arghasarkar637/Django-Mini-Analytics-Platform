from datetime import datetime
from django.core.exceptions import ValidationError


def validate_advertiser_row(row):
    name = row.get("name")
    if not name or not str(name).strip():
        raise ValidationError("Name is required")

    return {"name": str(name).strip()}


def validate_campaign_row(row, advertiser_map):
    name = row.get("name")
    advertiser_name = row.get("advertiser_name")
    start_date = row.get("start_date")
    end_date = row.get("end_date")

    if not name or not str(name).strip():
        raise ValidationError("Campaign name is required")

    if not advertiser_name or not str(advertiser_name).strip():
        raise ValidationError("Advertiser name is required")

    advertiser = advertiser_map.get(str(advertiser_name).strip())
    if not advertiser:
        raise ValidationError("Advertiser not found")

    if not start_date:
        raise ValidationError("Start date is required")

    if not end_date:
        raise ValidationError("End date is required")

    try:
        start_date = datetime.strptime(str(start_date).strip(), "%Y-%m-%d").date()
        end_date = datetime.strptime(str(end_date).strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError("Start date and end date must be in YYYY-MM-DD format")

    if start_date > end_date:
        raise ValidationError("Start date cannot be after end date")

    return {
        "name": str(name).strip(),
        "advertiser": advertiser,
        "start_date": start_date,
        "end_date": end_date,
    }


def validate_adgroup_row(row, campaign_map):
    name = row.get("name")
    campaign_name = row.get("campaign_name")

    if not name or not str(name).strip():
        raise ValidationError("AdGroup name is required")

    if not campaign_name or not str(campaign_name).strip():
        raise ValidationError("Campaign name is required")

    campaign = campaign_map.get(str(campaign_name).strip())
    if not campaign:
        raise ValidationError("Campaign not found")

    return {
        "name": str(name).strip(),
        "campaign": campaign,
    }


def validate_performance_row(row, adgroup_map):
    adgroup_name = row.get("adgroup_name")
    date_value = row.get("date")
    clicks = row.get("clicks")
    impressions = row.get("impressions")
    cost = row.get("cost")

    if not adgroup_name or not str(adgroup_name).strip():
        raise ValidationError("AdGroup name is required")

    adgroup = adgroup_map.get(str(adgroup_name).strip())
    if not adgroup:
        raise ValidationError("AdGroup not found")

    if not date_value:
        raise ValidationError("Date is required")

    try:
        perf_date = datetime.strptime(str(date_value).strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError("Date must be in YYYY-MM-DD format")

    try:
        clicks = int(clicks)
    except (TypeError, ValueError):
        raise ValidationError("Clicks must be an integer")

    try:
        impressions = int(impressions)
    except (TypeError, ValueError):
        raise ValidationError("Impressions must be an integer")

    try:
        cost = float(cost)
    except (TypeError, ValueError):
        raise ValidationError("Cost must be a number")

    if clicks < 0:
        raise ValidationError("Clicks cannot be negative")

    if impressions < 0:
        raise ValidationError("Impressions cannot be negative")

    if cost < 0:
        raise ValidationError("Cost cannot be negative")

    campaign = adgroup.campaign
    if not (campaign.start_date <= perf_date <= campaign.end_date):
        raise ValidationError("Performance date must be within campaign date range")

    return {
        "date": perf_date,
        "adgroup": adgroup,
        "clicks": clicks,
        "impressions": impressions,
        "cost": cost,
    }