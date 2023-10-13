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


class Radian(models.Model):
    _name = "l10n_co_edi_jorels.radian"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Radian events"

    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ], string='Status', required=True, readonly=True, copy=False, tracking=True, default='draft')
    date = fields.Date("Date", required=True, readonly=True, default=fields.Date.context_today, copy=False)
    event_id = fields.Many2one(comodel_name="l10n_co_edi_jorels.events", string="Event", required=True, readonly=True,
                               tracking=True, ondelete='RESTRICT', states={'draft': [('readonly', False)]},
                               domain=[('code', 'in', ('030', '031', '032', '033', '034'))])
    name = fields.Char(string="Reference", compute="_compute_name", store=True, copy=False, readonly=True,
                       default=lambda self: _("New"))
    number = fields.Integer(string="Number", readonly=True, states={'draft': [('readonly', False)]}, tracking=True,
                            copy=False)
    prefix = fields.Char(string="Prefix", readonly=True, states={'draft': [('readonly', False)]}, tracking=True,
                         copy=False)
    note = fields.Text(string="Note", readonly=True, states={'draft': [('readonly', False)]})
    rejection_concept_id = fields.Many2one(comodel_name="l10n_co_edi_jorels.rejection_concepts",
                                           string="Rejection concept", required=False, readonly=True,
                                           ondelete='RESTRICT', states={'draft': [('readonly', False)]}, tracking=True,
                                           copy=False)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, copy=False,
                                 default=lambda self: self.env.company,
                                 states={'draft': [('readonly', False)]})
    move_id = fields.Many2one(comodel_name="account.move", string="Invoice", required=True, readonly=True,
                              states={'draft': [('readonly', False)]}, copy=True,
                              domain=[('move_type', 'in', ('in_invoice', 'in_refund', 'out_invoice', 'out_refund'))],
                              tracking=True)

    # Storing synchronous and production modes
    edi_sync = fields.Boolean(string="Sync", copy=False, readonly=True,
                              default=lambda self: self.env.company.is_not_test, store=True,
                              compute="_compute_edi_is_not_test")
    edi_is_not_test = fields.Boolean(string="In production", copy=False, readonly=True,
                                     default=lambda self: self.env.company.is_not_test, store=True,
                                     compute="_compute_edi_is_not_test")

    # Edi response fields
    edi_is_valid = fields.Boolean("Is valid?", copy=False, readonly=True, states={'draft': [('readonly', False)]})
    edi_is_restored = fields.Boolean("Is restored?", copy=False, readonly=True)
    edi_algorithm = fields.Char("Algorithm", copy=False, readonly=True)
    edi_class = fields.Char("Class", copy=False, readonly=True)
    edi_number = fields.Char("Number", copy=False, readonly=True)
    edi_uuid = fields.Char("UUID", copy=False, readonly=True, states={'draft': [('readonly', False)]})
    edi_issue_date = fields.Date("Date", copy=False, readonly=True, states={'draft': [('readonly', False)]})
    edi_expedition_date = fields.Char("Expedition date", copy=False, readonly=True)
    edi_zip_key = fields.Char("Zip key", copy=False, readonly=True, states={'draft': [('readonly', False)]})
    edi_status_code = fields.Char("Status code", copy=False, readonly=True)
    edi_status_description = fields.Char("Status description", copy=False, readonly=True)
    edi_status_message = fields.Char("Status message", copy=False, readonly=True)
    edi_errors_messages = fields.Char("Error messages", copy=False, readonly=True)
    edi_xml_name = fields.Char("XML name", copy=False, readonly=True)
    edi_zip_name = fields.Char("Zip name", copy=False, readonly=True)
    edi_signature = fields.Char("Signature", copy=False, readonly=True)
    edi_qr_code = fields.Char("QR code", copy=False, readonly=True)
    edi_qr_data = fields.Char("QR data", copy=False, readonly=True)
    edi_qr_link = fields.Char("QR link", copy=False, readonly=True)
    edi_pdf_download_link = fields.Char("PDF link", copy=False, readonly=True)
    edi_xml_base64 = fields.Binary("XML", copy=False, readonly=True)
    edi_application_response_base64 = fields.Binary("Application response", copy=False, readonly=True)
    edi_attached_document_base64 = fields.Binary("Attached document", copy=False, readonly=True,
                                                 states={'draft': [('readonly', False)]})
    edi_pdf_base64 = fields.Binary("PDF", copy=False, readonly=True, states={'draft': [('readonly', False)]})
    edi_zip_base64 = fields.Binary("Zip document", copy=False, readonly=True)
    edi_type_environment = fields.Many2one(comodel_name="l10n_co_edi_jorels.type_environments",
                                           string="Type environment", copy=False, readonly=True,
                                           states={'draft': [('readonly', False)]},
                                           default=lambda self: self._default_edi_type_environment())
    edi_payload = fields.Text("Payload", copy=False, readonly=True)

    # For mail attached
    edi_attached_zip_base64 = fields.Binary('Attached zip', attachment=True, copy=False, readonly=True,
                                            states={'draft': [('readonly', False)]})

    user_id = fields.Many2one('res.users', string='Salesperson', tracking=True,
                              readonly=True, states={'draft': [('readonly', False)]},
                              default=lambda self: self.env.user, copy=False)

    type = fields.Selection([
        ('customer', 'Customer Event'),
        ('supplier', 'Supplier Event'),
    ], readonly=True, states={'draft': [('readonly', False)]}, index=True, change_default=True,
        default=lambda self: self._context.get('type', 'customer'), tracking=True)

    def dian_preview(self):
        for rec in self:
            if rec.move_id.ei_uuid:
                return {
                    'type': 'ir.actions.act_url',
                    'target': 'new',
                    'url': 'https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey=' + rec.move_id.ei_uuid,
                }

    def _send_email(self):
        for rec in self:
            mail_template = rec.env.ref('l10n_co_edi_jorels.email_template_radian', False)
            ctx = dict(active_model='l10n_co_edi_jorels.radian')
            if mail_template:
                mail_template.with_context(ctx).send_mail(res_id=rec.id, force_send=True,
                                                          email_layout_xmlid='mail.mail_notification_light')
        return True

    def action_send_email(self):
        self.ensure_one()
        mail_template = self.env.ref('l10n_co_edi_jorels.email_template_radian', False)
        ctx = dict(
            default_model='l10n_co_edi_jorels.radian',
            mail_post_autofollow=True,
            default_composition_mode='comment',
            default_use_template=bool(mail_template),
            default_res_id=self.id,
            default_template_id=mail_template and mail_template.id or False,
            force_email=True,
            default_email_layout_xmlid="mail.mail_notification_light",
        )
        return {
            'type': 'ir.actions.act_window',
            'name': _('Send Radian Event by Email'),
            'res_model': 'mail.compose.message',
            'src_model': 'l10n_co_edi_jorels.radian',
            'view_mode': 'form',
            'target': 'new',
            'view_type': 'form',
            'views': [(False, 'form')],
            'view_id': False,
            'context': ctx,
        }

    def _default_edi_type_environment(self):
        if not self.env['l10n_co_edi_jorels.type_environments'].search_count([]):
            self.env['res.company'].init_csv_data('l10n_co_edi_jorels.l10n_co_edi_jorels.type_environments')
        return 1 if self.env.company.is_not_test else 2

    @api.depends("edi_type_environment")
    def _compute_edi_is_not_test(self):
        for rec in self:
            if rec.edi_type_environment:
                rec.edi_is_not_test = (rec.edi_type_environment.id == 1)
            else:
                rec.edi_is_not_test = rec.company_id.is_not_test
            rec.edi_sync = rec.edi_is_not_test

    @api.depends("prefix", "number")
    def _compute_name(self):
        for rec in self:
            if rec.prefix and rec.number:
                rec.name = rec.prefix + str(rec.number)
            else:
                rec.name = _("New")

    def write_response(self, response, payload):
        for rec in self:
            rec.edi_is_valid = response['is_valid']
            rec.edi_is_restored = response['is_restored']
            rec.edi_algorithm = response['algorithm']
            rec.edi_class = response['class']
            rec.edi_number = response['number']
            rec.edi_uuid = response['uuid']
            rec.edi_issue_date = response['issue_date']
            rec.edi_expedition_date = response['expedition_date']
            rec.edi_zip_key = response['zip_key']
            rec.edi_status_code = response['status_code']
            rec.edi_status_description = response['status_description']
            rec.edi_status_message = response['status_message']
            rec.edi_errors_messages = str(response['errors_messages'])
            rec.edi_xml_name = response['xml_name']
            rec.edi_zip_name = response['zip_name']
            rec.edi_signature = response['signature']
            rec.edi_qr_code = response['qr_code']
            rec.edi_qr_data = response['qr_data']
            rec.edi_qr_link = response['qr_link']
            rec.edi_pdf_download_link = response['pdf_download_link']
            rec.edi_xml_base64 = response['xml_base64_bytes']
            rec.edi_application_response_base64 = response['application_response_base64_bytes']
            rec.edi_attached_document_base64 = response['attached_document_base64_bytes']
            rec.edi_pdf_base64 = response['pdf_base64_bytes']
            rec.edi_zip_base64 = response['zip_base64_bytes']
            rec.edi_type_environment = response['type_environment_id']
            rec.edi_payload = payload

    def action_post(self):
        for rec in self:
            if rec.state != 'draft':
                continue

            if rec.type == 'customer' and rec.move_id.move_type not in ('out_invoice', 'out_refund'):
                raise UserError(_("The invoice must be a sales invoice"))
            if rec.type == 'supplier' and rec.move_id.move_type not in ('in_invoice', 'in_refund'):
                raise UserError(_("The invoice must be a purchase invoice"))

            # Sequence
            name_sequence = "radian_" + rec.event_id.code + "_" + rec.type
            seq_search = self.env['ir.sequence'].search([
                ('code', '=', name_sequence),
                ('company_id', '=', rec.company_id.id)
            ])
            if not seq_search:
                seq_search = self.env['ir.sequence'].search([('code', '=', name_sequence)])

            prefix, suffix = seq_search[0]._get_prefix_suffix()

            if not rec.name or rec.name in ('New', _('New')):
                rec.name = seq_search[0].with_context(force_company=rec.company_id.id).next_by_code(name_sequence)

            if rec.name and rec.name not in ('New', _('New')) and rec.name[0:len(prefix)] == prefix:
                rec.number = ''.join([i for i in rec.name[len(prefix):] if i.isdigit()])
                rec.prefix = prefix
            else:
                raise UserError(_("The DIAN event sequence is wrong."))

            # Posted
            rec.write({'state': 'posted'})

            if not rec.company_id.enable_validate_state:
                rec.validate_dian()

        return True

    def action_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})
        return True

    def action_cancel(self):
        for rec in self:
            rec.write({'state': 'cancel'})
        return True

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel'):
                raise UserError(_('You cannot delete an event which is not draft or cancelled.'))
            elif rec.name and rec.name not in ('New', _('New')):
                raise UserError(_('You cannot delete an event after it has been posted (and received a number). '
                                  'You can set it back to "Draft" state and modify its content, then re-confirm it.'))
        return super(Radian, self).unlink()

    def get_json_request(self):
        for rec in self:
            if rec.event_id.code == '031' and not rec.rejection_concept_id:
                raise UserError(_("The rejection concept is required for the DIAN claim event."))
            if not rec.move_id.ei_uuid:
                raise UserError(_("The invoice UUID (CUFE) is required for DIAN events."))
            if not rec.user_id.type_document_identification_id:
                raise UserError(_("The document type for user is required for DIAN events."))
            if not rec.user_id.vat:
                raise UserError(_("The document number (VAT) for user is required for DIAN events."))
            if not rec.user_id.first_name:
                raise UserError(_("The user first name is required for DIAN events"))
            if not rec.user_id.surname:
                raise UserError(_("The user surname is required for DIAN events"))
            if not rec.number or not rec.prefix:
                raise UserError(_("The number and prefix are required for DIAN events"))
            if not rec.user_id or not rec.user_id.function:
                raise UserError(_("The user and his/her job title (function) is required for DIAN events"))

            json_request = {
                "prefix": rec.prefix,
                "number": rec.number,
                "sync": rec.company_id.is_not_test,
                "uuid": rec.move_id.ei_uuid,
                "person": {
                    "id_code": rec.user_id.type_document_identification_id.id,
                    "id_number": ''.join([i for i in rec.user_id.vat if i.isdigit()]),
                    "first_name": rec.user_id.first_name,
                    "surname": rec.user_id.surname,
                    "job_title": rec.user_id.function,
                    "country_code": 46,
                    "company_department": "Contabilidad"
                },
            }

            if rec.event_id.code == '031' and rec.rejection_concept_id:
                json_request['rejection_code'] = rec.rejection_concept_id.id

            # Notes
            if rec.note:
                notes = [{
                    "text": rec.note
                }]
                json_request['notes'] = notes

        return json_request

    def validate_dian(self):
        for rec in self:
            if rec.state != 'posted':
                continue

            # TODO: Validate in order, to avoid conflicts
            if rec.company_id.ei_enable and not rec.edi_is_valid and (
                    (rec.type == 'supplier' and rec.event_id.code in ('030', '031', '032', '033')) or \
                    (rec.type == 'customer' and rec.event_id.code == '034')
            ):
                rec.validate_dian_generic()
                if rec.edi_is_valid and rec.edi_uuid:
                    rec._send_email()

    def validate_dian_generic(self):
        for rec in self:
            try:
                if not rec.company_id.ei_enable:
                    continue

                requests_data = rec.get_json_request()

                # Payload
                payload = json.dumps(requests_data, indent=2, sort_keys=False)

                # API key and URL
                if rec.company_id.api_key:
                    token = rec.company_id.api_key
                else:
                    raise UserError(_("You must configure a token"))

                api_url = self.env['ir.config_parameter'].sudo().get_param('jorels.edipo.api_url',
                                                                           'https://edipo.jorels.com')
                params = {
                    'token': token,
                    'code': rec.event_id.code
                }
                header = {"accept": "application/json", "Content-Type": "application/json"}

                # Request
                api_url = api_url + "/basic_event"

                rec.edi_is_not_test = rec.company_id.is_not_test

                if not rec.edi_is_not_test:
                    if rec.company_id.test_set_id:
                        params['test_set_id'] = rec.company_id.test_set_id
                    else:
                        raise UserError(_("You have not configured a 'TestSetId'."))

                _logger.debug('API URL: %s', api_url)
                _logger.debug("DIAN Validation Request: %s", json.dumps(requests_data, indent=2, sort_keys=False))
                # raise Warning(json.dumps(requests_data, indent=2, sort_keys=False))

                num_attemps = int(self.env['ir.config_parameter'].sudo().get_param('jorels.edipo.num_attemps', '2'))
                if not rec.edi_is_not_test:
                    num_attemps = 1

                for i in range(num_attemps):
                    try:
                        response = requests.post(api_url,
                                                 json.dumps(requests_data),
                                                 headers=header,
                                                 params=params).json()
                    except Exception as e:
                        _logger.warning("Invalid response: %s", e)

                    _logger.debug('API Response: %s', response)

                    if 'is_valid' in response and response['is_valid']:
                        break

                if 'detail' in response:
                    raise UserError(response['detail'])
                if 'message' in response:
                    if response['message'] == 'Unauthenticated.' or response['message'] == '':
                        raise UserError(_("Authentication error with the API"))
                    else:
                        if 'errors' in response:
                            raise UserError(response['message'] + '/ errors: ' + str(response['errors']))
                        else:
                            raise UserError(response['message'])
                elif 'is_valid' in response:
                    rec.write_response(response, payload)
                    if response['is_valid']:
                        # self.env.user.notify_success(message=_("The validation at DIAN has been successful."))
                        _logger.debug("The validation at DIAN has been successful.")
                    elif 'zip_key' in response:
                        if response['zip_key'] is not None:
                            if not rec.edi_is_not_test:
                                # self.env.user.notify_success(message=_("Document sent to DIAN in habilitation."))
                                _logger.debug("Document sent to DIAN in habilitation.")
                            else:
                                temp_message = {rec.edi_status_message, rec.edi_errors_messages,
                                                rec.edi_status_description, rec.edi_status_code}
                                raise UserError(str(temp_message))
                        else:
                            raise UserError(_('A valid Zip key was not obtained. Try again.'))
                    else:
                        raise UserError(_('The document could not be validated in DIAN.'))
                else:
                    raise UserError(_("No logical response was obtained from the API."))
            except Exception as e:
                _logger.debug("Failed to process the request for document: %s: %s", (rec.name, e))
                if not rec.company_id.ei_always_validate:
                    raise UserError(_("Failed to process the request for document: %s: %s") % (rec.name, e))
                else:
                    rec.message_post(body=_("DIAN Electronic invoicing: "
                                            "Failed to process the request for document: %s: %s") % (rec.name, e))

    def status_zip(self):
        for rec in self:
            try:
                if not rec.company_id.ei_enable:
                    continue

                # This line ensures that the fields are updated in Odoo, before the request
                payload = json.dumps(rec.get_json_request(), indent=2, sort_keys=False)

                _logger.debug('Payload: %s', payload)

                if rec.edi_zip_key or rec.edi_uuid:
                    requests_data = {}
                    _logger.debug('API Requests: %s', requests_data)

                    # API key and URL
                    if rec.company_id.api_key:
                        token = rec.company_id.api_key
                    else:
                        raise UserError(_("You must configure a token"))

                    api_url = self.env['ir.config_parameter'].sudo().get_param('jorels.edipo.api_url',
                                                                               'https://edipo.jorels.com')
                    params = {
                        'token': token,
                        'environment': rec.edi_type_environment.id
                    }
                    header = {"accept": "application/json", "Content-Type": "application/json"}

                    # Request
                    if rec.edi_zip_key:
                        api_url = api_url + "/zip/" + rec.edi_zip_key
                    else:
                        api_url = api_url + "/document/" + rec.edi_uuid

                    _logger.debug('API URL: %s', api_url)

                    response = requests.post(api_url,
                                             json.dumps(requests_data),
                                             headers=header,
                                             params=params).json()
                    _logger.debug('API Response: %s', response)

                    if 'detail' in response:
                        raise UserError(response['detail'])
                    if 'message' in response:
                        if response['message'] == 'Unauthenticated.' or response['message'] == '':
                            raise UserError(_("Authentication error with the API"))
                        else:
                            if 'errors' in response:
                                raise UserError(response['message'] + '/ errors: ' + str(response['errors']))
                            else:
                                raise UserError(response['message'])
                    elif 'is_valid' in response:
                        rec.write_response(response, payload)
                        if response['is_valid']:
                            # self.env.user.notify_success(message=_("The validation at DIAN has been successful."))
                            _logger.debug("The validation at DIAN has been successful.")
                        elif 'zip_key' in response or 'uuid' in response:
                            if response['zip_key'] is not None or response['uuid'] is not None:
                                if not rec.edi_is_not_test:
                                    # self.env.user.notify_success(message=_("Document sent to DIAN in testing."))
                                    _logger.debug("Document sent to DIAN in testing.")
                                else:
                                    temp_message = {rec.edi_status_message, rec.edi_errors_messages,
                                                    rec.edi_status_description, rec.edi_status_code}
                                    raise UserError(str(temp_message))
                            else:
                                raise UserError(_('A valid Zip key or UUID was not obtained. Try again.'))
                        else:
                            raise UserError(_('The document could not be validated in DIAN.'))
                    else:
                        raise UserError(_("No logical response was obtained from the API."))
                else:
                    raise UserError(_("A zip key or UUID is required to check the status of the document."))

            except Exception as e:
                _logger.debug("Failed to process the request: %s", e)
                raise UserError(_("Failed to process the request: %s") % e)

    def button_open_form_current(self):
        view = self.env.ref('l10n_co_edi_jorels.view_l10n_co_edi_jorels_radian_form')
        context = self.env.context
        rec_id = 0
        for rec in self:
            rec_id = rec.id

        return {
            'name': _('Radian events'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'l10n_co_edi_jorels.radian',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'current',
            'res_id': rec_id,
            'context': context,
        }
