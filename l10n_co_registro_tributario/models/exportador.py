# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class Exportador(models.Model):
    _description = u'Exportador'
    _name = 'aprgt.rut.exportador'

    registro_unico_tributario = fields.Many2one('aprgt.registro.unico.tributario', string='Registro Único Tributario', required=True)
    modo = fields.Selection([('1', '1 - Comercio Transfronterizo'),
                             ('2', '2 - Movimiento de Personas'),
                             ('3', '3 - Movimiento de Consumidores'),
                             ('4', '4 - Presencia Comercial')], string='57. Modo', required=True)
    cpc = fields.Selection([('61', '61 - Servicios de comercio al por mayor'),
                            ('62', '62 - Servicios de comercio al por menor'),
                            ('63', '63 - Servicios de hospedaje, alimentos y bebidas'),
                            ('64', '64 - Servicios de transporte terrestre'),
                            ('65', '65 - Servicios de transporte marítimo'),
                            ('66', '66 - Servicios de transporte aéreo'),
                            ('67', '67 - Servicios auxiliares para transporte'),
                            ('68', '68 - Servicios postales y de courier'),
                            ('69', '69 - Servicios de distribución de electricidad, gas y agua'),
                            ('71', '71 - Servicios de intermediación financiera, seguros y auxiliares'),
                            ('72', '72 - Servicios inmobiliarios y finca raíz'),
                            ('73', '73 - Servicios de arrendamiento con o sin opción de compra, sin operarios'),
                            ('81', '81 - Servicios de investigación y desarrollo'),
                            ('82', '82 - Servicios profesionales, científicos y técnicos (servivios legales, de contabilidad y asesorías en impuestos)'),
                            ('83', '83 - Otros servicios profesionales (servicios de arquitectura, ingeniería y otros servicios técnicos)'),
                            ('84', '84 - Telecomunicaciones'),
                            ('85', '85 - Otros servicios de soporte (agencias de empleo, servicios de seguridad, servicios de empaque)'),
                            ('86', '86 - Servicios de producción con base en honorarios y contratos'),
                            ('87', '87 - Servicios de reparación y mantenimiento'),
                            ('91', '91 - Administración pública y otros servicios a la comunidad'),
                            ('92', '92 - Servicios de educación'),
                            ('93', '93 - Servicios de salud'),
                            ('94', '94 - Servicios sanitarios, de disposición de residuos y de protección al medio ambiente'),
                            ('95', '95 - Servicios suministrados por organizaciones'),
                            ], string='58. CPC', required=True)

    @api.constrains('modo', 'cpc')
    def _check_modo_cpc(self):
        if self.modo and self.cpc:
            recs = self._get_duplicated(self.id)
            if recs:
                raise ValidationError(_('Ya existe un registro en la solapa Exportadores con el Modo y CPC ingresados.'))

    def _get_duplicated(self, record_id):
        match_domain = [('modo', '=', self.modo), ('cpc', '=', self.cpc), ('registro_unico_tributario', '=', self.registro_unico_tributario.id)]
        if record_id:
            match_domain.append(('id', '!=', record_id))
        return self.search(match_domain)
