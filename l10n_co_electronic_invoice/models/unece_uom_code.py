# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductsUnidadMedida(models.Model):
    _name = "unece.uom.code"
    _description = "Código de unidad de medida UNECE"

    name = fields.Char(string="Referencia")
    code = fields.Char(string="Codigo")
    active = fields.Boolean(string="Activo", default=True)
