# -*- coding: utf-8 -*-
# Copyright 2016 David Arnold, DevCO Colombia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from openerp import models, fields, api, _


class ResCountry(models.Model):
    _inherit = 'res.country'

    code_dian = fields.Char('Code Dian', size=3, translate=False)


class ResState(models.Model):
    _inherit = 'res.country.state'

    iso = fields.Char('iso', size=3, translate=False)

    _sql_constraints = [
        ('state_uniq', 'unique(name, country_id)',
         _('The state you are trying to create already exists.'))]


class ResCity(models.Model):
    _name = 'res.country.state.city'
    _description = 'City'

    name = fields.Char('City', required=True)
    state_id = fields.Many2one('res.country.state', 'State')
    statcode = fields.Char(
        'DANE Code', size=5, translate=False,
        help='Code of the Colombian statistical department')
    country_id = fields.Many2one('res.country', 'Country', required=True)

    _sql_constraints = [
        ('state_uniq', 'unique(name, state_id, country_id)',
         _('The city you are trying to create already exists.'))]

    def _enforce_address_domains(self):
        domain = dict(state_id=[])
        if self.country_id:
            domain['state_id'] = [('country_id', '=', self.country_id.id)]
        return {'domain': domain}

    @api.onchange('state_id')
    def _onchange_state(self):
        if self.state_id:
            self.country_id = self.state_id.country_id
        return self._enforce_address_domains()

    @api.onchange('country_id')
    def _onchange_country(self):
        if self.country_id:
            if self.state_id.country_id != self.country_id:
                self.state_id = False
        return self._enforce_address_domains()

    @api.model
    def create(self, vals):
        if vals.get('state_id'):
            vals['country_id'] = self.env[
                'res.country.state'
            ].browse(vals.get('state_id')).country_id.id

        return super(ResCity, self).create(vals)
