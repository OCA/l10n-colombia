# Copyright 2026 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_co_withholding_advance_enabled = fields.Boolean(
        string="Autorretención en Facturas de Clientes",
        config_parameter="l10n_co_withholding_advance.enabled",
    )
    l10n_co_withholding_advance_debit_id = fields.Many2one(
        comodel_name="account.account",
        string="Cuenta de autorretención débito",
        config_parameter="l10n_co_withholding_advance.debit_account_id",
    )
    l10n_co_withholding_advance_credit_id = fields.Many2one(
        comodel_name="account.account",
        string="Cuenta de autorretención crédito",
        config_parameter="l10n_co_withholding_advance.credit_account_id",
    )
    l10n_co_withholding_advance_rate = fields.Float(
        string="Tasa de autorretención (%)",
        config_parameter="l10n_co_withholding_advance.rate",
    )
