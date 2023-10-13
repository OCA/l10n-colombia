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

{
    'name': "Facturación electrónica DIAN para Colombia por Jorels SAS",
    'summary': 'Facturación electrónica DIAN para Colombia por Jorels SAS',
    'description': "Electronic invoicing management for companies in Colombia",
    'author': "Jorels SAS",
    'license': "LGPL-3",
    'category': 'Invoicing & Payments',
    'version': '16.0.22.08.03.14.10',
    'website': "https://www.jorels.com",
    'images': ['static/images/main_screenshot.png'],
    'support': 'info@jorels.com',

    # Odoo, OCA and Jorels dependencies
    'depends': [
        'account',
        'l10n_co',
        # 'web_notify',
        'update_from_csv',
        'account_debit_note',
        'base_vat',
        # 'universal_discount'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/data.xml',
        'views/config/res_company.xml',
        'views/config/res_config_settings_views.xml',
        'views/config/resolution_views.xml',
        'views/config/uom_uom_views.xml',
        'views/config/account_taxes_view.xml',
        'views/config/customer_software_views.xml',
        'views/config/account_journal_views.xml',
        'views/config/product_template_views.xml',
        'views/account_move_view.xml',
        'views/res_partner_view.xml',
        'views/mail_message_views.xml',
        'views/account_move_reversal_view.xml',
        'views/radian_views.xml',
        'report/report_invoice.xml',
        'data/mail_template_data.xml',
    ],
    'external_dependencies': {
        'python': [
            'num2words',
            'pathlib',
            'qrcode',
            'requests',
        ]
    },
    'installable': True,
    'application': False,
}
