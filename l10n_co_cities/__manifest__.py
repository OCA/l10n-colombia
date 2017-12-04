# -*- coding: utf-8 -*-
{
    'name': "App-247 Colombia Cities",

    'summary': """
        Colombia Cities""",

    'description': """
        Colombia Cities
    """,

    'author': "App-247",
    'website': "http://www.app-247.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '10.0.1.0.2',

    # any module necessary for this one to work correctly
    'depends': ['l10n_co_states'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/res_state_cities.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'auto_install': False,
    'installable': True,
}