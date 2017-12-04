# -*- coding: utf-8 -*-

from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class PartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    apbnk_tipo_cuenta = fields.Selection([('ahorro', 'Ahorro'),
                                   ('corriente', 'Corriente')], string="Tipo de Cuenta", default='corriente')

    def _get_tipo_cuenta(self):
        return dict(self.fields_get(['apbnk_tipo_cuenta'])['apbnk_tipo_cuenta']['selection'])[self.apbnk_tipo_cuenta]
