# -*- coding: utf-8 -*-
{
    'version': '1.0',
    'name': 'Colombian Geodata',
    'summary': 'Cities, departments and UI improvements.',
    'category': 'Localization',

    'author': 'DevCO',
    'website': 'https://www.felicity.com.co',
    'license': 'LGPL-3',

    'depends': ['base', 'sales_team'],
    'data': [
        'security/ir.model.access.csv',
        'data/res_country_state.xml',
        'data/res_country_state_city.xml',
        'data/res_config_co.xml',
        'data/res.country.csv',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
        'views/res_country_state_city_view.xml'],
}
