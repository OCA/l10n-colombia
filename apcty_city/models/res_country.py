# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import logging

_logger = logging.getLogger(__name__)


class City(models.Model):
    _description = "City"
    _name = 'apcty.city'
    _order = 'country_id, state_id, name'

    country_id = fields.Many2one('res.country', string='Country', required=True)
    state_id = fields.Many2one('res.country.state', string='State', required=True,
                               domain="[('country_id', '=', country_id)]")
    name = fields.Char(string='City Name', required=True,
                       help='Administrative divisions of a state.')
    code = fields.Char(string='City Code', help='The city code.', required=False)

    @api.multi
    def name_get(self):
        return [(rec.id, rec.name + ' - ' + rec.state_id.name + ' (' + rec.country_id.code + ')') for rec in
                self]

    @api.model
    def create(self, vals):
        if vals.get('code'):
            vals['code'] = vals['code'].upper()
        return super(City, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('code'):
            vals['code'] = vals['code'].upper()
        return super(City, self).write(vals)

    @api.constrains('country_id', 'state_id')
    def _check_country_id_state_id(self):
        if self.state_id.country_id != self.country_id:
            _logger.error('Error ! The state does not belong to the selected country.')

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if not self.country_id:
            self.state_id = False
        else:
            if self.state_id and self.state_id.country_id != self.country_id:
                self.state_id = False


class Country(models.Model):
    _inherit = 'res.country'

    apcty_city_ids = fields.One2many('apcty.city', 'country_id', string='Cities')


class CountryState(models.Model):
    _inherit = 'res.country.state'

    apcty_city_ids = fields.One2many('apcty.city', 'state_id', string='Cities')
    apcty_has_cities = fields.Boolean(string='Has Cities')
