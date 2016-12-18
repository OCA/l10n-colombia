# -*- coding: utf-8 -*-
# Copyright 2016 David Arnold, DevCO Colombia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from openerp import models, api


class CRMLead(models.Model):
    _name = 'crm.lead'
    _inherit = ['crm.lead', 'partner.city.abstract']

    @api.model
    def _address_fields(self):
        return super(CRMLead, self)._address_fields() + ['city_id']

    @api.model
    def create(self, vals):
        return super(CRMLead, self).create(self._complete_address(vals))

    @api.multi
    def write(self, vals):
        return super(CRMLead, self).write(self._complete_address(vals))
