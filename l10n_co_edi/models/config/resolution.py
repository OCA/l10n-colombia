# -*- coding: utf-8 -*-
#
# Jorels S.A.S. - Copyright (2019-2022)
#
# This file is part of l10n_co_edi_jorels.
#
# l10n_co_edi_jorels is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# l10n_co_edi_jorels is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with l10n_co_edi_jorels.  If not, see <https://www.gnu.org/licenses/>.
#
# email: info@jorels.com
#

import json
import logging

import requests
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class Resolution(models.Model):
    _name = 'l10n_co_edi_jorels.resolution'
    _description = 'Electronic invoice resolution'
    _rec_name = 'name'

    name = fields.Char(string="Name", compute='_compute_name')

    resolution_api_sync = fields.Boolean(string="Synchronize with API?", default=True)

    # Range Resolution DIAN
    resolution_type_document_id = fields.Many2one(comodel_name="l10n_co_edi_jorels.type_documents",
                                                  string='Document type',
                                                  required=True, ondelete='RESTRICT')
    resolution_prefix = fields.Char(string="Prefix", required=True)
    resolution_resolution = fields.Char(string="Resolution")
    resolution_resolution_date = fields.Date(string="Resolution date")
    resolution_technical_key = fields.Char(string="Technical key")
    resolution_from = fields.Integer(string="From", required=True)
    resolution_to = fields.Integer(string="To", required=True)
    resolution_date_from = fields.Date(string="Date from")
    resolution_date_to = fields.Date(string="Date to")

    resolution_id = fields.Integer(string="Api ID", readonly=True, copy=False, index=True)
    resolution_number = fields.Integer(string="Number", readonly=True, copy=False)
    resolution_next_consecutive = fields.Char(string="Next consecutive", readonly=True, copy=False)

    resolution_message = fields.Char(string="Message", readonly=True)

    company_id = fields.Many2one('res.company', string='Company', readonly=False, copy=False, required=True,
                                 default=lambda self: self.env.company)

    def _compute_name(self):
        for rec in self:
            if rec.resolution_id:
                rec.name = str(rec.resolution_id) + ' - ' + \
                           rec.resolution_type_document_id.name + \
                           ' [' + rec.resolution_type_document_id.code + ']'
            else:
                rec.name = rec.resolution_type_document_id.name

    @api.model_create_single
    def create(self, vals):
        if vals['resolution_api_sync']:
            vals, success = self.post_resolution(vals)
            if success:
                return super(Resolution, self).create(vals)
            else:
                raise UserError(_("Could not save record to API"))
        else:
            return super(Resolution, self).create(vals)

    def write(self, vals):
        for rec in self:
            if rec.resolution_api_sync:
                vals, success = self.put_resolution(vals)
                if success:
                    return super(Resolution, self).write(vals)
                else:
                    raise UserError(_("Could not update record in API"))
            else:
                return super(Resolution, self).write(vals)

    def unlink(self):
        for rec in self:
            if rec.resolution_api_sync:
                success = self.delete_resolution()
                if success:
                    return super(models.Model, self).unlink()
                else:
                    raise UserError(_("Could not delete record in API"))
            else:
                return super(models.Model, self).unlink()

    # Resolution creation
    def post_resolution(self, vals):
        success = False
        try:
            requests_data = {
                'code': vals['resolution_type_document_id']
            }

            if vals['resolution_prefix']:
                requests_data['prefix'] = vals['resolution_prefix']

            if vals['resolution_resolution']:
                requests_data['resolution'] = vals['resolution_resolution']

            if vals['resolution_resolution_date']:
                requests_data['resolution_date'] = vals['resolution_resolution_date']

            if vals['resolution_technical_key']:
                requests_data['technical_key'] = vals['resolution_technical_key']

            requests_data['number_from'] = vals['resolution_from']
            requests_data['number_to'] = vals['resolution_to']

            if vals['resolution_date_from']:
                requests_data['date_from'] = vals['resolution_date_from']

            if vals['resolution_date_to']:
                requests_data['date_to'] = vals['resolution_date_to']

            _logger.debug("Request create resolution DIAN: %s",
                          json.dumps(requests_data, indent=2, sort_keys=False))

            token = str(self.env.company.api_key)
            api_url = self.env['ir.config_parameter'].sudo().get_param('jorels.edipo.api_url',
                                                                       'https://edipo.jorels.com')
            params = {'token': token}
            header = {"accept": "application/json", "Content-Type": "application/json"}
            api_url = api_url + "/resolution"
            response = requests.post(api_url,
                                     json.dumps(requests_data),
                                     headers=header,
                                     params=params).json()
            _logger.debug('API Response: %s', response)

            if 'resolution' in response:
                vals['resolution_id'] = response['resolution']['id']
                vals['resolution_number'] = response['resolution']['number']
                vals['resolution_next_consecutive'] = response['resolution']['next_consecutive']
                success = True

            if 'detail' in response:
                raise UserError(response['detail'])
            if 'message' in response:
                if response['message'] == 'Unauthenticated.':
                    vals['resolution_message'] = _('Unable to authenticate with the API. '
                                                   'Please check your API key and try again.')
                else:
                    vals['resolution_message'] = response['message']
            else:
                vals['resolution_message'] = _('Unable to communicate with the API')
        except Exception as e:
            vals['resolution_message'] = _("API connection error!")
            _logger.debug("Connection error: %s", e)
        return vals, success

    # Resolution update
    def put_resolution(self, vals):
        success = False
        for rec in self:
            try:
                # Resolution api id for update
                resolution_id = str(rec.resolution_id)

                requests_data = {
                    'code': rec.resolution_type_document_id.id,
                    'prefix': rec.resolution_prefix,
                    'resolution': rec.resolution_resolution,
                    'resolution_date': fields.Date.to_string(rec.resolution_resolution_date),
                    'technical_key': rec.resolution_technical_key,
                    'number_from': rec.resolution_from,
                    'number_to': rec.resolution_to,
                    'date_from': fields.Date.to_string(rec.resolution_date_from),
                    'date_to': fields.Date.to_string(rec.resolution_date_to)
                }

                len_prefix = len('resolution_')
                for val in vals:
                    if val != 'company_id':
                        requests_data[val[len_prefix:]] = vals[val]

                if not requests_data['prefix']:
                    requests_data.pop('prefix')

                if not requests_data['resolution']:
                    requests_data.pop('resolution')

                if not requests_data['resolution_date']:
                    requests_data.pop('resolution_date')

                if not requests_data['technical_key']:
                    requests_data.pop('technical_key')

                if not requests_data['date_from']:
                    requests_data.pop('date_from')

                if not requests_data['date_to']:
                    requests_data.pop('date_to')

                _logger.debug("Request update resolution DIAN: %s",
                              json.dumps(requests_data, indent=2, sort_keys=False))

                token = str(self.env.company.api_key)
                api_url = self.env['ir.config_parameter'].sudo().get_param('jorels.edipo.api_url',
                                                                           'https://edipo.jorels.com')
                params = {'token': token}
                header = {"accept": "application/json", "Content-Type": "application/json"}
                api_url = api_url + "/resolution/" + resolution_id
                response = requests.put(api_url,
                                        json.dumps(requests_data),
                                        headers=header,
                                        params=params).json()
                _logger.debug('API Response: %s', response)

                if 'resolution' in response:
                    vals['resolution_number'] = response['resolution']['number']
                    vals['resolution_next_consecutive'] = response['resolution']['next_consecutive']
                    success = True

                if 'detail' in response:
                    raise UserError(response['detail'])
                if 'message' in response:
                    if response['message'] == 'Unauthenticated.':
                        vals['resolution_message'] = _('Unable to authenticate with the API. '
                                                       'Please check your API key and try again.')
                    else:
                        vals['resolution_message'] = response['message']
                else:
                    vals['resolution_message'] = _('Unable to communicate with the API')
            except Exception as e:
                vals['resolution_message'] = _("API connection error!")
                _logger.debug("Connection error: %s", e)
        return vals, success

    # Resolution removal
    def delete_resolution(self):
        success = False
        for rec in self:
            try:
                # Resolution api id for update
                resolution_id = str(rec.resolution_id)

                # The function str() is necessary for 'False' answers and boolean exceptions
                token = str(self.env.company.api_key)
                api_url = self.env['ir.config_parameter'].sudo().get_param('jorels.edipo.api_url',
                                                                           'https://edipo.jorels.com')
                params = {'token': token}
                header = {"accept": "application/json", "Content-Type": "application/json"}
                api_url = api_url + "/resolution/" + str(resolution_id)
                response = requests.delete(api_url,
                                           headers=header,
                                           params=params).json()
                _logger.debug('API Response: %s', response)

                if 'detail' in response:
                    raise UserError(response['detail'])
                if 'message' in response:
                    if response['message'] == 'Unauthenticated.':
                        rec.resolution_message = _('Unable to authenticate with the API. '
                                                   'Please check your API key and try again.')
                    elif response['message'] == 'Resolución eliminada con éxito':
                        success = True
                    else:
                        rec.resolution_message = response['message']
                else:
                    rec.resolution_message = _('Unable to communicate with the API')
            except Exception as e:
                rec.resolution_message = _('API connection error!')
                _logger.debug("Connection error: %s", e)
                raise UserError(rec.resolution_message)
        return success
