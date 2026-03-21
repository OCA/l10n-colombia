# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _get_l10n_co_dian_self_params(self):
        self.ensure_one()
        return (
            self.l10n_co_regimen_fiscal,
            self.l10n_co_responsibility_ids,
            self.l10n_co_ciiu_id,
        )
