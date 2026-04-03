1.  Install the module from the Apps menu
2.  The module will automatically load all Colombian EDI reference data
    and create the necessary configuration fields

## Automatic Operation

Once installed, the module operates automatically:

- **Data Loading**: All Colombian EDI reference data is automatically
  loaded including payment methods, responsibility types, and tax types
- **Field Creation**: Required fields for EDI compliance are automatically
  added to relevant models
- **Configuration**: Colombian-specific settings are applied to companies
  and partners

## Manual Configuration

If you need to manually configure EDI settings:

1.  Go to **Invoicing > Configuration > Colombian Localization**
2.  Configure payment methods, responsibility types, and tax types
3.  Set up company and partner information with required Colombian fields

## Configuration

The module automatically provides:

- Colombian payment methods (DIAN approved)
- Responsibility types for tax purposes
- Tax types and classifications
- CIIU codes for economic activities
- UNSPSC codes for products and services
- UOM codes for units of measure
- Geographic data (states, cities, postal codes)


## Troubleshooting

If EDI data is not loading properly:

1.  Check that the module dependencies are installed
2.  Verify that Colombian localization is properly configured
3.  Review Odoo logs for any data loading errors
4.  Ensure all required fields are properly mapped
