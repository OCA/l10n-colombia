# Copyright 2026 juparmer - Juan Arcos <juanparmer@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Colombia - Actividades Económicas",
    "summary": "Códigos de actividades económicas CIIU para Colombia",
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "category": "Accounting/Localizations",
    "website": "https://github.com/OCA/l10n-colombia",
    "author": "Juan Arcos, Odoo Community Association (OCA)",
    "maintainers": ["juanparmer"],
    "license": "AGPL-3",
    "depends": [
        "base",
        "contacts",
        "account",
        "base_address_extended",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/l10n_co_economic_activity_data.xml",
        "views/l10n_co_economic_activity_views.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
