# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class Bank(models.Model):
    _inherit = 'res.bank'

    apcty_city_id = fields.Many2one('apcty.city', string='City', ondelete='restrict',
                                    domain="[('state_id', '=', state)]")
    apcty_has_cities = fields.Boolean(related='state.apcty_has_cities', string='Has Cities', store=False)

    @api.onchange('country')
    def _onchange_country(self):
        self.state = False
        if self.country:
            return {'domain': {'state': [('country_id', '=', self.country.id)]}}
        else:
            return {'domain': {'state': []}}

    @api.onchange('state')
    def _onchange_state(self):
        self.apcty_city_id = False
        if self.state:
            return {'domain': {'apcty_city_id': [('state_id', '=', self.state.id)]}}
        else:
            return {'domain': {'apcty_city_id': []}}

    @api.onchange('apcty_city_id')
    def _onchange_apcty_city_id(self):
        if self.apcty_city_id:
            self.city = self.apcty_city_id.name

    @api.multi
    @api.constrains('country', 'state', )
    def _check_country_state(self):
        for rec in self:
            if rec.state:
                if rec.country:
                    if rec.state.country_id != rec.country:
                        raise ValidationError(_('Error ! The state does not belong to the selected country.'))
                else:
                    raise ValidationError(_('Error ! Please select the country.'))

    @api.multi
    @api.constrains('apcty_city_id', 'state')
    def _check_apcty_city_id_state(self):
        for rec in self:
            if rec.state and rec.state.apcty_has_cities and rec.apcty_city_id:
                if rec.apcty_city_id.state_id != rec.state:
                    raise ValidationError(_('Error ! The city does not belong to the selected state.'))

    @api.multi
    @api.constrains('street', 'street2')
    def _check_street_street2(self):
        for rec in self:
            if rec.street2 and not rec.street:
                raise ValidationError(_('Error ! Please enter street value.'))

    @api.multi
    @api.constrains('city', 'state')
    def _check_city_state(self):
        for rec in self:
            if rec.country and rec.country.id == 'base.co':
                if rec.city and not rec.state:
                    raise ValidationError(_('Error ! Please select the state.'))

    @api.multi
    @api.constrains('apcty_city_id', 'city', 'street', )
    def _check_apcty_city_id_city_street(self):
        for rec in self:
            if rec.street and not (rec.city or rec.apcty_city_id):
                if rec.state:
                    if rec.state.apcty_has_cities:
                        raise ValidationError(_('Error ! Please select the city.'))
                    else:
                        raise ValidationError(_('Error ! Please enter the city.'))
                else:
                    raise ValidationError(_('Error ! Please enter the city.'))
