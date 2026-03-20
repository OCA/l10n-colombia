# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class L10nLatamIdentificationType(models.Model):
    _inherit = "l10n_latam.identification.type"

    l10n_co_document_iso_code = fields.Char(string="ISO Code")
