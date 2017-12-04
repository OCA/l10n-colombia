# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class DireccionSeccional(models.Model):
    _description = u"Dirección Seccional"
    _name = 'aprgt.direccion.seccional'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    active = fields.Boolean('Active', default=True)

    @api.onchange('name')
    def _onchange_name(self):
        self.name = u" ".join(self.name.split(None)) if self.name else self.name
        recs = self._get_duplicated_by_name(self._origin.id, self.name)
        if recs:
            return {'warning': {
                'title': _('Duplicated Name!'),
                'message': _('The name entered already exists.')}
            }

    @api.onchange('code')
    def _onchange_code(self):
        self.code = u" ".join(self.code.split(None)) if self.code else self.code
        recs = self._get_duplicated_by_code(self._origin.id, self.code)
        if recs:
            return {'warning': {
                'title': _('Duplicated Code!'),
                'message': _('The code entered already exists.')}
            }

    @api.constrains('name')
    def _check_name(self):
        recs = self._get_duplicated_by_name(self.id, self.name)
        if len(recs):
            raise ValidationError(_("The name entered %s already exists.\n") % recs[0].name.upper())

    @api.constrains('code')
    def _check_code(self):
        recs = self._get_duplicated_by_code(self.id, self.code)
        if len(recs):
            raise ValidationError(_("The code entered %s already exists.\n") % recs[0].code.upper())

    @api.model
    def _get_duplicated_by_name(self, record_id, name):
        match_domain = []

        if name:
            match_domain.append(('name', '=ilike', self._get_whitespace_cleaned_name(name)))
        else:
            return []
        if record_id:
            match_domain.append(('id', '!=', record_id))

        return self.search(match_domain)

    @api.model
    def _get_duplicated_by_code(self, record_id, code):
        match_domain = []

        if code:
            match_domain.append(('code', '=ilike', self._get_whitespace_cleaned_name(code)))
        else:
            return []
        if record_id:
            match_domain.append(('id', '!=', record_id))

        return self.search(match_domain)

    @api.model
    def _get_whitespace_cleaned_name(self, name):
        return u" ".join(name.split(None)) if name else name
