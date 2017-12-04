# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
import logging

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    aprgt_registro_unico_tributario_ids = fields.One2many('aprgt.registro.unico.tributario', 'partner_id', string='RUT')
