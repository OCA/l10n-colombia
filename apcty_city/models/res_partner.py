# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    apcty_city_id = fields.Many2one('apcty.city', string='City', ondelete='restrict',
                                    domain="[('state_id', '=', state_id)]")
    apcty_has_cities = fields.Boolean(related='state_id.apcty_has_cities', string='Has Cities', store=False)

    @api.onchange('country_id')
    def _onchange_country_id(self):
        self.state_id = False
        return super(Partner, self)._onchange_country_id()

    @api.onchange('state_id')
    def _onchange_state_id(self):
        self.apcty_city_id = False
        if self.state_id:
            return {'domain': {'apcty_city_id': [('state_id', '=', self.state_id.id)]}}
        else:
            return {'domain': {'apcty_city_id': []}}

    @api.onchange('apcty_city_id')
    def _onchange_apcty_city_id(self):
        if self.apcty_city_id:
            self.city = self.apcty_city_id.name

    @api.multi
    @api.constrains('country_id', 'state_id', )
    def _check_country_id_state_id(self):
        for rec in self:
            if rec.state_id:
                if rec.country_id:
                    if rec.state_id.country_id != rec.country_id:
                        _logger.error('Error ! The state does not belong to the selected country.')
                else:
                    _logger.error('Error ! Please select the country.')

    @api.multi
    @api.constrains('apcty_city_id', 'state_id')
    def _check_apcty_city_id_state_id(self):
        for rec in self:
            if rec.state_id and rec.state_id.apcty_has_cities and rec.apcty_city_id:
                if rec.apcty_city_id.state_id != rec.state_id:
                    raise ValidationError(_('Error ! The city does not belong to the selected state.'))

    @api.multi
    @api.constrains('city', 'state_id')
    def _check_city_state_id(self):
        for rec in self:
            if rec.country_id and rec.country_id.id == 'base.co':
                if rec.city and not rec.state_id:
                    raise ValidationError(_('Error ! Please select the state.'))

    @api.multi
    @api.constrains('apcty_city_id', 'city', 'street', )
    def _check_apcty_city_id_city_street(self):
        for rec in self:
            if rec.street:
                if not (rec.city or rec.apcty_city_id):
                    if rec.state_id:
                        if rec.state_id.apcty_has_cities:
                            raise ValidationError(_('Error ! Please select the city.'))
                        else:
                            raise ValidationError(_('Error ! Please enter the city.'))
                    else:
                        raise ValidationError(_('Error ! Please enter the city.'))

    @api.multi
    @api.constrains('street', 'street2')
    def _check_street_street2(self):
        for rec in self:
            if not rec.street:
                if rec.street2:
                    raise ValidationError(_('Error ! Please enter the street.'))

    @api.model
    def _install_city(self):
        for rec in self.search([]):
            _logger.info('Processing city for partner ' + rec.name)
            if rec.apcty_city_id:
                rec.city = rec.apcty_city_id.name
