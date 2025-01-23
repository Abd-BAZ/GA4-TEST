from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, RunReportRequest
from google.oauth2 import service_account

# Path to your credentials JSON file
credentials_path = "credentials/ga-4-website-448507-3efe2dc5a106.json"

# Authenticate
credentials = service_account.Credentials.from_service_account_file(credentials_path)
client = BetaAnalyticsDataClient(credentials=credentials)

property_id = "473956527"

# Sample request to fetch active users
request = RunReportRequest(
    property=f"properties/{property_id}",
    date_ranges=[DateRange(start_date="7daysAgo", end_date="yesterday")],
    metrics=[Metric(name="activeUsers")]
)

response = client.run_report(request)

# Print the response to verify data
print(response)
