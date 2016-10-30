# -*- coding: utf-8 -*-
# Copyright 2016 David Arnold, DevCO Colombia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Colombian Geodata',
    'version': '10.0.1.0.0',
    'author': 'DevCO Colombia SAS',
    'maintainer': 'DevCO Colombia',
    'website': 'http://devco.co',
    'license': 'LGPL',
    'category': 'Localization',
    'summary': 'Cities, departments and UI improvements.',
    'depends': ['base', 'sales_team'],
    'data': [
        'security/ir.model.access.csv',
        'data/res_country_state.xml',
        'data/res_country_state_city.xml',
        'data/res_config_co.xml',
        'data/res.country.csv',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
        'views/res_country_state_city_view.xml',
    ],
    'post_init_hook': '_fill_city_id',
}
