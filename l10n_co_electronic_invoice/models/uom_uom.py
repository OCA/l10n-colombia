# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _  # noqa


class uomuom(models.Model):
    _inherit = "uom.uom"

    unece_code_id = fields.Many2one(
        "unece.uom.code",
        string="Código de unidad de medida UNECE",
        help="Código de unidad de medida UNECE adoptado por la DIAN",
    )
