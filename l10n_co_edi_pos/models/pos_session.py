# -*- coding: utf-8 -*-
#
#   Jorels S.A.S. - Copyright (C) 2019-2023
#
#   This file is part of l10n_co_edi_jorels_pos.
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Lesser General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public License
#   along with this program. If not, see <https://www.gnu.org/licenses/>.
#
#   email: info@jorels.com
#


import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        result = super()._pos_ui_models_to_load()

        result.append('l10n_co_edi_jorels.type_regimes')
        result.append('l10n_co_edi_jorels.type_liabilities')
        result.append('l10n_co_edi_jorels.municipalities')
        result.append('l10n_latam.identification.type')

        return result

    def _loader_params_l10n_co_edi_jorels_type_regimes(self):
        return {
            'search_params': {
                'fields': ['name'],
            },
        }

    def _loader_params_l10n_co_edi_jorels_type_liabilities(self):
        return {
            'search_params': {
                'fields': ['name'],
            },
        }

    def _loader_params_l10n_co_edi_jorels_municipalities(self):
        return {
            'search_params': {
                'fields': ['name'],
            },
        }

    def _loader_params_l10n_latam_identification_type(self):
        return {
            'search_params': {
                'fields': ['name', 'l10n_co_document_code'],
            },
        }

    def _loader_params_res_partner(self):
        result = super(PosSession, self)._loader_params_res_partner()

        result['search_params']['fields'].append('company_type')
        result['search_params']['fields'].append('l10n_latam_identification_type_id')
        result['search_params']['fields'].append('type_regime_id')
        result['search_params']['fields'].append('type_liability_id')
        result['search_params']['fields'].append('municipality_id')
        result['search_params']['fields'].append('email_edi')

        return result

    def _loader_params_res_company(self):
        result = super(PosSession, self)._loader_params_res_company()

        result['search_params']['fields'].append('municipality_id')
        result['search_params']['fields'].append('city')

        return result

    def _get_pos_ui_l10n_co_edi_jorels_type_regimes(self, params):
        return self.env['l10n_co_edi_jorels.type_regimes'].search_read(**params['search_params'])

    def _get_pos_ui_l10n_co_edi_jorels_type_liabilities(self, params):
        return self.env['l10n_co_edi_jorels.type_liabilities'].search_read(**params['search_params'])

    def _get_pos_ui_l10n_co_edi_jorels_municipalities(self, params):
        return self.env['l10n_co_edi_jorels.municipalities'].search_read(**params['search_params'])

    def _get_pos_ui_l10n_latam_identification_type(self, params):
        return self.env['l10n_latam.identification.type'].search_read(**params['search_params'])

    # def _get_pos_ui_res_partner(self, params):
    #     result = super(PosSession, self)._get_pos_ui_res_partner()
    #     return self.env['res.partner'].with_context(**params['context']).search_read(**params['search_params'])

    # def _get_pos_ui_res_company(self, params):
    #     return self.env['res.company'].with_context(**params['context']).search_read(**params['search_params'])
