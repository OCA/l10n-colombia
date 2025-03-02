# -*- coding: utf-8 -*-
#
# Jorels S.A.S. - Copyright (2019-2022)
#
# This file is part of l10n_co_edi_jorels_pos.
#
# l10n_co_edi_jorels_pos is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# l10n_co_edi_jorels_pos is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with l10n_co_edi_jorels_pos.  If not, see <https://www.gnu.org/licenses/>.
#
# email: info@jorels.com
#

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class PosConfig(models.Model):
    _inherit = 'pos.config'

    def _default_electronic_invoice_journal(self):
        return self.env['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', self.env.company.id)],
                                                  limit=1)

    electronic_invoice_journal_id = fields.Many2one(
        'account.journal', string='Electronic Invoice Journal',
        domain=[('type', '=', 'sale')],
        help="Accounting journal used to create electronic invoices.",
        default=_default_electronic_invoice_journal)

    @api.constrains('company_id', 'electronic_invoice_journal_id')
    def _check_company_electronic_invoice_journal(self):
        for config in self:
            if config.electronic_invoice_journal_id \
                    and config.electronic_invoice_journal_id.company_id.id != config.company_id.id:
                raise ValidationError(
                    _("The electronic invoice journal and the point of sale %s must belong to its company.", config.name))

    @api.constrains('pricelist_id', 'use_pricelist', 'available_pricelist_ids', 'journal_id', 'invoice_journal_id',
                    'electronic_invoice_journal_id', 'payment_method_ids')
    def _check_currencies(self):
        super(PosConfig, self)._check_currencies()

        if self.electronic_invoice_journal_id.currency_id \
                and self.electronic_invoice_journal_id.currency_id.id != self.currency_id.id:
            raise ValidationError(
                _("The electronic invoice journal must be in the same currency as the Sales Journal or the company currency if that is not set."))

    def setup_defaults(self, company):
        super(PosConfig, self).setup_defaults(company)

        self.setup_electronic_invoice_journal(company)

    def setup_electronic_invoice_journal(self, company):
        for pos_config in self:
            electronic_invoice_journal_id = pos_config.electronic_invoice_journal_id or self.env[
                'account.journal'].search([('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1)
            if electronic_invoice_journal_id:
                pos_config.write({'electronic_invoice_journal_id': electronic_invoice_journal_id.id})
