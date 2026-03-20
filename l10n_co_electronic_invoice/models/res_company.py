# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_co_autoretenedor = fields.Boolean(string="¿Es Autorretenedor?")
    l10n_co_regimen_fiscal = fields.Selection(
        related="partner_id.l10n_co_regimen_fiscal",
        readonly=False,
        string="Regimen Fiscal",
    )
    l10n_co_responsibility_ids = fields.Many2many(
        "l10n_co.responsibility.type",
        related="partner_id.l10n_co_responsibility_ids",
        readonly=False,
        string="Responsabilidades",
    )

    l10n_co_ciiu_id = fields.Many2one(
        "l10n_co.ciiu",
        "Principal actividad economica",
        related="partner_id.l10n_co_ciiu_id",
        readonly=False,
    )
    l10n_co_ciiu_ids = fields.Many2many(
        "l10n_co.ciiu",
        related="partner_id.l10n_co_ciiu_ids",
        readonly=False,
        string="Otras actividades economicas",
    )

    @api.onchange("l10n_co_regimen_fiscal")
    def _onchange_regimen_fiscal(self):
        for record in self:
            autoretenedor = record.l10n_co_autoretenedor
            if record.l10n_co_regimen_fiscal == "O-15":
                autoretenedor = True
            record.l10n_co_autoretenedor = autoretenedor

    def _localization_use_documents(self):
        """Colombian localization use documents"""
        self.ensure_one()
        return (
            self.account_fiscal_country_id.code == "CO"
            or super()._localization_use_documents()
        )
