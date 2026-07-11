## Business Need

In Colombia, partners (companies and individuals) are identified by their NIT
(Número de Identificación Tributaria) or Cédula. Odoo's standard VAT validation
does not include a Colombian validator, so saving a partner with `country_id`
set to Colombia raises a `ValidationError` — even when the entered number is
perfectly valid locally. This blocks normal data entry workflows for any
Colombian company using Odoo.

## Approach

This module adds a `check_vat_co` method to `res.partner`, which is the exact
hook Odoo's `simple_vat_check` looks for dynamically. It strips non-numeric
characters (dots, hyphens, spaces) and accepts any identifier between 3 and 11
digits, covering both NIT (up to 10 digits + check digit) and Cédula formats.
No changes to existing views or workflows are required — the validator is picked
up automatically by Odoo's constraint engine.

## Useful Information

- **Depends on:** `base`, `account` (for the VAT constraint logic in
  `res.partner`)
- **Works well with:** `l10n_co` (Colombian chart of accounts) and any module
  that creates or imports partners with Colombian fiscal data
- **Suggested setup:** recommended for any Odoo instance where the primary
  operating country is Colombia, or in multicompany setups that include at least
  one Colombian legal entity