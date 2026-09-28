# Copyright 2026 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Colombia - Withholding Certificates",
    "summary": "Wizard and PDF certificates for Colombian withholdings",
    "description": "Generate ReteFuente, ReteIVA, and ReteICA certificates from posted accounting data.",
    "version": "18.0.1.0.0",
    "development_status": "Alpha",
    "category": "Accounting/Localizations",
    "website": "https://github.com/OCA/l10n-colombia",
    "author": "Fernando Fernandez",
    "maintainers": ["ffernandezm"],
    "license": "AGPL-3",
    "depends": [
        "account",
        "l10n_co",
        "l10n_co_withholding",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/withholding_certificate_wizard_views.xml",
        "views/menu_views.xml",
        "report/withholding_certificate_report.xml",
        "report/withholding_certificate_templates.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
