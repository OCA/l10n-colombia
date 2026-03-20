# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PaymentMethod(models.Model):
    _name = "l10n_co.payment.method"
    _description = "Método de Pago Colombia"

    name = fields.Char(string="Nombre")
    code = fields.Char(string="Código")
    active = fields.Boolean(string="Activo", default=True)
