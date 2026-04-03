# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
import uuid
from datetime import datetime
from hashlib import sha384

import pytz
import requests
import xmltodict
from lxml import etree
from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..utils.constants import DIAN_ACTION_BASE, DIAN_URLS

_logger = logging.getLogger(__name__)

RADIAN_EVENTS = [
    ("030", "Acuse de recibo de Factura Electrónica de Venta"),
    ("032", "Recibo del bien y/o prestación del servicio"),
    ("033", "Aceptación expresa"),
    ("031", "Reclamo de la Factura Electrónica de Venta"),
]

RADIAN_PREREQUISITES = {
    "030": [],  # Acuse: no prerequisites
    "032": ["030"],  # Recibo B/S: requires Acuse
    "033": ["030", "032"],  # Aceptación: requires Acuse + Recibo B/S
    "031": ["030"],  # Reclamo: requires Acuse
}

RADIAN_EXCLUSIONS = {
    "033": ["031"],  # Aceptación blocks Reclamo
    "031": ["033"],  # Reclamo blocks Aceptación
}

RADIAN_STATUS_MAP = {
    "030": "receipt_sent",
    "032": "goods_received",
    "033": "accepted",
    "031": "rejected",
}


class L10nCoRadianEventWizard(models.TransientModel):
    _name = "l10n_co.dian.radian.event.wizard"
    _description = "Wizard para envío de eventos RADIAN a la DIAN"

    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Factura",
        required=True,
        readonly=True,
    )
    event_type = fields.Selection(
        selection=RADIAN_EVENTS,
        string="Tipo de Evento",
        required=True,
        default="030",
    )
    note = fields.Text(string="Nota")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get("active_model") == "account.move":
            res["move_id"] = self.env.context.get("active_id")
        return res

    def action_send_event(self):
        """Enviar evento RADIAN a la DIAN."""
        self.ensure_one()
        move = self.move_id
        event = self.event_type

        if not move.l10n_co_edi_cufe_cude_ref:
            raise UserError(
                self.env._(
                    "La factura debe tener un CUFE/CUDE asignado "
                    "para enviar eventos RADIAN."
                )
            )

        self._validate_radian_event(move, event)

        try:
            service = self.env["l10n_co.dian.self.service"]
            signer = service._get_signer(move)

            xml_content = self._generate_application_response(
                move, signer.public_cert, signer.private_key
            )
            signed_xml = signer._document_sign(xml_content)
            self._send_event(move, signed_xml, signer)
            self._register_radian_event(move, event)

            move.message_post(
                body=Markup(
                    f"""<p class='text-success'>[RADIAN] EDI - DIAN
                    <br/>Evento <b>{dict(RADIAN_EVENTS)[event]}</b>
                    enviado exitosamente.</p>"""
                ),
            )

        except UserError:
            raise
        except Exception as e:
            _logger.error("Error al enviar evento RADIAN: %s", str(e))
            raise UserError(
                self.env._(
                    "Error al enviar evento RADIAN: %(error)s",
                    error=str(e),
                )
            ) from e

        return {"type": "ir.actions.act_window_close"}

    def _get_sent_events(self, move):
        """Return list of event codes already sent for this move."""
        if not move.l10n_co_radian_events_sent:
            return []
        return move.l10n_co_radian_events_sent.split(",")

    def _validate_radian_event(self, move, event_code):
        """Validate RADIAN event sequencing and exclusions."""
        sent = self._get_sent_events(move)
        event_label = dict(RADIAN_EVENTS).get(event_code, event_code)

        if event_code in sent:
            raise UserError(
                self.env._(
                    "El evento '%(event)s' ya fue enviado para esta factura.",
                    event=event_label,
                )
            )

        for prereq in RADIAN_PREREQUISITES.get(event_code, []):
            if prereq not in sent:
                prereq_label = dict(RADIAN_EVENTS).get(prereq, prereq)
                raise UserError(
                    self.env._(
                        "Debe enviar primero '%(prereq)s' antes de enviar '%(event)s'.",
                        prereq=prereq_label,
                        event=event_label,
                    )
                )

        for excluded in RADIAN_EXCLUSIONS.get(event_code, []):
            if excluded in sent:
                excluded_label = dict(RADIAN_EVENTS).get(excluded, excluded)
                raise UserError(
                    self.env._(
                        "No se puede enviar '%(event)s' porque ya se "
                        "envió '%(excluded)s' para esta factura.",
                        event=event_label,
                        excluded=excluded_label,
                    )
                )

    def _register_radian_event(self, move, event_code):
        """Register successfully sent RADIAN event on the move."""
        sent = self._get_sent_events(move) + [event_code]
        vals = {"l10n_co_radian_events_sent": ",".join(sent)}
        new_status = RADIAN_STATUS_MAP.get(event_code)
        if new_status:
            vals["l10n_co_radian_status"] = new_status
        move.write(vals)

    def _generate_application_response(self, move, cert, key):
        """Generate ApplicationResponse XML for RADIAN event."""
        NS_MAP = {
            None: (
                "urn:oasis:names:specification:ubl:schema:xsd:ApplicationResponse-2"
            ),
            "cac": (
                "urn:oasis:names:specification:ubl:schema:xsd"
                ":CommonAggregateComponents-2"
            ),
            "cbc": (
                "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
            ),
            "ext": (
                "urn:oasis:names:specification:ubl:schema:xsd"
                ":CommonExtensionComponents-2"
            ),
            "ds": "http://www.w3.org/2000/09/xmldsig#",
            "sts": "http://www.dian.gov.co/contratos/facturaelectronica/v1/Structures",
            "xades": "http://uri.etsi.org/01903/v1.3.2#",
            "xades141": "http://uri.etsi.org/01903/v1.4.1#",
        }

        NS_CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
        NS_CAC = (
            "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
        )
        NS_EXT = (
            "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
        )
        NS_STS = "http://www.dian.gov.co/contratos/facturaelectronica/v1/Structures"

        root = etree.Element("ApplicationResponse", nsmap=NS_MAP)

        ubl_extensions = etree.SubElement(root, etree.QName(NS_EXT, "UBLExtensions"))
        ubl_ext_1 = etree.SubElement(
            ubl_extensions, etree.QName(NS_EXT, "UBLExtension")
        )
        ext_content_1 = etree.SubElement(
            ubl_ext_1, etree.QName(NS_EXT, "ExtensionContent")
        )
        dian_extensions = etree.SubElement(
            ext_content_1, etree.QName(NS_STS, "DianExtensions")
        )

        invoice_source = etree.SubElement(
            dian_extensions, etree.QName(NS_STS, "InvoiceSource")
        )
        id_code = etree.SubElement(
            invoice_source, etree.QName(NS_CBC, "IdentificationCode")
        )
        id_code.text = "CO"
        id_code.set("listAgencyID", "6")
        id_code.set("listAgencyName", "United Nations Economic Commission for Europe")
        id_code.set(
            "listSchemeURI",
            "urn:oasis:names:specification:ubl:codelist:gc:CountryIdentificationCode-2.1",
        )

        supplier_vat = move.company_id.partner_id._l10n_co_get_vat_splited()[0] or ""

        sale_journal = self.env["account.journal"].search(
            [
                ("company_id", "=", move.company_id.id),
                ("type", "=", "sale"),
                ("l10n_co_dian_operation_mode", "!=", False),
            ],
            limit=1,
        )
        journal = sale_journal or move.journal_id
        software_id = journal.l10n_co_dian_software_identification or ""
        software_pin = journal.l10n_co_dian_software_pin or ""

        sw_provider = etree.SubElement(
            dian_extensions, etree.QName(NS_STS, "SoftwareProvider")
        )
        provider_id = etree.SubElement(sw_provider, etree.QName(NS_STS, "ProviderID"))
        provider_id.text = supplier_vat
        provider_id.set("schemeAgencyID", "195")
        provider_id.set(
            "schemeAgencyName",
            "CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)",
        )
        provider_id.set("schemeID", "4")
        provider_id.set("schemeName", "31")

        sw_id = etree.SubElement(sw_provider, etree.QName(NS_STS, "SoftwareID"))
        sw_id.text = software_id
        sw_id.set("schemeAgencyID", "195")
        sw_id.set(
            "schemeAgencyName",
            "CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)",
        )

        event_id = f"{move.name}-{self.event_type}"
        security_code_input = software_id + software_pin + event_id
        security_code = sha384(security_code_input.encode()).hexdigest()

        sw_security = etree.SubElement(
            dian_extensions, etree.QName(NS_STS, "SoftwareSecurityCode")
        )
        sw_security.text = security_code
        sw_security.set("schemeAgencyID", "195")
        sw_security.set(
            "schemeAgencyName",
            "CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)",
        )

        auth_provider = etree.SubElement(
            dian_extensions, etree.QName(NS_STS, "AuthorizationProvider")
        )
        auth_provider_id = etree.SubElement(
            auth_provider, etree.QName(NS_STS, "AuthorizationProviderID")
        )
        auth_provider_id.text = "800197268"
        auth_provider_id.set("schemeAgencyID", "195")
        auth_provider_id.set(
            "schemeAgencyName",
            "CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)",
        )
        auth_provider_id.set("schemeID", "4")
        auth_provider_id.set("schemeName", "31")

        ubl_ext_2 = etree.SubElement(
            ubl_extensions, etree.QName(NS_EXT, "UBLExtension")
        )
        etree.SubElement(ubl_ext_2, etree.QName(NS_EXT, "ExtensionContent"))

        etree.SubElement(root, etree.QName(NS_CBC, "UBLVersionID")).text = "UBL 2.1"

        etree.SubElement(
            root, etree.QName(NS_CBC, "CustomizationID")
        ).text = self.event_type

        etree.SubElement(
            root, etree.QName(NS_CBC, "ProfileID")
        ).text = "DIAN 2.1: ApplicationResponse de la Factura Electrónica de Venta"

        is_test_env = journal.l10n_co_dian_operation_mode in ("test", "demo")
        profile_execution_id = "2" if is_test_env else "1"

        etree.SubElement(
            root, etree.QName(NS_CBC, "ProfileExecutionID")
        ).text = profile_execution_id

        etree.SubElement(root, etree.QName(NS_CBC, "ID")).text = event_id

        now = datetime.now(pytz.timezone("America/Bogota"))
        issue_date = now.date().isoformat()
        issue_time = now.isoformat(timespec="seconds").split("T")[1]
        cude_input = (
            event_id
            + issue_date
            + issue_time
            + supplier_vat
            + software_pin
            + profile_execution_id
        )
        cude = sha384(cude_input.encode()).hexdigest()

        uuid_el = etree.SubElement(root, etree.QName(NS_CBC, "UUID"))
        uuid_el.text = cude
        uuid_el.set("schemeName", "CUDE-SHA384")
        uuid_el.set("schemeID", profile_execution_id)
        etree.SubElement(root, etree.QName(NS_CBC, "IssueDate")).text = issue_date
        etree.SubElement(root, etree.QName(NS_CBC, "IssueTime")).text = issue_time
        sender_party = etree.SubElement(root, etree.QName(NS_CAC, "SenderParty"))
        sender_tax = etree.SubElement(
            sender_party, etree.QName(NS_CAC, "PartyTaxScheme")
        )
        etree.SubElement(
            sender_tax, etree.QName(NS_CBC, "RegistrationName")
        ).text = move.company_id.name
        company_id_el = etree.SubElement(sender_tax, etree.QName(NS_CBC, "CompanyID"))
        company_id_el.text = supplier_vat
        company_id_el.set("schemeAgencyID", "195")
        company_id_el.set(
            "schemeAgencyName",
            "CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)",
        )
        tax_scheme = etree.SubElement(sender_tax, etree.QName(NS_CAC, "TaxScheme"))
        s_code, s_name = {"48": ("01", "IVA"), "49": ("ZZ", "No aplica")}.get(
            move.company_id.partner_id.l10n_co_regimen_fiscal, ("01", "IVA")
        )
        etree.SubElement(tax_scheme, etree.QName(NS_CBC, "ID")).text = s_code
        etree.SubElement(tax_scheme, etree.QName(NS_CBC, "Name")).text = s_name

        customer_vat = (
            move.partner_id.commercial_partner_id._l10n_co_get_vat_splited()[0] or ""
        )
        receiver_party = etree.SubElement(root, etree.QName(NS_CAC, "ReceiverParty"))
        receiver_tax = etree.SubElement(
            receiver_party, etree.QName(NS_CAC, "PartyTaxScheme")
        )
        etree.SubElement(
            receiver_tax, etree.QName(NS_CBC, "RegistrationName")
        ).text = move.partner_id.commercial_partner_id.name
        partner_id_el = etree.SubElement(receiver_tax, etree.QName(NS_CBC, "CompanyID"))
        partner_id_el.text = customer_vat
        partner_id_el.set("schemeAgencyID", "195")
        partner_id_el.set(
            "schemeAgencyName",
            "CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)",
        )
        receiver_tax_scheme = etree.SubElement(
            receiver_tax, etree.QName(NS_CAC, "TaxScheme")
        )
        r_code, r_name = {"48": ("01", "IVA"), "49": ("ZZ", "No aplica")}.get(
            move.partner_id.commercial_partner_id.l10n_co_regimen_fiscal,
            ("ZZ", "No aplica"),
        )
        etree.SubElement(receiver_tax_scheme, etree.QName(NS_CBC, "ID")).text = r_code
        etree.SubElement(receiver_tax_scheme, etree.QName(NS_CBC, "Name")).text = r_name

        doc_response = etree.SubElement(root, etree.QName(NS_CAC, "DocumentResponse"))
        response = etree.SubElement(doc_response, etree.QName(NS_CAC, "Response"))
        etree.SubElement(
            response, etree.QName(NS_CBC, "ResponseCode")
        ).text = self.event_type
        etree.SubElement(response, etree.QName(NS_CBC, "Description")).text = dict(
            RADIAN_EVENTS
        ).get(self.event_type, "")

        doc_ref = etree.SubElement(
            doc_response, etree.QName(NS_CAC, "DocumentReference")
        )
        etree.SubElement(doc_ref, etree.QName(NS_CBC, "ID")).text = move.name
        uuid_ref = etree.SubElement(doc_ref, etree.QName(NS_CBC, "UUID"))
        uuid_ref.text = move.l10n_co_edi_cufe_cude_ref
        uuid_ref.set("schemeName", "CUFE-SHA384")

        return etree.tostring(root, xml_declaration=True, encoding="UTF-8")

    def _send_event(self, move, signed_xml, signer):
        """Send the RADIAN event via SOAP to DIAN."""
        if move.journal_id._is_demo_mode():
            demo_response = self._build_demo_radian_response(move)
            values = xmltodict.parse(demo_response)
            self._process_radian_response(move, values)
            return

        service = self.env["l10n_co.dian.self.service"]

        zip_content = service._zip_content(
            signed_xml.decode("utf-8") if isinstance(signed_xml, bytes) else signed_xml,
            f"{move.name}-{self.event_type}.xml",
        )

        created_time, expires_time = service._get_security_timestamp()

        journal = move.journal_id
        mode = journal.l10n_co_dian_operation_mode
        ws_url = DIAN_URLS.get(mode)
        if not ws_url:
            raise UserError(
                self.env._(
                    "No se encontró URL DIAN para el modo '%(mode)s'",
                    mode=mode,
                )
            )

        action = DIAN_ACTION_BASE + "SendEventUpdateStatus"
        soap_envelope = self.env["ir.qweb"]._render(
            "l10n_co_electronic_invoice_self.dian_soap_envelope",
            {
                "to_id": f"id-{uuid.uuid1()}",
                "to": ws_url,
                "timestamp_id": f"TS-{uuid.uuid1()}",
                "created": created_time,
                "expires": expires_time,
                "action": action,
                "body": zip_content,
            },
        )

        signed_envelope = signer._envelope_sign(str(soap_envelope))

        response = requests.post(
            ws_url,
            data=signed_envelope,
            headers={"Content-Type": "application/soap+xml; charset=utf-8"},
            timeout=30,
        )
        response.raise_for_status()

        values = xmltodict.parse(response.content)
        self._process_radian_response(move, values)

    def _build_demo_radian_response(self, move):
        """Construir respuesta RADIAN simulada para modo demo."""
        now = (
            datetime.now(pytz.UTC)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )

        ns_o = (
            "http://docs.oasis-open.org/wss/2004/01"
            "/oasis-200401-wss-wssecurity-secext-1.0.xsd"
        )
        ns_u = (
            "http://docs.oasis-open.org/wss/2004/01"
            "/oasis-200401-wss-wssecurity-utility-1.0.xsd"
        )
        soap_ns = "http://schemas.xmlsoap.org/soap/envelope/"
        return f"""<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="{soap_ns}"
            xmlns:o="{ns_o}"
            xmlns:u="{ns_u}">
    <s:Header>
        <o:Security>
            <u:Timestamp>
                <u:Created>{now}</u:Created>
            </u:Timestamp>
        </o:Security>
    </s:Header>
    <s:Body>
        <SendEventUpdateStatusResponse xmlns="http://wcf.dian.colombia">
            <SendEventUpdateStatusResult
xmlns:b="http://schemas.datacontract.org/2004/07/UploadDocumentResponse">
                <b:StatusCode>00</b:StatusCode>
                <b:StatusDescription>[DEMO] Evento RADIAN \
{dict(RADIAN_EVENTS).get(self.event_type, "")} \
procesado (simulación)</b:StatusDescription>
                <b:StatusMessage>Evento procesado en modo \
demostración para factura {move.name}</b:StatusMessage>
                <b:ErrorMessage/>
            </SendEventUpdateStatusResult>
        </SendEventUpdateStatusResponse>
    </s:Body>
</s:Envelope>"""

    def _process_radian_response(self, move, values):
        """Process the DIAN response for a RADIAN event."""
        try:
            envelope = values.get("s:Envelope", {})
            body = envelope.get("s:Body", {})
            response = body.get("SendEventUpdateStatusResponse", {})
            result = response.get("SendEventUpdateStatusResult", {})

            status_code = result.get("b:StatusCode")
            status_description = result.get("b:StatusDescription", "")
            status_message = result.get("b:StatusMessage", "")

            if status_code == "00":
                move.message_post(
                    body=Markup(
                        f"""<p class='text-success'>[RADIAN] EDI - DIAN
                        <br/>Evento aceptado: {status_description}</p>"""
                    ),
                )
            else:
                error_messages = result.get("b:ErrorMessage", {})
                if isinstance(error_messages, dict):
                    error_messages = error_messages.get("c:string", [])
                if isinstance(error_messages, str):
                    error_messages = [error_messages]
                errors_html = "<br/>".join(error_messages) if error_messages else ""
                move.message_post(
                    body=Markup(
                        f"""<p class='text-danger'>[RADIAN] EDI - DIAN
                        <br/>StatusCode: {status_code}
                        <br/>{status_description}
                        <br/>{status_message}
                        <br/>{errors_html}</p>"""
                    ),
                )

        except Exception as e:
            _logger.error("Error al procesar respuesta RADIAN: %s", str(e))
            move.message_post(
                body=Markup(
                    f"""<p class='text-danger'>[RADIAN] EDI - DIAN
                    <br/>Error al procesar respuesta: {str(e)}</p>"""
                ),
            )
