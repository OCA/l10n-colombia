# Copyright 2026 juparmer - Juan Arcos <juanparmer@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class L10nCoEconomicActivity(models.Model):
    _name = "l10n.co.economic.activity"
    _description = "Actividad Económica CIIU Colombia"
    _order = "code"
    _rec_name = "complete_name"

    code = fields.Char(
        string="Código",
        required=True,
        index=True,
        help="Código CIIU de la actividad económica",
    )
    name = fields.Char(
        string="Descripción",
        required=True,
        translate=True,
        help="Descripción de la actividad económica",
    )
    complete_name = fields.Char(
        string="Nombre Completo",
        compute="_compute_complete_name",
        store=True,
        recursive=True,
    )
    active = fields.Boolean(
        string="Activo",
        default=True,
        help="Indica si la actividad económica está activa",
    )

    _sql_constraints = [
        (
            "code_unique",
            "unique(code)",
            "El código de actividad económica debe ser único.",
        ),
    ]

    @api.depends("code", "name")
    def _compute_complete_name(self):
        for activity in self:
            activity.complete_name = f"[{activity.code}] {activity.name}"
