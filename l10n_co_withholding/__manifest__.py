# Copyright 2026 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Colombia - Retención en la Fuente",
    "summary": "Retención en la fuente (RteFte), ReteIVA y ReteICA para Colombia",
    "author": "Juan Arcos, Odoo Community Association (OCA)",
    "maintainers": ["juanparmer"],
    "website": "https://github.com/OCA/l10n-colombia",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "version": "18.0.1.0.0",
    "depends": [
        "account",
        "l10n_co",
        "base_address_extended",
        "l10n_co_economic_activities",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/l10n_co_reteica_data.xml",
        "views/res_partner_views.xml",
        "views/res_config_settings_views.xml",
        "views/account_tax_views.xml",
        "views/account_move_views.xml",
        "views/l10n_co_reteica_rate_views.xml",
    ],
    "external_dependencies": {
        "python": [],
    },
    "assets": {},
    "application": False,
    "installable": True,
    "auto_install": False,
    "post_init_hook": "_l10n_co_withholding_post_init",
}
