# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResponsibilityType(models.Model):
    _name = "l10n_co.responsibility.type"
    _description = "Responsabilidad fiscal - Régimen fiscal"
    _rec_name = "display_name"

    name = fields.Char(string="Referencia")
    active = fields.Boolean(string="Activo", default=True)
    code = fields.Char(string="Codigo")
    display_name = fields.Char(string="Nombre", compute="_compute_name")

    def _compute_name(self):
        for i in self:
            i.display_name = f"{i.code} {i.name}"
