# -*- coding: utf-8 -*-

from odoo.osv import expression
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class CiiuGroup(models.Model):
    _description = "CIIU Group"
    _name = "apciu.group"

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    active = fields.Boolean('Active', default=True)
    apciu_section_id = fields.Many2one('apciu.section', string='Section', required='True')
    apciu_division_id = fields.Many2one('apciu.division', string='Division', required='True')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for rec in self:
            name = rec.code + ' - ' + rec.name
            result.append((rec.id, name))
        return result

    @api.onchange('apciu_section_id')
    def _onchange_apciu_section_id(self):
        if not self.apciu_section_id:
            self.apciu_division_id = False
        else:
            if self.apciu_division_id and self.apciu_division_id.apciu_section_id != self.apciu_section_id:
                self.apciu_division_id = False
        if self.apciu_section_id:
            return {'domain': {'apciu_division_id': [('apciu_section_id', '=', self.apciu_section_id.id)]}}
        else:
            return {'domain': {'apciu_division_id': []}}

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
