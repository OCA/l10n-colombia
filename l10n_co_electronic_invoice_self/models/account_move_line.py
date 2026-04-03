# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_l10n_co_dian_self_params(self):
        params = []
        sale_lines = self.filtered(lambda line: line.product_id)
        for line in sale_lines:
            params.append(line.tax_ids)
            params.append(line.product_uom_id.unece_code_id)
            product_code = (
                line.product_id.product_tmpl_id.product_unspsc_id
                or line.product_id.default_code
            )
            params.append(product_code)
        return params
