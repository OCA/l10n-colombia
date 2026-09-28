# Copyright 2026 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase


class TestL10nCoWithholdingCertificateClassification(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account_2365 = cls._get_or_create_account("236505")
        cls.account_2367 = cls._get_or_create_account("236705")
        cls.account_2368 = cls._get_or_create_account("236805")

    @classmethod
    def _get_or_create_account(cls, code):
        account = cls.env["account.account"].with_company(cls.env.company).search(
            [("code", "=", code), ("company_ids", "in", cls.env.company.id)], limit=1
        )
        if not account:
            account = cls.env["account.account"].with_company(cls.env.company).create(
                {
                    "code": code,
                    "name": "Withholding " + code,
                    "account_type": "liability_current",
                    "company_ids": [(6, 0, [cls.env.company.id])],
                }
            )
        return account

    def test_explicit_withholding_type_has_priority(self):
        tax = self.env["account.tax"].create(
            {
                "name": "RteFte explicit",
                "amount": -4.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "l10n_co_withholding_type": "rte_fte",
            }
        )
        self.assertEqual(tax.l10n_co_get_certificate_withholding_type(), "rte_fte")

    def test_withholding_type_is_used_when_available(self):
        tax = self.env["account.tax"].create(
            {
                "name": "RteIVA from withholding",
                "amount": -2.85,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "l10n_co_withholding_type": "rte_iva",
            }
        )
        self.assertEqual(tax.l10n_co_get_certificate_withholding_type(), "rte_iva")

    def test_family_account_code_is_used_as_fallback(self):
        tax = self.env["account.tax"].create(
            {
                "name": "RteICA account family",
                "amount": -1.5,
                "amount_type": "percent",
                "type_tax_use": "purchase",
            }
        )
        tax.invoice_repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        )[0].account_id = self.account_2368
        self.assertEqual(tax.l10n_co_get_certificate_withholding_type(), "rte_ica")

    def test_multiple_taxes_return_mapping(self):
        tax_fte = self.env["account.tax"].create(
            {
                "name": "Tax FTE",
                "amount": -4.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
            }
        )
        tax_iva = self.env["account.tax"].create(
            {
                "name": "Tax IVA",
                "amount": -2.85,
                "amount_type": "percent",
                "type_tax_use": "purchase",
            }
        )
        tax_fte.invoice_repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        )[0].account_id = self.account_2365
        tax_iva.invoice_repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        )[0].account_id = self.account_2367

        result = self.env["account.tax"].browse([tax_fte.id, tax_iva.id]).l10n_co_get_certificate_withholding_type()
        self.assertEqual(result[tax_fte.id], "rte_fte")
        self.assertEqual(result[tax_iva.id], "rte_iva")

    def test_no_match_returns_false(self):
        tax = self.env["account.tax"].create(
            {
                "name": "Unknown tax",
                "amount": 5.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
            }
        )
        self.assertFalse(tax.l10n_co_get_certificate_withholding_type())

    def test_ambiguous_repartition_returns_false_without_metadata(self):
        tax = self.env["account.tax"].create(
            {
                "name": "Ambiguous withholding",
                "amount": -2.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
            }
        )
        tax.invoice_repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        )[0].account_id = self.account_2365
        tax.refund_repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        )[0].account_id = self.account_2367
        self.assertFalse(tax.l10n_co_get_certificate_withholding_type())

    def test_explicit_type_wins_over_ambiguous_repartition(self):
        tax = self.env["account.tax"].create(
            {
                "name": "Explicit withholding",
                "amount": -2.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "l10n_co_withholding_type": "rte_fte",
            }
        )
        tax.invoice_repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        )[0].account_id = self.account_2367
        self.assertEqual(tax.l10n_co_get_certificate_withholding_type(), "rte_fte")
