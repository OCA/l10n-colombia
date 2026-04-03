# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_unspsc_id = fields.Many2one("product.unspsc", string="Producto UNSPSC")
    product_brand = fields.Char(string="Marca")
    product_model = fields.Char(string="Modelo")
    l10n_co_edi_ref_nominal_tax = fields.Float(
        string="Tarifa Nominal Impuesto Consumo",
        help="Tarifa nominal del impuesto al consumo "
        "(litros para licores, ml para cerveza). "
        "Usado para cálculo de impuestos per-unit "
        "(códigos 32, 34).",
    )
