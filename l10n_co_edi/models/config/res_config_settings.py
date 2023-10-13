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


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Api key
    api_key = fields.Char(related="company_id.api_key", string="Api key", readonly=False)

    ei_always_validate = fields.Boolean(related="company_id.ei_always_validate",
                                        string="Always validate invoices",
                                        default=False, readonly=False)

    # Test
    is_not_test = fields.Boolean(related="company_id.is_not_test", string="Production environment", default=False,
                                 readonly=False)
    test_set_id = fields.Char(related="company_id.test_set_id", string="TestSetId", readonly=False)
    enable_validate_state = fields.Boolean(related="company_id.enable_validate_state",
                                           string="Enable intermediate 'DIAN Validation' state",
                                           default=True, readonly=False)
    enable_mass_send_print = fields.Boolean(related="company_id.enable_mass_send_print",
                                            string="Automatic invoice email when validating (In production)",
                                            default=False, readonly=False)

    # Report
    report_custom_text = fields.Html(related="company_id.report_custom_text", string="Header text", readonly=False)
    footer_custom_text = fields.Html(related="company_id.footer_custom_text", string="Footer text", readonly=False)

    ei_include_pdf_attachment = fields.Boolean(related="company_id.ei_include_pdf_attachment",
                                               string="Include PDF attachment on electronic invoice email",
                                               default=True, readonly=False)

    # Enable/disable electronic invoicing for company
    ei_enable = fields.Boolean(related="company_id.ei_enable",
                               string="Enable electronic invoicing for this company", default=True, readonly=False)

    # Ignore email edi
    ei_ignore_edi_email_check = fields.Boolean(related="company_id.ei_ignore_edi_email_check",
                                               string="Ignore edi email check", default=False, readonly=False)

    # Update resolutions on Odoo database
    @api.model
    def action_update_resolutions(self):
        if not self.env.company.ei_enable:
            return {
                "name": _("Resolutions"),
                "type": "ir.actions.act_window",
                "res_model": "l10n_co_edi_jorels.resolution",
                "views": [[False, "tree"], [False, "form"]],
            }

        try:
            token = str(self.env.company.api_key)
            api_url = self.env['ir.config_parameter'].sudo().get_param('jorels.edipo.api_url',
                                                                       'https://edipo.jorels.com')
            params = {'token': token}
            header = {"accept": "application/json", "Content-Type": "application/json"}
            api_url = api_url + "/resolutions"
            response = requests.get(api_url,
                                    headers=header,
                                    params=params).json()
            _logger.debug('API Response: %s', response)

            if 'detail' in response:
                raise UserError(response['detail'])
            if 'message' in response:
                if response['message'] == 'Unauthenticated.' or response['message'] == '':
                    raise UserError(_('Unable to authenticate with the API. Please check your API key and try again.'))
                else:
                    raise UserError(response['message'])
            else:
                # Now create new resolutions
                for resolution in response:
                    if resolution['resolution_date']:
                        if int(resolution['resolution_date'].split('-')[0]) < 2000:
                            resolution['resolution_date'] = "'2000-01-01'"
                        else:
                            resolution['resolution_date'] = "'" + resolution['resolution_date'] + "'"
                    else:
                        resolution['resolution_date'] = 'NULL'

                    if resolution['date_from']:
                        if int(resolution['date_from'].split('-')[0]) < 2000:
                            resolution['date_from'] = "'2000-01-01'"
                        else:
                            resolution['date_from'] = "'" + resolution['date_from'] + "'"
                    else:
                        resolution['date_from'] = 'NULL'

                    if resolution['date_to']:
                        if int(resolution['date_to'].split('-')[0]) < 2000:
                            resolution['date_to'] = "'2000-01-01'"
                        else:
                            resolution['date_to'] = "'" + resolution['date_to'] + "'"
                    else:
                        resolution['date_to'] = 'NULL'

                    # Syncing Odoo with API
                    resolution_search = self.env['l10n_co_edi_jorels.resolution'].search([
                        ('resolution_id', '=', resolution['id'])
                    ])

                    # TO DO: Update with UPDATE if it already exists
                    # If it is not already in the database then add it
                    if not resolution_search:
                        self._cr.execute(
                            "INSERT INTO l10n_co_edi_jorels_resolution (" \
                            "resolution_api_sync," \
                            "resolution_type_document_id," \
                            "resolution_prefix," \
                            "resolution_resolution," \
                            "resolution_resolution_date," \
                            "resolution_technical_key," \
                            "resolution_from," \
                            "resolution_to," \
                            "resolution_date_from," \
                            "resolution_date_to," \
                            "resolution_id," \
                            "resolution_number," \
                            "resolution_next_consecutive," \
                            "company_id," \
                            "create_uid," \
                            "create_date," \
                            "write_uid," \
                            "write_date" \
                            ") VALUES (TRUE, %d, '%s', NULLIF('%s','None'), %s, NULLIF('%s','None'), %d, %d, %s, %s, %d, %d, '%s', %d, %d, %s, %d, %s)" %
                            (
                                resolution['type_document_id'],
                                resolution['prefix'],
                                resolution['resolution'],
                                resolution['resolution_date'],
                                resolution['technical_key'],
                                resolution['from'],
                                resolution['to'],
                                resolution['date_from'],
                                resolution['date_to'],
                                resolution['id'],
                                resolution['number'],
                                resolution['next_consecutive'],
                                self.env.company.id,
                                self.env.user.id,
                                'NOW()',
                                self.env.user.id,
                                'NOW()'
                            )
                        )
        except Exception as e:
            raise UserError(e)

        # To update or redirect to the resolutions views
        return {
            "name": _("Resolutions"),
            "type": "ir.actions.act_window",
            "res_model": "l10n_co_edi_jorels.resolution",
            "views": [[False, "tree"], [False, "form"]],
        }

    # Environment update
    def button_put_environment(self):
        if not self.env.company.ei_enable:
            return

        try:
            for rec in self:
                environment = 1 if rec.is_not_test else 2
                requests_data = {'code': environment}
                _logger.debug("Request environment DIAN: %s", json.dumps(requests_data, indent=2, sort_keys=False))

                token = rec.api_key
                api_url = self.env['ir.config_parameter'].sudo().get_param('jorels.edipo.api_url',
                                                                           'https://edipo.jorels.com')
                params = {'token': token}
                header = {"accept": "application/json", "Content-Type": "application/json"}
                api_url = api_url + "/environment"

                response = requests.put(api_url,
                                        json.dumps(requests_data),
                                        headers=header,
                                        params=params).json()
                _logger.debug('API Response PUT environment: %s', response)

                if 'detail' in response:
                    raise UserError(response['detail'])
                if 'message' in response:
                    # rec.env.user.notify_info(message=response['message'])
                    _logger.debug(response['message'])
                else:
                    # rec.env.user.notify_info(message=_("Now sync the resolutions"))
                    _logger.debug("Now sync the resolutions")
        except Exception as e:
            _logger.debug("Communication error: %s", e)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['is_not_test'] = self.env.company.is_not_test
        res['enable_validate_state'] = self.env.company.enable_validate_state
        res['enable_mass_send_print'] = self.env.company.enable_mass_send_print
        res['ei_include_pdf_attachment'] = self.env.company.ei_include_pdf_attachment
        res['ei_enable'] = self.env.company.ei_enable
        res['ei_always_validate'] = self.env.company.ei_always_validate
        res['ei_ignore_edi_email_check'] = self.env.company.ei_ignore_edi_email_check
        return res
