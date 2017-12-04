# -*- coding: utf-8 -*-
{
    'name': "App-247 CIIU Codes",
    # prefix: apciu

    'summary': """
        CIIU codes""",

    'description': """
        CIIU codes
    """,

    'author': "App-247",
    'website': "http://www.app-247.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '10.0.1.0.2',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ciiu_section.xml',
        'data/ciiu_division.xml',
        'data/ciiu_group.xml',
        'data/ciiu_class.xml',
        'views/views.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'auto_install': False,
    'installable': True,
}