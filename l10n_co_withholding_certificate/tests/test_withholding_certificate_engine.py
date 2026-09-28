# Copyright 2026 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestL10nCoWithholdingCertificateEngine(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.company.country_id = cls.env.ref("base.co")
        cls.partner_a = cls.env["res.partner"].create({"name": "Cliente A", "company_type": "company"})
        cls.partner_b = cls.env["res.partner"].create({"name": "Cliente B", "company_type": "company"})
        cls.commercial_partner = cls.env["res.partner"].create(
            {"name": "ABC SAS", "company_type": "company"}
        )
        cls.child_a = cls.env["res.partner"].create(
            {"name": "Contacto A", "parent_id": cls.commercial_partner.id, "type": "contact"}
        )
        cls.child_b = cls.env["res.partner"].create(
            {"name": "Contacto B", "parent_id": cls.commercial_partner.id, "type": "contact"}
        )
        cls.engine = cls.env["l10n_co.withholding.certificate.engine"]

    def _create_withholding_tax(
        self,
        name,
        amount,
        tax_type="purchase",
        withholding_type="rte_fte",
        company=None,
    ):
        company = company or self.company
        return self.env["account.tax"].with_company(company).create(
            {
                "name": name,
                "amount": amount,
                "amount_type": "percent",
                "type_tax_use": tax_type,
                "l10n_co_withholding_type": withholding_type,
                "company_id": company.id,
            }
        )

    def _create_vendor_bill(self, partner, amount, tax, company=None, journal=None):
        company = company or self.company
        product = self.env["product.product"].with_company(company).create(
            {"name": "Servicio", "type": "service", "company_id": company.id}
        )
        move_values = {
            "move_type": "in_invoice",
            "company_id": company.id,
            "partner_id": partner.id,
            "invoice_date": "2026-01-15",
            "date": "2026-01-15",
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "quantity": 1.0,
                        "price_unit": amount,
                        "tax_ids": [(6, 0, [tax.id])],
                    },
                )
            ],
        }
        if journal:
            move_values["journal_id"] = journal.id
        move = self.env["account.move"].with_company(company).create(move_values)
        move.action_post()
        return move

    def _create_vendor_credit_note(self, partner, amount, tax):
        move = self.env["account.move"].create(
            {
                "move_type": "in_refund",
                "company_id": self.company.id,
                "partner_id": partner.id,
                "invoice_date": "2026-01-20",
                "date": "2026-01-20",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env["product.product"].create({"name": "NC", "type": "service"}).id,
                            "quantity": 1.0,
                            "price_unit": amount,
                            "tax_ids": [(6, 0, [tax.id])],
                        },
                    )
                ],
            }
        )
        move.action_post()
        return move

    def test_engine_returns_posted_withholding_for_single_partner(self):
        tax = self._create_withholding_tax("ReteFuente 2.5%", -2.5, "purchase", "rte_fte")
        self._create_vendor_bill(self.partner_a, 1000000.0, tax)

        data = self.engine.get_certificate_data(
            self.company,
            "2026-01-01",
            "2026-12-31",
            "rte_fte",
            partners=self.partner_a,
        )

        self.assertEqual(data["certificate_type"], "rte_fte")
        self.assertEqual(len(data["partners"]), 1)
        self.assertEqual(data["partners"][0]["base_amount"], 1000000.0)
        self.assertEqual(data["partners"][0]["withheld_amount"], 25000.0)

    def test_engine_consolidates_two_invoices_for_same_partner(self):
        tax = self._create_withholding_tax("ReteFuente 2.5%", -2.5, "purchase", "rte_fte")
        self._create_vendor_bill(self.partner_a, 1000000.0, tax)
        self._create_vendor_bill(self.partner_a, 500000.0, tax)

        data = self.engine.get_certificate_data(self.company, "2026-01-01", "2026-12-31", "rte_fte")

        self.assertEqual(len(data["partners"]), 1)
        self.assertEqual(data["partners"][0]["partner"].id, self.partner_a.id)
        self.assertEqual(data["partners"][0]["base_amount"], 1500000.0)
        self.assertEqual(data["partners"][0]["withheld_amount"], 37500.0)

    def test_engine_separates_partners(self):
        tax = self._create_withholding_tax("ReteFuente 2.5%", -2.5, "purchase", "rte_fte")
        self._create_vendor_bill(self.partner_a, 1000000.0, tax)
        self._create_vendor_bill(self.partner_b, 2000000.0, tax)

        data = self.engine.get_certificate_data(self.company, "2026-01-01", "2026-12-31", "rte_fte")

        partner_ids = [partner["partner"].id for partner in data["partners"]]
        self.assertEqual(sorted(partner_ids), sorted([self.partner_a.id, self.partner_b.id]))

    def test_engine_handles_invoice_and_credit_note_net_total(self):
        tax = self._create_withholding_tax("ReteFuente 2.5%", -2.5, "purchase", "rte_fte")
        self._create_vendor_bill(self.partner_a, 1000000.0, tax)
        self._create_vendor_credit_note(self.partner_a, 200000.0, tax)

        data = self.engine.get_certificate_data(self.company, "2026-01-01", "2026-12-31", "rte_fte")

        self.assertEqual(data["partners"][0]["base_amount"], 800000.0)
        self.assertEqual(data["partners"][0]["withheld_amount"], 20000.0)

    def test_engine_ignores_draft_moves(self):
        tax = self._create_withholding_tax("ReteFuente 2.5%", -2.5, "purchase", "rte_fte")
        draft_move = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "company_id": self.company.id,
                "partner_id": self.partner_a.id,
                "invoice_date": "2026-02-01",
                "date": "2026-02-01",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env["product.product"].create({"name": "Draft", "type": "service"}).id,
                            "quantity": 1.0,
                            "price_unit": 1000000.0,
                            "tax_ids": [(6, 0, [tax.id])],
                        },
                    )
                ],
            }
        )

        data = self.engine.get_certificate_data(self.company, "2026-01-01", "2026-12-31", "rte_fte")
        self.assertEqual(data["partners"], [])
        self.assertFalse(draft_move.state == "posted")

    def test_engine_filters_by_certificate_type(self):
        rte_fte = self._create_withholding_tax("ReteFuente 2.5%", -2.5, "purchase", "rte_fte")
        rte_iva = self._create_withholding_tax("ReteIVA 1.5%", -1.5, "purchase", "rte_iva")
        self._create_vendor_bill(self.partner_a, 1000000.0, rte_fte)
        self._create_vendor_bill(self.partner_a, 1000000.0, rte_iva)

        rte_fte_data = self.engine.get_certificate_data(self.company, "2026-01-01", "2026-12-31", "rte_fte")
        rte_iva_data = self.engine.get_certificate_data(self.company, "2026-01-01", "2026-12-31", "rte_iva")

        self.assertEqual(rte_fte_data["partners"][0]["withheld_amount"], 25000.0)
        self.assertEqual(rte_iva_data["partners"][0]["withheld_amount"], 15000.0)

    def test_engine_invalid_certificate_type_raises(self):
        with self.assertRaises(ValidationError):
            self.engine.get_certificate_data(self.company, "2026-01-01", "2026-12-31", "rte_xxx")

    def test_engine_rejects_invalid_date_range(self):
        with self.assertRaises(ValidationError):
            self.engine.get_certificate_data(self.company, "2026-12-31", "2026-01-01", "rte_fte")

    def test_engine_tracks_move_line_ids(self):
        tax = self._create_withholding_tax("ReteFuente 2.5%", -2.5, "purchase", "rte_fte")
        self._create_vendor_bill(self.partner_a, 1000000.0, tax)

        data = self.engine.get_certificate_data(self.company, "2026-01-01", "2026-12-31", "rte_fte")

        self.assertTrue(data["partners"][0]["concepts"][0]["move_line_ids"])

    def test_engine_groups_by_concept(self):
        tax_a = self._create_withholding_tax("ReteFuente servicios", -2.5, "purchase", "rte_fte")
        tax_b = self._create_withholding_tax("ReteFuente arrendamiento", -2.5, "purchase", "rte_fte")
        tax_b.l10n_co_withholding_concept = "arrendamiento_inmueble"
        self._create_vendor_bill(self.partner_a, 1000000.0, tax_a)
        self._create_vendor_bill(self.partner_a, 500000.0, tax_b)

        data = self.engine.get_certificate_data(self.company, "2026-01-01", "2026-12-31", "rte_fte")

        self.assertEqual(len(data["partners"][0]["concepts"]), 2)

    def test_engine_ignores_other_company_lines(self):
        company_b = self.env["res.company"].create({"name": "Company B"})
        country = self.env.ref("base.co")
        company_b.country_id = country
        expense_account_b = self.env["account.account"].with_company(company_b).create(
            {
                "code": "600001",
                "name": "Company B Expense",
                "account_type": "expense",
                "company_ids": [(6, 0, [company_b.id])],
            }
        )
        payable_account_b = self.env["account.account"].with_company(company_b).create(
            {
                "code": "220001",
                "name": "Company B Payable",
                "account_type": "liability_payable",
                "reconcile": True,
                "company_ids": [(6, 0, [company_b.id])],
            }
        )
        self.partner_a.with_company(company_b).property_account_payable_id = payable_account_b
        journal_b = self.env["account.journal"].with_company(company_b).create(
            {
                "name": "Compras Company B",
                "code": "CPB1",
                "type": "purchase",
                "company_id": company_b.id,
                "default_account_id": expense_account_b.id,
            }
        )
        tax_group_b = self.env["account.tax.group"].with_company(company_b).create(
            {"name": "Taxes B", "company_id": company_b.id, "country_id": country.id}
        )
        tax = self.env["account.tax"].with_company(company_b).create(
            {
                "name": "ReteFuente 2.5%",
                "amount": -2.5,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "l10n_co_withholding_type": "rte_fte",
                "company_id": company_b.id,
                "country_id": country.id,
                "tax_group_id": tax_group_b.id,
            }
        )
        self._create_vendor_bill(
            self.partner_a, 1000000.0, tax, company=company_b, journal=journal_b
        )

        data = self.engine.get_certificate_data(self.company, "2026-01-01", "2026-12-31", "rte_fte")
        self.assertEqual(data["partners"], [])

    def test_engine_filters_specific_partner(self):
        tax = self._create_withholding_tax("ReteFuente 2.5%", -2.5, "purchase", "rte_fte")
        self._create_vendor_bill(self.partner_a, 1000000.0, tax)
        self._create_vendor_bill(self.partner_b, 2000000.0, tax)

        data = self.engine.get_certificate_data(self.company, "2026-01-01", "2026-12-31", "rte_fte", partners=self.partner_a)
        self.assertEqual(len(data["partners"]), 1)
        self.assertEqual(data["partners"][0]["partner"].id, self.partner_a.id)

    def test_engine_filters_by_date_range(self):
        tax = self._create_withholding_tax("ReteFuente 2.5%", -2.5, "purchase", "rte_fte")
        self._create_vendor_bill(self.partner_a, 1000000.0, tax)

        data = self.engine.get_certificate_data(self.company, "2026-02-01", "2026-12-31", "rte_fte")
        self.assertEqual(data["partners"], [])

    def test_engine_consolidates_child_contacts_by_commercial_partner(self):
        tax = self._create_withholding_tax("ReteFuente 2.5%", -2.5)
        self._create_vendor_bill(self.child_a, 1000000.0, tax)
        self._create_vendor_bill(self.child_b, 500000.0, tax)

        data = self.engine.get_certificate_data(
            self.company, "2026-01-01", "2026-12-31", "rte_fte"
        )

        self.assertEqual(len(data["partners"]), 1)
        self.assertEqual(data["partners"][0]["partner"], self.commercial_partner)
        self.assertEqual(data["partners"][0]["base_amount"], 1500000.0)
        self.assertEqual(data["partners"][0]["withheld_amount"], 37500.0)

    def test_engine_commercial_partner_filter_includes_child_contacts(self):
        tax = self._create_withholding_tax("ReteFuente 2.5%", -2.5)
        self._create_vendor_bill(self.child_a, 1000000.0, tax)
        self._create_vendor_bill(self.child_b, 500000.0, tax)

        data = self.engine.get_certificate_data(
            self.company,
            "2026-01-01",
            "2026-12-31",
            "rte_fte",
            partners=self.commercial_partner,
        )

        self.assertEqual(len(data["partners"]), 1)
        self.assertEqual(data["partners"][0]["base_amount"], 1500000.0)
