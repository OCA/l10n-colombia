# Copyright 2026 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_co_is_retention_agent = fields.Boolean(
        string="Agente de Retención",
        help="Indica si la empresa actúa como agente de retención.",
    )
    l10n_co_default_rte_fte_tax_ids = fields.Many2many(
        comodel_name="account.tax",
        relation="res_company_l10n_co_rte_fte_tax_rel",
        column1="company_id",
        column2="tax_id",
        string="ReteFte por Defecto",
        domain=[
            ("l10n_co_withholding_type", "=", "rte_fte"),
        ],
        help="Impuestos de retención en la fuente que se aplican por defecto.",
    )
    l10n_co_default_rte_iva_tax_ids = fields.Many2many(
        comodel_name="account.tax",
        relation="res_company_l10n_co_rte_iva_tax_rel",
        column1="company_id",
        column2="tax_id",
        string="ReteIVA por Defecto",
        domain=[
            ("l10n_co_withholding_type", "=", "rte_iva"),
        ],
        help="Impuestos de retención de IVA que se aplican por defecto.",
    )
    l10n_co_default_rte_ica_tax_ids = fields.Many2many(
        comodel_name="account.tax",
        relation="res_company_l10n_co_rte_ica_tax_rel",
        column1="company_id",
        column2="tax_id",
        string="ReteICA por Defecto",
        domain=[
            ("l10n_co_withholding_type", "=", "rte_ica"),
        ],
        help="Impuestos de retención de ICA que se aplican por defecto.",
    )

    @api.model
    def _l10n_co_get_uvt_value(self, year=None):
        if year is None:
            year = fields.Date.context_today(self).year
        param = self.env["ir.config_parameter"].sudo()
        uvt_value = param.get_param("l10n_co_withholding.uvt_value")
        return float(uvt_value) if uvt_value else 52374.0
