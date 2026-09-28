# Copyright 2026 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestL10nCoWithholdingCertificateReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.country_id = cls.env.ref("base.co")
        cls.partner_a = cls.env["res.partner"].create(
            {"name": "Report Partner A", "vat": "900111222"}
        )
        cls.partner_b = cls.env["res.partner"].create(
            {"name": "Report Partner B", "vat": "900333444"}
        )
        cls.child_a = cls.env["res.partner"].create(
            {"name": "Report Contact A", "parent_id": cls.partner_a.id, "type": "contact"}
        )
        cls.tax = cls.env["account.tax"].create(
            {
                "name": "Report ReteFuente",
                "amount": -2.5,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "l10n_co_withholding_type": "rte_fte",
                "l10n_co_withholding_concept": "servicios",
            }
        )
        cls.iva_tax = cls.env["account.tax"].create(
            {
                "name": "Report ReteIVA",
                "amount": -15.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "l10n_co_withholding_type": "rte_iva",
                "l10n_co_withholding_concept": "servicios",
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Report service", "type": "service"}
        )
        cls.wizard_model = cls.env["l10n_co.withholding.certificate.wizard"]
        cls.report_action = cls.env.ref(
            "l10n_co_withholding_certificate.action_report_withholding_certificate"
        )

    def _create_bill(self, partner, amount):
        return self._create_bill_with_tax(partner, amount, self.tax)

    def _create_bill_with_tax(self, partner, amount, tax, date_value="2026-06-15"):
        move = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "company_id": self.company.id,
                "partner_id": partner.id,
                "invoice_date": date_value,
                "date": date_value,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
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

    def _create_wizard(
        self,
        partners=None,
        certificate_type="rte_fte",
        period_type="annual",
        bimester=False,
        date_from=False,
        date_to=False,
    ):
        values = {
            "company_id": self.company.id,
            "certificate_type": certificate_type,
            "fiscal_year": 2026,
            "period_type": period_type,
        }
        if bimester:
            values["bimester"] = bimester
        if date_from:
            values["date_from"] = date_from
        if date_to:
            values["date_to"] = date_to
        if partners:
            values["partner_ids"] = [(6, 0, partners.ids)]
        return self.wizard_model.create(values)

    def test_report_action_configuration(self):
        self.assertEqual(self.report_action.report_type, "qweb-pdf")
        self.assertEqual(
            self.report_action.report_name,
            "l10n_co_withholding_certificate.rte_fte_certificate",
        )
        self.assertEqual(
            self.report_action.model, "l10n_co.withholding.certificate.wizard"
        )

    def test_iva_report_action_configuration(self):
        report = self.env.ref(
            "l10n_co_withholding_certificate.action_report_withholding_iva_certificate"
        )
        self.assertEqual(report.report_type, "qweb-pdf")
        self.assertEqual(report.model, "l10n_co.withholding.certificate.wizard")

    def test_report_values_come_from_engine_for_one_partner(self):
        self._create_bill(self.partner_a, 1000000.0)
        wizard = self._create_wizard(self.partner_a)
        values = self.env[
            "report.l10n_co_withholding_certificate.rte_fte_certificate"
        ]._get_report_values([wizard.id])

        self.assertEqual(len(values["certificates"]), 1)
        certificate = values["certificates"][0]
        self.assertEqual(certificate["partner"], self.partner_a)
        self.assertEqual(certificate["base_amount"], 1000000.0)
        self.assertEqual(certificate["withheld_amount"], 25000.0)
        self.assertEqual(certificate["concepts"][0]["concept"], "servicios")

    def test_report_values_create_one_certificate_per_partner(self):
        self._create_bill(self.partner_a, 1000000.0)
        self._create_bill(self.partner_b, 500000.0)
        wizard = self._create_wizard(self.partner_a | self.partner_b)
        values = self.env[
            "report.l10n_co_withholding_certificate.rte_fte_certificate"
        ]._get_report_values([wizard.id])

        self.assertEqual(len(values["certificates"]), 2)
        self.assertEqual(
            {certificate["partner"] for certificate in values["certificates"]},
            {self.partner_a, self.partner_b},
        )

    def test_report_uses_selected_company_and_commercial_partner(self):
        self._create_bill(self.child_a, 1000000.0)
        wizard = self._create_wizard(self.child_a)
        values = self.env[
            "report.l10n_co_withholding_certificate.rte_fte_certificate"
        ]._get_report_values([wizard.id])

        certificate = values["certificates"][0]
        self.assertEqual(certificate["company"], self.company)
        self.assertEqual(certificate["partner"], self.partner_a)

    def test_action_print_certificate_does_not_need_preview(self):
        self._create_bill(self.partner_a, 1000000.0)
        wizard = self._create_wizard(self.partner_a)
        action = wizard.action_print_certificate()

        self.assertEqual(action["type"], "ir.actions.report")
        self.assertEqual(action["report_name"], self.report_action.report_name)

    def test_action_print_without_data_raises_user_error(self):
        wizard = self._create_wizard(self.partner_a)
        with self.assertRaisesRegex(UserError, "No withholding entries"):
            wizard.action_print_certificate()

    def test_qweb_html_contains_title_and_partner(self):
        self._create_bill(self.partner_a, 1000000.0)
        wizard = self._create_wizard(self.partner_a)
        html, report_type = self.env["ir.actions.report"].with_context(
            force_report_rendering=True
        )._render_qweb_html(
            "l10n_co_withholding_certificate.action_report_withholding_certificate",
            wizard.ids,
        )

        self.assertEqual(report_type, "html")
        self.assertIn(b"CERTIFICADO DE RETENCI", html)
        self.assertIn(b"Report Partner A", html)

    def test_qweb_pdf_renders_nonempty_document(self):
        self._create_bill(self.partner_a, 1000000.0)
        wizard = self._create_wizard(self.partner_a)
        pdf, report_type = self.env["ir.actions.report"].with_context(
            force_report_rendering=True
        )._render_qweb_pdf(
            "l10n_co_withholding_certificate.action_report_withholding_certificate",
            wizard.ids,
        )

        self.assertEqual(report_type, "pdf")
        self.assertTrue(pdf)
        self.assertTrue(pdf.startswith(b"%PDF"))

    def test_report_issue_date_is_context_date(self):
        self._create_bill(self.partner_a, 1000000.0)
        wizard = self._create_wizard(self.partner_a)
        values = self.env[
            "report.l10n_co_withholding_certificate.rte_fte_certificate"
        ]._get_report_values([wizard.id])
        self.assertEqual(
            values["certificates"][0]["issue_date"],
            fields.Date.context_today(self.env.user),
        )

    def test_iva_action_does_not_need_preview(self):
        self._create_bill_with_tax(self.partner_a, 1000000.0, self.iva_tax)
        wizard = self._create_wizard(
            self.partner_a,
            certificate_type="rte_iva",
            period_type="bimonthly",
            bimester="3",
        )
        action = wizard.action_print_certificate()
        iva_report = self.env.ref(
            "l10n_co_withholding_certificate.action_report_withholding_iva_certificate"
        )
        self.assertEqual(action["report_name"], iva_report.report_name)

    def test_iva_bimester_labels_and_values(self):
        for bimester, label, bill_date in (
            ("1", "Enero - Febrero", "2026-01-15"),
            ("3", "Mayo - Junio", "2026-05-15"),
            ("6", "Noviembre - Diciembre", "2026-11-15"),
        ):
            self._create_bill_with_tax(
                self.partner_a, 1000000.0, self.iva_tax, date_value=bill_date
            )
            wizard = self._create_wizard(
                self.partner_a,
                certificate_type="rte_iva",
                period_type="bimonthly",
                bimester=bimester,
            )
            values = self.env[
                "report.l10n_co_withholding_certificate.rte_fte_certificate"
            ]._get_report_values([wizard.id])
            self.assertEqual(values["period_label"], label)
            self.assertEqual(values["certificates"][0]["certificate_type"], "rte_iva")

    def test_iva_custom_period_label(self):
        self._create_bill_with_tax(
            self.partner_a, 1000000.0, self.iva_tax, date_value="2026-03-15"
        )
        wizard = self._create_wizard(
            self.partner_a,
            certificate_type="rte_iva",
            period_type="custom",
            date_from="2026-03-01",
            date_to="2026-04-15",
        )
        values = self.env[
            "report.l10n_co_withholding_certificate.rte_fte_certificate"
        ]._get_report_values([wizard.id])
        self.assertIn("2026", values["period_label"])
        self.assertIn("2026", values["period_label"])

    def test_iva_report_isolates_source_withholding_type(self):
        self._create_bill_with_tax(self.partner_a, 1000000.0, self.tax)
        self._create_bill_with_tax(self.partner_a, 500000.0, self.iva_tax)
        wizard = self._create_wizard(
            self.partner_a,
            certificate_type="rte_iva",
            period_type="bimonthly",
            bimester="3",
        )
        values = self.env[
            "report.l10n_co_withholding_certificate.rte_fte_certificate"
        ]._get_report_values([wizard.id])
        concepts = values["certificates"][0]["concepts"]
        self.assertEqual(len(concepts), 1)
        self.assertEqual(concepts[0]["withheld_amount"], 75000.0)

    def test_iva_note_credit_is_net_in_report(self):
        self._create_bill_with_tax(self.partner_a, 1000000.0, self.iva_tax)
        refund = self.env["account.move"].create(
            {
                "move_type": "in_refund",
                "company_id": self.company.id,
                "partner_id": self.partner_a.id,
                "invoice_date": "2026-06-20",
                "date": "2026-06-20",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 1.0,
                            "price_unit": 200000.0,
                            "tax_ids": [(6, 0, [self.iva_tax.id])],
                        },
                    )
                ],
            }
        )
        refund.action_post()
        wizard = self._create_wizard(
            self.partner_a,
            certificate_type="rte_iva",
            period_type="bimonthly",
            bimester="3",
        )
        values = self.env[
            "report.l10n_co_withholding_certificate.rte_fte_certificate"
        ]._get_report_values([wizard.id])
        self.assertEqual(values["certificates"][0]["base_amount"], 800000.0)
        self.assertEqual(values["certificates"][0]["withheld_amount"], 120000.0)

    def test_iva_qweb_contains_title_and_bimester(self):
        self._create_bill_with_tax(self.partner_a, 1000000.0, self.iva_tax)
        wizard = self._create_wizard(
            self.partner_a,
            certificate_type="rte_iva",
            period_type="bimonthly",
            bimester="3",
        )
        html, report_type = self.env["ir.actions.report"].with_context(
            force_report_rendering=True
        )._render_qweb_html(
            "l10n_co_withholding_certificate.action_report_withholding_iva_certificate",
            wizard.ids,
        )
        self.assertEqual(report_type, "html")
        self.assertIn("CERTIFICADO DE RETENCIÓN DE IVA".encode(), html)
        self.assertIn("Mayo - Junio".encode(), html)

    def _create_real_reteiva_move(self, partner, amount, move_type="in_invoice"):
        vat_tax = self.env.ref("account.96_l10n_co_tax_1")
        reteiva_tax = self.env.ref("account.96_l10n_co_tax_12")
        company = reteiva_tax.company_id
        move = self.env["account.move"].with_company(company).create(
            {
                "move_type": move_type,
                "company_id": company.id,
                "partner_id": partner.id,
                "invoice_date": "2026-05-15",
                "date": "2026-05-15",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 1.0,
                            "price_unit": amount,
                            "tax_ids": [(6, 0, [vat_tax.id, reteiva_tax.id])],
                        },
                    )
                ],
            }
        )
        move.action_post()
        return move

    def test_real_l10n_co_reteiva_tax_configuration(self):
        vat_tax = self.env.ref("account.96_l10n_co_tax_1")
        reteiva_tax = self.env.ref("account.96_l10n_co_tax_12")
        self.assertEqual(vat_tax.name, "19% VAT")
        self.assertEqual(vat_tax.amount, 19.0)
        self.assertEqual(reteiva_tax.name, "15% RteVAT 19%")
        self.assertEqual(reteiva_tax.amount, -2.85)
        self.assertEqual(reteiva_tax.tax_group_id.name, "R IVA 2.85%")
        self.assertFalse(reteiva_tax.l10n_co_withholding_type)
        account = reteiva_tax.invoice_repartition_line_ids.filtered(
                lambda line: line.repartition_type == "tax"
            ).account_id.with_company(reteiva_tax.company_id)
        self.assertEqual(account.code, "236700")

    def test_real_reteiva_invoice_is_reported_by_engine(self):
        self._create_real_reteiva_move(self.partner_a, 1000000.0)
        wizard = self._create_wizard(
            self.partner_a,
            certificate_type="rte_iva",
            period_type="bimonthly",
            bimester="3",
        )
        wizard.company_id = self.env.ref("account.96_l10n_co_tax_12").company_id
        values = self.env[
            "report.l10n_co_withholding_certificate.rte_fte_certificate"
        ]._get_report_values([wizard.id])
        certificate = values["certificates"][0]
        self.assertEqual(certificate["base_amount"], 1000000.0)
        self.assertEqual(certificate["withheld_amount"], 28500.0)
        self.assertEqual(certificate["concepts"][0]["rate"], -2.85)

    def test_real_reteiva_credit_note_is_reported_net(self):
        self._create_real_reteiva_move(self.partner_a, 1000000.0)
        self._create_real_reteiva_move(
            self.partner_a, 200000.0, move_type="in_refund"
        )
        wizard = self._create_wizard(
            self.partner_a,
            certificate_type="rte_iva",
            period_type="bimonthly",
            bimester="3",
        )
        wizard.company_id = self.env.ref("account.96_l10n_co_tax_12").company_id
        values = self.env[
            "report.l10n_co_withholding_certificate.rte_fte_certificate"
        ]._get_report_values([wizard.id])
        certificate = values["certificates"][0]
        self.assertEqual(certificate["base_amount"], 800000.0)
        self.assertEqual(certificate["withheld_amount"], 22800.0)

    def test_real_reteiva_pdf_shows_effective_rate_and_values(self):
        self._create_real_reteiva_move(self.partner_a, 1000000.0)
        wizard = self._create_wizard(
            self.partner_a,
            certificate_type="rte_iva",
            period_type="bimonthly",
            bimester="3",
        )
        wizard.company_id = self.env.ref("account.96_l10n_co_tax_12").company_id
        html, report_type = self.env["ir.actions.report"].with_context(
            force_report_rendering=True
        )._render_qweb_html(
            "l10n_co_withholding_certificate.action_report_withholding_iva_certificate",
            wizard.ids,
        )
        self.assertEqual(report_type, "html")
        self.assertIn(b"2.85", html)
        self.assertIn(b"1,000,000", html)
        self.assertIn(b"28,500", html)

    def _create_real_reteica_move(self, partner, amount, move_type="in_invoice"):
        reteica_tax = self.env.ref("account.96_l10n_co_tax_44")
        company = reteica_tax.company_id
        move = self.env["account.move"].with_company(company).create(
            {
                "move_type": move_type,
                "company_id": company.id,
                "partner_id": partner.id,
                "invoice_date": "2026-05-15",
                "date": "2026-05-15",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.with_company(company).id,
                            "quantity": 1.0,
                            "price_unit": amount,
                            "tax_ids": [(6, 0, [reteica_tax.id])],
                        },
                    )
                ],
            }
        )
        move.action_post()
        return move

    def _create_ica_wizard(self, partners=None, period_type="bimonthly"):
        tax_company = self.env.ref("account.96_l10n_co_tax_44").company_id
        values = {
            "company_id": tax_company.id,
            "certificate_type": "rte_ica",
            "fiscal_year": 2026,
            "period_type": period_type,
        }
        if period_type == "bimonthly":
            values["bimester"] = "3"
        if period_type == "custom":
            values.update({"date_from": "2026-05-01", "date_to": "2026-06-30"})
        if partners:
            values["partner_ids"] = [(6, 0, partners.ids)]
        return self.wizard_model.create(values)

    def test_real_reteica_tax_configuration(self):
        tax = self.env.ref("account.96_l10n_co_tax_44")
        account = tax.invoice_repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        ).account_id.with_company(tax.company_id)
        self.assertEqual(tax.name, "0.69% RteICA")
        self.assertEqual(tax.amount, -0.69)
        self.assertEqual(tax.tax_group_id.name, "R ICA 0.69%")
        self.assertEqual(account.code, "236800")
        self.assertEqual(tax.l10n_co_get_certificate_withholding_type(), "rte_ica")

    def test_real_reteica_invoice_and_pdf(self):
        self._create_real_reteica_move(self.partner_a, 1000000.0)
        wizard = self._create_ica_wizard(self.partner_a)
        values = self.env[
            "report.l10n_co_withholding_certificate.rte_fte_certificate"
        ]._get_report_values([wizard.id])
        certificate = values["certificates"][0]
        self.assertEqual(certificate["certificate_type"], "rte_ica")
        self.assertEqual(certificate["base_amount"], 1000000.0)
        self.assertEqual(certificate["withheld_amount"], 6900.0)
        self.assertEqual(certificate["concepts"][0]["rate"], -0.69)

        html, report_type = self.env["ir.actions.report"].with_context(
            force_report_rendering=True
        )._render_qweb_html(
            "l10n_co_withholding_certificate.action_report_withholding_ica_certificate",
            wizard.ids,
        )
        self.assertEqual(report_type, "html")
        self.assertIn(b"CERTIFICADO DE RETENCI", html)
        self.assertIn(b"ICA", html)

    def test_real_reteica_credit_note_net_and_custom_period(self):
        self._create_real_reteica_move(self.partner_a, 1000000.0)
        self._create_real_reteica_move(
            self.partner_a, 200000.0, move_type="in_refund"
        )
        wizard = self._create_ica_wizard(self.partner_a, period_type="custom")
        values = self.env[
            "report.l10n_co_withholding_certificate.rte_fte_certificate"
        ]._get_report_values([wizard.id])
        self.assertEqual(values["date_from"].isoformat(), "2026-05-01")
        self.assertEqual(values["date_to"].isoformat(), "2026-06-30")
        self.assertIn("2026", values["period_label"])
        self.assertEqual(values["certificates"][0]["base_amount"], 800000.0)
        self.assertEqual(values["certificates"][0]["withheld_amount"], 5520.0)

    def test_reteica_multipartner_and_action(self):
        self._create_real_reteica_move(self.partner_a, 1000000.0)
        self._create_real_reteica_move(self.partner_b, 500000.0)
        wizard = self._create_ica_wizard(self.partner_a | self.partner_b)
        action = wizard.action_print_certificate()
        report = self.env.ref(
            "l10n_co_withholding_certificate.action_report_withholding_ica_certificate"
        )
        self.assertEqual(action["report_name"], report.report_name)
        values = self.env[
            "report.l10n_co_withholding_certificate.rte_fte_certificate"
        ]._get_report_values([wizard.id])
        self.assertEqual(len(values["certificates"]), 2)
