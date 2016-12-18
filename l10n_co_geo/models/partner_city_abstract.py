# -*- coding: utf-8 -*-
# Copyright 2016 David Arnold, DevCO Colombia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from openerp import models, fields, api


class PartnerCityAbstract(models.AbstractModel):
    _name = 'partner.city.abstract'

    city_id = fields.Many2one('res.country.state.city', 'City')

    def _enforce_address_domains(self):
        domain = dict(city_id=[], state_id=[])
        if self.country_id:
            domain['state_id'] = [('country_id', '=', self.country_id.id)]
            domain['city_id'] = [('country_id', '=', self.country_id.id)]
        if self.state_id:
            domain['city_id'] = [('state_id', '=', self.state_id.id)]
        return {'domain': domain}

    @api.onchange('city_id')
    def _onchange_city(self):
        self.city = self.city_id.name
        if self.city_id:
            self.state_id = self.city_id.state_id
            self.country_id = self.city_id.country_id
        return self._enforce_address_domains()

    @api.onchange('state_id')
    def _onchange_state(self):
        if self.state_id:
            if self.city_id.state_id != self.state_id:
                self.city_id = False
            self.country_id = self.state_id.country_id
        return self._enforce_address_domains()

    @api.onchange('country_id')
    def _onchange_country(self):
        if self.country_id:
            if self.city_id.country_id != self.country_id:
                self.city_id = False
            if self.state_id.country_id != self.country_id:
                self.state_id = False
        return self._enforce_address_domains()

    def _complete_address(self, vals):

        def set_to_zero(vals, field):
            return field in vals and not vals.get(field)
        if vals.get('city_id'):
            vals['state_id'] = self.env[
                'res.country.state.city'
            ].browse(vals.get('city_id')).state_id.id
        if set_to_zero(vals, 'state_id') and self.city_id:
            vals['state_id'] = self.city_id.state_id.id
        if vals.get('state_id'):
            vals['country_id'] = self.env[
                'res.country.state'
            ].browse(vals.get('state_id')).country_id.id
        if set_to_zero(vals, 'country_id') and self.city_id or self.state_id:
            country_rel = self.city_id or self.state_id
            vals['country_id'] = country_rel.country_id.id
        return vals
