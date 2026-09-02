# Copyright 2026 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_co_tax_regime = fields.Selection(
        selection=[
            ("ordinary", "Régimen Ordinario"),
            ("simple", "Régimen Simple"),
            ("non_taxpayer", "No Contribuyente / No Responsable"),
        ],
        string="Régimen Tributario",
        help=(
            "Régimen tributario del partner para determinar"
            " las retenciones aplicables."
        ),
    )
    l10n_co_is_gran_contribuyente = fields.Boolean(
        string="Gran Contribuyente",
        help="Indica si el partner está calificado como gran contribuyente.",
    )
    l10n_co_is_authorretenedor = fields.Boolean(
        string="Autorretenedor",
        help="Indica si el partner es autorretenedor de renta.",
    )
    l10n_co_is_retention_agent = fields.Boolean(
        string="Agente de Retención",
        help="Indica si el partner actúa como agente de retención.",
    )
    city_id = fields.Many2one(
        comodel_name="res.city",
        string="Ciudad",
        help=(
            "Ciudad/municipio del partner. Se usa para determinar"
            " las tarifas de ReteICA aplicables."
        ),
    )

    @api.onchange("l10n_co_tax_regime")
    def _onchange_l10n_co_tax_regime(self):
        if self.l10n_co_tax_regime == "simple":
            self.l10n_co_is_authorretenedor = False
