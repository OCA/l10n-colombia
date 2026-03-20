# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import io
import logging
import zipfile

from odoo import api, models

from ..utils.constants import DIAN_PROVIDER_CODE

_logger = logging.getLogger(__name__)


class AccountMoveSend(models.AbstractModel):
    _inherit = "account.move.send"

    @api.model
    def _get_invoice_extra_attachments(self, move):
        """Override to replace EDI XML attachment with a ZIP containing
        the AttachedDocument XML + invoice PDF.

        DIAN ZIP naming convention (Anexo Técnico v1.9, section 6.5.8):
        z{nit_10}{ppp}{aa}{consecutive_hex_8}.zip
        """
        result = super()._get_invoice_extra_attachments(move)

        if not move._is_l10n_co_electronic_document_enabled():
            return result

        existing_zip = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "account.move"),
                ("res_id", "=", move.id),
                ("name", "=like", "z%.zip"),
                ("mimetype", "=", "application/zip"),
            ],
            limit=1,
            order="id desc",
        )
        if existing_zip:
            other_attachments = self.env["ir.attachment"]
            for att in result:
                if att.name and att.name.startswith("ad") and att.name.endswith(".xml"):
                    continue
                if att.mimetype == "application/pdf" or (
                    att.name and att.name.endswith(".pdf")
                ):
                    continue
                other_attachments += att
            return other_attachments + existing_zip

        ad_attachment = self.env["ir.attachment"]
        pdf_attachment = self.env["ir.attachment"]
        other_attachments = self.env["ir.attachment"]

        for att in result:
            if att.name and (att.name.startswith("ad") and att.name.endswith(".xml")):
                ad_attachment = att
            elif att.mimetype == "application/pdf" or (
                att.name and att.name.endswith(".pdf")
            ):
                pdf_attachment = att
            else:
                other_attachments += att

        if not ad_attachment:
            return result

        if not pdf_attachment:
            pdf_attachment = move.invoice_pdf_report_id
        if not pdf_attachment:
            pdf_content, _report_type = self.env["ir.actions.report"]._render_qweb_pdf(
                "account.account_invoices",
                res_ids=[move.id],
            )
            pdf_attachment = self.env["ir.attachment"].create(
                {
                    "name": f"{move.name}.pdf",
                    "type": "binary",
                    "datas": base64.b64encode(pdf_content),
                    "res_model": "account.move",
                    "res_id": move.id,
                    "mimetype": "application/pdf",
                }
            )

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            xml_data = base64.b64decode(ad_attachment.datas)
            zf.writestr(ad_attachment.name, xml_data)

            if pdf_attachment and pdf_attachment.datas:
                pdf_data = base64.b64decode(pdf_attachment.datas)
                pdf_name = pdf_attachment.name or f"{move.name}.pdf"
                zf.writestr(pdf_name, pdf_data)

        zip_bytes = zip_buffer.getvalue()
        zip_name = self._get_dian_zip_name(move, ad_attachment.name)

        zip_attachment = self.env["ir.attachment"].create(
            {
                "name": zip_name,
                "type": "binary",
                "datas": base64.b64encode(zip_bytes),
                "res_model": "account.move",
                "res_id": move.id,
                "mimetype": "application/zip",
            }
        )

        return other_attachments + zip_attachment

    @api.model
    def _get_dian_zip_name(self, move, ad_filename):
        """Build DIAN-compliant ZIP filename from the AttachedDocument name.

        ZIP format: z{nit_10}{ppp}{aa}{consecutive_hex_8}.zip
        The consecutive is reused from the AD filename if possible.
        """
        if ad_filename and ad_filename.startswith("ad") and len(ad_filename) > 22:
            base = ad_filename[2:]  # remove "ad" prefix
            base = base.rsplit(".", 1)[0]  # remove .xml
            return f"z{base}.zip"

        company = move.company_id
        vat = company.partner_id.vat or ""
        nit = vat.split("-")[0].strip().replace(".", "")
        nit_10 = nit.zfill(10)[:10]
        year_2 = move.invoice_date.strftime("%y") if move.invoice_date else "00"
        return f"z{nit_10}{DIAN_PROVIDER_CODE}{year_2}00000000.zip"
