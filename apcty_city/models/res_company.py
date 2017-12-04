# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class Company(models.Model):
    _inherit = 'res.company'

    apcty_city_id = fields.Many2one('apcty.city', string='City', ondelete='restrict',
                                    domain="[('state_id', '=', state_id)]")
    apcty_has_cities = fields.Boolean(related='state_id.apcty_has_cities', string='Has Cities', store=False)
