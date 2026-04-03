# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    @api.model
    def _default_l10n_co_tax_type(self):
        obj = self.env["l10n_co.tax.type"]
        default = obj.search([("code", "=", "01")], limit=1)
        return default.id

    l10n_co_tax_type_id = fields.Many2one(
        "l10n_co.tax.type",
        string="Tipo de impuesto",
        default=lambda self: self._default_l10n_co_tax_type(),
    )
