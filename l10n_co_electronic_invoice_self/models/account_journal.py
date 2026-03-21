# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

import xmltodict
from markupsafe import Markup

from odoo import fields, models
from odoo.exceptions import UserError

from ..utils.constants import DIAN_ACTION_BASE

_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = "account.journal"

    l10n_co_dian_operation_mode = fields.Selection(
        selection=[
            ("demo", "Demostración"),
            ("test", "Habilitación"),
            ("production", "Producción"),
        ],
        default="demo",
        required=True,
        string="Modo de Operación",
        help="Demostración: genera XML y firma con certificado demo, no envía a DIAN. "
        "Habilitación: envía al ambiente de pruebas DIAN. "
        "Producción: envía al ambiente productivo DIAN.",
    )

    l10n_co_dian_software_identification = fields.Char(string="Identificación")
    l10n_co_dian_software_pin = fields.Char(string="Pin")

    l10n_co_dian_resolution_type = fields.Selection(
        selection=[
            ("FACTURA ELECTRÓNICA DE VENTA", "FACTURA ELECTRÓNICA DE VENTA"),
            ("FACTURA D.E./P.O.S.", "FACTURA D.E. / P.O.S."),
            ("FACTURA POR TALONARIO O DE PAPEL", "FACTURA POR TALONARIO O DE PAPEL"),
            ("DOCUMENTO SOPORTE", "DOCUMENTO SOPORTE"),
        ],
        string="Tipo de Resolución",
        copy=False,
        help="Corresponde al tipo de resolución de la factura",
    )
    l10n_co_dian_software_technical_key = fields.Char(
        string="Clave técnica (Producción)"
    )
    l10n_co_electronic_document_prefix = fields.Char(string="Prefijo")
    l10n_co_electronic_document_start_number = fields.Integer(string="Número de Inicio")
    l10n_co_electronic_document_end_number = fields.Integer(string="Número de Fin")
    l10n_co_electronic_document_resolution = fields.Char(string="Resolución")
    l10n_co_electronic_document_start_resolution_date = fields.Date(
        string="Fecha de Inicio de Resolución"
    )
    l10n_co_electronic_document_end_resolution_date = fields.Date(
        string="Fecha de Fin de Resolución"
    )
    l10n_co_electronic_document_message = fields.Text(string="Mensaje de Resolución")

    l10n_co_dian_resolution_type_test = fields.Selection(
        selection=[
            ("FACTURA ELECTRÓNICA DE VENTA", "FACTURA ELECTRÓNICA DE VENTA"),
            ("FACTURA D.E./P.O.S.", "FACTURA D.E. / P.O.S."),
            ("FACTURA POR TALONARIO O DE PAPEL", "FACTURA POR TALONARIO O DE PAPEL"),
            ("DOCUMENTO SOPORTE", "DOCUMENTO SOPORTE"),
        ],
        string="Tipo de Resolución (Habilitación)",
        copy=False,
        default="FACTURA ELECTRÓNICA DE VENTA",
        help="Corresponde al tipo de resolución de la factura (Habilitación)",
    )
    l10n_co_electronic_document_resolution_test = fields.Char(
        string="Resolución (Hab.)", default="000000000"
    )
    l10n_co_dian_software_technical_key_test = fields.Char(
        string="Clave Técnica (Hab.)"
    )
    l10n_co_dian_test_set_id = fields.Char(
        string="TestSetId (Hab.)",
        help="Identificador del set de pruebas asignado por la "
        "DIAN al registrar el software. Requerido para "
        "SendTestSetAsync en ambiente de habilitación.",
    )
    l10n_co_electronic_document_prefix_test = fields.Char(string="Prefijo (Hab.)")
    l10n_co_electronic_document_start_number_test = fields.Integer(
        string="Número de Inicio (Hab.)"
    )
    l10n_co_electronic_document_end_number_test = fields.Integer(
        string="Número de Fin (Hab.)"
    )
    l10n_co_electronic_document_start_resolution_date_test = fields.Date(
        string="Fecha Inicio Resolución (Hab.)"
    )
    l10n_co_electronic_document_end_resolution_date_test = fields.Date(
        string="Fecha Fin Resolución (Hab.)"
    )
    l10n_co_electronic_document_message_test = fields.Text(
        string="Mensaje Resolución (Hab.)"
    )

    def _is_demo_mode(self):
        self.ensure_one()
        return self.l10n_co_dian_operation_mode == "demo"

    def _is_support_document_type(self):
        self.ensure_one()
        resolution_type = self.l10n_co_dian_resolution_type
        if self.l10n_co_dian_operation_mode in ("test", "demo"):
            resolution_type = self.l10n_co_dian_resolution_type_test
        return resolution_type == "DOCUMENTO SOPORTE" and self.type == "purchase"

    def _get_electronic_document_dates(self):
        self.ensure_one()
        if self.l10n_co_dian_operation_mode == "production":
            return (
                self.l10n_co_electronic_document_start_resolution_date,
                self.l10n_co_electronic_document_end_resolution_date,
            )
        return (
            self.l10n_co_electronic_document_start_resolution_date_test,
            self.l10n_co_electronic_document_end_resolution_date_test,
        )

    def _get_electronic_document_numbering_range(self):
        self.ensure_one()
        if self.l10n_co_dian_operation_mode == "production":
            return (
                self.l10n_co_electronic_document_prefix,
                self.l10n_co_electronic_document_start_number,
                self.l10n_co_electronic_document_end_number,
            )
        return (
            self.l10n_co_electronic_document_prefix_test,
            self.l10n_co_electronic_document_start_number_test,
            self.l10n_co_electronic_document_end_number_test,
        )

    def _get_l10n_co_dian_self_params(self):
        self.ensure_one()
        if self.l10n_co_dian_operation_mode == "production":
            return (
                self.l10n_co_dian_operation_mode,
                self.l10n_co_dian_software_identification,
                self.l10n_co_dian_software_pin,
                self.l10n_co_dian_software_technical_key,
                self.l10n_co_electronic_document_resolution,
                self.l10n_co_electronic_document_start_resolution_date,
                self.l10n_co_electronic_document_end_resolution_date,
                self.l10n_co_electronic_document_start_number,
                self.l10n_co_electronic_document_end_number,
            )
        return (
            self.l10n_co_dian_operation_mode,
            self.l10n_co_dian_software_identification,
            self.l10n_co_dian_software_pin,
            self.l10n_co_dian_software_technical_key_test,
            self.l10n_co_electronic_document_resolution_test,
            self.l10n_co_electronic_document_start_resolution_date_test,
            self.l10n_co_electronic_document_end_resolution_date_test,
            self.l10n_co_electronic_document_start_number_test,
            self.l10n_co_electronic_document_end_number_test,
        )

    def action_query_numbering_range(self):
        """Query DIAN for numbering ranges via GetNumberingRange."""
        self.ensure_one()
        service = self.env["l10n_co.dian.self.service"]

        try:
            signer = service._get_signer(self)
            xml_content = service._generate_numbering_range_xml(self)

            action_url = DIAN_ACTION_BASE + "GetNumberingRange"
            soap = service._build_soap_envelope(
                self, xml_content, action_url, signer, body_zipped=False
            )

            if self._is_demo_mode():
                response = service._build_demo_numbering_range_response()
            else:
                response = service._send_to_dian(self, soap)

            response_str = (
                response if isinstance(response, bytes) else response.encode("utf-8")
            )
            values = xmltodict.parse(response_str)
            service._get_numbering_range_response_process(self, values)

        except Exception as e:
            _logger.error("Error querying numbering range: %s", str(e), exc_info=True)
            self.message_post(
                body=Markup(
                    f"""<p class='text-danger'>[ERROR] EDI - DIAN
                    <br/>Error al consultar rangos de numeración: <b>{str(e)}</b></p>"""
                ),
            )
            raise UserError(
                self.env._(
                    "Error al consultar rangos de numeración: %(error)s",
                    error=str(e),
                )
            ) from e
