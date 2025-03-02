# -*- coding: utf-8 -*-
#
# Jorels S.A.S. - Copyright (2019-2022)
#
# This file is part of l10n_co_ciius.
#
# l10n_co_ciius is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# l10n_co_ciius is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with l10n_co_ciius.  If not, see <https://www.gnu.org/licenses/>.
#
# email: info@jorels.com
#

import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class Ciiu(models.Model):
    _name = "l10n_co_ciius.ciiu"
    _description = "CIIU"
    _rec_name = "code"

    name = fields.Char('Name', required=True, readonly=True)
    code = fields.Char('Code', required=True, readonly=True)
    section_id = fields.Many2one(comodel_name='l10n_co_ciius.ciiu_section', string='Section', required=True,
                                 readonly=True)
    division_id = fields.Many2one(comodel_name='l10n_co_ciius.ciiu_division', string='Division', required=True,
                                  readonly=True)
    subdivision_id = fields.Many2one(comodel_name='l10n_co_ciius.ciiu_subdivision', string="Subdivision", required=True,
                                     readonly=True)
