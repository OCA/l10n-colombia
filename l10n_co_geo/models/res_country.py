# -*- coding: utf-8 -*-
# Copyright 2016 David Arnold, DevCO Colombia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from openerp import models, fields


class ResCountry(models.Model):
    _inherit = 'res.country'

    code_dian = fields.Char(
        string='Code Dian',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=3,
        translate=False
    )
