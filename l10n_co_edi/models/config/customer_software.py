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

import re
import logging

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class CustomerSoftware(models.Model):
    _name = "l10n_co_edi_jorels.customer_software"
    _description = "Customer software"

    name = fields.Char(string="Name", required=True)

    # Custom receipt parameters
    receipt_event_field = fields.Selection([('subject', 'Subject'), ('body', 'Body')], "Field", default='subject',
                                           required=True)
    receipt_event_find = fields.Char("Contains")
    receipt_event_startswith = fields.Char("Starts with")
    receipt_event_endswith = fields.Char("Ends with")

    # Custom rejection parameters
    rejection_event_field = fields.Selection([('subject', 'Subject'), ('body', 'Body')], "Field", default='subject',
                                             required=True)
    rejection_event_find = fields.Char("Contains")
    rejection_event_startswith = fields.Char("Starts with")
    rejection_event_endswith = fields.Char("Ends with")

    # Custom acceptance parameters
    acceptance_event_field = fields.Selection([('subject', 'Subject'), ('body', 'Body')], "Field", default='subject',
                                              required=True)
    acceptance_event_find = fields.Char("Contains")
    acceptance_event_startswith = fields.Char("Starts with")
    acceptance_event_endswith = fields.Char("Ends with")

    # Custom number parameters
    number_field = fields.Selection([('subject', 'Subject'), ('body', 'Body')], "Field", default='subject',
                                    required=True)
    number_before = fields.Char("Before")
    number_after = fields.Char("After")

    def check_receipt(self, msg_dict):
        self.ensure_one()
        event_field = self.receipt_event_field
        ef = self.receipt_event_find if self.receipt_event_find else ''
        es = self.receipt_event_startswith if self.receipt_event_startswith else ''
        ee = self.receipt_event_endswith if self.receipt_event_endswith else ''
        return msg_dict[event_field].find(ef) != -1 \
               and msg_dict[event_field].startswith(es) != -1 \
               and msg_dict[event_field].endswith(ee) != -1

    def check_rejection(self, msg_dict):
        self.ensure_one()
        event_field = self.rejection_event_field
        ef = self.rejection_event_find if self.rejection_event_find else ''
        es = self.rejection_event_startswith if self.rejection_event_startswith else ''
        ee = self.rejection_event_endswith if self.rejection_event_endswith else ''
        return msg_dict[event_field].find(ef) != -1 \
               and msg_dict[event_field].startswith(es) != -1 \
               and msg_dict[event_field].endswith(ee) != -11

    def check_acceptance(self, msg_dict):
        self.ensure_one()
        event_field = self.acceptance_event_field
        ef = self.acceptance_event_find if self.acceptance_event_find else ''
        es = self.acceptance_event_startswith if self.acceptance_event_startswith else ''
        ee = self.acceptance_event_endswith if self.acceptance_event_endswith else ''
        return msg_dict[event_field].find(ef) != -1 \
               and msg_dict[event_field].startswith(es) != -1 \
               and msg_dict[event_field].endswith(ee) != -11

    def get_invoice_event(self, msg_dict):
        self.ensure_one()
        if self.check_receipt(msg_dict):
            return 'receipt'
        elif self.check_rejection(msg_dict):
            return 'rejection'
        elif self.check_acceptance(msg_dict):
            return 'acceptance'
        else:
            return 'none'

    def get_move_id(self, mail_message):
        """Return move_id from mail message"""
        self.ensure_one()

        try:
            number_before = self.number_before if self.number_before else ''
            number_after = self.number_after if self.number_after else ''
            search_text = mail_message.subject if self.number_field == 'subject' else mail_message.body
            result = re.search(number_before + '(.*)' + number_after, search_text).group(1)
            for res in result.split(" "):
                if res:
                    invoice_number = res
                    invoice_rec = self.env['account.move'].search([('number_formatted', '=', invoice_number)])[0]
                    return invoice_rec.id
        except AttributeError:
            _logger.debug("The invoice number does not match in the search")
        except IndexError:
            _logger.debug("There are no existing invoice numbers")

        return False
