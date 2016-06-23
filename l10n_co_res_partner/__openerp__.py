# -*- coding: utf-8 -*-
{
    'name': 'Colombia - Terceros',
    'category': 'Localization',
    'version': '9.0.0.1.0',
    'author': 'Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'maintainer': 'dominic.krimmer@gmail.com',
    'website': 'https://www.plastinorte.com',
    'summary': 'Colombia Terceros: Extended Partner / '
               'Contact Module - Odoo 9.0',
    'images': ['images/main_screenshot.png'],
    'depends': [
        'account',
        'account_accountant',
        'base'
    ],
    'data': [
        'views/l10n_co_res_partner.xml',
        'views/ciiu.xml',
        'data/ciiu.csv',
        'data/l10n_states_co_data.xml',
        'data/l10n_cities_co_data.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
}
