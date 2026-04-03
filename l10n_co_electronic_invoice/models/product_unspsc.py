# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductsUNSPSC(models.Model):
    _name = "product.unspsc"
    _description = "Producto UNSPSC"

    name = fields.Char(string="Nombre Producto")
    active = fields.Boolean(string="Activo", default=True)
    product_code = fields.Char(string="Código Producto")
    segment_code = fields.Char(string="Código Segmento")
    segment_name = fields.Char(string="Nombre Segmento")
    family_code = fields.Char(string="Código Familia")
    family_name = fields.Char(string="Nombre Familia")
    class_code = fields.Char(string="Código Clase")
    class_name = fields.Char(string="Nombre Clase")
