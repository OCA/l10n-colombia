# -*- coding: utf-8 -*-
# Copyright 2016 David Arnold, DevCO Colombia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api


class ResCity(models.Model):
    _name = 'res.country.state.city'
    _description = 'Ciudad'
    _rec_name = "display_name"

    name = fields.Char(
        string=u'City',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="",
        size=50,
        translate=True,
    )

    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string=u'State',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    phone_prefix = fields.Char(
        string=u'Phone Prefix',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="",
        size=50,
        translate=True,
    )

    statcode = fields.Char(
        string=u'DANE Code',
        size=5,
        help='Code of the Colombian statistical department',
        required=False,
        readonly=False,
        index=False,
        default=None,
        translate=True,
    )

    country_id = fields.Many2one(
        comodel_name='res.country',
        string=u'Country',
        related='state_id.country_id',
        store=True,
        readonly=True)

    display_name = fields.Char(
        string='Name',
        compute="_compute_display_name",
        inverse='_inverse_display_name',
        search='_search_display_name'
    )

    @api.depends('name', 'state_id.iso')
    def _compute_display_name(self):
        self.ensure_one()
        names = [self.name, self.state_id.iso, self.state_id.country_id.code]
        self.display_name = ', '.join(filter(None, names))

    def _inverse_display_name(self):
        self.ensure_one()
        self.name = self.display_name.split(', ')[0].strip()

    def _search_display_name(self, operator, value):
        if operator == 'like':
            operator = 'ilike'
        return [('name', operator, value)]
