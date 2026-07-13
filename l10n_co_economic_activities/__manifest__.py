# -*- coding: utf-8 -*-
{
    'name': 'Colombia - Actividades Económicas',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Códigos de actividades económicas CIIU para Colombia',
    'description': """
Actividades Económicas Colombia
================================
Este módulo agrega los códigos de actividades económicas CIIU (Clasificación 
Industrial Internacional Uniforme) adaptados para Colombia por el DANE.

Características:
- Modelo de actividades económicas con código y descripción
- Campos en partners para actividad principal, secundaria y otras actividades
- Datos precargados con los códigos CIIU oficiales de la DIAN
- Base para facturación electrónica y retenciones
    """,
    'author': 'OCA',
    'website': 'https://github.com/OCA/l10n-colombia',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'contacts',
        'account',
        'base_address_extended',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/l10n_co_economic_activity_data.xml',
        'views/l10n_co_economic_activity_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
