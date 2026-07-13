# Copyright 2026 juparmer - Juan Arcos <juanparmer@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Colombia - Verification Digit",
    "summary": "Compute Colombian NIT verification digit (DIAN algorithm)",
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "category": "Accounting",
    "website": "https://github.com/OCA/l10n-colombia",
    "author": "Juan Arcos, Odoo Community Association (OCA)",
    "maintainers": ["juanparmer"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "preloadable": False,
    "depends": ["l10n_latam_base", "l10n_co"],
    "data": [
        "views/res_partner_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_co_verification_digit/static/src/css/l10n_co_verification_digit.css",
        ],
    },
}
