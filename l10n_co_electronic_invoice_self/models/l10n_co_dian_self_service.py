# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import io
import logging
import uuid
import zipfile
from collections import defaultdict
from datetime import datetime, timedelta
from hashlib import sha384

import pytz
import requests
import xmltodict
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from lxml import etree
from markupsafe import Markup

from odoo import fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import frozendict
from odoo.tools.misc import file_path

from odoo.addons.account_edi_ubl_cii.models.account_edi_common import FloatFmt

from ..utils.constants import (
    BUYER_NOT_IDENTIFIED_VAT,
    DIAN_ACTION_BASE,
    DIAN_PROVIDER_CODE,
    DIAN_URLS,
    PROFILE_ID,
    SCHEMES,
    UUID_SCHEME_NAME,
)
from ..utils.xml_sign import XMLSigner

_logger = logging.getLogger(__name__)

DEMO_CERT_PATH = "l10n_co_electronic_invoice_self/static/demo_certificate.pem"
DEMO_KEY_PATH = "l10n_co_electronic_invoice_self/static/demo_private_key.pem"


class L10nCoDianSelfService(models.AbstractModel):
    _name = "l10n_co.dian.self.service"
    _description = "Service to generate XML UBL and sign it for DIAN Colombia"
    _inherit = ["account.edi.xml.ubl_21"]

    # -------------------------------------------------------------------------
    # EDI Import (drag & drop / chatter)
    # -------------------------------------------------------------------------

    def _import_invoice_l10n_co(self, invoice, file_data, new=False):
        """Import a Colombian DIAN electronic invoice XML.

        Delegates standard UBL 2.1 field extraction to the parent builder,
        then populates Colombian-specific fields (CUFE/CUDE, document type,
        DIAN status).
        """
        ubl_builder = self.env["account.edi.xml.ubl_21"]
        result = ubl_builder._import_invoice_ubl_cii(invoice, file_data, new)
        if not result:
            return result

        tree = file_data["xml_tree"]
        vals = {}

        uuid_node = tree.find(".//{*}UUID")
        if uuid_node is not None and uuid_node.text:
            vals["l10n_co_edi_cufe_cude_ref"] = uuid_node.text.strip()

        type_code = tree.findtext(".//{*}InvoiceTypeCode")
        if not type_code and etree.QName(tree).localname == "CreditNote":
            type_code = "91"
        if type_code:
            doc_type = self.env["l10n_latam.document.type"].search(
                [
                    ("code", "=", type_code),
                    ("country_id.code", "=", "CO"),
                ],
                limit=1,
            )
            if doc_type:
                vals["l10n_latam_document_type_id"] = doc_type.id

        invoice_id = tree.findtext(".//{*}ID")
        if invoice_id and invoice.move_type in (
            "in_invoice",
            "in_refund",
            "in_receipt",
        ):
            doc_type = vals.get("l10n_latam_document_type_id") and self.env[
                "l10n_latam.document.type"
            ].browse(vals["l10n_latam_document_type_id"])
            prefix = doc_type.doc_code_prefix if doc_type else ""
            if prefix and not invoice_id.startswith(prefix):
                vals["name"] = f"{prefix} {invoice_id}"
            else:
                vals["name"] = invoice_id

        vals["l10n_co_dian_status"] = "accepted"

        if vals:
            invoice.write(vals)

        return True

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def _generate_signed_xml(self, move):
        """Generate UBL XML, sign it, return (signed_xml_bytes, signer)."""
        try:
            signer = self._get_signer(move)

            generation_date = datetime.now()
            move.l10n_co_dian_generation_date = generation_date
            xml_content, errors = self._export_invoice(move)
            if errors:
                raise ValidationError(
                    self.env._(
                        "Error al generar XML UBL:\n%(errors)s",
                        errors="\n".join(errors.values()),
                    )
                )
            xml_content = self._fill_dian_data(xml_content, move)
            signed_xml = signer._document_sign(xml_content)
            _logger.info(
                "XML Content generado y firmado exitosamente para %s",
                move.name,
            )

            return signed_xml, signer
        except Exception as e:
            _logger.error("Error al generar XML firmado: %s", str(e), exc_info=True)
            raise UserError(
                self.env._(
                    "Error al generar XML firmado: %(error)s",
                    error=str(e),
                )
            ) from e

    def _build_soap_envelope(
        self,
        move_or_journal,
        xml_content,
        action_url,
        signer,
        body_zipped=True,
        dian_xml_filename=None,
    ):
        """Generate SOAP envelope and sign it. Returns signed soap bytes."""
        created_time, expires_time = self._get_security_timestamp()

        if move_or_journal._name == "account.move":
            name = dian_xml_filename or move_or_journal.name
            journal = move_or_journal.journal_id
        else:
            name = "query"
            journal = move_or_journal

        mode = journal.l10n_co_dian_operation_mode
        ws_url = DIAN_URLS.get(mode, "https://demo.dian.gov.co")

        if body_zipped:
            zip_inner_name = name if name.endswith(".xml") else f"{name}.xml"
            zip_b64 = self._zip_content(xml_content, zip_inner_name)
            zip_name = name.replace(".xml", ".zip")
            if not zip_name.endswith(".zip"):
                zip_name = f"{name}.zip"
            body = self._build_wcf_body(action_url, zip_name, zip_b64, journal)
        else:
            body = xml_content

        soap_envelope = self.env["ir.qweb"]._render(
            "l10n_co_electronic_invoice_self.dian_soap_envelope",
            {
                "to_id": f"id-{uuid.uuid1()}",
                "to": ws_url,
                "timestamp_id": f"TS-{uuid.uuid1()}",
                "created": created_time,
                "expires": expires_time,
                "action": action_url,
                "body": body,
            },
        )
        signed_soap = signer._envelope_sign(str(soap_envelope))
        _logger.info("Envelope XML generado y firmado para %s", name)
        return signed_soap

    def _build_wcf_body(self, action_url, filename, content_b64, journal):
        """Build the WCF method XML body for DIAN SOAP requests.

        SendBillSync: fileName + contentFile
        SendTestSetAsync: fileName + contentFile + testSetId

        The wcf namespace is already declared on the soap:Envelope
        parent, so we don't redeclare it here.
        """
        method = action_url.rsplit("/", 1)[-1]
        parts = [
            f"<wcf:{method}>",
            f"<wcf:fileName>{filename}</wcf:fileName>",
            f"<wcf:contentFile>{content_b64}</wcf:contentFile>",
        ]
        if method == "SendTestSetAsync":
            test_set_id = journal.l10n_co_dian_test_set_id or ""
            parts.append(f"<wcf:testSetId>{test_set_id}</wcf:testSetId>")
        parts.append(f"</wcf:{method}>")
        return "".join(parts)

    def _send_to_dian(self, journal, soap_data):
        """POST SOAP data to DIAN via requests. Returns response bytes."""
        mode = journal.l10n_co_dian_operation_mode
        url = DIAN_URLS.get(mode)
        if not url:
            raise UserError(
                self.env._(
                    "No se encontró URL DIAN para el modo '%(mode)s'",
                    mode=mode,
                )
            )
        response = requests.post(
            url,
            data=soap_data,
            headers={"Content-Type": "application/soap+xml; charset=utf-8"},
            timeout=30,
        )
        # DIAN returns HTTP 500 with SOAP Fault body on errors.
        # We return the content regardless of status code so the
        # response processor can extract the fault details.
        if response.status_code >= 500:
            _logger.warning(
                "DIAN returned HTTP %s for %s. "
                "Body will be parsed for SOAP Fault details.",
                response.status_code,
                url,
            )
        return response.content

    def _process_response(self, record, response_bytes, response_tag):
        """Parse SOAP response and update the record."""
        if isinstance(response_bytes, str):
            response_bytes = response_bytes.encode("utf-8")
        values = xmltodict.parse(response_bytes)
        return self._process_document_response(record, values, response_tag)

    def _save_audit_attachment(self, move, suffix, content, dian_filename=None):
        """Save content as ir.attachment linked to the move. Returns the attachment."""
        if isinstance(content, str):
            content = content.encode("utf-8")
        name = dian_filename or f"{move.name}_{suffix}.xml"
        return self.env["ir.attachment"].create(
            {
                "name": name,
                "type": "binary",
                "datas": base64.b64encode(content),
                "res_model": "account.move",
                "res_id": move.id,
                "mimetype": "application/xml",
            }
        )

    def _get_dian_file_consecutive(self, company):
        """Get next DIAN file consecutive as 8-digit hex string."""
        seq = self.env["ir.sequence"].next_by_code("l10n_co.dian.file.consecutive")
        if not seq:
            return "00000001"
        return format(int(seq), "08x")

    def _get_dian_filename(self, move, doc_prefix):
        """Build DIAN-compliant filename.

        Format: {prefix}{nit_10}{ppp}{aa}{consecutive_hex_8}.xml
        - prefix: fv, nc, nd, ar, ad
        - nit_10: company NIT without DV, 10 digits zero-padded
        - ppp: 000 (software propio)
        - aa: last 2 digits of current year
        - consecutive_hex_8: 8 hex digits from sequence

        See Anexo Técnico v1.9, section 6.5.7
        """
        company = move.company_id
        vat = company.partner_id.vat or ""
        nit = vat.split("-")[0].strip().replace(".", "")
        nit_10 = nit.zfill(10)[:10]

        year_2 = fields.Date.context_today(move).strftime("%y")
        consecutive = self._get_dian_file_consecutive(company)

        return f"{doc_prefix}{nit_10}{DIAN_PROVIDER_CODE}{year_2}{consecutive}.xml"

    def _generate_numbering_range_xml(self, journal):
        """Generate XML for numbering range query (GetNumberingRange)."""
        return self.env["ir.qweb"]._render(
            "l10n_co_electronic_invoice_self.dian_numbering_range_query_content",
            {"record": journal},
        )

    # -------------------------------------------------------------------------
    # GetStatus (query by CUFE/trackId — section 7.11)
    # -------------------------------------------------------------------------

    def _query_status(self, move):
        """Query DIAN GetStatus by CUFE or TrackId.

        Available in both habilitación and producción.
        Uses the same response structure as SendBillSync.
        """
        track_id = move.l10n_co_edi_cufe_cude_ref or move.l10n_co_dian_zip_key
        if not track_id:
            raise UserError(self.env._("No hay CUFE ni TrackId para consultar."))

        journal = move.journal_id
        signer = self._get_signer(move)

        action_url = DIAN_ACTION_BASE + "GetStatus"
        get_status_body = (
            f"<wcf:GetStatus><wcf:trackId>{track_id}</wcf:trackId></wcf:GetStatus>"
        )
        soap = self._build_soap_envelope(
            move,
            get_status_body,
            action_url,
            signer,
            body_zipped=False,
        )

        if journal._is_demo_mode():
            response = self._build_demo_response(move, "production")
        else:
            response = self._send_to_dian(journal, soap)

        self._save_audit_attachment(move, "get_status_response", response)

        self._process_response(move, response, "GetStatusResponse")

        move.invalidate_recordset(["l10n_co_dian_status", "l10n_co_edi_cufe_cude_ref"])

    # -------------------------------------------------------------------------
    # GetStatusZip (query async test result — section 7.12)
    # -------------------------------------------------------------------------

    def _query_zip_status(self, move):
        """Query DIAN GetStatusZip for the result of a SendTestSetAsync.

        Sends a SOAP request with the zipKey/trackId and processes the
        response using the same logic as SendBillSync (section 7.12).
        """
        zip_key = move.l10n_co_dian_zip_key
        if not zip_key:
            raise UserError(
                self.env._(
                    "No hay ZipKey para consultar. "
                    "El documento debe haberse enviado primero."
                )
            )

        journal = move.journal_id
        signer = self._get_signer(move)

        action_url = DIAN_ACTION_BASE + "GetStatusZip"
        get_status_body = (
            f"<wcf:GetStatusZip><wcf:trackId>{zip_key}</wcf:trackId></wcf:GetStatusZip>"
        )
        soap = self._build_soap_envelope(
            move,
            get_status_body,
            action_url,
            signer,
            body_zipped=False,
        )

        if journal._is_demo_mode():
            response = self._build_demo_response(move, "production")
        else:
            response = self._send_to_dian(journal, soap)

        self._save_audit_attachment(move, "get_status_zip_response", response)

        response_data = self._process_response(move, response, "GetStatusZipResponse")

        move.invalidate_recordset(["l10n_co_dian_status", "l10n_co_edi_cufe_cude_ref"])
        if move.l10n_co_dian_status == "accepted":
            application_response_xml = (
                response_data.get("application_response")
                if isinstance(response_data, dict)
                else None
            )
            signed_xml_att = self.env["ir.attachment"].search(
                [
                    ("res_model", "=", "account.move"),
                    ("res_id", "=", move.id),
                    ("name", "=like", "%xml_firmado%"),
                ],
                limit=1,
                order="id desc",
            )
            if signed_xml_att:
                signed_xml = base64.b64decode(signed_xml_att.datas)
                attached_doc = self._build_attached_document_xml(
                    move,
                    signed_xml,
                    application_response_xml,
                    signer=signer,
                )
                doc_prefix = "ad"
                dian_ad_name = self._get_dian_filename(move, doc_prefix)
                self._save_audit_attachment(
                    move,
                    "attached_document",
                    attached_doc,
                    dian_filename=dian_ad_name,
                )

        return move.l10n_co_dian_status

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------

    def _get_signer(self, move_or_journal):
        """Return an XMLSigner using the appropriate certificate for the context."""
        if move_or_journal._name == "account.move":
            journal = move_or_journal.journal_id
        else:
            journal = move_or_journal
        if journal._is_demo_mode():
            cert, key = self._get_demo_certificate_and_key()
        else:
            certificate = self._get_certificate(move_or_journal)
            cert, key = self._get_certificate_and_key(certificate)
        return XMLSigner(None, cert, key)

    def _get_security_timestamp(self, expires=5):
        created_dt = datetime.now(pytz.UTC)
        expires_dt = created_dt + timedelta(minutes=expires)
        created_time = created_dt.isoformat(timespec="milliseconds").replace(
            "+00:00", "Z"
        )
        expires_time = expires_dt.isoformat(timespec="milliseconds").replace(
            "+00:00", "Z"
        )
        return created_time, expires_time

    def _zip_content(self, content, name):
        """Compress XML content into a zip and return base64."""
        content_bytes = (
            content if isinstance(content, bytes) else content.encode("utf-8")
        )
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(name, content_bytes)

        zip_content = zip_buffer.getvalue()
        return base64.b64encode(zip_content).decode("utf-8")

    def _get_certificate(self, move):
        """Get valid certificate for the move's company."""
        certificate = self.env["certificate.certificate"].search(
            [
                ("company_id", "=", move.company_id.id),
                ("is_valid", "=", True),
                ("active", "=", True),
            ],
            limit=1,
        )
        if not certificate:
            raise UserError(
                self.env._("No se encontró certificado válido para firmar el XML")
            )
        if not certificate.private_key_id:
            raise UserError(self.env._("No hay clave privada asociada al certificado"))
        return certificate

    def _get_certificate_and_key(self, certificate):
        try:
            public_crt = certificate.pem_certificate
            cert = x509.load_pem_x509_certificate(
                base64.b64decode(public_crt), backend=default_backend()
            )

            private_key_pem = certificate.private_key_id.pem_key
            key = serialization.load_pem_private_key(
                base64.b64decode(private_key_pem), None, backend=default_backend()
            )

            return cert, key

        except Exception as e:
            _logger.error("Error al cargar certificado/clave: %s", str(e))
            raise UserError(
                self.env._(
                    "Error al cargar el certificado o clave privada: %(error)s",
                    error=str(e),
                )
            ) from e

    def _get_demo_certificate_and_key(self):
        """Get demo certificate and key for demonstration mode."""
        try:
            cert_path = file_path(DEMO_CERT_PATH)
            key_path = file_path(DEMO_KEY_PATH)
        except FileNotFoundError as e:
            raise UserError(
                self.env._(
                    "No se encontraron los archivos de certificado demo. "
                    "Verifique que existan en static/ del módulo."
                )
            ) from e
        with open(cert_path, "rb") as f:
            cert = x509.load_pem_x509_certificate(f.read(), backend=default_backend())
        with open(key_path, "rb") as f:
            key = serialization.load_pem_private_key(
                f.read(), None, backend=default_backend()
            )
        return cert, key

    def _build_attached_document_xml(
        self, move, signed_xml_content, application_response_xml=None, signer=None
    ):
        """Build AttachedDocument UBL 2.1 XML, sign it, and return bytes.

        Follows DIAN Anexo Técnico v1.9, section 6.4 (AttachedDocument).
        Contains the signed invoice XML and the ApplicationResponse from DIAN.
        The AttachedDocument itself is also digitally signed (XAdES-EPES).
        """
        now = datetime.now(pytz.timezone("America/Bogota"))
        journal = move.journal_id
        is_test = journal.l10n_co_dian_operation_mode == "test"
        is_demo = journal._is_demo_mode()
        profile_execution_id = "2" if (is_test or is_demo) else "1"

        doc_type_code = move.l10n_latam_document_type_id.code
        doc_type_map = {
            "01": "Contenedor de Factura Electrónica",
            "02": "Contenedor de Factura Electrónica",
            "03": "Contenedor de Factura Electrónica",
            "91": "Contenedor de Nota Crédito",
            "92": "Contenedor de Nota Débito",
            "20": "Contenedor de Documento Soporte",
            "30": "Contenedor de Documento Soporte",
        }
        doc_type_text = doc_type_map.get(
            doc_type_code, "Contenedor de Documento Electrónico"
        )

        cufe_cude = move.l10n_co_edi_cufe_cude_ref or ""
        cufe_scheme_name = UUID_SCHEME_NAME.get(doc_type_code, "CUFE-SHA384")

        supplier = move.company_id.partner_id
        supplier_vat, supplier_dv = supplier._l10n_co_get_vat_splited()
        supplier_vat = supplier_vat or ""
        supplier_doc_code = (
            supplier.l10n_latam_identification_type_id.l10n_co_document_code or "31"
        )
        supplier_responsibilities = (
            ";".join(supplier.l10n_co_responsibility_ids.mapped("code")) or "R-99-PN"
        )
        supplier_tax_code, supplier_tax_name = self.REGIMEN_TO_TAX_SCHEME.get(
            supplier.l10n_co_regimen_fiscal, ("01", "IVA")
        )

        customer = move.partner_id.commercial_partner_id
        customer_vat, customer_dv = customer._l10n_co_get_vat_splited()
        customer_vat = customer_vat or ""
        customer_doc_code = (
            customer.l10n_latam_identification_type_id.l10n_co_document_code or "13"
        )
        customer_responsibilities = (
            ";".join(customer.l10n_co_responsibility_ids.mapped("code")) or "R-99-PN"
        )
        customer_tax_code, customer_tax_name = self.REGIMEN_TO_TAX_SCHEME.get(
            customer.l10n_co_regimen_fiscal, ("ZZ", "No aplica")
        )

        signed_xml_str = (
            signed_xml_content.decode("utf-8")
            if isinstance(signed_xml_content, bytes)
            else signed_xml_content
        )

        if not application_response_xml and is_demo:
            application_response_xml = self._build_demo_application_response(
                move, now, profile_execution_id
            )
        ar_str = ""
        if application_response_xml:
            ar_str = (
                application_response_xml.decode("utf-8")
                if isinstance(application_response_xml, bytes)
                else application_response_xml
            )

        template_values = {
            "profile_execution_id": profile_execution_id,
            "document_id": move.name,
            "issue_date": now.date().isoformat(),
            "issue_time": now.strftime("%H:%M:%S-05:00"),
            "document_type": doc_type_text,
            "sender_name": move.company_id.name,
            "sender_vat": supplier_vat,
            "sender_scheme_id": supplier_dv or "",
            "sender_scheme_name": supplier_doc_code,
            "sender_tax_level_code": supplier_responsibilities,
            "sender_tax_scheme_id": supplier_tax_code,
            "sender_tax_scheme_name": supplier_tax_name,
            "receiver_name": customer.name,
            "receiver_vat": customer_vat,
            "receiver_scheme_id": customer_dv or "",
            "receiver_scheme_name": customer_doc_code,
            "receiver_tax_level_code": customer_responsibilities,
            "receiver_tax_scheme_id": customer_tax_code,
            "receiver_tax_scheme_name": customer_tax_name,
            "signed_xml_cdata": "___SIGNED_XML_PLACEHOLDER___",
            "cufe_cude": cufe_cude,
            "cufe_scheme_name": cufe_scheme_name,
            "invoice_issue_date": (
                move.invoice_date.isoformat() if move.invoice_date else ""
            ),
            "application_response_cdata": (
                "___APP_RESPONSE_PLACEHOLDER___" if ar_str else ""
            ),
            "validation_result_code": "02",
            "validation_date": now.date().isoformat(),
            "validation_time": now.strftime("%H:%M:%S-05:00"),
        }
        xml_content = self.env["ir.qweb"]._render(
            "l10n_co_electronic_invoice_self.dian_attached_document",
            template_values,
        )
        xml_bytes = str(xml_content).encode("utf-8")
        if signer:
            xml_bytes = signer._document_sign(xml_bytes)

        # Inject CDATA sections AFTER signing. lxml (used by the signer)
        # cannot preserve CDATA — it parses them as text and re-serializes
        # as escaped entities (&lt; &gt;). We replace the placeholders in
        # the final serialized output. This is safe because XML C14N
        # (used for signature digest) treats CDATA and escaped text as
        # semantically identical, so the signature remains valid.
        xml_str = xml_bytes.decode("utf-8")
        xml_str = xml_str.replace(
            "___SIGNED_XML_PLACEHOLDER___",
            f"<![CDATA[{signed_xml_str}]]>",
        )
        if ar_str:
            xml_str = xml_str.replace(
                "___APP_RESPONSE_PLACEHOLDER___",
                f"<![CDATA[{ar_str}]]>",
            )

        return xml_str.encode("utf-8")

    def _build_demo_application_response(self, move, now, profile_execution_id):
        """Build a simulated ApplicationResponse for demo AttachedDocument."""
        doc_type_code = move.l10n_latam_document_type_id.code
        cufe_cude = move.l10n_co_edi_cufe_cude_ref or ""
        cufe_scheme_name = UUID_SCHEME_NAME.get(doc_type_code, "CUFE-SHA384")

        fake_cude = sha384(
            f"DEMO-AR-{move.name}-{now.isoformat()}".encode()
        ).hexdigest()

        supplier = move.company_id.partner_id
        supplier_vat, supplier_dv = supplier._l10n_co_get_vat_splited()
        supplier_doc_code = (
            supplier.l10n_latam_identification_type_id.l10n_co_document_code or "31"
        )

        template_values = {
            "profile_execution_id": profile_execution_id,
            "response_id": str(uuid.uuid4().int)[:8],
            "cude": fake_cude,
            "cude_scheme_name": "CUDE-SHA384",
            "issue_date": now.date().isoformat(),
            "issue_time": now.strftime("%H:%M:%S-05:00"),
            "receiver_name": move.company_id.name,
            "receiver_vat": supplier_vat or "",
            "receiver_scheme_id": supplier_dv or "",
            "receiver_scheme_name": supplier_doc_code,
            "document_id": move.name,
            "cufe": cufe_cude,
            "cufe_scheme_name": cufe_scheme_name,
        }
        ar_xml = self.env["ir.qweb"]._render(
            "l10n_co_electronic_invoice_self.dian_demo_application_response",
            template_values,
        )
        return str(ar_xml)

    def _build_demo_response(self, move, operation_mode):
        """Build a simulated DIAN response for demonstration mode."""
        now = (
            datetime.now(pytz.UTC)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )

        doc_name = move.name if move._name == "account.move" else "DEMO"
        fake_cufe = sha384(f"DEMO-{doc_name}-{now}".encode()).hexdigest()

        if operation_mode == "test":
            template_id = (
                "l10n_co_electronic_invoice_self.dian_demo_send_test_set_async_response"
            )
            values = {
                "created": now,
                "zip_key": str(uuid.uuid4()),
            }
        else:
            template_id = (
                "l10n_co_electronic_invoice_self.dian_demo_send_bill_sync_response"
            )
            values = {
                "created": now,
                "xml_document_key": fake_cufe,
            }

        response_xml = self.env["ir.qweb"]._render(template_id, values)

        _logger.info("[DEMO] Respuesta DIAN simulada para %s", doc_name)
        return str(response_xml).encode("utf-8")

    def _build_demo_numbering_range_response(self):
        """Build simulated numbering range response for demo mode."""
        now = (
            datetime.now(pytz.UTC)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )
        response_xml = self.env["ir.qweb"]._render(
            "l10n_co_electronic_invoice_self.dian_demo_numbering_range_response",
            {"created": now},
        )
        return str(response_xml).encode("utf-8")

    def _get_numbering_range_response_process(self, record, values):
        """Process numbering range query response from DIAN."""
        try:
            create_date = (
                values.get("s:Envelope", {})
                .get("s:Header", {})
                .get("o:Security", {})
                .get("u:Timestamp", {})
                .get("u:Created", False)
            )

            if create_date:
                create_date = datetime.fromisoformat(create_date).replace(tzinfo=None)
            else:
                create_date = fields.Datetime.now()

            envelope = values.get("s:Envelope", {})
            body = envelope.get("s:Body", {})
            response = body.get("GetNumberingRangeResponse", {})
            result = response.get("GetNumberingRangeResult", {})

            operation_code = result.get("b:OperationCode")
            if operation_code != "100":
                operation_desc = result.get(
                    "b:OperationDescription", "Error desconocido"
                )
                _logger.warning("[ERROR] EDI - DIAN: %s", operation_desc)
                record.message_post(
                    body=Markup(f"""<p class='text-danger'>[ERROR] EDI - DIAN
                        <br/>{operation_desc}</p>"""),
                )
                return {"create_date": create_date}

            response_list = result.get("b:ResponseList", {})
            number_ranges = response_list.get("c:NumberRangeResponse", [])
            if not isinstance(number_ranges, list):
                number_ranges = [number_ranges]

            target_resolution = record.l10n_co_electronic_document_resolution
            target_prefix = record.l10n_co_electronic_document_prefix

            if not target_resolution and not target_prefix:
                record.message_post(
                    body=Markup(
                        "<p class='text-danger'>[ERROR] EDI - DIAN"
                        "<br/>Configure la resolución y/o el prefijo "
                        f"en el diario <b>{record.name}</b> antes "
                        "de consultar.</p>"
                    ),
                )
                return {"create_date": create_date}

            matching_range = None
            for range_item in number_ranges:
                res_match = (
                    not target_resolution
                    or range_item.get("c:ResolutionNumber") == target_resolution
                )
                prefix_match = (
                    not target_prefix or range_item.get("c:Prefix") == target_prefix
                )
                if res_match and prefix_match:
                    matching_range = range_item
                    break

            if matching_range:
                record.write(
                    {
                        "l10n_co_electronic_document_resolution": (
                            matching_range.get("c:ResolutionNumber")
                        ),
                        "l10n_co_electronic_document_prefix": (
                            matching_range.get("c:Prefix")
                        ),
                        "l10n_co_electronic_document_start_number": int(
                            matching_range.get("c:FromNumber", 0)
                        ),
                        "l10n_co_electronic_document_end_number": int(
                            matching_range.get("c:ToNumber", 0)
                        ),
                        "l10n_co_dian_software_technical_key": (
                            matching_range.get("c:TechnicalKey")
                            if isinstance(
                                matching_range.get("c:TechnicalKey"),
                                str,
                            )
                            else False
                        ),
                        "l10n_co_electronic_document_start_resolution_date": (
                            matching_range.get("c:ValidDateFrom")
                        ),
                        "l10n_co_electronic_document_end_resolution_date": (
                            matching_range.get("c:ValidDateTo")
                        ),
                        "l10n_co_electronic_document_message": (
                            f"Resolución de Facturación Nº "
                            f"{matching_range.get('c:ResolutionNumber')}"
                            f", fecha "
                            f"{matching_range.get('c:ValidDateFrom')}"
                            f" a "
                            f"{matching_range.get('c:ValidDateTo')}"
                            f", Prefijo "
                            f"{matching_range.get('c:Prefix')}"
                            f", numeración desde "
                            f"{matching_range.get('c:FromNumber')}"
                            f" Hasta "
                            f"{matching_range.get('c:ToNumber')}"
                        ),
                    }
                )
                record.message_post(
                    body=Markup(
                        "<p class='text-success'>[SUCCESS] EDI - DIAN"
                        "<br/>Resolución "
                        f"{matching_range.get('c:ResolutionNumber')}"
                        f" prefijo "
                        f"{matching_range.get('c:Prefix')}"
                        " procesada exitosamente.</p>"
                    ),
                )
            else:
                available = [
                    f"{r.get('c:Prefix')} ({r.get('c:ResolutionNumber')})"
                    for r in number_ranges
                ]
                record.message_post(
                    body=Markup(
                        "<p class='text-warning'>"
                        "[WARNING] EDI - DIAN<br/>"
                        f"No se encontró rango para resolución "
                        f"<b>{target_resolution}</b> prefijo "
                        f"<b>{target_prefix}</b>.<br/>"
                        f"Rangos disponibles: {', '.join(available)}"
                        "</p>"
                    ),
                )
            return {"create_date": create_date}

        except Exception as e:
            _logger.error("Error al procesar respuesta DIAN: %s", str(e))
            record.message_post(
                body=Markup(f"""<p>[ERROR] EDI - DIAN<br/>Error al \
                    procesar respuesta. <b>{str(e)}</b></p>"""),
            )
            return {"create_date": fields.Datetime.now()}

    def _format_dian_errors(self, result):
        """Format DIAN error messages as a compact HTML list."""
        error_messages = result.get("b:ErrorMessage", {})
        if isinstance(error_messages, dict):
            error_messages = error_messages.get("c:string", [])
        if isinstance(error_messages, str):
            error_messages = [error_messages]
        if not error_messages:
            return ""

        items = []
        for msg in error_messages:
            is_notice = "Notificación:" in msg
            icon = "&#9888;" if is_notice else "&#10060;"
            detail = msg
            rule = ""
            if msg.startswith("Regla:"):
                parts = msg.split(",", 1)
                rule = parts[0].replace("Regla:", "").strip()
                detail = parts[1].strip() if len(parts) > 1 else msg
            for prefix in ("Rechazo: ", "Notificación: "):
                detail = detail.replace(prefix, "", 1)
            label = f"<b>[{rule}]</b> " if rule else ""
            items.append(f"<li>{icon} {label}{detail}</li>")

        return (
            "<ul style='margin:4px 0;padding-left:16px;"
            "font-size:0.95em;'>" + "".join(items) + "</ul>"
        )

    def _extract_async_errors(self, result):
        """Extract error messages from SendTestSetAsync response."""
        error_parts = []
        error_list = result.get("b:ErrorMessageList", {})
        if isinstance(error_list, dict):
            track_ids = error_list.get("b:XmlParamsResponseTrackId", {})
            if isinstance(track_ids, dict):
                track_ids = [track_ids]
            if isinstance(track_ids, list):
                for track in track_ids:
                    msg = track.get("b:processedMessage", "")
                    fname = track.get("b:xmlFileName", "")
                    if msg:
                        error_parts.append(f"{fname}: {msg}" if fname else msg)
        elif isinstance(error_list, str) and error_list:
            error_parts.append(error_list)

        if not error_parts:
            # Fallback: dump the full result for debugging
            _logger.warning(
                "SendTestSetAsync error with no parseable details: %s",
                result,
            )
            error_parts.append("Error sin detalles. Revise los logs del servidor.")

        return "<br/>".join(error_parts)

    def _process_document_response(self, record, values, response_tag):
        """Process generic DIAN electronic document response."""
        try:
            create_date = (
                values.get("s:Envelope", {})
                .get("s:Header", {})
                .get("o:Security", {})
                .get("u:Timestamp", {})
                .get("u:Created", False)
            )

            if create_date:
                create_date = datetime.fromisoformat(create_date).replace(tzinfo=None)
            else:
                create_date = fields.Datetime.now()

            envelope = values.get("s:Envelope", {})
            body = envelope.get("s:Body", {})

            fault = body.get("s:Fault")
            if fault:
                reason = fault.get("s:Reason", {}).get("s:Text", {})
                if isinstance(reason, dict):
                    reason = reason.get("#text", "")
                fault_code = (
                    fault.get("s:Code", {}).get("s:Subcode", {}).get("s:Value", {})
                )
                if isinstance(fault_code, dict):
                    fault_code = fault_code.get("#text", "")
                error_msg = f"{fault_code}: {reason}" if fault_code else str(reason)
                _logger.error(
                    "DIAN SOAP Fault for %s: %s",
                    record.name if hasattr(record, "name") else record,
                    error_msg,
                )
                record.message_post(
                    body=Markup(
                        f"""<p class='text-danger'>
                        [ERROR] EDI - DIAN (SOAP Fault)
                        <br/>{error_msg}</p>"""
                    ),
                )
                record.write({"l10n_co_dian_status": "error"})
                return {"create_date": create_date}

            response = body.get(response_tag, {})
            result = response.get(f"{response_tag}Result") or response.get(
                response_tag.replace("Response", "Result"), {}
            )

            if response_tag == "SendTestSetAsyncResponse":
                zip_key = result.get("b:ZipKey")
                if zip_key:
                    record.message_post(
                        body=Markup(
                            f"""<p class='text-success'>
                            [SUCCESS] EDI - DIAN
                            <br/>Documento enviado a habilitación.
                            ZipKey: <b>{zip_key}</b></p>"""
                        ),
                    )
                    record.write(
                        {
                            "l10n_co_dian_status": "sent",
                            "l10n_co_dian_zip_key": zip_key,
                        }
                    )
                    return {"create_date": create_date}

                error_msgs = self._extract_async_errors(result)
                record.message_post(
                    body=Markup(
                        f"""<p class='text-danger'>
                        [ERROR] EDI - DIAN
                        <br/>{error_msgs}</p>"""
                    ),
                )
                record.write({"l10n_co_dian_status": "error"})
                return {"create_date": create_date}

            if response_tag == "GetStatusZipResponse":
                dian_response = result.get("b:DianResponse")
                if dian_response:
                    result = dian_response

            status_code = result.get("b:StatusCode")
            status_description = result.get("b:StatusDescription", "")
            status_message = result.get("b:StatusMessage", "")
            xml_document_key = result.get("b:XmlDocumentKey", "")

            xml_base64_bytes = result.get("b:XmlBase64Bytes", "")

            if status_code == "00":
                vals_to_write = {
                    "l10n_co_dian_status": "accepted",
                    "l10n_co_edi_cufe_cude_ref": xml_document_key or False,
                }
                # Mark sales invoices as RADIAN pending
                if record._name == "account.move" and record.move_type == "out_invoice":
                    vals_to_write["l10n_co_radian_status"] = "pending"
                record.write(vals_to_write)
                record.message_post(
                    body=Markup(
                        f"""<p class='text-success'>[SUCCESS] EDI - DIAN
                        <br/>{status_description}
                        <br/>CUFE/CUDE: <b>{xml_document_key}</b></p>"""
                    ),
                )
                if xml_base64_bytes:
                    return {
                        "create_date": create_date,
                        "application_response": base64.b64decode(xml_base64_bytes),
                    }
            elif status_code == "99":
                record.write({"l10n_co_dian_status": "rejected"})
                errors_html = self._format_dian_errors(result)
                record.message_post(
                    body=Markup(
                        f"<p class='text-danger'>"
                        f"[REJECTED] EDI - DIAN<br/>"
                        f"{status_description}<br/>"
                        f"{status_message}</p>"
                        f"{errors_html}"
                    ),
                )
            else:
                record.write({"l10n_co_dian_status": "error"})
                _logger.warning(
                    "DIAN unexpected StatusCode=%s for %s. "
                    "response_tag=%s, body_keys=%s, response_keys=%s, "
                    "result_keys=%s",
                    status_code,
                    record.name,
                    response_tag,
                    list(body.keys()) if isinstance(body, dict) else type(body),
                    list(response.keys())
                    if isinstance(response, dict)
                    else type(response),
                    list(result.keys()) if isinstance(result, dict) else type(result),
                )
                record.message_post(
                    body=Markup(
                        f"""<p class='text-warning'>[WARNING] EDI - DIAN
                        <br/>StatusCode: {status_code}
                        <br/>{status_description}
                        <br/>{status_message}</p>"""
                    ),
                )

            return {"create_date": create_date}

        except Exception as e:
            _logger.error("Error al procesar respuesta DIAN: %s", str(e))
            record.message_post(
                body=Markup(
                    f"""<p class='text-danger'>[ERROR] EDI - DIAN<br/>Error al
                    procesar respuesta. <b>{str(e)}</b></p>"""
                ),
            )
            return {"create_date": fields.Datetime.now()}

    # -------------------------------------------------------------------------
    # UBL 2.1 overrides
    # -------------------------------------------------------------------------

    def _export_invoice_constraints(self, invoice, vals):
        return super()._export_invoice_constraints(invoice, vals)

    def _add_invoice_header_nodes(self, document_node, vals):
        super()._add_invoice_header_nodes(document_node, vals)
        invoice = vals["invoice"]
        is_nc_nd_no_ref = (
            invoice.move_type in ("out_refund", "in_refund")
            and not invoice.reversed_entry_id
        ) or (
            invoice.debit_origin_id is False
            and invoice.l10n_co_dian_operation_type == "32"
        )
        if is_nc_nd_no_ref:
            start_date = invoice.l10n_co_invoice_period_start
            end_date = invoice.l10n_co_invoice_period_end
        else:
            start_date, end_date = invoice.journal_id._get_electronic_document_dates()
        document_node.update(
            {
                "xsi:schemaLocation": SCHEMES[vals["document_type"]],
                "cbc:UBLVersionID": {"_text": "UBL 2.1"},
                "cbc:CustomizationID": {
                    "_text": invoice._l10n_co_electronic_document_customization_id()
                },
                "cbc:ProfileID": {
                    "_text": PROFILE_ID[invoice.l10n_latam_document_type_id.code]
                },
                "cbc:ProfileExecutionID": {
                    "_text": "2"
                    if invoice.journal_id.l10n_co_dian_operation_mode
                    in ("test", "demo")
                    else "1"
                },
                "cbc:UUID": {
                    "schemeID": "2"
                    if invoice.journal_id.l10n_co_dian_operation_mode
                    in ("test", "demo")
                    else "1",
                    "schemeName": UUID_SCHEME_NAME[
                        invoice.l10n_latam_document_type_id.code
                    ],
                },
                "cbc:IssueDate": {
                    "_text": invoice.l10n_co_dian_generation_date.astimezone(
                        pytz.timezone("America/Bogota")
                    )
                    .date()
                    .isoformat()
                },
                "cbc:IssueTime": {
                    "_text": invoice.l10n_co_dian_generation_date.astimezone(
                        pytz.timezone("America/Bogota")
                    )
                    .isoformat(timespec="seconds")
                    .split("T")[1]
                },
                "cbc:InvoiceTypeCode": {
                    "_text": invoice.l10n_latam_document_type_id.code
                }
                if vals["document_type"] == "invoice"
                else None,
                "cbc:CreditNoteTypeCode": {
                    "_text": invoice.l10n_latam_document_type_id.code
                }
                if vals["document_type"] == "credit_note"
                else None,
                "cbc:Note": None,
                "cbc:DocumentCurrencyCode": {
                    "_text": "COP",
                    "listAgencyID": "6",
                    "listAgencyName": "United Nations Economic Commission for Europe",
                    "listID": "ISO 4217 Alpha",
                },
                "cbc:LineCountNumeric": {
                    "_text": len(
                        [
                            base_line
                            for base_line in vals["base_lines"]
                            if not base_line["special_mode"]
                        ]
                    )
                },
                "cac:InvoicePeriod": {
                    "cbc:StartDate": {
                        "_text": start_date.isoformat() if start_date else ""
                    },
                    "cbc:EndDate": {"_text": end_date.isoformat() if end_date else ""},
                }
                if start_date
                and end_date
                and (
                    is_nc_nd_no_ref
                    or invoice.l10n_latam_document_type_id.code
                    in ("01", "02", "03", "05")
                )
                else None,
                "cac:DiscrepancyResponse": self._get_discrepancy_response_node(invoice),
            }
        )

        # DIAN CAD05: no spaces in document ID
        if "cbc:ID" in document_node:
            doc_id = document_node["cbc:ID"].get("_text", "")
            document_node["cbc:ID"]["_text"] = doc_id.replace(" ", "")

        document_node["cac:OrderReference"]["cbc:SalesOrderID"] = None
        document_node["cac:BillingReference"] = (
            self._get_billing_reference_node(invoice)
            if invoice.reversed_entry_id or invoice.debit_origin_id
            else None
        )

        document_node.update(
            {
                "cac:PrepaidPayment": [
                    {
                        "cbc:ID": {"_text": p["name"]},
                        "cbc:PaidAmount": {
                            "_text": self.format_float(
                                p["amount"], invoice.company_currency_id.decimal_places
                            ),
                            "currencyID": invoice.company_currency_id.name,
                        },
                        "cbc:ReceivedDate": {"_text": p["date"]},
                    }
                    for p in vals["prepayments"]
                ]
                if vals["document_type"] in {"invoice", "credit_note"}
                else None,
            }
        )
        return

    def _add_invoice_config_vals(self, vals):
        super()._add_invoice_config_vals(vals)
        invoice = vals["invoice"]

        vals.update(
            {
                "document_type": "debit_note"
                if invoice.debit_origin_id
                else "credit_note"
                if invoice.move_type in ("out_refund", "in_refund")
                else "invoice",
                "algorithm": UUID_SCHEME_NAME[invoice.l10n_latam_document_type_id.code],
                "prepayments": [],
                "use_company_currency": True,
                "fixed_taxes_as_allowance_charges": False,
            }
        )
        return

    def _add_invoice_base_lines_vals(self, vals):
        super()._add_invoice_base_lines_vals(vals)
        for base_line in vals["base_lines"]:
            self._transform_iva_withholding_base_amount(base_line)
        return

    def _transform_iva_withholding_base_amount(self, base_line):
        def get_tax_data(tax_code):
            return next(
                (
                    tax_data
                    for tax_data in base_line["tax_details"]["taxes_data"]
                    if tax_data["tax"].l10n_co_tax_type_id.code == tax_code
                ),
                None,
            )

        tax_data_05 = get_tax_data("05")
        if tax_data_05:
            tax_data_01 = get_tax_data("01")
            tax_data_05["base_amount"] = (
                tax_data_01["tax_amount"] if tax_data_01 else 0.0
            )
        return

    def _add_invoice_tax_grouping_function_vals(self, vals):
        invoice = vals["invoice"]
        is_support_document = invoice.journal_id._is_support_document_type()
        self._add_document_tax_grouping_function_vals(vals)
        total_grouping_function = vals["total_grouping_function"]
        tax_grouping_function = vals["tax_grouping_function"]

        def total_grouping_function_excluding_support_document(base_line, tax_data):
            tax = tax_data and tax_data["tax"]
            if (
                is_support_document
                and tax
                and tax.l10n_co_tax_type_id.code not in {"01", "05", "06"}
            ):
                return None
            return total_grouping_function(base_line, tax_data)

        def tax_grouping_function_excluding_support_document(base_line, tax_data):
            tax = tax_data and tax_data["tax"]
            if (
                is_support_document
                and tax
                and tax.l10n_co_tax_type_id.code not in {"01", "05", "06"}
            ):
                return None
            return tax_grouping_function(base_line, tax_data)

        vals["total_grouping_function"] = (
            total_grouping_function_excluding_support_document
        )
        vals["tax_grouping_function"] = tax_grouping_function_excluding_support_document
        return

    def _is_withholding(self, tax):
        """Check if a tax is a withholding (retention) tax."""
        if tax.l10n_co_tax_type_id:
            return tax.l10n_co_tax_type_id.is_withholding_tax
        # Fallback: negative amount taxes are withholdings
        return tax.amount < 0

    def _add_document_tax_grouping_function_vals(self, vals):
        def total_grouping_function(base_line, tax_data):
            if tax_data and self._is_withholding(tax_data["tax"]):
                return None
            return True

        def tax_grouping_function(base_line, tax_data):
            tax = tax_data and tax_data["tax"]
            if not tax:
                return None

            if tax.l10n_co_tax_type_id.code == "32":
                amount = (
                    tax.amount
                    / base_line["product_id"].l10n_co_edi_ref_nominal_tax
                    * base_line["quantity"]
                )
            elif tax.l10n_co_tax_type_id.code == "34":
                amount = (
                    tax.amount
                    * 100
                    / base_line["product_id"].l10n_co_edi_ref_nominal_tax
                )
            elif tax.l10n_co_tax_type_id.code == "05":
                if iva_tax := next(
                    (
                        tax_data["tax"]
                        for tax_data in base_line["tax_details"]["taxes_data"]
                        if tax_data["tax"].l10n_co_tax_type_id.code == "01"
                    ),
                    None,
                ):
                    amount = tax.amount * 100 / iva_tax.amount
            else:
                amount = tax.amount

            is_wh = self._is_withholding(tax)
            return {
                "l10n_co_tax_type_id": tax.l10n_co_tax_type_id,
                "amount_type": tax.amount_type,
                "amount": abs(amount) if is_wh else amount,
                "is_withholding_tax": is_wh,
            }

        vals["total_grouping_function"] = total_grouping_function
        vals["tax_grouping_function"] = tax_grouping_function
        return

    def _get_cufe_cude_cuds(self, document_node, vals):
        invoice = vals["invoice"]
        is_support_document = invoice.journal_id._is_support_document_type()

        def format_float(amount, precision_digits=vals["currency_dp"]):
            return self.format_float(amount, precision_digits)

        def get_tax_amount(tax_code):
            def grouping_function(base_line, tax_data):
                if not tax_data:
                    return False
                tax = tax_data["tax"]
                code = tax.l10n_co_tax_type_id.code
                if code:
                    return code == tax_code
                if tax_code == "01" and tax.amount > 0:
                    return True
                return False

            agg = self.env["account.tax"]._aggregate_base_lines_tax_details(
                vals["base_lines"], grouping_function
            )
            agg_vals = self.env["account.tax"]._aggregate_base_lines_aggregated_values(
                agg
            )
            if True in agg_vals:
                return agg_vals[True]["tax_amount"]
            return 0.0

        journal = invoice.journal_id
        is_test = journal.l10n_co_dian_operation_mode in ("test", "demo")

        if invoice.l10n_latam_document_type_id.code in (
            "05",
            "91",
            "92",
            "95",
            "96",
        ):
            key = journal.l10n_co_dian_software_pin
        else:
            key = (
                journal.l10n_co_dian_software_technical_key_test
                if is_test
                else journal.l10n_co_dian_software_technical_key
            )

        monetary_total_tag = (
            "cac:LegalMonetaryTotal"
            if vals["document_type"] in {"invoice", "credit_note"}
            else "cac:RequestedMonetaryTotal"
        )
        supplier_vat = vals["supplier"]._l10n_co_get_vat_splited()[0]
        customer_vat = vals["customer"]._l10n_co_get_vat_splited()[0]

        cufe_cude_cuds_vals = {
            "invoice_id": document_node["cbc:ID"]["_text"],
            "issue_date": document_node["cbc:IssueDate"]["_text"],
            "issue_time": document_node["cbc:IssueTime"]["_text"],
            "ValFac": document_node[monetary_total_tag]["cbc:LineExtensionAmount"][
                "_text"
            ],
            "tax_code_01": "01",
            "ValImp1": format_float(get_tax_amount("01")),
            "tax_code_04": "04",
            "ValImp2": format_float(get_tax_amount("04")),
            "tax_code_03": "03",
            "ValImp3": format_float(get_tax_amount("03")),
            "ValTotFac": document_node[monetary_total_tag]["cbc:PayableAmount"][
                "_text"
            ],
            "supplier_company_id": supplier_vat or "",
            "customer_company_id": customer_vat or "",
            "key": key or "missing_key",
            "profile_execution_id": document_node["cbc:ProfileExecutionID"]["_text"],
        }
        if is_support_document:
            for k in (
                "tax_code_04",
                "ValImp2",
                "tax_code_03",
                "ValImp3",
            ):
                cufe_cude_cuds_vals.pop(k)

        return "".join(str(v) for v in cufe_cude_cuds_vals.values())

    def _get_invoice_node(self, vals):
        document_node = super()._get_invoice_node(vals)
        self._fill_cufe_cude_cuds(document_node, vals)
        return document_node

    def _add_invoice_accounting_supplier_party_nodes(self, document_node, vals):
        super()._add_invoice_accounting_supplier_party_nodes(document_node, vals)
        partner = vals["supplier"]
        document_node["cac:AccountingSupplierParty"]["cbc:AdditionalAccountID"] = {
            "_text": "1" if partner.is_company else "2"
        }
        return

    def _add_invoice_accounting_customer_party_nodes(self, document_node, vals):
        super()._add_invoice_accounting_customer_party_nodes(document_node, vals)
        commercial = vals["customer"].commercial_partner_id
        is_company = commercial.is_company
        document_node["cac:AccountingCustomerParty"]["cbc:AdditionalAccountID"] = {
            "_text": "1" if is_company else "2"
        }

        if not is_company:
            party = document_node["cac:AccountingCustomerParty"].get("cac:Party", {})
            party["cac:Person"] = {
                "cbc:FirstName": {"_text": commercial.name or ""},
                "cbc:FamilyName": {"_text": commercial.name or ""},
            }
        return

    def _add_invoice_payment_means_nodes(self, document_node, vals):
        invoice = vals["invoice"]
        document_node["cac:PaymentMeans"] = {
            "cbc:ID": {"_text": invoice.l10n_co_payment_term},
            "cbc:PaymentMeansCode": {"_text": invoice.l10n_co_payment_method_id.code},
            "cbc:PaymentDueDate": {"_text": invoice.invoice_date_due},
            "cbc:PaymentID": {"_text": invoice.payment_reference or invoice.name},
        }
        return

    def _fill_cufe_cude_cuds(self, document_node, vals):
        invoice = vals["invoice"]
        cufe_cude_cuds = self._get_cufe_cude_cuds(document_node, vals)
        document_node["cbc:UUID"]["_text"] = sha384(cufe_cude_cuds.encode()).hexdigest()
        document_node["cbc:Note"] = {"_text": cufe_cude_cuds}

        if invoice.currency_id != invoice.company_currency_id:
            trm = self.format_float(
                1 / invoice.invoice_currency_rate
                if invoice.invoice_currency_rate
                else 1.0,
                6,
            )
            document_node["cac:PaymentExchangeRate"] = {
                "cbc:SourceCurrencyCode": {"_text": "COP"},
                "cbc:SourceCurrencyBaseRate": {"_text": trm},
                "cbc:TargetCurrencyCode": {"_text": invoice.currency_id.name},
                "cbc:TargetCurrencyBaseRate": {"_text": "1.00"},
                "cbc:CalculationRate": {"_text": trm},
                "cbc:Date": {
                    "_text": invoice.invoice_date.isoformat()
                    if invoice.invoice_date
                    else ""
                },
            }
        return

    def _get_address_node(self, vals):
        partner = vals["partner"]
        city_code = (
            str(partner.city_id.zipcode).zfill(5)
            if partner.city_id and partner.city_id.zipcode
            else partner.zip or ""
        )
        state_code = (
            str(partner.state_id.code).zfill(2)
            if partner.state_id and partner.state_id.code
            else ""
        )
        return {
            "cbc:ID": {"_text": city_code},
            "cbc:CityName": {"_text": partner.city or ""},
            "cbc:PostalZone": {"_text": partner.zip or ""},
            "cbc:CountrySubentity": {"_text": partner.state_id.name or ""},
            "cbc:CountrySubentityCode": {"_text": state_code},
            "cac:AddressLine": {
                "cbc:Line": {
                    "_text": f"{partner.street or ''} {partner.street2 or ''}".strip()
                }
            },
            "cac:Country": {
                "cbc:IdentificationCode": {"_text": partner.country_id.code},
                "cbc:Name": {
                    "_text": partner.country_id.name,
                    "languageID": "es" if partner.country_code == "CO" else "en",
                },
            },
        }

    REGIMEN_TO_TAX_SCHEME = {
        "48": ("01", "IVA"),  # Responsable IVA
        "49": ("ZZ", "No aplica"),  # No responsable IVA
    }

    def _get_party_tax_scheme(self, partner):
        """Return TaxScheme dict for PartyTaxScheme (table 13.2.6.2)."""
        regimen = partner.l10n_co_regimen_fiscal
        code, name = self.REGIMEN_TO_TAX_SCHEME.get(regimen, ("ZZ", "No aplica"))
        return {
            "cbc:ID": {"_text": code},
            "cbc:Name": {"_text": name},
        }

    def _get_corporate_prefix(self, invoice):
        """Return the correct prefix for CorporateRegistrationScheme.

        Invoices and support documents use the resolution prefix
        from the journal. NC/ND use the document type prefix since
        they share the journal with invoices.
        """
        doc_code = invoice.l10n_latam_document_type_id.code
        if doc_code in ("01", "02", "03", "05"):
            prefix, _, _ = invoice.journal_id._get_electronic_document_numbering_range()
            return prefix or invoice.journal_id.code
        return (
            invoice.l10n_latam_document_type_id.doc_code_prefix
            or invoice.journal_id.code
        )

    def _get_party_node(self, vals):
        partner = vals["partner"]
        invoice = vals["invoice"]
        role = vals["role"]
        commercial_partner = partner.commercial_partner_id
        vat, verification_code = commercial_partner._l10n_co_get_vat_splited()
        is_foreign = commercial_partner.country_id.code != "CO"

        if is_foreign:
            doc_code = (
                commercial_partner.l10n_latam_identification_type_id.l10n_co_document_code
                or "42"  # Default: ID Extranjera
            )
            return {
                "cac:PartyIdentification": {
                    "cbc:ID": {
                        "_text": vat,
                        "schemeName": doc_code,
                        "schemeAgencyID": "195",
                        "schemeAgencyName": (
                            "CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)"
                        ),
                    }
                }
                if vat
                else None,
                "cac:PartyName": {"cbc:Name": {"_text": partner.display_name}},
                "cac:PhysicalLocation": {
                    "cac:Address": {
                        "cac:Country": {
                            "cbc:IdentificationCode": {
                                "_text": commercial_partner.country_id.code
                            },
                            "cbc:Name": {
                                "_text": commercial_partner.country_id.name,
                                "languageID": "en",
                            },
                        },
                    }
                },
                "cac:PartyTaxScheme": {
                    "cbc:RegistrationName": {"_text": commercial_partner.name},
                    "cbc:CompanyID": {
                        "_text": vat,
                        "schemeName": doc_code,
                        "schemeAgencyName": "CO, DIAN (Dirección de Impuestos "
                        "y Aduanas Nacionales)",
                        "schemeAgencyID": "195",
                    },
                    "cbc:TaxLevelCode": {"_text": "R-99-PN"},
                    "cac:TaxScheme": {
                        "cbc:ID": {"_text": "ZZ"},
                        "cbc:Name": {"_text": "No aplica"},
                    },
                },
                "cac:PartyLegalEntity": {
                    "cbc:RegistrationName": {"_text": commercial_partner.name},
                    "cbc:CompanyID": {
                        "_text": vat,
                        "schemeName": doc_code,
                        "schemeAgencyName": "CO, DIAN (Dirección de Impuestos "
                        "y Aduanas Nacionales)",
                        "schemeAgencyID": "195",
                    },
                },
                "cac:Contact": {
                    "cbc:Name": {"_text": partner.name},
                    "cbc:Telephone": {"_text": partner.phone},
                    "cbc:ElectronicMail": {"_text": partner.email},
                },
            }

        doc_code = (
            commercial_partner.l10n_latam_identification_type_id.l10n_co_document_code
            or "13"  # Default: Cédula de ciudadanía
        )

        return {
            "cbc:IndustryClassificationCode": {
                "_text": invoice.company_id.l10n_co_ciiu_id.code
            }
            if role == "supplier" and invoice.l10n_latam_document_type_id.code != "95"
            else None,
            "cac:PartyIdentification": {
                "cbc:ID": {
                    "_text": vat,
                    "schemeName": doc_code,
                    "schemeAgencyID": "195",
                    "schemeAgencyName": (
                        "CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)"
                    ),
                    "schemeID": verification_code if verification_code else None,
                }
            }
            if vat
            else None,
            "cac:PartyName": {"cbc:Name": {"_text": partner.display_name}},
            "cac:PhysicalLocation": {
                "cac:Address": self._get_address_node({"partner": partner})
            }
            if partner.vat != BUYER_NOT_IDENTIFIED_VAT
            else None,
            "cac:PartyTaxScheme": {
                "cbc:RegistrationName": {"_text": commercial_partner.name},
                "cbc:CompanyID": {
                    "_text": vat,
                    "schemeName": doc_code,
                    "schemeAgencyName": "CO, DIAN (Dirección de Impuestos "
                    "y Aduanas Nacionales)",
                    "schemeAgencyID": "195",
                    "schemeID": verification_code if verification_code else None,
                },
                "cbc:TaxLevelCode": {
                    "_text": ";".join(
                        commercial_partner.l10n_co_responsibility_ids.mapped("code")
                    )
                },
                "cac:RegistrationAddress": self._get_address_node(
                    {"partner": commercial_partner}
                )
                if commercial_partner.vat != BUYER_NOT_IDENTIFIED_VAT
                else None,
                "cac:TaxScheme": self._get_party_tax_scheme(commercial_partner),
            },
            "cac:PartyLegalEntity": {
                "cbc:RegistrationName": {"_text": commercial_partner.name},
                "cbc:CompanyID": {
                    "_text": vat,
                    "schemeName": doc_code,
                    "schemeAgencyName": "CO, DIAN (Dirección de Impuestos "
                    "y Aduanas Nacionales)",
                    "schemeAgencyID": "195",
                    "schemeID": verification_code if verification_code else None,
                },
                "cac:CorporateRegistrationScheme": {
                    "cbc:ID": {"_text": self._get_corporate_prefix(invoice)},
                    "cbc:Name": {"_text": vat},
                }
                if role == "supplier"
                else None,
            }
            if partner.vat != BUYER_NOT_IDENTIFIED_VAT
            else None,
            "cac:Contact": {
                "cbc:Name": {"_text": partner.name},
                "cbc:Telephone": {"_text": partner.phone},
                "cbc:ElectronicMail": {"_text": partner.email},
            }
            if partner.vat != BUYER_NOT_IDENTIFIED_VAT
            else None,
        }

    def _get_discrepancy_response_node(self, invoice):
        """Get DiscrepancyResponse for credit/debit notes.

        For notes WITH reference (operation type 20, 30):
            ReferenceID + ResponseCode + Description
        For notes WITHOUT reference (operation type 22, 32):
            ResponseCode + Description (no ReferenceID)

        ResponseCode comes from l10n_co_discrepancy_response_code:
            NC: 1-5 (ConceptoNotaCredito-2.1)
            ND: 1-4 (ConceptoNotaDebito-2.1)
        """
        is_credit = invoice.move_type in ("out_refund", "in_refund")
        is_debit = bool(invoice.debit_origin_id)
        if not is_credit and not is_debit:
            return None

        discrepancy = invoice.l10n_co_discrepancy_response_code or ""
        dian_code = discrepancy.split("_")[-1] if "_" in discrepancy else "1"
        discrepancy_label = dict(
            invoice._fields["l10n_co_discrepancy_response_code"].selection
        ).get(discrepancy, "")
        if " - " in discrepancy_label:
            discrepancy_label = discrepancy_label.split(" - ", 1)[1]

        reference = invoice.reversed_entry_id if is_credit else invoice.debit_origin_id

        node = {}
        if reference:
            node["cbc:ReferenceID"] = {"_text": reference.name}
        node["cbc:ResponseCode"] = {"_text": dian_code}
        node["cbc:Description"] = {"_text": discrepancy_label}
        return node

    def _get_billing_reference_node(self, invoice):
        """Get the BillingReference node for credit/debit notes.

        Only present when the note references an existing invoice.
        """
        reference_invoice = None
        if (
            invoice.move_type in ("out_refund", "in_refund")
            and invoice.reversed_entry_id
        ):
            reference_invoice = invoice.reversed_entry_id
        elif invoice.debit_origin_id:
            reference_invoice = invoice.debit_origin_id

        if reference_invoice:
            ref_doc_code = reference_invoice.l10n_latam_document_type_id.code
            scheme_name = UUID_SCHEME_NAME.get(ref_doc_code, "CUFE-SHA384")
            return {
                "cac:InvoiceDocumentReference": {
                    "cbc:ID": {"_text": reference_invoice.name},
                    "cbc:UUID": {
                        "_text": reference_invoice.l10n_co_edi_cufe_cude_ref,
                        "schemeName": scheme_name,
                    },
                    "cbc:IssueDate": {
                        "_text": reference_invoice.invoice_date.isoformat()
                    },
                }
            }
        return None

    def _add_document_tax_total_nodes(self, document_node, vals):
        base_lines_aggregated_tax_details = {}
        aggregated_tax_details = {}
        base_unit_measure_by_grouping_key = defaultdict(float)

        def grouping_function(base_line, tax_data):
            grouping_key = vals["tax_grouping_function"](base_line, tax_data)
            if grouping_key is not None and tax_data[
                "tax"
            ].l10n_co_tax_type_id.code in ["32", "34"]:
                base_unit_measure_by_grouping_key[frozendict(grouping_key)] += (
                    base_line["product_id"].l10n_co_edi_ref_nominal_tax
                    * (
                        base_line["quantity"]
                        if tax_data["tax"].l10n_co_tax_type_id.code == "34"
                        else 1
                    )
                )
            return grouping_key

        base_lines_aggregated_tax_details = self.env[
            "account.tax"
        ]._aggregate_base_lines_tax_details(
            vals["base_lines"],
            grouping_function,
        )
        aggregated_tax_details = self.env[
            "account.tax"
        ]._aggregate_base_lines_aggregated_values(
            base_lines_aggregated_tax_details,
        )

        grouped_aggregated_tax_details_by_tax_type = {
            "tax": defaultdict(dict),
            "withholding_tax": defaultdict(dict),
        }

        for grouping_key, values in aggregated_tax_details.items():
            if grouping_key:
                l10n_co_tax_type_id = grouping_key["l10n_co_tax_type_id"]
                key = "withholding_tax" if grouping_key["is_withholding_tax"] else "tax"
                grouped_aggregated_tax_details_by_tax_type[key][l10n_co_tax_type_id][
                    grouping_key
                ] = values
                values["base_unit_measure"] = base_unit_measure_by_grouping_key[
                    grouping_key
                ]

        document_node["cac:TaxTotal"] = [
            self._get_tax_total_node(
                {**vals, "aggregated_tax_details": tax_details, "role": "document"}
            )
            for tax_details in grouped_aggregated_tax_details_by_tax_type[
                "tax"
            ].values()
        ]
        withholding_nodes = [
            self._get_tax_total_node(
                {
                    **vals,
                    "aggregated_tax_details": tax_details,
                    "role": "document",
                    "sign": -1,
                }
            )
            for tax_details in grouped_aggregated_tax_details_by_tax_type[
                "withholding_tax"
            ].values()
        ]
        if withholding_nodes:
            document_node["cac:WithholdingTaxTotal"] = withholding_nodes

    def _add_invoice_monetary_total_nodes(self, document_node, vals):
        super()._add_invoice_monetary_total_nodes(document_node, vals)
        prepaid_amount = sum(p["amount"] for p in vals["prepayments"])
        monetary_total_tag = self._get_tags_for_document_type(vals)["monetary_total"]
        document_node[monetary_total_tag].update(
            {
                "cbc:PrepaidAmount": {
                    "_text": self.format_float(prepaid_amount, vals["currency_dp"]),
                    "currencyID": vals["currency_name"],
                }
                if prepaid_amount
                else None,
                "cbc:PayableAmount": {
                    "_text": document_node[monetary_total_tag][
                        "cbc:TaxInclusiveAmount"
                    ]["_text"],
                    "currencyID": vals["currency_name"],
                },
            }
        )
        return

    def _get_tax_subtotal_node(self, vals):
        tax_details = vals["tax_details"]
        grouping_key = vals["grouping_key"]

        if grouping_key["l10n_co_tax_type_id"].code not in ["32", "34"]:
            # Use parent to get properly templated node, then
            # remove Percent from TaxSubtotal level (DIAN requires
            # it only inside TaxCategory, not at TaxSubtotal).
            tax_subtotal_node = super()._get_tax_subtotal_node(vals)
            tax_subtotal_node["cbc:Percent"] = None
        else:
            tax_subtotal_node = {
                "cbc:TaxAmount": {
                    "_text": self.format_float(
                        tax_details["tax_amount"], vals["currency_dp"]
                    ),
                    "currencyID": vals["currency_name"],
                },
                "cbc:BaseUnitMeasure": {
                    "_text": tax_details["base_unit_measure"],
                    "unitCode": "LTR"
                    if grouping_key["l10n_co_tax_type_id"].code == "32"
                    else "ML",
                },
                "cbc:PerUnitAmount": {
                    "_text": self.format_float(grouping_key["amount"], 2),
                    "currencyID": vals["currency_name"],
                },
                "cac:TaxCategory": self._get_tax_category_node(vals),
            }

        return tax_subtotal_node

    def _get_tax_category_node(self, vals):
        grouping_key = vals["grouping_key"]
        tax_type = grouping_key.get("l10n_co_tax_type_id")
        tax_code = tax_type.code if tax_type else "01"
        tax_name = tax_type.name if tax_type else "IVA"
        if tax_name == "No Aplica":
            tax_name = "No aplica"
        return {
            "cbc:Percent": {"_text": FloatFmt(abs(grouping_key["amount"]), 2, 3)}
            if tax_code not in {"32", "34"}
            else None,
            "cac:TaxScheme": {
                "cbc:ID": {"_text": tax_code},
                "cbc:Name": {"_text": tax_name},
            },
        }

    def _add_document_line_tax_category_nodes(self, line_node, vals):
        # DIAN does not use ClassifiedTaxCategory on invoice lines
        pass

    def _add_document_line_amount_nodes(self, line_node, vals):
        super()._add_document_line_amount_nodes(line_node, vals)
        base_line = vals["base_line"]
        uom = base_line["product_uom_id"].unece_code_id.code or "94"
        quantity_tag = self._get_tags_for_document_type(vals)["line_quantity"]
        line_node[quantity_tag]["unitCode"] = uom
        return

    def _add_invoice_line_note_nodes(self, line_node, vals):
        invoice = vals["invoice"]
        base_line = vals["base_line"]
        if invoice.l10n_latam_document_type_id.code == "09" and base_line["product_id"]:
            line_node["cbc:Note"] = {
                "_text": f"Contrato de servicios AIU por \
Concepto de: {base_line['product_id'].name}"
            }
        return

    def _add_invoice_line_period_nodes(self, line_node, vals):
        super()._add_invoice_line_period_nodes(line_node, vals)
        line = vals["base_line"]["record"]
        invoice = vals["invoice"]
        is_support_document = invoice.journal_id._is_support_document_type()
        if is_support_document:
            line_node["cac:InvoicePeriod"] = {
                "cbc:StartDate": {"_text": line.move_id.invoice_date},
                "cbc:DescriptionCode": {"_text": 1},
                "cbc:Description": {"_text": "Por operación"},
            }
        return

    def _add_document_line_tax_total_nodes(self, line_node, vals):
        base_unit_measure_by_grouping_key = defaultdict(float)

        def grouping_function(base_line, tax_data):
            grouping_key = vals["tax_grouping_function"](base_line, tax_data)
            if grouping_key is not None and tax_data[
                "tax"
            ].l10n_co_tax_type_id.code in ["32", "34"]:
                base_unit_measure_by_grouping_key[frozendict(grouping_key)] += (
                    base_line["product_id"].l10n_co_edi_ref_nominal_tax
                    * (
                        base_line["quantity"]
                        if tax_data["tax"].l10n_co_tax_type_id.code == "34"
                        else 1
                    )
                )
            return grouping_key

        aggregated_tax_details = self.env[
            "account.tax"
        ]._aggregate_base_line_tax_details(
            vals["base_line"],
            grouping_function,
        )

        grouped_aggregated_tax_details_by_tax_type = {
            "tax": defaultdict(dict),
            "withholding_tax": defaultdict(dict),
        }

        for grouping_key, values in aggregated_tax_details.items():
            if grouping_key:
                l10n_co_tax_type_id = grouping_key["l10n_co_tax_type_id"]
                key = "withholding_tax" if grouping_key["is_withholding_tax"] else "tax"
                grouped_aggregated_tax_details_by_tax_type[key][l10n_co_tax_type_id][
                    grouping_key
                ] = values
                values["base_unit_measure"] = base_unit_measure_by_grouping_key[
                    grouping_key
                ]

        line_node["cac:TaxTotal"] = [
            self._get_tax_total_node(
                {**vals, "aggregated_tax_details": tax_details, "role": "line"}
            )
            for tax_details in grouped_aggregated_tax_details_by_tax_type[
                "tax"
            ].values()
        ]
        withholding_nodes = [
            self._get_tax_total_node(
                {
                    **vals,
                    "aggregated_tax_details": tax_details,
                    "role": "line",
                    "sign": -1,
                }
            )
            for tax_details in grouped_aggregated_tax_details_by_tax_type[
                "withholding_tax"
            ].values()
        ]
        if withholding_nodes:
            line_node["cac:WithholdingTaxTotal"] = withholding_nodes
        return

    def _add_invoice_line_item_nodes(self, line_node, vals):
        super()._add_invoice_line_item_nodes(line_node, vals)
        base_line = vals["base_line"]
        line = base_line["record"]
        invoice = vals["invoice"]
        is_support_document = invoice.journal_id._is_support_document_type()
        product = base_line["product_id"]
        if line.move_id.l10n_latam_document_type_id.code in ("02", "30"):
            line_node["cac:Item"]["cbc:BrandName"] = {
                "_text": product.product_brand or ""
            }
            line_node["cac:Item"]["cbc:ModelName"] = {
                "_text": product.product_model or ""
            }

        if product.default_code:
            line_node["cac:Item"]["cac:SellersItemIdentification"] = {
                "cbc:ID": {"_text": product.default_code},
                "cbc:ExtendedID": {"_text": product.default_code}
                if is_support_document
                else None,
            }

        unspsc = (
            product.product_tmpl_id.product_unspsc_id
            if hasattr(product.product_tmpl_id, "product_unspsc_id")
            else False
        )
        if unspsc:
            line_node["cac:Item"]["cac:StandardItemIdentification"] = {
                "cbc:ID": {
                    "_text": unspsc.product_code,
                    "schemeID": "001",
                    "schemeAgencyID": "10",
                    "schemeName": "UNSPSC",
                }
            }
        elif product.default_code:
            line_node["cac:Item"]["cac:StandardItemIdentification"] = {
                "cbc:ID": {
                    "_text": product.default_code,
                    "schemeID": "999",
                    "schemeName": "Estándar de adopción del contribuyente",
                }
            }

        if product.barcode:
            line_node["cac:Item"]["cac:AdditionalItemIdentification"] = {
                "cbc:ID": {
                    "_text": product.barcode,
                    "schemeID": "0160",
                    "schemeName": "GTIN",
                }
            }
        return

    def _get_line_discount_allowance_charge_node(self, vals):
        discount_node = super()._get_line_discount_allowance_charge_node(vals)
        if discount_node:
            discount_node["cbc:AllowanceChargeReasonCode"] = {"_text": "00"}
            discount_node["cbc:MultiplierFactorNumeric"] = {
                "_text": vals["base_line"]["discount"]
            }
            discount_node["cbc:BaseAmount"] = {
                "_text": self.format_float(vals["gross_subtotal"], vals["currency_dp"]),
                "currencyID": vals["currency_name"],
            }
        return discount_node

    def _add_document_line_price_nodes(self, line_node, vals):
        super()._add_document_line_price_nodes(line_node, vals)
        base_line = vals["base_line"]
        uom = base_line["product_uom_id"].unece_code_id.code or "94"
        line_node["cac:Price"]["cbc:BaseQuantity"] = {
            "_text": base_line["quantity"],
            "unitCode": uom,
        }
        return

    def _get_document_nsmap(self, vals):
        nsmap = super()._get_document_nsmap(vals)
        nsmap.update(
            {
                "ext": (
                    "urn:oasis:names:specification:ubl:schema:xsd"
                    ":CommonExtensionComponents-2"
                ),
                "ds": "http://www.w3.org/2000/09/xmldsig#",
                "sts": (
                    "dian:gov:co:facturaelectronica:Structures-2-1"
                    if vals["document_type"] == "invoice"
                    else "http://www.dian.gov.co/contratos"
                    "/facturaelectronica/v1/Structures"
                ),
                "xades": "http://uri.etsi.org/01903/v1.3.2#",
                "xades141": "http://uri.etsi.org/01903/v1.4.1#",
                "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            }
        )
        return nsmap

    def _fill_dian_data(self, xml_content, record):
        """Fill invoice data for DIAN submission.

        Injects ext:UBLExtensions with:
        - UBLExtension[1]: DianExtensions (InvoiceControl, InvoiceSource,
          SoftwareProvider, SoftwareSecurityCode, AuthorizationProvider, QRCode)
        - UBLExtension[2]: Empty placeholder for digital signature
        """
        NS_EXT = (
            "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
        )
        NS_CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"

        is_support_document = record.journal_id._is_support_document_type()
        doc_code = record.l10n_latam_document_type_id.code
        if doc_code in ("01", "02", "03", "04"):
            NS_STS = "dian:gov:co:facturaelectronica:Structures-2-1"
        else:
            NS_STS = "http://www.dian.gov.co/contratos/facturaelectronica/v1/Structures"

        if isinstance(xml_content, str):
            xml_content = xml_content.encode("utf-8")

        root = etree.fromstring(xml_content)

        ubl_extensions = etree.Element(etree.QName(NS_EXT, "UBLExtensions"))
        ubl_ext_1 = etree.SubElement(
            ubl_extensions, etree.QName(NS_EXT, "UBLExtension")
        )
        ext_content_1 = etree.SubElement(
            ubl_ext_1, etree.QName(NS_EXT, "ExtensionContent")
        )
        dian_extensions = etree.SubElement(
            ext_content_1, etree.QName(NS_STS, "DianExtensions")
        )

        journal = record.journal_id
        (
            _operation_mode,
            software_id,
            software_pin,
            technical_key,
            resolution,
            start_date,
            end_date,
            start_number,
            end_number,
        ) = journal._get_l10n_co_dian_self_params()
        prefix, _, _ = journal._get_electronic_document_numbering_range()
        supplier_vat, supplier_dv = (
            record.company_id.partner_id._l10n_co_get_vat_splited()
        )
        supplier_vat = supplier_vat or ""

        if doc_code not in ("91", "92", "95", "96"):
            if is_support_document:
                control_tag = "SupportDocumentControl"
            else:
                control_tag = "InvoiceControl"

            invoice_control = etree.SubElement(
                dian_extensions, etree.QName(NS_STS, control_tag)
            )
            etree.SubElement(
                invoice_control, etree.QName(NS_STS, "InvoiceAuthorization")
            ).text = str(resolution or "")
            auth_period = etree.SubElement(
                invoice_control, etree.QName(NS_STS, "AuthorizationPeriod")
            )
            etree.SubElement(auth_period, etree.QName(NS_CBC, "StartDate")).text = (
                str(start_date) if start_date else ""
            )
            etree.SubElement(auth_period, etree.QName(NS_CBC, "EndDate")).text = (
                str(end_date) if end_date else ""
            )
            authorized_invoices = etree.SubElement(
                invoice_control, etree.QName(NS_STS, "AuthorizedInvoices")
            )
            etree.SubElement(
                authorized_invoices, etree.QName(NS_STS, "Prefix")
            ).text = prefix or ""
            etree.SubElement(
                authorized_invoices, etree.QName(NS_STS, "From")
            ).text = str(start_number)
            etree.SubElement(authorized_invoices, etree.QName(NS_STS, "To")).text = str(
                end_number
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
        provider_id.set("schemeID", supplier_dv or "")
        provider_id.set("schemeName", "31")

        sw_id = etree.SubElement(sw_provider, etree.QName(NS_STS, "SoftwareID"))
        sw_id.text = software_id or ""
        sw_id.set("schemeAgencyID", "195")
        sw_id.set(
            "schemeAgencyName",
            "CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)",
        )

        invoice_number = (record.name or "").replace(" ", "")
        security_code_input = (
            (software_id or "") + (software_pin or "") + invoice_number
        )
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

        customer_vat, _ = (
            record.partner_id.commercial_partner_id._l10n_co_get_vat_splited()
        )
        customer_vat = customer_vat or ""
        cufe_element = root.find(
            ".//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}UUID"
        )
        cufe = cufe_element.text if cufe_element is not None else ""

        line_ext_element = root.find(
            ".//{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}"
            "LegalMonetaryTotal/"
            "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}"
            "LineExtensionAmount"
        )
        if line_ext_element is None:
            line_ext_element = root.find(
                ".//{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}"
                "RequestedMonetaryTotal/"
                "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}"
                "LineExtensionAmount"
            )
        val_fac = line_ext_element.text if line_ext_element is not None else "0.00"

        val_iva = "0.00"
        val_otro_im = "0.00"
        NS_CAC_FULL = (
            "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
        )
        NS_CBC_FULL = (
            "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
        )
        iva_total = 0.0
        otros_total = 0.0
        for tax_total in root.findall(f".//{{{NS_CAC_FULL}}}TaxTotal"):
            tax_subtotals = tax_total.findall(f"{{{NS_CAC_FULL}}}TaxSubtotal")
            for subtotal in tax_subtotals:
                tax_scheme = subtotal.find(
                    f"{{{NS_CAC_FULL}}}TaxCategory/{{{NS_CAC_FULL}}}TaxScheme"
                    f"/{{{NS_CBC_FULL}}}ID"
                )
                tax_amount_el = subtotal.find(f"{{{NS_CBC_FULL}}}TaxAmount")
                if tax_scheme is not None and tax_amount_el is not None:
                    try:
                        amount = float(tax_amount_el.text)
                    except (ValueError, TypeError):
                        amount = 0.0
                    if tax_scheme.text == "01":
                        iva_total += amount
                    elif tax_scheme.text != "01":
                        otros_total += amount
        val_iva = f"{iva_total:.2f}"
        val_otro_im = f"{otros_total:.2f}"

        total_element = root.find(
            f".//{{{NS_CAC_FULL}}}LegalMonetaryTotal/{{{NS_CBC_FULL}}}PayableAmount"
        )
        if total_element is None:
            total_element = root.find(
                f".//{{{NS_CAC_FULL}}}RequestedMonetaryTotal"
                f"/{{{NS_CBC_FULL}}}PayableAmount"
            )
        val_tol_fac = total_element.text if total_element is not None else "0.00"

        issue_date_el = root.find(f".//{{{NS_CBC_FULL}}}IssueDate")
        issue_date = issue_date_el.text if issue_date_el is not None else ""
        issue_time_el = root.find(f".//{{{NS_CBC_FULL}}}IssueTime")
        issue_time = issue_time_el.text if issue_time_el is not None else ""

        # URL per Anexo Técnico v1.9, section 11.7.1
        catalog_url = (
            "https://catalogo-vpfe-hab.dian.gov.co"
            if journal.l10n_co_dian_operation_mode in ("test", "demo")
            else "https://catalogo-vpfe.dian.gov.co"
        )
        qr_code = etree.SubElement(dian_extensions, etree.QName(NS_STS, "QRCode"))
        qr_code.text = (
            f"NumFac: {record.name}\n"
            f"FecFac: {issue_date}\n"
            f"HorFac: {issue_time}\n"
            f"NitFac: {supplier_vat}\n"
            f"DocAdq: {customer_vat}\n"
            f"ValFac: {val_fac}\n"
            f"ValIva: {val_iva}\n"
            f"ValOtroIm: {val_otro_im}\n"
            f"ValTolFac: {val_tol_fac}\n"
            f"CUFE: {cufe}\n"
            f"{catalog_url}/document/searchqr?documentkey={cufe}"
        )

        ubl_ext_2 = etree.SubElement(
            ubl_extensions, etree.QName(NS_EXT, "UBLExtension")
        )
        etree.SubElement(ubl_ext_2, etree.QName(NS_EXT, "ExtensionContent"))

        root.insert(0, ubl_extensions)

        return etree.tostring(root, xml_declaration=True, encoding="UTF-8")
