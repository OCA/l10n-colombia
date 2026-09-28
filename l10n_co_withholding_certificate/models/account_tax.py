# Copyright 2026 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Certificate classification API for Colombian withholding taxes.

The certificate layer must remain separate from the withholding calculation layer.
The source of truth for certification is the posted accounting result, not the draft
calculation state stored in l10n_co_withholding.
"""

from odoo import models


class AccountTax(models.Model):
    _inherit = "account.tax"

    def _l10n_co_get_account_family_certificate_type(self):
        """Infer a certificate type from the tax account family.

        The Colombian accounting chart uses dedicated account families for each
        withholding type: 2365 = ReteFte, 2367 = ReteIVA and 2368 = ReteICA.
        """
        self.ensure_one()

        rep_lines = (
            self.invoice_repartition_line_ids | self.refund_repartition_line_ids
        ).filtered(
            lambda line: line.repartition_type == "tax" and line.account_id
        )

        account_family_types = set()
        for rep_line in rep_lines:
            account_code = (
                rep_line.account_id.with_company(self.company_id).code or ""
            ).strip()
            if account_code.startswith("2365"):
                account_family_types.add("rte_fte")
            elif account_code.startswith("2367"):
                account_family_types.add("rte_iva")
            elif account_code.startswith("2368"):
                account_family_types.add("rte_ica")

        return account_family_types.pop() if len(account_family_types) == 1 else False

    def _l10n_co_infer_certificate_withholding_type(self):
        """Return the certificate type in precedence order.

        1. Explicit withholding metadata already defined by l10n_co_withholding
        2. Account family fallback from posted accounting lines
        3. False
        """
        self.ensure_one()

        if getattr(self, "l10n_co_withholding_type", False):
            return self.l10n_co_withholding_type
        return self._l10n_co_get_account_family_certificate_type()

    def l10n_co_get_certificate_withholding_type(self):
        """Return the certificate type for one or many taxes.

        For a single record it returns a value in {'rte_fte', 'rte_iva', 'rte_ica'}
        or False. For multiple records it returns a dict mapping each tax id to the
        inferred certificate type.
        """
        if len(self) == 1:
            return self._l10n_co_infer_certificate_withholding_type()
        return {
            tax.id: tax._l10n_co_infer_certificate_withholding_type()
            for tax in self
        }
