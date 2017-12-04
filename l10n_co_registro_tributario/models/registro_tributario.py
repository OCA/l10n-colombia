# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
from datetime import date

_logger = logging.getLogger(__name__)


class RegistroTributario(models.Model):
    _description = u"Registro Único Tributario"
    _name = 'aprgt.registro.unico.tributario'

    partner_id = fields.Many2one('res.partner', string='Partner', required=True, ondelete='cascade')
    concepto = fields.Selection([('01', '01 - Inscripción'),
                                 ('02', '02 - Actualización'),
                                 ('03', '03 - Actualización de Oficio'),
                                 ('3', '3 - Revisión'),
                                 ('09', '09 - Solicitud de actualización de datos de identificación')
                                 ], string='2. Concepto', required=True)
    numero_formulario = fields.Char(string='4. Número de Formulario', required=True)
    numero_identificacion_tributaria = fields.Char(string='5. Número de Identificación Tributaria (NIT)', required=True)
    digito_verificacion = fields.Char(string='6. DV', size=1, required=True)
    direccion_seccional_id = fields.Many2one('aprgt.direccion.seccional', string='12. Dirección Seccional', required=True, ondelete='restrict')
    buzon_electronico = fields.Char(string='14. Buzón Electrónico', required=False)
    tipo_contribuyente = fields.Selection([('1', 'Persona Jurídica'),
                                           ('2', 'Persona Natural o Sucesión Ilíquida')],
                                          string='24. Tipo de Contribuyente', required=True)
    tipo_documento = fields.Selection([(None, ''),
                                       ('11', '11 - Registro civil de nacimiento'),
                                       ('12', '12 - Tarjeta de identidad'),
                                       ('13', '13 - Cédula de ciudadanía'),
                                       ('14', '14 - Certificado de la Registraduría para sucesiones ilíquidas de personas'
                                              ' naturales que no tienen ningún documento de identificación'),
                                       ('15', '15 - Tipo de documento que identifica una sucesión ilíquida, expedido por la notaría o por un juzgado'),
                                       ('21', '21 - Tarjeta de extranjería'),
                                       ('22', '22 - Cédula de extranjería'),
                                       ('31', '31 - NIT'),
                                       ('33', '33 - Identificación de extranjeros diferentes al NIT asignado por la DIAN'),
                                       ('41', '41 - Pasaporte'),
                                       ('42', '42 - Documento de identificación extranjero'),
                                       ('43', '43 - Sin identificación del exterior o para uso definido por la DIAN'),
                                       ('44', '44 - Documento de identificación extranjero Persona Jurídica'),
                                       ('46', '46 - Carné Diplomático')
                                       ], string='25. Tipo de Documento')
    numero_identificacion = fields.Char(string='26. Número de Identificación')
    fecha_expedicion = fields.Date(string='27. Fecha Expedición')
    lugar_expedicion_city = fields.Char('30. Ciudad/Municipio')
    lugar_expedicion_apcty_city_id = fields.Many2one("apcty.city", string='30. Ciudad/Municipio', ondelete='restrict')
    lugar_expedicion_state_id = fields.Many2one("res.country.state", string='29. Departamento', ondelete='restrict')
    lugar_expedicion_apcty_has_cities = fields.Boolean(related='lugar_expedicion_state_id.apcty_has_cities', string='Has Cities', store=False)
    lugar_expedicion_country_id = fields.Many2one('res.country', string='28. País', ondelete='restrict')
    primer_apellido = fields.Char(string='31. Primer Apellido', size=100)
    segundo_apellido = fields.Char(string='32. Segundo Apellido', size=100)
    primer_nombre = fields.Char(string='33. Primer Nombre', size=100)
    otros_nombres = fields.Char(string='34. Otros Nombres', size=100)
    razon_social = fields.Char(string='35. Razón Social', size=500)
    nombre_comercial = fields.Char(string='36. Nombre Comercial', size=500)
    sigla = fields.Char(string='37. Sigla', size=100)
    ubicacion_city = fields.Char('40. Ciudad / Municipio')
    ubicacion_apcty_city_id = fields.Many2one("apcty.city", string='40. Ciudad/Municipio', ondelete='restrict')
    ubicacion_state_id = fields.Many2one("res.country.state", string='39. Departamento', ondelete='restrict')
    ubicacion_apcty_has_cities = fields.Boolean(related='ubicacion_state_id.apcty_has_cities', string='Has Cities', store=False)
    ubicacion_country_id = fields.Many2one('res.country', string='38. País', ondelete='restrict')
    direccion_principal = fields.Char(string='41. Dirección Principal', size=100)
    correo_electronico = fields.Char(string='42. Correo Electrónico', size=100)
    codigo_postal = fields.Char(string='43. Código Postal', change_default=True)
    telefono1 = fields.Char(string='44. Teléfono 1', size=100)
    telefono2 = fields.Char(string='45. Teléfono 2', size=100)
    numero_establecimientos = fields.Integer(string='52. Número Establecimientos')
    forma_exportacion = fields.Selection([('1', '1 - Directo'),
                                          ('2', '2 - Indirecto'),
                                          ('3', '3 - Directo o Indirecto')], string='55. Forma')
    tipo_exportacion = fields.Selection([('1', '1 - Pendiente por definir'),
                                         ('2', '2 - Servicios'),
                                         ('3', '3 - Bienes y Servicios'),
                                         ], string='56. Tipo')
    anexos = fields.Boolean('59. Anexos')
    numero_folios = fields.Integer('60. No. de Folios')
    fecha = fields.Date('61. Fecha', required=True)
    nombre = fields.Char('984. Nombre')
    cargo = fields.Char('985. Cargo')
    active = fields.Boolean('Active', default=True)

    clasificacion_ids = fields.One2many('aprgt.rut.clasificacion', 'registro_unico_tributario', string='Clasificación')
    responsabilidad_ids = fields.Many2many('aprgt.responsabilidad', string='Responsabilidades, Calidades y Atributos')
    exportador_ids = fields.One2many('aprgt.rut.exportador', 'registro_unico_tributario', string='Exportador')
    usuario_aduanero_ids = fields.Many2many('aprgt.usuario.aduanero', string='Obligados Aduaneros')

    @api.onchange('lugar_expedicion_apcty_city_id')
    def _onchange_lugar_expedicion_apcty_city_id(self):
        if self.lugar_expedicion_apcty_city_id:
            self.lugar_expedicion_city = self.lugar_expedicion_apcty_city_id.name

    @api.onchange('lugar_expedicion_state_id')
    def _onchange_lugar_expedicion_state_id(self):
        if self.lugar_expedicion_state_id:
            return {'domain': {'lugar_expedicion_apcty_city_id': [('state_id', '=', self.lugar_expedicion_state_id.id)]}}
        else:
            return {'domain': {'lugar_expedicion_apcty_city_id': []}}

    @api.onchange('lugar_expedicion_country_id')
    def _onchange_lugar_expedicion_country_id(self):
        if self.lugar_expedicion_country_id:
            return {'domain': {'lugar_expedicion_state_id': [('country_id', '=', self.lugar_expedicion_country_id.id)]}}
        else:
            return {'domain': {'lugar_expedicion_state_id': []}}

    @api.onchange('ubicacion_apcty_city_id')
    def _onchange_ubicacion_apcty_city_id(self):
        if self.ubicacion_apcty_city_id:
            self.ubicacion_city = self.ubicacion_apcty_city_id.name

    @api.onchange('ubicacion_state_id')
    def _onchange_ubicacion_state_id(self):
        if self.ubicacion_state_id:
            return {'domain': {'ubicacion_apcty_city_id': [('state_id', '=', self.ubicacion_state_id.id)]}}
        else:
            return {'domain': {'ubicacion_apcty_city_id': []}}

    @api.onchange('ubicacion_country_id')
    def _onchange_ubicacion_country_id(self):
        if self.ubicacion_country_id:
            return {'domain': {'ubicacion_state_id': [('country_id', '=', self.ubicacion_country_id.id)]}}
        else:
            return {'domain': {'ubicacion_state_id': []}}

    @api.onchange('numero_formulario')
    def _onchange_numero_formulario(self):
        recs = self._get_duplicated_by_field(self._origin.id, 'numero_formulario', self.numero_formulario)
        if recs:
            return {'warning': {
                'title': _('Número de Formulario Duplicado!'),
                'message': _('El número de formulario ingresado ya existe.')}
            }

    @api.onchange('numero_identificacion_tributaria')
    def _onchange_numero_identificacion_tributaria(self):
        if self.numero_identificacion_tributaria:
            if not self.numero_identificacion_tributaria.isdigit():
                return {'warning': {
                    'title': _('NIT No Válido!'),
                    'message': _('El NIT debe contener solo dígitos.')}
                }

    @api.onchange('digito_verificacion')
    def _onchange_digito_verificacion(self):
        if self.digito_verificacion and not (self.digito_verificacion.isdigit() and len(self.digito_verificacion) == 1):
            return {'warning': {
                'title': _('Dígito de Verificación No Válido!'),
                'message': _('El dígito de verificación ingresado no es válido.')}
            }

    @api.onchange('fecha')
    def _onchange_fecha(self):
        if self.fecha:
            if fields.Date.from_string(self.fecha) > date.today():
                return {'warning': {
                    'title': _('Fecha Inválida!'),
                    'message': _('La fecha no puede estar en el futuro.')}
                }

    @api.onchange('fecha_expedicion')
    def _onchange_fecha_expedicion(self):
        if self.fecha_expedicion:
            if fields.Date.from_string(self.fecha_expedicion) > date.today():
                return {'warning': {
                    'title': _('Fecha de Expedición Inválida!'),
                    'message': _('La fecha de expedición no puede estar en el futuro.')}
                }

    @api.constrains('tipo_documento', 'numero_identificacion')
    def _check_identification(self):
        if bool(self.tipo_documento) != bool(self.numero_identificacion):
            raise ValidationError(_("Identificación Inválida.\n"
                                    "Si se selecciona un tipo de documento se debe ingresar un número de"
                                    " identificación y viceversa."))

    @api.model
    def _get_duplicated_by_field(self, record_id, name, value, op='=ilike'):
        match_domain = []

        if value:
            match_domain.append((name, op, value))
        else:
            return []
        if record_id:
            match_domain.append(('id', '!=', record_id))

        return self.search(match_domain)
