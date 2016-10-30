# -*- coding: utf-8 -*-
# Copyright 2016 David Arnold, DevCO Colombia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from openerp import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    city = fields.Char(
        invisible=True
    )

    state_id = fields.Many2one(
        'res.country.state',
        related='city_id.state_id',
        readonly=True,
    )

    city_id = fields.Many2one(
        comodel_name='res.country.state.city',
        string=u'City',
        ondelete='cascade'
    )

    @api.onchange('city_id')
    def onchange_city(self):
        self.city = self.city_id.name
