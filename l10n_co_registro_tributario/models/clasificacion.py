# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

CNT_OTRAS_ACTIVIDADES = 2


class Clasificacion(models.Model):
    _description = u'Clasificación'
    _name = 'aprgt.rut.clasificacion'

    registro_unico_tributario = fields.Many2one('aprgt.registro.unico.tributario', string='Registro Único Tributario', required=True)
    actividad_economica = fields.Many2one('apciu.class', string='46/48/50. Actividad Económica', required=True)
    fecha_inicio = fields.Date(string='47/49. Fecha Inicio')
    tipo = fields.Selection([('principal', 'Principal'),
                             ('secundaria', 'Secundaria'),
                             ('otra', 'Otra Actividad'),
                             ],
                            string='Tipo', required=True)

    @api.model
    def _get_field_selection_text(self, name, key):
        t = [item for item in self._fields[name].selection if item[0] == key]
        if t:
            return t[0][1]

    @api.constrains('tipo')
    def _check_tipo(self):
        if self.tipo:
            recs = self._get_duplicated_by_field(self.id, 'tipo', self.tipo)
            cnt = CNT_OTRAS_ACTIVIDADES if self.tipo == 'otra' else 1
            if len(recs) and (self.tipo in ('principal', 'secundaria') or (self.tipo == 'otra' and len(recs) == cnt)):
                raise ValidationError(_('Ya existe(n) %d registro(s) en la solapa Clasificación para el Tipo %s.') % (cnt, self._get_field_selection_text('tipo', self.tipo)))

    @api.constrains('actividad_economica')
    def _check_actividad_economica(self):
        if self.actividad_economica:
            recs = self._get_duplicated_by_field(self.id, 'actividad_economica', self.actividad_economica.id)
            if recs:
                raise ValidationError(_('Ya existe un registro en la solapa Clasificación para la actividad %s') % self.actividad_economica.name)

    def _get_duplicated_by_field(self, record_id, name, value, op='='):
        match_domain = [(name, op, value), ('registro_unico_tributario', '=', self.registro_unico_tributario.id)]
        if record_id:
            match_domain.append(('id', '!=', record_id))
        return self.search(match_domain)
