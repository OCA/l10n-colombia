# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class TaxType(models.Model):
    _name = "l10n_co.tax.type"
    _description = "Tipo de Impuesto - Tributo"

    name = fields.Char(string="Referencia")
    code = fields.Char(string="Código")
    is_withholding_tax = fields.Boolean(string="Es retención?", default=False)
    active = fields.Boolean(string="Activo", default=True)
