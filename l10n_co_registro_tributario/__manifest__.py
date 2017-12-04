# -*- coding: utf-8 -*-
{
    'name': "App-247 Registro Tributario",
    # code: aprgt
    'summary': """
        App-247 Registro Tributario""",

    'description': """
        App-247 Registro Tributario
    """,

    'author': "App-247",
    'website': "http://www.app-247.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '10.0.1.0.1',

    # any module necessary for this one to work correctly
    'depends': ['l10n_co_ciiu_codes', 'apcty_city'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/responsabilidad.xml',
        'data/direccion_seccional.xml',
        'data/usuario_aduanero.xml',
        # 'views/templates.xml',
        'views/partner.xml',
        'views/registro_unico_tributario.xml',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'auto_install': False,
    'installable': True,
}