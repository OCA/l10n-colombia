# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import logging

from odoo import models
from odoo.exceptions import UserError

from ..utils.constants import (
    DIAN_ACTION_BASE,
    DOCUMENT_TYPE_CONFIG,
)

_logger = logging.getLogger(__name__)


class AccountEdiFormat(models.Model):
    _inherit = "account.edi.format"

    def _get_move_applicability(self, move):
        self.ensure_one()
        if self.code != "l10n_co_dian_self":
            return super()._get_move_applicability(move)

        if not move._is_l10n_co_electronic_document_enabled():
            return None

        is_outgoing = move.move_type in ("out_invoice", "out_refund")
        is_support_doc = (
            move.move_type in ("in_invoice", "in_refund")
            and move.journal_id._is_support_document_type()
        )
        if is_outgoing or is_support_doc:
            return {
                "post": self._l10n_co_post_invoices,
                "edi_content": self._l10n_co_get_edi_content,
            }
        return None

    def _needs_web_services(self):
        self.ensure_one()
        if self.code == "l10n_co_dian_self":
            return True
        return super()._needs_web_services()

    def _is_compatible_with_journal(self, journal):
        self.ensure_one()
        if self.code == "l10n_co_dian_self":
            return (
                journal.type in ("sale", "purchase")
                and journal.company_id.account_fiscal_country_id.code == "CO"
                and journal.l10n_latam_use_documents
            )
        return super()._is_compatible_with_journal(journal)

    def _is_enabled_by_default_on_journal(self, journal):
        self.ensure_one()
        if self.code == "l10n_co_dian_self":
            return True
        return super()._is_enabled_by_default_on_journal(journal)

    def _check_move_configuration(self, move):
        self.ensure_one()
        if self.code != "l10n_co_dian_self":
            return super()._check_move_configuration(move)

        errors = []
        journal = move.journal_id
        is_demo = journal._is_demo_mode()

        if is_demo:
            prefix, start_number, _end_number = (
                journal._get_electronic_document_numbering_range()
            )
            if not prefix or not start_number:
                errors.append(
                    self.env._(
                        "Diario: Debe configurar al menos el prefijo y "
                        "número de inicio en el rango de numeración."
                    )
                )
        else:
            journal_params = journal._get_l10n_co_dian_self_params()
            if not all(journal_params):
                errors.append(
                    self.env._(
                        "Diario: Debe configurar el rango de numeración "
                        "de la facturación electrónica."
                    )
                )

        is_nc_nd_no_ref = (
            move.move_type in ("out_refund", "in_refund") and not move.reversed_entry_id
        )
        if is_nc_nd_no_ref and (
            not move.l10n_co_invoice_period_start or not move.l10n_co_invoice_period_end
        ):
            errors.append(
                self.env._(
                    "NC/ND sin referencia: Debe informar el "
                    "Periodo de Inicio y Periodo de Fin del "
                    "período de facturación que modifica."
                )
            )

        company_params = move.company_id._get_l10n_co_dian_self_params()
        if not all(company_params):
            errors.append(
                self.env._(
                    "Empresa: Debe configurar los parámetros fiscales "
                    "para la generación de documentos electrónicos."
                )
            )

        partner_missing = move.partner_id._check_l10n_co_dian_self_params()
        if partner_missing:
            errors.append(
                self.env._(
                    "Cliente (%(name)s): Falta configurar: %(fields)s.",
                    name=move.partner_id.commercial_partner_id.name,
                    fields=", ".join(partner_missing),
                )
            )

        move_line_params = move.line_ids._get_l10n_co_dian_self_params()
        if not move_line_params or not all(move_line_params):
            errors.append(
                self.env._(
                    "Productos: Deben tener configurados los parámetros "
                    "fiscales para la generación de documentos electrónicos "
                    "(código UNSPSC o referencia interna, impuesto, "
                    "unidad de medida)."
                )
            )

        taxes_without_type = move.invoice_line_ids.mapped("tax_ids").filtered(
            lambda t: not t.l10n_co_tax_type_id
        )
        if taxes_without_type:
            tax_names = ", ".join(taxes_without_type.mapped("name"))
            errors.append(
                self.env._(
                    "Impuestos sin tipo DIAN configurado: "
                    "%(taxes)s. Configure el campo 'Tipo de "
                    "impuesto DIAN' en cada impuesto.",
                    taxes=tax_names,
                )
            )

        if not is_demo:
            certificate = self.env["certificate.certificate"].search(
                [
                    ("company_id", "=", move.company_id.id),
                    ("is_valid", "=", True),
                    ("active", "=", True),
                ],
                limit=1,
            )
            if not certificate:
                errors.append(
                    self.env._(
                        "La empresa debe tener configurado un certificado válido."
                    )
                )
        self._check_export_invoice_configuration(move, errors)
        self._check_nc_nd_configuration(move, errors)

        return errors

    def _check_export_invoice_configuration(self, move, errors):
        """Validate export invoice specific configuration."""
        if move.l10n_latam_document_type_id.code != "02":
            return
        partner_country = move.partner_id.commercial_partner_id.country_id.code
        if partner_country == "CO":
            errors.append(
                self.env._(
                    "Factura de exportación: El cliente no puede "
                    "tener país Colombia. Seleccione un cliente "
                    "con país extranjero."
                )
            )
        if move.currency_id.name != "USD":
            errors.append(
                self.env._(
                    "Factura de exportación: La moneda del documento "
                    "debe ser USD (Dólar estadounidense)."
                )
            )
        products_no_brand = move.invoice_line_ids.filtered(
            lambda ln: ln.display_type == "product"
            and ln.product_id
            and not ln.product_id.product_brand
        ).mapped("product_id.name")
        if products_no_brand:
            errors.append(
                self.env._(
                    "Factura de exportación: Los productos "
                    "deben tener Marca configurada: %(p)s.",
                    p=", ".join(products_no_brand),
                )
            )
        products_no_model = move.invoice_line_ids.filtered(
            lambda ln: ln.display_type == "product"
            and ln.product_id
            and not ln.product_id.product_model
        ).mapped("product_id.name")
        if products_no_model:
            errors.append(
                self.env._(
                    "Factura de exportación: Los productos "
                    "deben tener Modelo configurado: %(p)s.",
                    p=", ".join(products_no_model),
                )
            )

    def _check_nc_nd_configuration(self, move, errors):
        """Validate credit/debit note specific configuration."""
        is_credit = move.move_type in ("out_refund", "in_refund")
        is_debit = bool(move.debit_origin_id)

        if not (is_credit or is_debit):
            return

        discrepancy = move.l10n_co_discrepancy_response_code
        if not discrepancy:
            errors.append(
                self.env._(
                    "Debe seleccionar el Concepto de Corrección "
                    "para notas crédito y notas débito."
                )
            )
        else:
            if is_credit and not discrepancy.startswith("nc_"):
                errors.append(
                    self.env._(
                        "El Concepto de Corrección debe ser de tipo "
                        "Nota Crédito (NC) para este documento."
                    )
                )
            elif is_debit and not discrepancy.startswith("nd_"):
                errors.append(
                    self.env._(
                        "El Concepto de Corrección debe ser de tipo "
                        "Nota Débito (ND) para este documento."
                    )
                )

        ref_invoice = move.reversed_entry_id if is_credit else move.debit_origin_id
        if ref_invoice:
            if not ref_invoice.l10n_co_edi_cufe_cude_ref:
                errors.append(
                    self.env._(
                        "La factura referenciada (%(name)s) no tiene "
                        "CUFE/CUDE. Debe haber sido enviada y aceptada "
                        "por la DIAN antes de generar una nota.",
                        name=ref_invoice.name,
                    )
                )
            if ref_invoice.l10n_co_dian_status not in (
                "accepted",
                "sent",
            ):
                errors.append(
                    self.env._(
                        "La factura referenciada (%(name)s) no ha sido "
                        "aceptada por la DIAN (estado: %(status)s).",
                        name=ref_invoice.name,
                        status=dict(
                            ref_invoice._fields["l10n_co_dian_status"].selection
                        ).get(ref_invoice.l10n_co_dian_status, "N/A"),
                    )
                )

    # -------------------------------------------------------------------------
    # Direct orchestration
    # -------------------------------------------------------------------------

    def _l10n_co_post_invoices(self, invoices):
        """Generate, sign, and send Colombian electronic invoices to DIAN.

        :returns: dict {move: {'success': True, 'attachment': att} | {'error': msg}}
        """
        result = {}
        service = self.env["l10n_co.dian.self.service"]
        for move in invoices:
            try:
                journal = move.journal_id
                mode = journal.l10n_co_dian_operation_mode
                is_demo = journal._is_demo_mode()
                doc_config = self._l10n_co_get_doc_config(move)
                doc_prefix = doc_config["dian_file_prefix"]

                dian_xml_name = service._get_dian_filename(move, doc_prefix)
                dian_ad_name = service._get_dian_filename(move, "ad")

                signed_xml, signer = service._generate_signed_xml(move)
                service._save_audit_attachment(
                    move,
                    "xml_firmado",
                    signed_xml,
                    dian_filename=dian_xml_name,
                )

                action_key = "action_test" if mode == "test" else "action"
                action_url = DIAN_ACTION_BASE + doc_config[action_key]
                soap = service._build_soap_envelope(
                    move,
                    signed_xml,
                    action_url,
                    signer,
                    dian_xml_filename=dian_xml_name,
                )

                service._save_audit_attachment(
                    move,
                    "soap_envelope",
                    soap,
                )

                if is_demo:
                    response = service._build_demo_response(move, mode)
                else:
                    response = service._send_to_dian(journal, soap)
                service._save_audit_attachment(move, "respuesta_dian", response)

                tag_key = "response_tag_test" if mode == "test" else "response_tag"
                response_data = service._process_response(
                    move, response, doc_config[tag_key]
                )
                application_response_xml = (
                    response_data.get("application_response")
                    if isinstance(response_data, dict)
                    else None
                )

                move.invalidate_recordset(
                    ["l10n_co_dian_status", "l10n_co_edi_cufe_cude_ref"]
                )

                dian_status = move.l10n_co_dian_status
                if dian_status == "accepted":
                    attached_doc = service._build_attached_document_xml(
                        move,
                        signed_xml,
                        application_response_xml,
                        signer=signer,
                    )
                    attachment = service._save_audit_attachment(
                        move,
                        "attached_document",
                        attached_doc,
                        dian_filename=dian_ad_name,
                    )
                    result[move] = {"success": True, "attachment": attachment}
                elif dian_status == "sent":
                    result[move] = {"success": True}
                elif dian_status in ("rejected", "error"):
                    result[move] = {
                        "error": self.env._(
                            "La DIAN rechazó o reportó un error en el documento. "
                            "Revise el chatter para más detalles."
                        ),
                        "blocking_level": "warning",
                    }
                else:
                    result[move] = {"success": True}

            except Exception as e:
                _logger.error(
                    "Error processing Colombian EDI for %s: %s",
                    move.name,
                    str(e),
                    exc_info=True,
                )
                result[move] = {
                    "error": str(e),
                    "blocking_level": "error",
                }
        return result

    def _l10n_co_get_doc_config(self, move):
        """Return DIAN config dict for this move's document type."""
        key = (
            move.move_type,
            bool(move.debit_origin_id),
            move.journal_id._is_support_document_type(),
        )
        config = DOCUMENT_TYPE_CONFIG.get(key)
        if not config:
            raise UserError(
                self.env._(
                    "Tipo de documento no soportado para facturación electrónica."
                )
            )
        return config

    def _l10n_co_get_edi_content(self, move):
        """Return EDI XML bytes for download/email.

        Prefers AttachedDocument (ad*.xml). Falls back to signed
        XML (xml_firmado) when AttachedDocument is not yet available
        (e.g. habilitación mode before GetStatusZip).
        """
        att = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "account.move"),
                ("res_id", "=", move.id),
                "|",
                ("name", "=like", "ad%.xml"),
                ("name", "=like", f"{move.name}%attached_document.xml"),
            ],
            limit=1,
            order="id desc",
        )
        if not att:
            # Fallback: return signed XML when AD not yet available
            att = self.env["ir.attachment"].search(
                [
                    ("res_model", "=", "account.move"),
                    ("res_id", "=", move.id),
                    ("name", "=like", "%xml_firmado%"),
                ],
                limit=1,
                order="id desc",
            )
        return base64.b64decode(att.datas) if att else b""
