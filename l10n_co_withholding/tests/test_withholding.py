# Copyright 2026 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase


class TestL10nCoWithholding(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.company.country_id = cls.env.ref("base.co")
        cls.company.l10n_co_is_retention_agent = True
        cls.partner_person = cls.env["res.partner"].create(
            {
                "name": "Persona Natural Test",
                "company_type": "person",
                "l10n_co_tax_regime": "ordinary",
            },
        )
        cls.partner_company = cls.env["res.partner"].create(
            {
                "name": "Empresa Test",
                "company_type": "company",
                "l10n_co_tax_regime": "ordinary",
            },
        )
        cls.partner_simple = cls.env["res.partner"].create(
            {
                "name": "Régimen Simple Test",
                "company_type": "person",
                "l10n_co_tax_regime": "simple",
            },
        )
        cls.partner_non_taxpayer = cls.env["res.partner"].create(
            {
                "name": "No Contribuyente Test",
                "company_type": "person",
                "l10n_co_tax_regime": "non_taxpayer",
            },
        )

    def test_partner_fields(self):
        self.assertEqual(self.partner_person.l10n_co_tax_regime, "ordinary")
        self.assertEqual(self.partner_person.company_type, "person")
        self.assertFalse(self.partner_person.l10n_co_is_gran_contribuyente)

    def test_simple_regime_onchange(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Simple",
                "l10n_co_tax_regime": "simple",
                "l10n_co_is_authorretenedor": True,
            },
        )
        partner.l10n_co_tax_regime = "simple"
        partner._onchange_l10n_co_tax_regime()
        self.assertFalse(partner.l10n_co_is_authorretenedor)

    def test_withholding_tax_concept(self):
        tax = self.env["account.tax"].create(
            {
                "name": "Test RteFte 4%",
                "amount": -4.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "l10n_co_withholding_type": "rte_fte",
                "l10n_co_withholding_concept": "servicios",
                "l10n_co_min_base_uvt": 4.0,
            },
        )
        self.assertEqual(tax.l10n_co_withholding_type, "rte_fte")
        self.assertEqual(tax.l10n_co_withholding_concept, "servicios")
        self.assertEqual(tax.l10n_co_min_base_uvt, 4.0)

    def test_min_base_check(self):
        tax = self.env["account.tax"].create(
            {
                "name": "Test Min Base",
                "amount": -4.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "l10n_co_min_base_uvt": 4.0,
            },
        )
        move = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner_person.id,
            },
        )
        self.assertTrue(move.l10n_co_check_min_base(tax, 500000))
        self.assertFalse(move.l10n_co_check_min_base(tax, 100))

    def test_company_uvt_value(self):
        uvt_value = self.company._l10n_co_get_uvt_value()
        self.assertEqual(uvt_value, 52374.0)

    def test_company_withholding_config(self):
        self.assertTrue(self.company.l10n_co_is_retention_agent)
        wh_tax = self.env["account.tax"].create(
            {
                "name": "Test WH Config",
                "amount": -4.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "l10n_co_withholding_type": "rte_fte",
            },
        )
        self.company.l10n_co_default_rte_fte_tax_ids = [(6, 0, [wh_tax.id])]
        self.assertIn(wh_tax, self.company.l10n_co_default_rte_fte_tax_ids)

    def test_get_applicable_withholding_taxes(self):
        wh_tax = self.env["account.tax"].create(
            {
                "name": "Test WH Applicable",
                "amount": -4.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "l10n_co_withholding_type": "rte_fte",
            },
        )
        self.company.l10n_co_default_rte_fte_tax_ids = [(6, 0, [wh_tax.id])]
        move = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner_person.id,
            },
        )
        applicable = move.l10n_co_get_applicable_withholding_taxes()
        self.assertIn(wh_tax, applicable)

    def test_simple_regime_filters_rte_fte(self):
        rte_fte = self.env["account.tax"].create(
            {
                "name": "Test WH RteFte",
                "amount": -4.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "l10n_co_withholding_type": "rte_fte",
            },
        )
        rte_iva = self.env["account.tax"].create(
            {
                "name": "Test WH ReteIVA",
                "amount": -2.85,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "l10n_co_withholding_type": "rte_iva",
            },
        )
        self.company.l10n_co_default_rte_fte_tax_ids = [(6, 0, [rte_fte.id])]
        self.company.l10n_co_default_rte_iva_tax_ids = [(6, 0, [rte_iva.id])]
        move = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner_simple.id,
            },
        )
        applicable = move.l10n_co_get_applicable_withholding_taxes()
        self.assertNotIn(rte_fte, applicable)
        self.assertIn(rte_iva, applicable)

    def test_non_taxpayer_no_withholding(self):
        wh_tax = self.env["account.tax"].create(
            {
                "name": "Test WH Non-Taxpayer",
                "amount": -4.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "l10n_co_withholding_type": "rte_fte",
            },
        )
        self.company.l10n_co_default_rte_fte_tax_ids = [(6, 0, [wh_tax.id])]
        move = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner_non_taxpayer.id,
            },
        )
        applicable = move.l10n_co_get_applicable_withholding_taxes()
        self.assertNotIn(wh_tax, applicable)

    def test_compute_withholding_taxes(self):
        wh_tax = self.env["account.tax"].create(
            {
                "name": "Test WH Compute",
                "amount": -4.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "l10n_co_withholding_type": "rte_fte",
            },
        )
        self.company.l10n_co_default_rte_fte_tax_ids = [(6, 0, [wh_tax.id])]
        product = self.env["product.product"].create(
            {
                "name": "Test Service",
                "type": "service",
            },
        )
        move = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner_person.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "name": "Test Service",
                            "quantity": 1.0,
                            "price_unit": 100000.0,
                        },
                    ),
                ],
            },
        )
        result = move.l10n_co_compute_withholding_taxes()
        self.assertGreater(result["applied"], 0)
        lines = move.line_ids.filtered(lambda line: line.display_type == "product")
        self.assertIn(wh_tax, lines[0].tax_ids)

    def test_ciiu_code_field(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test CIIU",
                "company_type": "company",
                "l10n_co_economic_activity_id": self.env.ref(
                    "l10n_co_economic_activities.activity_6201",
                ).id,
            },
        )
        self.assertEqual(partner.l10n_co_economic_activity_id.code, "6201")
