from django.conf import settings
from django.utils import timezone
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

print(f"Time Zone: {settings.TIME_ZONE}")
print(f"Use TZ: {settings.USE_TZ}")

now_utc = timezone.now()
local_date = timezone.localdate()

print(f"UTC Now: {now_utc}")
print(f"Local Date (Brazil): {local_date}")

# Check if local date is correct relative to UTC
# Brazil is UTC-3 (or -2 in DST, though DST is currently off)
# If it's 23:00 UTC on day X, it should be 20:00 on day X in Brazil (same day)
# If it's 01:00 UTC on day Y, it should be 22:00 on day Y-1 in Brazil (previous day)

expected_offset = -3 # Standard BRT offset
server_hour_utc = now_utc.hour
local_day_matches_utc = now_utc.date() == local_date

print(f"\nVerification Logic:")
if server_hour_utc < 3:
    # It's early morning UTC, so in Brazil it should be late night previous day
    if local_date == now_utc.date():
        print("FAIL: Local date is same as UTC, but should be previous day (00:00-02:59 UTC is previous day in BRT)")
    else:
        print("SUCCESS: Local date is correctly behind UTC (late night previous day)")
else:
    # It's 03:00+ UTC, so in Brazil it's same day
    if local_date == now_utc.date():
        print("SUCCESS: Local date matches UTC date (as expected for this hour)")
    else:
        print(f"FAIL/WARNING: Local date {local_date} differs from UTC date {now_utc.date()} unexpectedly for hour {server_hour_utc} UTC")
