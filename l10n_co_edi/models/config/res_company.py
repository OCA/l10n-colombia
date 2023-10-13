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
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    type_document_identification_id = fields.Many2one(comodel_name='l10n_co_edi_jorels.type_document_identifications',
                                                      compute='_compute_edi',
                                                      inverse="_inverse_type_document_identification_id",
                                                      string="Identification document type")
    type_organization_id = fields.Many2one(comodel_name='l10n_co_edi_jorels.type_organizations', compute='_compute_edi',
                                           inverse="_inverse_type_organization_id", string="Organization type")
    type_regime_id = fields.Many2one('l10n_co_edi_jorels.type_regimes', compute='_compute_edi',
                                     inverse="_inverse_type_regime_id", string="Regime type")
    type_liability_id = fields.Many2one('l10n_co_edi_jorels.type_liabilities', compute='_compute_edi',
                                        inverse="_inverse_type_liability_id", string="Liability type")
    ei_operation = fields.Selection([
        ('aiu', 'AIU'),
        ('standard', 'Standard'),
        ('mandates', 'Mandates'),
        ('transport', 'Transport'),
        ('exchange', 'Exchange')
    ], string="Operation type", default='standard', required=True)
    business_name = fields.Char(string="Company name to invoice")
    merchant_registration = fields.Char(string="Merchant registration", compute='_compute_merchant_registration',
                                        store=True)
    municipality_id = fields.Many2one('l10n_co_edi_jorels.municipalities', compute='_compute_edi',
                                      inverse="_inverse_municipality_id", string="Municipality")
    trade_name = fields.Char(related='partner_id.trade_name', store=True, readonly=False)

    # Electronic invoice sender Mail
    email_edi = fields.Char(related='partner_id.email_edi', store=True, readonly=False)
    email_edi_formatted = fields.Char('Formatted Email Edi', compute='_compute_email_edi_formatted',
                                      help='Format email edi address "Name <email_edi@domain>"')

    vat_formatted = fields.Char(string="Formatted Tax ID", compute="_compute_vat_formatted")

    # address -> street
    # phone -> phone
    # email -> email

    # Api key
    api_key = fields.Char(string="Api key")

    ei_always_validate = fields.Boolean(string="Always validate invoices", default=False)

    # Test
    is_not_test = fields.Boolean(string="Production environment", default=False)
    test_set_id = fields.Char(string="TestSetId")
    enable_validate_state = fields.Boolean(string="Enable intermediate 'DIAN Validation' state",
                                           default=True)
    enable_mass_send_print = fields.Boolean(string="Automatic invoice email when validating (In production)",
                                            default=False)

    # Report
    report_custom_text = fields.Html(string="Header text")
    footer_custom_text = fields.Html(string="Footer text")

    ei_include_pdf_attachment = fields.Boolean(string="Include PDF attachment on electronic invoice email",
                                               default=True)

    # Enable/disable electronic invoicing for company
    ei_enable = fields.Boolean(string="Enable electronic invoicing for this company", default=True)

    # Ignore email edi
    ei_ignore_edi_email_check = fields.Boolean(string="Ignore edi email check", default=False)

    def _compute_vat_formatted(self):
        for rec in self:
            type_document_identification_id = self.get_type_document_identification_id()
            if type_document_identification_id:
                if rec.vat:
                    identification_number_general = ''.join([i for i in rec.partner_id.vat if i.isdigit()])
                    # If it is Nit remove the check digit
                    if type_document_identification_id == 6:
                        rec.vat_formatted = identification_number_general[:-1]
                    else:
                        rec.vat_formatted = identification_number_general
                else:
                    rec.vat_formatted = ''
            else:
                rec.vat_formatted = ''

    @api.depends('name', 'email_edi')
    def _compute_email_edi_formatted(self):
        for partner in self:
            if partner.email_edi:
                partner.email_edi_formatted = tools.formataddr(
                    ((partner.name + _(' - Electronic invoicing')) or u"False", partner.email_edi or u"False"))
            else:
                partner.email_edi_formatted = ''

    def get_l10n_co_document_code(self):
        for rec in self.filtered(lambda company: company.partner_id):
            l10n_co_document_code = None
            if rec.type_document_identification_id.id:
                values = {
                    1: 'civil_registration',
                    2: 'id_card',
                    3: 'id_document',
                    4: 'residence_document',
                    5: 'foreign_id_card',
                    6: 'rut',
                    7: 'passport',
                    8: 'external_id',
                    9: 'external_id',
                    10: 'id_document'
                }
                l10n_co_document_code = values[rec.type_document_identification_id.id]

            return l10n_co_document_code

    def get_company_type(self):
        for rec in self.filtered(lambda company: company.partner_id):
            company_type = None
            if rec.type_organization_id.id:
                values = {
                    1: 'company',
                    2: 'person'
                }
                company_type = values[rec.type_organization_id.id]

            return company_type

    def get_type_document_identification_id(self):
        for rec in self:
            document_type = rec.partner_id.l10n_latam_identification_type_id.l10n_co_document_code
            if document_type:
                values = {
                    'civil_registration': 1,
                    'id_card': 2,
                    'id_document': 3,
                    'national_citizen_id': 3,
                    'residence_document': 4,
                    'foreign_id_card': 5,
                    'rut': 6,
                    'passport': 7,
                    'external_id': 8,
                    'diplomatic_card': 0,
                }
                document_type_id = values[document_type]
                if 1 <= document_type_id <= 8:
                    return document_type_id
            return None

    def get_type_organization_id(self):
        for rec in self:
            company_type = rec.partner_id.company_type
            values = {
                'person': 2,
                'company': 1
            }
            return values[company_type]

    def _compute_edi(self):
        for company in self.filtered(lambda company_rec: company_rec.partner_id):
            type_document_identification_id = self.get_type_document_identification_id()
            type_organization_id = self.get_type_organization_id()
            type_regime_id = company.partner_id.type_regime_id
            type_liability_id = company.partner_id.type_liability_id
            municipality_id = company.partner_id.municipality_id
            company.update({
                'type_regime_id': type_regime_id,
                'type_liability_id': type_liability_id,
                'municipality_id': municipality_id,
                'type_document_identification_id': type_document_identification_id,
                'type_organization_id': type_organization_id
            })

    def _inverse_type_regime_id(self):
        for company in self:
            company.partner_id.type_regime_id = company.type_regime_id

    def _inverse_type_liability_id(self):
        for company in self:
            company.partner_id.type_liability_id = company.type_liability_id

    def _inverse_municipality_id(self):
        for company in self:
            company.partner_id.municipality_id = company.municipality_id

    def _inverse_type_document_identification_id(self):
        for company in self:
            l10n_co_document_code = self.get_l10n_co_document_code()
            l10n_latam_identification_type_rec = self.env['l10n_latam.identification.type'].search(
                [('l10n_co_document_code', '=', l10n_co_document_code)]
            )[0]
            company.partner_id.l10n_latam_identification_type_id = l10n_latam_identification_type_rec.id

    def _inverse_type_organization_id(self):
        for company in self:
            company.partner_id.company_type = self.get_company_type()

    @api.depends('company_registry')
    def _compute_merchant_registration(self):
        for rec in self:
            rec.merchant_registration = rec.company_registry

    # Environment update
    def update_environment(self, environment):
        if not self.env.company.ei_enable:
            return False

        for rec in self:
            success = False
            try:
                requests_data = {
                    'code': environment
                }
                _logger.debug("Request environment DIAN: %s",
                              json.dumps(requests_data, indent=2, sort_keys=False))

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

                response = requests.get(api_url,
                                        headers=header,
                                        params=params).json()
                _logger.debug('API Response GET environment: %s', response)

                if 'type_environment_id' in response:
                    if environment == response['type_environment_id']:
                        # rec.env.user.notify_info(message=_("The environment has been updated. Sync the resolutions"))
                        _logger.debug("The environment has been updated. Sync the resolutions")
                        success = True

                if 'message' in response:
                    # rec.env.user.notify_info(message=response['message'])
                    _logger.debug(response['message'])

            except Exception as e:
                _logger.debug("Communication error: %s", e)

            return success

    def write(self, vals):
        for rec in self:
            if 'is_not_test' in vals:
                if vals['is_not_test'] != rec.is_not_test:
                    environment = 1 if vals['is_not_test'] else 2
                    if not self.update_environment(environment):
                        vals['is_not_test'] = not vals['is_not_test']

        return super(ResCompany, self).write(vals)
