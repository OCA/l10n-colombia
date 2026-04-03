# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_co_regimen_fiscal = fields.Selection(
        selection=[
            ("48", "Impuesto sobre las ventas – IVA"),
            ("49", "No responsable de IVA"),
        ],
        string="Regimen Fiscal",
    )
    l10n_co_responsibility_ids = fields.Many2many(
        "l10n_co.responsibility.type", string="Responsabilidades"
    )
    l10n_co_ciiu_id = fields.Many2one("l10n_co.ciiu", "Principal actividad economica")
    l10n_co_ciiu_ids = fields.Many2many(
        "l10n_co.ciiu", string="Otras actividades economicas"
    )

    def _l10n_co_get_vat_splited(self):
        """Split VAT into (nit, verification_digit).

        For NIT (code 31) or any VAT with hyphen: '901193767-6' → ('901193767', '6')
        For other types without hyphen: '12345678' → ('12345678', None)
        """
        self.ensure_one()
        vat = self.vat or ""
        if "-" in vat:
            parts = vat.split("-", 1)
            return parts[0], parts[1]
        return vat, None
