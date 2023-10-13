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

import logging
import re

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    type_regime_id = fields.Many2one(comodel_name='l10n_co_edi_jorels.type_regimes', string="Regime type",
                                     ondelete='RESTRICT')
    type_liability_id = fields.Many2one(comodel_name='l10n_co_edi_jorels.type_liabilities',
                                        string="Liability type", ondelete='RESTRICT')
    merchant_registration = fields.Char(string="Merchant registration")
    municipality_id = fields.Many2one(comodel_name='l10n_co_edi_jorels.municipalities', string="Municipality",
                                      ondelete='RESTRICT')
    tax_resident_co = fields.Boolean(string="Tax resident in Colombia?", default=True)
    email_edi = fields.Char("Email for invoicing")

    trade_name = fields.Char(string="Trade name", copy=False)

    customer_software_id = fields.Many2one(comodel_name='l10n_co_edi_jorels.customer_software',
                                           string="Customer software", copy=False, ondelete='RESTRICT')
    type_document_identification_id = fields.Many2one(comodel_name="l10n_co_edi_jorels.type_document_identifications",
                                                      string="Type document identification", readonly=True,
                                                      compute='_compute_type_document_identification_id', store=True,
                                                      copy=False, ondelete='RESTRICT')
    # surname, second_surname, first_name, other_names
    surname = fields.Char("Surname", compute="_compute_names", store=True)
    second_surname = fields.Char("Second surname", compute="_compute_names", store=True)
    first_name = fields.Char("Name", compute="_compute_names", store=True)
    other_names = fields.Char("Other names", compute="_compute_names", store=True)

    # Postal fields
    postal_id = fields.Many2one(comodel_name='l10n_co_edi_jorels.postal', copy=True, string="Postal",
                                compute="_compute_postal_id", store=True)
    postal_department_id = fields.Many2one(comodel_name='l10n_co_edi_jorels.departments', copy=True,
                                           string="Postal department", compute="_compute_postal_id", store=True)
    postal_municipality_id = fields.Many2one(comodel_name='l10n_co_edi_jorels.municipalities', copy=True,
                                             string="Postal municipality", compute="_compute_postal_id", store=True)

    edi_sanitize_vat = fields.Char('Sanitized vat', compute='_compute_edi_sanitize_vat', store=True, readonly=True)

    @classmethod
    def _edi_sanitize_vat(cls, vat, type_document_identification_id):
        sanitize_vat = vat and re.sub(r'\W+', '', vat).upper() or False
        if sanitize_vat:
            if type_document_identification_id in (1, 2, 3, 4, 5, 6, 10):
                id_number = ''.join([i for i in sanitize_vat if i.isdigit()])
            else:
                id_number = sanitize_vat

            # If it is Nit remove the check digit
            if type_document_identification_id == 6:
                return id_number[:-1]
            else:
                return id_number
        else:
            return None

    @api.depends('vat', 'type_document_identification_id')
    def _compute_edi_sanitize_vat(self):
        """Sanitize vat in colombia for document type"""
        for rec in self:
            rec.edi_sanitize_vat = rec._edi_sanitize_vat(rec.vat, rec.type_document_identification_id.id)

    @api.depends('l10n_latam_identification_type_id')
    def _compute_type_document_identification_id(self):
        if not self.env['l10n_co_edi_jorels.type_document_identifications'].search_count([]):
            self.env['res.company'].init_csv_data('l10n_co_edi_jorels.l10n_co_edi_jorels.type_document_identifications')

        for rec in self:
            rec.type_document_identification_id = None
            if rec.l10n_latam_identification_type_id.l10n_co_document_code:
                values = {
                    'civil_registration': 1,
                    'id_card': 2,
                    'id_document': 3,
                    'national_citizen_id': 3,
                    'foreign_colombian_card': 4,
                    'foreign_resident_card': 5,
                    'rut': 6,
                    'passport': 7,
                    'foreign_id_card': 8,
                    'external_id': 9,
                    'niup_id': 10,
                    'residence_document': None,
                    'diplomatic_card': None,
                }
                if rec.l10n_latam_identification_type_id.l10n_co_document_code in values:
                    rec.type_document_identification_id = values[
                        rec.l10n_latam_identification_type_id.l10n_co_document_code]

    @api.depends('zip', 'country_id')
    def _compute_postal_id(self):
        for rec in self:
            if rec.zip and rec.country_id and rec.country_id.code == 'CO':
                postal_obj = rec.env['l10n_co_edi_jorels.postal']
                postal_search = postal_obj.sudo().search([('name', '=', rec.zip)])
                if postal_search:
                    rec.postal_id = postal_search[0].id
                    rec.postal_department_id = rec.env['l10n_co_edi_jorels.departments'].sudo().search(
                        [('code', '=', rec.postal_id.department_id.code)]
                    )[0].id
                    rec.postal_municipality_id = rec.env['l10n_co_edi_jorels.municipalities'].sudo().search(
                        [('code', '=', rec.postal_id.municipality_id.code)]
                    )[0].id
            else:
                rec.postal_id = None
                rec.postal_department_id = None
                rec.postal_municipality_id = None

    @api.depends('name', 'company_type')
    def _compute_names(self):
        for rec in self:
            if rec.name:
                rec.first_name = None
                rec.other_names = None
                rec.surname = None
                rec.second_surname = None

                if rec.is_company:
                    rec.first_name = rec.name
                else:
                    split_name = rec.name.split(',')
                    if len(split_name) > 1:
                        # Surnames
                        split_surname = split_name[0].split()
                        if len(split_surname) == 0 or len(split_surname) == 1:
                            rec.surname = split_surname[0]
                        elif len(split_surname) == 2:
                            rec.surname = split_surname[0]
                            rec.second_surname = split_surname[1]
                        else:
                            rec.surname = ' '.join(split_surname[0:-1])
                            rec.second_surname = ' '.join(split_surname[-1:])

                        # Names
                        split_names = split_name[1].split()
                        rec.first_name = split_names[0]
                        if len(split_names) > 1:
                            rec.other_names = ' '.join(split_names[1:])
                    else:
                        split_name = rec.name.split()
                        if len(split_name) == 0 or len(split_name) == 1:
                            rec.first_name = rec.name
                        elif len(split_name) == 2:
                            rec.first_name = split_name[0]
                            rec.surname = split_name[1]
                        elif len(split_name) == 3:
                            rec.first_name = split_name[0]
                            rec.surname = split_name[1]
                            rec.second_surname = split_name[2]
                        elif len(split_name) == 4:
                            rec.first_name = split_name[0]
                            rec.other_names = split_name[1]
                            rec.surname = split_name[2]
                            rec.second_surname = split_name[3]
                        else:
                            rec.first_name = split_name[0]
                            rec.other_names = split_name[1]
                            rec.surname = ' '.join(split_name[2:-1])
                            rec.second_surname = ' '.join(split_name[-1:])
