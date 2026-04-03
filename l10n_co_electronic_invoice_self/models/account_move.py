# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import io
import logging

from lxml import etree

from odoo import api, fields, models
from odoo.exceptions import UserError

try:
    import qrcode
except ImportError:
    qrcode = None

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_edi_decoder(self, file_data, new=False):
        """Intercept Colombian DIAN XMLs before the generic UBL decoder."""
        if file_data.get("type") == "xml":
            tree = file_data["xml_tree"]
            if self._is_l10n_co_dian_xml(tree):
                if etree.QName(tree).localname == "AttachedDocument":
                    file_data["xml_tree"] = self._ubl_parse_attached_document(tree)
                return self.env["l10n_co.dian.self.service"]._import_invoice_l10n_co
        return super()._get_edi_decoder(file_data, new=new)

    @api.model
    def _is_l10n_co_dian_xml(self, tree):
        """Detect Colombian DIAN XML by ProfileID containing 'DIAN'."""
        profile_id = tree.findtext(".//{*}ProfileID") or ""
        return "DIAN" in profile_id

    l10n_co_is_support_document = fields.Boolean(
        string="Es Documento Soporte",
        compute="_compute_l10n_co_is_support_document",
    )
    l10n_co_radian_events_sent = fields.Char(
        string="Eventos RADIAN enviados",
        copy=False,
        help="Códigos de eventos RADIAN enviados, separados por coma. Ej: 030,032,033",
    )
    l10n_co_radian_status = fields.Selection(
        selection=[
            ("pending", "Pendiente"),
            ("receipt_sent", "Acuse enviado"),
            ("goods_received", "Bienes/Servicios recibidos"),
            ("accepted", "Aceptada"),
            ("rejected", "Reclamada"),
        ],
        string="Estado RADIAN",
        copy=False,
    )

    @api.depends("journal_id")
    def _compute_l10n_co_is_support_document(self):
        for move in self:
            move.l10n_co_is_support_document = (
                move.journal_id._is_support_document_type()
                if move.journal_id
                else False
            )

    def action_query_dian_status(self):
        """Query DIAN for document status.

        Uses GetStatusZip (by zipKey) in test/habilitación mode,
        or GetStatus (by CUFE/trackId) in production mode.
        """
        self.ensure_one()
        service = self.env["l10n_co.dian.self.service"]
        mode = self.journal_id.l10n_co_dian_operation_mode
        if mode == "test" and self.l10n_co_dian_zip_key:
            service._query_zip_status(self)
        elif self.l10n_co_edi_cufe_cude_ref:
            service._query_status(self)
        elif self.l10n_co_dian_zip_key:
            service._query_zip_status(self)
        else:
            raise UserError(
                self.env._(
                    "No hay CUFE ni ZipKey para consultar el estado del documento."
                )
            )

    def action_open_radian_wizard(self):
        """Abrir el wizard de eventos RADIAN."""
        self.ensure_one()
        return {
            "name": "Enviar Evento RADIAN",
            "type": "ir.actions.act_window",
            "res_model": "l10n_co.dian.radian.event.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_model": "account.move",
                "active_id": self.id,
            },
        }

    @api.depends("l10n_latam_available_document_type_ids")
    def _compute_l10n_latam_document_type(self):
        super()._compute_l10n_latam_document_type()
        for move in self.filtered(
            lambda m: m.state == "draft"
            and m.journal_id
            and m.move_type in ("in_invoice", "in_refund")
            and m.journal_id._is_support_document_type()
        ):
            doc_types = move.l10n_latam_available_document_type_ids._origin
            if move.move_type == "in_refund":
                preferred = doc_types.filtered(lambda d: d.code == "95")
            else:
                preferred = doc_types.filtered(lambda d: d.code == "05")
            if preferred and move.l10n_latam_document_type_id not in preferred:
                move.l10n_latam_document_type_id = preferred[0]
        return

    def _is_l10n_co_electronic_document_enabled(self):
        """Return True if the journal is configured for CO e-docs."""
        return (
            self.journal_id.l10n_latam_use_documents
            and self.company_id.account_fiscal_country_id.code == "CO"
            and self.l10n_latam_document_type_id
        )

    def _l10n_co_electronic_document_customization_id(self):
        """Return the DIAN CustomizationID based on document and partner type."""
        if self.journal_id._is_support_document_type():
            is_domestic = self.partner_id.commercial_partner_id.country_code == "CO"
            return "10" if is_domestic else "11"
        if self.l10n_latam_document_type_id.code == "02":
            return "32"
        return self.l10n_co_dian_operation_type or "10"

    def _get_colombian_formatted_sequence(self, number=0):
        if self.l10n_latam_document_type_id.code in ("01", "02", "03", "05"):
            prefix, start_number, _end_number = (
                self.journal_id._get_electronic_document_numbering_range()
            )
        else:
            prefix = self.l10n_latam_document_type_id.doc_code_prefix
            start_number = 1
        return f"{prefix}{start_number + number}"

    def _get_starting_sequence(self):
        if self._is_l10n_co_electronic_document_enabled():
            return self._get_colombian_formatted_sequence(0)
        return super()._get_starting_sequence()

    def _get_next_sequence_format(self):
        """Override to handle custom start number for Colombian electronic invoices."""
        if not self._is_l10n_co_electronic_document_enabled():
            return super()._get_next_sequence_format()

        last_sequence = self._get_last_sequence()
        config = self._get_colombian_electronic_invoice_config()
        self._check_sequence_limit_reached(last_sequence, config)

        if self._should_start_new_sequence(last_sequence, config):
            return self._create_new_sequence_format(config)

        return super()._get_next_sequence_format()

    def _get_colombian_electronic_invoice_config(self):
        """Return numbering range config for the current document type."""
        if self.l10n_latam_document_type_id.code in ("01", "02", "03", "05"):
            prefix, start_number, end_number = (
                self.journal_id._get_electronic_document_numbering_range()
            )
            return {
                "prefix": prefix,
                "start_number": start_number,
                "end_number": end_number,
            }
        return {
            "prefix": self.l10n_latam_document_type_id.doc_code_prefix,
            "start_number": 1,
            "end_number": None,
        }

    def _check_sequence_limit_reached(self, last_sequence, config):
        """Raise UserError if the authorized numbering range has been exhausted."""
        if not (
            last_sequence
            and config["end_number"]
            and last_sequence.startswith(config["prefix"])
        ):
            return

        try:
            last_number = self._extract_sequence_number(last_sequence, config["prefix"])
        except (ValueError, AttributeError):
            _logger.warning("Could not parse sequence number: %s", last_sequence)
            return

        if last_number >= config["end_number"]:
            raise UserError(
                self.env._(
                    "Se ha alcanzado el número final autorizado "
                    "(%(end)s) para la facturación electrónica en el "
                    "diario %(journal)s. Por favor, configure un nuevo "
                    "rango de numeración o contacte al administrador "
                    "del sistema.",
                    end=config["end_number"],
                    journal=self.journal_id.name,
                )
            )

    def _should_start_new_sequence(self, last_sequence, config):
        """Return True if a fresh sequence should be started."""
        if not last_sequence or not last_sequence.startswith(config["prefix"]):
            return True

        if not config["end_number"]:
            return False

        try:
            last_number = self._extract_sequence_number(last_sequence, config["prefix"])
            return (
                last_number < config["start_number"]
                or last_number > config["end_number"]
            )
        except (ValueError, AttributeError):
            return True

    def _extract_sequence_number(self, sequence, prefix):
        """Extract the numeric part from a sequence string after the prefix."""
        return int(sequence.replace(prefix, "").strip())

    def _create_new_sequence_format(self, config):
        """Build a sequence format starting from the configured start_number."""
        starting_sequence = self._get_starting_sequence()
        format_string, format_values = self._get_sequence_format_param(
            starting_sequence
        )
        sequence_number_reset = self._deduce_sequence_number_reset(starting_sequence)
        date_start, date_end, forced_year_start, forced_year_end = (
            self._get_sequence_date_range(sequence_number_reset)
        )

        format_values["seq"] = config["start_number"] - 1
        format_values["year"] = self._truncate_year_to_length(
            forced_year_start or date_start.year, format_values["year_length"]
        )
        format_values["year_end"] = self._truncate_year_to_length(
            forced_year_end or date_end.year, format_values["year_end_length"]
        )
        format_values["month"] = self[self._sequence_date_field].month

        return format_string, format_values

    # -------------------------------------------------------------------------
    # DIAN PDF helpers
    # -------------------------------------------------------------------------

    def _l10n_co_get_dian_qr_url(self):
        """Return the DIAN QR validation URL for this invoice."""
        self.ensure_one()
        cufe = self.l10n_co_edi_cufe_cude_ref or ""
        mode = self.journal_id.l10n_co_dian_operation_mode
        base = (
            "https://catalogo-vpfe-hab.dian.gov.co"
            if mode in ("test", "demo")
            else "https://catalogo-vpfe.dian.gov.co"
        )
        return f"{base}/document/searchqr?documentkey={cufe}"

    def _l10n_co_get_dian_qr_image(self):
        """Return base64 QR code image for the DIAN validation URL."""
        self.ensure_one()
        if not qrcode:
            return ""
        qr = qrcode.QRCode(box_size=4, border=1)
        qr.add_data(self._l10n_co_get_dian_qr_url())
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()

    def _l10n_co_get_dian_document_name(self):
        """Return DIAN document type name for the PDF title."""
        self.ensure_one()
        doc_code = self.l10n_latam_document_type_id.code or ""
        names = {
            "01": "Factura Electrónica de Venta",
            "02": "Factura Electrónica de Exportación",
            "03": "Factura Electrónica (Contingencia)",
            "05": "Documento Soporte",
            "91": "Nota Crédito Electrónica",
            "92": "Nota Débito Electrónica",
            "95": "Nota de Ajuste al Documento Soporte",
        }
        return names.get(doc_code, "")

    def _l10n_co_get_resolution_dates(self):
        """Return the resolution validity dates as text."""
        self.ensure_one()
        try:
            start_date, end_date = self.journal_id._get_electronic_document_dates()
        except Exception:
            return ""
        if start_date and end_date:
            return f"{start_date.isoformat()} a {end_date.isoformat()}"
        return ""

    def _l10n_co_get_numbering_range_text(self):
        """Return the authorized numbering range text."""
        self.ensure_one()
        try:
            prefix, start, end = (
                self.journal_id._get_electronic_document_numbering_range()
            )
        except Exception:
            return ""
        if not (prefix and start):
            return ""
        range_text = f"{prefix}{start}"
        if end:
            range_text += f" a {prefix}{end}"
        resolution = self.journal_id.l10n_co_electronic_document_resolution or ""
        if resolution and resolution != "000000000":
            return f"Resolución No. {resolution} - Rango {range_text}"
        return f"Rango {range_text}"

    def _l10n_co_get_resolution_message(self):
        """Build resolution message using the document's own prefix."""
        self.ensure_one()
        journal = self.journal_id
        mode = journal.l10n_co_dian_operation_mode
        if mode == "production":
            resolution = journal.l10n_co_electronic_document_resolution
            start_date = journal.l10n_co_electronic_document_start_resolution_date
            end_date = journal.l10n_co_electronic_document_end_resolution_date
        else:
            resolution = journal.l10n_co_electronic_document_resolution_test
            start_date = journal.l10n_co_electronic_document_start_resolution_date_test
            end_date = journal.l10n_co_electronic_document_end_resolution_date_test

        doc_code = self.l10n_latam_document_type_id.code
        if doc_code in ("01", "02", "03", "05"):
            prefix, _, _ = journal._get_electronic_document_numbering_range()
            doc_prefix = prefix or ""
        else:
            doc_prefix = self.l10n_latam_document_type_id.doc_code_prefix or ""
        if not resolution:
            return ""
        parts = [f"Resolución Nº {resolution}"]
        if start_date and end_date:
            parts.append(f"del {start_date} al {end_date}")
        if doc_prefix:
            parts.append(f"Prefijo {doc_prefix}")
        return ", ".join(parts)

    def _get_last_sequence_domain(self, relaxed=False):
        where_string, param = super()._get_last_sequence_domain(relaxed)
        if (
            self.company_id.account_fiscal_country_id.code == "CO"
            and self.l10n_latam_use_documents
        ):
            where_string += (
                " AND l10n_latam_document_type_id = %(l10n_latam_document_type_id)s"
            )
            param["l10n_latam_document_type_id"] = (
                self.l10n_latam_document_type_id.id or 0
            )
        return where_string, param
