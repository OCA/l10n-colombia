# -*- coding: utf-8 -*-
{
    'name': "App-247 DANE Code",
    # Prefix: apdnc
    'summary': """
        Adds DANE code to country, state and city""",

    'description': """
        Adds DANE code to country, state and city
    """,

    'author': "App-247",
    'website': "http://www.app-247.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '10.0.1.0.2',

    # any module necessary for this one to work correctly
    'depends': ['apcty_city'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'auto_install': False,
    'installable': True,
}