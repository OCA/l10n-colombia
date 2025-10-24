1.  Install the module from the Apps menu
2.  The module will automatically create a scheduled action for daily
    TRM updates

## Automatic Operation

Once installed, the module operates automatically:

- **Daily Updates**: The scheduled action runs daily to fetch the latest
  TRM rate
- **Automatic Rate Creation**: USD currency rates are automatically
  created/updated for all companies
- **Logging**: All operations are logged for monitoring and
  troubleshooting

## Manual TRM Update

If you need to manually update the TRM rate:

1.  Go to **Go to Invoicing > Configuration > Currency Rates Providers**
2.  Select specific provider "Superfinanciera Colombia"
3.  Find the action "Update Rates Now"

## Configuration

No additional configuration is required. The module uses the official
Superfinanciera web service endpoint and automatically handles:

- Date formatting
- SOAP request construction
- Response parsing
- Error handling

## Monitoring

Check the Odoo logs to monitor TRM updates:

- Successful updates will show: "TRM vigente en la fecha [date] es de:
  [rate] COP"
- Rate creation/updates will be logged with company and rate information
- Any errors will be logged with full exception details

## Troubleshooting

If TRM updates fail:

1.  Check internet connectivity
2.  Verify Superfinanciera service availability
3.  Review Odoo logs for specific error messages
4.  Ensure the scheduled action is active and properly configured
