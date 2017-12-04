# -*- coding: utf-8 -*-
{
    'name': "App-247 City",

    'summary': """
        Add city entity""",

    'description': """
        Add city entity
    """,

    'author': "App247",
    'website': "http://www.App-247.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '10.0.1.0.2',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sales_team'],

    # always loaded
    'data': [
        'data/res_partner.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/res_partner_view.xml',
        'views/res_bank_view.xml',
        'views/res_company_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'auto_install': False,
    'installable': True,
}