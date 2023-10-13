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

from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    edi_tax_id = fields.Many2one('l10n_co_edi_jorels.taxes', string="Tax type (DIAN)", ondelete='RESTRICT', copy=True)

    dian_report_tax_base = fields.Selection([
        ('auto', 'Auto'),
        ('no_report', 'Not reporting the taxable base to the DIAN')
    ], string="Taxable base (DIAN)", default='auto', copy=True)
