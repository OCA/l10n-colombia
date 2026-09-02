## Business Need

In Colombia, every company must declare its CIIU economic activity codes (Clasificación Industrial Internacional Uniforme) as defined by the DANE and required by the DIAN for electronic invoicing and withholding tax calculations.

## Approach

This module adds an `l10n.co.economic.activity` model with CIIU codes and extends `res.partner` with fields for primary, secondary, and other economic activities. Data is pre-loaded with official CIIU codes used by the DIAN.

## Useful Information

- **Depends on:** `base`, `contacts`, `account`, `base_address_extended`
- **Works well with:** `l10n_co_withholding`, `l10n_co_electronic_invoice`
- **Suggested setup:** Required for Colombian electronic invoicing and withholding tax configuration
