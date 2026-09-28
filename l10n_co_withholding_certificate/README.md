# Colombia - Withholding Certificates

This module generates Colombian withholding certificates from posted accounting data.

## Scope

It depends on `l10n_co_withholding` for Colombian withholding configuration and supports:

- ReteFuente
- ReteIVA
- ReteICA

The source of truth is posted `account.move.line` data. Taxes are classified first by `l10n_co_withholding_type`, with an accounting-family fallback for Colombian account families 2365, 2367, and 2368.

## Usage

Open the withholding certificate wizard from Accounting > Reporting. Select the company, certificate type, period, and optional commercial partners. The wizard calls the certificate engine and can render a PDF with one certificate page per commercial partner.

Supported periods are annual, bimonthly, and custom ranges according to the certificate type. Company filters, commercial-partner consolidation, posted entries, and invoice/credit-note signs are handled by the existing engine.

## Limitations

The current version does not provide XLSX export, email delivery, portal access, persistence of certificates, electronic signatures, cron jobs, or external APIs.
