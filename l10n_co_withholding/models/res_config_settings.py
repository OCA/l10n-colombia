# Copyright 2026 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_co_is_retention_agent = fields.Boolean(
        related="company_id.l10n_co_is_retention_agent",
        readonly=False,
        string="Agente de Retención Colombia",
    )
    l10n_co_default_rte_fte_tax_ids = fields.Many2many(
        related="company_id.l10n_co_default_rte_fte_tax_ids",
        readonly=False,
        string="ReteFte por Defecto",
    )
    l10n_co_default_rte_iva_tax_ids = fields.Many2many(
        related="company_id.l10n_co_default_rte_iva_tax_ids",
        readonly=False,
        string="ReteIVA por Defecto",
    )
    l10n_co_default_rte_ica_tax_ids = fields.Many2many(
        related="company_id.l10n_co_default_rte_ica_tax_ids",
        readonly=False,
        string="ReteICA por Defecto",
    )
