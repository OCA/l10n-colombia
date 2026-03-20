# Colombia - Factura Electrónica Software Propio

Módulo de facturación electrónica colombiana con integración directa a los servicios web
de la DIAN usando `account.edi` nativo de Odoo 18.

## Dependencias

Módulos nativos de Odoo:

- `account_edi` — Framework EDI
- `account_edi_ubl_cii` — Generación UBL 2.1
- `certificate` — Certificados digitales
- `l10n_co_electronic_invoice` — Datos maestros colombianos

Python: `xmlsig`, `lxml`, `cryptography`, `xmltodict`, `requests`, `qrcode`.

## Documentación

Ver `readme/DESCRIPTION.md` y `readme/USAGE.md`.

## Autor

IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>

## Licencia

AGPL-3.0
