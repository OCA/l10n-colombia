## Business Need

In Colombia, every NIT (Número de Identificación Tributaria) issued by the DIAN includes a verification digit (dígito de verificación) computed using a weighted sum algorithm defined in Orden Administrativa 4 of 1989. This digit is required on invoices, tax filings, and legal documents. Odoo does not compute or display this digit natively.

## Approach

This module adds a `compute_verification_digit` function that implements the DIAN algorithm and extends `res.partner` with a computed field `l10n_co_verification_digit` that displays the check digit next to the identification number on the partner form, separated by a hyphen (e.g., `900123456 - 8`). The verification digit is only shown when the identification type is NIT.

## Useful Information

- **Depends on:** `l10n_latam_base`, `l10n_co` (Colombian localization)
- **Works well with:** `l10n_co_electronic_invoice` and any module that displays partner tax identification
- **Suggested setup:** recommended for any Colombian Odoo instance that needs to display or validate the NIT verification digit on partner records and printed documents
