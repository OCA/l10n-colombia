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

from odoo import api, models

_logger = logging.getLogger(__name__)


class Message(models.Model):
    _inherit = 'mail.message'
    _description = 'Message'

    def search_invoice_events(self):
        for rec in self:
            email_from_search = re.search('<(.*)>', rec.email_from)
            if email_from_search:
                email_from = email_from_search.group(1)
            elif rec.email_from:
                email_from = rec.email_from
            else:
                email_from = ''

            if email_from:
                partner_rec = self.env['res.partner'].search([('email', '=', email_from)])
                if partner_rec:
                    cs = partner_rec.customer_software_id
                    move_id = cs.get_move_id(rec)
                    if move_id:
                        rec.res_id = move_id
                        rec.model = 'account.move'
                        invoice_rec = self.env[rec.model].search([('id', '=', rec.res_id)])[0]
                        if invoice_rec.event != 'acceptance':
                            invoice_rec.write({
                                'event': cs.get_invoice_event(rec)
                            })
                        else:
                            _logger.debug("The event status of the invoice cannot be changed")
                    else:
                        _logger.debug("Invoice ID does not exist in message ID: %s" % rec.message_id)
                else:
                    _logger.debug("It does not match the email of the contacts in the message ID: %s" % rec.message_id)
            else:
                _logger.debug("Not email from in message")
