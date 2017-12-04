# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Country(models.Model):
    _inherit = 'res.country'

    apdnc_dane_code = fields.Char(string="DANE Code", size=4, help="Código DANE para el país")

    @api.onchange('apdnc_dane_code')
    def _onchange_apdnc_dane_code(self):
        if self.apdnc_dane_code:
            recs = self.get_duplicated_by_dane_code(self._origin.id, self.apdnc_dane_code)
            if recs:
                return {'warning': {
                    'title': _('Duplicidad de Registros!'),
                    'message': _('Ya existe un país con el código DANE ingresado.')}
                }

    @api.model
    def get_duplicated_by_dane_code(self, record_id, dane_code):
        domain = [('apdnc_dane_code', '=', dane_code), ('id', '!=', record_id)]
        return self.search(domain)


class State(models.Model):
    _inherit = 'res.country.state'

    apdnc_dane_code = fields.Char(string="DANE Code", size=2, help="Código DANE para el departamento")

    @api.onchange('apdnc_dane_code')
    def _onchange_apdnc_dane_code(self):
        if self.country_id and self.apdnc_dane_code:
            recs = self.get_duplicated_by_dane_code(self._origin.id, self.country_id, self.apdnc_dane_code)
            if recs:
                return {'warning': {
                    'title': _('Duplicidad de Registros!'),
                    'message': _('Ya existe un departamento con el código DANE ingresado.')}
                }

    @api.constrains('apdnc_dane_code')
    def _check_apdnc_dane_code(self):
        if self.country_id and self.apdnc_dane_code:
            recs = self.get_duplicated_by_dane_code(self.id, self.country_id, self.apdnc_dane_code)
            if recs:
                raise ValidationError(_("Ya existe un departamento con el código DANE ingresado."))

    @api.model
    def get_duplicated_by_dane_code(self, record_id, country_id, dane_code):
        domain = [('country_id', '=', country_id.id), ('apdnc_dane_code', '=', dane_code), ('id', '!=',
                                                                                            record_id)]
        return self.search(domain)


class City(models.Model):
    _inherit = 'apcty.city'

    apdnc_dane_code = fields.Char(string="DANE Code", size=3, help="Código DANE para el municipio")

    @api.onchange('apdnc_dane_code', 'state_id')
    def _onchange_apdnc_dane_code(self):
        if self.state_id and self.apdnc_dane_code:
            recs = self.get_duplicated_by_dane_code(self._origin.id, self.state_id, self.apdnc_dane_code)
            if recs:
                return {'warning': {
                    'title': _('Duplicidad de Registros!'),
                    'message': _('Ya existe un municipio con el código DANE ingresado.')}
                }

    @api.constrains('apdnc_dane_code', 'state_id')
    def _check_apdnc_dane_code(self):
        if self.state_id and self.apdnc_dane_code:
            recs = self.get_duplicated_by_dane_code(self.id, self.state_id, self.apdnc_dane_code)
            if recs:
                raise ValidationError(_("Ya existe un municipio con el código DANE ingresado."))

    @api.model
    def get_duplicated_by_dane_code(self, record_id, state_id, dane_code):
        domain = [('state_id', '=', state_id.id), ('apdnc_dane_code', '=', dane_code), ('id', '!=',
                                                                                        record_id)]
        return self.search(domain)
