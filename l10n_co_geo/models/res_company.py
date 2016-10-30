# -*- coding: utf-8 -*-
# Copyright 2016 David Arnold, DevCO Colombia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from openerp import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    country_id = fields.Many2one(
        comodel_name='res.country',
        related='city_id.state_id.country_id',
        readonly=True,
        required=False,
        index=False,
        default=None,
        help=False,
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

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
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
    )

    @api.onchange('city_id')
    def _change_city(self):
        self.city = self.city_id.name
