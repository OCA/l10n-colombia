# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
import zipfile
from io import BytesIO

from odoo import api, models

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.model
    def _get_edi_supported_formats(self):
        """Add ZIP format support before the binary fallback.

        DIAN Colombia distributes electronic invoices as ZIP files
        containing the AttachedDocument XML.
        """
        formats = super()._get_edi_supported_formats()
        zip_format = {
            "format": "zip",
            "check": lambda att: att.mimetype
            in (
                "application/zip",
                "application/x-zip-compressed",
                "application/octet-stream",
            )
            and att.name
            and att.name.lower().endswith(".zip"),
            "decoder": self._decode_edi_zip,
        }
        formats.insert(-1, zip_format)
        return formats

    def _decode_edi_zip(self, filename, content):
        """Extract XML files from a ZIP and decode them as EDI attachments.

        DIAN ZIP files typically contain one or two XMLs:
        - The AttachedDocument (ad*.xml)
        - Optionally the signed invoice (fv*.xml, nc*.xml, etc.)

        We prioritize the AttachedDocument since it wraps the full document.
        """
        result = []
        try:
            with zipfile.ZipFile(BytesIO(content)) as zf:
                xml_entries = [
                    name for name in zf.namelist() if name.lower().endswith(".xml")
                ]
                for entry_name in xml_entries:
                    xml_content = zf.read(entry_name)
                    decoded = self._decode_edi_xml(entry_name, xml_content)
                    for file_data in decoded:
                        # AttachedDocument gets higher priority (lower weight)
                        if entry_name.lower().startswith("ad"):
                            file_data["sort_weight"] = 5
                        else:
                            file_data["sort_weight"] = 8
                        result.append(file_data)
        except zipfile.BadZipFile:
            _logger.warning("Could not decode ZIP file: %s", filename)
        return result
