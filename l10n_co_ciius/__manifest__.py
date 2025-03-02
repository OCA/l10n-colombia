# -*- coding: utf-8 -*-
#
# Jorels S.A.S. - Copyright (2019-2022)
#
# This file is part of l10n_co_ciius.
#
# l10n_co_ciius is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# l10n_co_ciius is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with l10n_co_ciius.  If not, see <https://www.gnu.org/licenses/>.
#
# email: info@jorels.com
#

{
    'name': "CIIU's para Colombia",
    'summary': "CIIU'S para Colombia by Jorels",
    'description': "CIIU'S para Colombia by Jorels",
    'author': "Jorels SAS",
    'license': "LGPL-3",
    'version': '16.0.22.03.10.00.39',
    'website': "https://www.jorels.com",
    'images': ['static/images/main_screenshot.png'],
    'support': 'info@jorels.com',
    'depends': [
        'base',
        'l10n_co',
        'update_from_csv',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_view.xml',
        'data/data.xml',
    ],
    'installable': True,
    'application': False,
}
