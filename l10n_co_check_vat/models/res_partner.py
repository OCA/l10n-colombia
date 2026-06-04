# Copyright 2026 juparmer - Juan Arcos <juanparmer@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def check_vat_co(self, vat):
        """
        Validate Colombian VAT (NIT / Cédula).
        Accepts 3-11 digits (ignoring spaces, dots, hyphens, etc.).
        """
        cleaned = re.sub(r"\D", "", vat or "")
        return 3 <= len(cleaned) <= 11
