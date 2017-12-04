# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    appnr_primer_nombre = fields.Char(string='Primer Nombre', size=100)
    appnr_otros_nombres = fields.Char(string='Otros Nombres', size=100)
    appnr_primer_apellido = fields.Char(string='Primer Apellido', size=100)
    appnr_segundo_apellido = fields.Char(string='Segundo Apellido', size=100)
    appnr_tipo_documento = fields.Selection([(None, ''),
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
                                             ], string='Tipo de Documento')
    appnr_numero_identificacion = fields.Char(string='Número de Identificación', size=20)
    appnr_digito_verificacion = fields.Char(string='Dígito de Verificación', size=1)

    @api.model
    def _default_appnr_naturaleza(self):
        return 'J' if self.is_company else 'N'

    appnr_naturaleza = fields.Selection([('N', 'Natural'),
                                         ('J', 'Jurídica')], compute='_compute_naturaleza', string='Naturaleza', readonly=True, default=_default_appnr_naturaleza)

    @api.model
    def sigla_tipo_documento(self, tipo):
        switcher = {
            '11': "R.C.",
            '12': "T.I.",
            '13': "C.C.",
            '14': 'S.I.N.',
            '15': 'S.I.',
            '21': 'T.E.',
            '22': 'C.E.',
            '31': 'NIT',
            '33': 'I.E.D.N.',
            '41': 'PAS',
            '42': 'D.I.E.N.',
            '43': 'S.I.E.',
            '44': 'D.I.E.J.',
            '46': 'C.D.',
        }
        res = switcher.get(tipo, "")
        return res

    @api.model
    def nombre_tipo_documento(self):
        switcher = {
            '11': u'Registro civil de nacimiento',
            '12': u'Tarjeta de Identidad',
            '13': u'Cédula de ciudadanía',
            '14': u'Certificado de la Registraduría para sucesiones ilíquidas de personas naturales que no tienen ningún documento de identificación',
            '15': u'Tipo de documento que identifica una sucesión ilíquida, expedido por la notaría o por un juzgado',
            '21': u'Tarjeta de extranjería',
            '22': u'Cédula de extranjería',
            '31': u'NIT',
            '33': u'Identificación de extranjeros diferentes al NIT asignado por la DIAN',
            '41': u'Pasaporte',
            '42': u'Documento de identificación extranjero',
            '43': u'Sin identificación del exterior o para uso definido por la DIAN',
            '44': u'Documento de identificación extranjero Persona Jurídica',
            '46': u'Carné Diplomático',
        }
        if self.appnr_tipo_documento:
            res = switcher.get(str(self.appnr_tipo_documento), u'')
        else:
            res = u''
        return res

    @api.model
    def identificacion(self, sigla=True):
        res = ''
        if self.appnr_tipo_documento and self.appnr_numero_identificacion:
            if sigla:
                res = self.sigla_tipo_documento(self.appnr_tipo_documento) + ': ' + self.appnr_numero_identificacion
            else:
                res = self.appnr_numero_identificacion
            if self.appnr_tipo_documento == '31':
                res = res + '-' + str(self.appnr_digito_verificacion)
        return res

    @api.model
    def _get_computed_name(self, primer_nombre, otros_nombres, primer_apellido, segundo_apellido):
        return u" ".join((p for p in (primer_nombre, otros_nombres, primer_apellido, segundo_apellido) if p))

    @api.multi
    @api.depends('is_company')
    def _compute_naturaleza(self):
        for rec in self:
            rec.appnr_naturaleza = 'J' if rec.is_company else 'N'

    @api.onchange('appnr_primer_nombre', 'appnr_otros_nombres', 'appnr_primer_apellido', 'appnr_segundo_apellido')
    def _onchange_subnames(self):
        if not self.is_company:
            self.env.context = self.with_context(skip_onchange_name=True).env.context
            self.name = self._get_computed_name(self.appnr_primer_nombre, self.appnr_otros_nombres,
                                                self.appnr_primer_apellido, self.appnr_segundo_apellido)

    @api.onchange('name')
    def _onchange_name(self):
        if self.env.context.get("skip_onchange_name"):
            self.env.context = self.with_context(skip_onchange_name=False).env.context
        else:
            self.inverse_name()
            partners = self._get_duplicated_partner_by_name(self._origin.id, self.name)
            if len(partners) > 0:
                return {'warning': {
                    'title': _('Duplicidad de Registros!'),
                    'message': _('Ya existe un tercero con el nombre ingresado.')}
                }

    @api.onchange('is_company')
    def _onchange_is_company(self):
        self.inverse_name()

    @api.onchange('appnr_naturaleza', 'appnr_tipo_documento')
    def _onchange_appnr_naturaleza_appnr_tipo_documento(self):
        if self.appnr_tipo_documento:
            if self.appnr_tipo_documento != '31':
                self.appnr_digito_verificacion = None
            if self.appnr_naturaleza == 'J' and self.appnr_tipo_documento not in ('15', '31', '33', '42', '43', '44'):
                return {'warning': {
                    'title': _('Tipo de Documento No Válido!'),
                    'message': _('El tipo de documento seleccionado no aplica para una persona jurídica.')}
                }

    @api.onchange('appnr_digito_verificacion')
    def _onchange_appnr_digito_verificacion(self):
        if self.appnr_digito_verificacion and not (self.appnr_digito_verificacion.isdigit() and len(self.appnr_digito_verificacion) == 1):
            return {'warning': {
                'title': _('Dígito de Verificación No Válido!'),
                'message': _('El dígito de verificación ingresado no es válido.')}
            }

    @api.onchange('appnr_numero_identificacion', 'appnr_tipo_documento')
    def _onchange_appnr_numero_identificaacion_appnr_tipo_documento(self):
        if self.appnr_tipo_documento and self.appnr_numero_identificacion:
            if self.appnr_tipo_documento in ('13', '31') and not self.appnr_numero_identificacion.isdigit():
                return {'warning': {
                    'title': _('Número de Identificación No Válido!'),
                    'message': _('Para el tipo de documento seleccionado, el número de identificación debe contener solo dígitos.')}
                }

    @api.constrains('is_company', 'appnr_numero_identificacion', 'parent_id', 'appnr_tipo_documento')
    def _check_identification(self):
        if bool(self.appnr_tipo_documento) != bool(self.appnr_numero_identificacion):
            raise ValidationError(_("Identificación Inválida.\n"
                                    "Si se selecciona un tipo de documento se debe ingresar un número de"
                                    " identificación y viceversa."))
        if self.appnr_numero_identificacion and self.appnr_tipo_documento and self.appnr_tipo_documento in ('13', '31') \
                and not self.appnr_numero_identificacion.isdigit():
            raise ValidationError(_('Para el tipo de documento seleccionado el número de identificación debe'
                                    ' contener solo dígitos.'))
        if self.appnr_tipo_documento and self.appnr_numero_identificacion:
            partners = self.get_duplicated_partner(self.id, self.appnr_tipo_documento, self.appnr_numero_identificacion)
            if len(partners) > 0:
                raise ValidationError(_("El tercero %s tiene la misma identificación ingresada.\n") % partners[0].name.upper())

    @api.constrains('appnr_digito_verificacion', 'appnr_tipo_documento')
    def _check_appnr_digito_verificacion_appnr_tipo_documento(self):
        if bool(self.appnr_digito_verificacion) != bool(
                        self.appnr_tipo_documento and self.appnr_tipo_documento == '31'):
            raise ValidationError(_('El dígito de verificación es requerido para el tipo de documento NIT y solo para él.'))
        if self.appnr_digito_verificacion:
            if not (self.appnr_digito_verificacion.isdigit() and len(self.appnr_digito_verificacion) == 1):
                raise ValidationError(_('El dígito de verificación no es válido'))

    @api.constrains('appnr_tipo_documento')
    def _check_appnr_tipo_documento_appnr_naturaleza(self):
        if self.appnr_tipo_documento:
            if self.appnr_naturaleza == 'J' and self.appnr_tipo_documento not in ('15', '31', '33', '42', '43', '44'):
                raise ValidationError(_('El tipo de documento no aplica para una persona jurídica.'))

    @api.multi
    def get_duplicated_partner(self, record_id, tipo_documento, numero_identificacion):
        self.ensure_one()
        return self._get_duplicated_partner_by_numero_identificacion(record_id, tipo_documento, numero_identificacion)

    @api.model
    def _get_duplicated_partner_by_numero_identificacion(self, record_id, tipo_documento, numero_identificacion):
        partner_match_domain = []

        if numero_identificacion:
            partner_match_domain.append(('appnr_numero_identificacion', '=', numero_identificacion))
        else:
            return []
        if tipo_documento:
            partner_match_domain.append(('appnr_tipo_documento', '=', tipo_documento))
        else:
            return []
        if record_id:
            partner_match_domain.append(('id', '!=', record_id))

        return self.search(partner_match_domain)

    @api.model
    def _get_duplicated_partner_by_name(self, record_id, name):
        partner_match_domain = []

        if name:
            partner_match_domain.append(('name', '=ilike', self._get_whitespace_cleaned_name(name)))
            _logger.info(str(partner_match_domain))
        else:
            return []
        if record_id:
            partner_match_domain.append(('id', '!=', record_id))
            _logger.info(str(partner_match_domain))

        return self.search(partner_match_domain)

    @api.model
    def _get_whitespace_cleaned_name(self, name):
        return u" ".join(name.split(None)) if name else name

    @api.model
    def _get_inverse_name(self, name, is_company=False):
        if is_company or not name:
            parts = [False]
        else:
            parts = self._get_whitespace_cleaned_name(name).split(" ", 3)
            if len(parts) == 2:
                parts.append(parts[1])
                parts[1] = False

        while len(parts) < 4:
            parts.append(False)

        return {"appnr_primer_nombre": parts[0], "appnr_otros_nombres": parts[1],
                "appnr_primer_apellido": parts[2], "appnr_segundo_apellido": parts[3]}

    @api.multi
    def inverse_name(self):
        self.ensure_one()
        parts = self._get_inverse_name(self.name, self.is_company)
        self.appnr_primer_nombre, self.appnr_otros_nombres = parts["appnr_primer_nombre"], parts["appnr_otros_nombres"]
        self.appnr_primer_apellido, self.appnr_segundo_apellido = parts["appnr_primer_apellido"], parts[
            "appnr_segundo_apellido"]

    @api.multi
    def naturaleza_tipo_documento(self):
        self.ensure_one()
        if self.is_company:
            self.appnr_naturaleza, self.appnr_tipo_documento = 'J', '31'

    @api.model
    def _install_partner_subnames(self):
        for rec in self.search([]):
            _logger.info('Processing inverse name for partner ' + rec.name)
            rec.inverse_name()

    @api.model
    def create(self, vals):
        """
        Actualización de los componentes del nombre durante la importación de registros
        :param vals:
        :return:
        """
        if not vals.get('is_company') and not (vals.get('appnr_primer_nombre') and vals.get('appnr_primer_apellido')):
            parts = self._get_inverse_name(vals.get('name'))
            vals['appnr_primer_nombre'], vals['appnr_otros_nombres'] = parts["appnr_primer_nombre"], parts["appnr_otros_nombres"]
            vals['appnr_primer_apellido'], vals['appnr_segundo_apellido'] = parts["appnr_primer_apellido"], parts[
                'appnr_segundo_apellido']
        return super(Partner, self).create(vals)
