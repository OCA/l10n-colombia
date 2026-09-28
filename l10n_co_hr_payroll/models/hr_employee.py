# Copyright 2026 Juan Arcos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    l10n_co_eps = fields.Many2one(
        comodel_name="res.partner",
        string="EPS",
        help="Entidad Promotora de Salud del trabajador.",
    )
    l10n_co_afp = fields.Many2one(
        comodel_name="res.partner",
        string="Fondo de Pensiones (AFP)",
        help="Administradora del Fondo de Pensiones del trabajador.",
    )