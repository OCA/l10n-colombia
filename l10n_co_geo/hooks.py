# -*- coding: utf-8 -*-
# Copyright 2016 David Arnold, DevCO Colombia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from openerp import api, SUPERUSER_ID


def _fill_city_id(cr, registry):
    """
    This is a utiliy function to help fill res_partner city_id,
    state and country with Bogota, Dc, Colombia.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    Partner = env['res.partner']
    all = ['|', ('active', '=', False), ('active', '=', True)]
    Partners = Partner.search(all + [('city_id', '!=', None)])
    bogota, dc, colombia = (
        env.ref('l10n_co_geo.city_0150'),
        env.ref('l10n_co_geo.state_03'),
        env.ref('base.co')
    )
    Partners.write({
        'city_id': bogota,
        'state_id': dc,
        'country_id': colombia
    })
