# Copyright 2026 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import date

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestL10nCoWithholdingCertificateWizard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.country_id = cls.env.ref("base.co")
        cls.wizard_model = cls.env["l10n_co.withholding.certificate.wizard"]
        cls.commercial_partner = cls.env["res.partner"].create(
            {"name": "Wizard Commercial Partner", "company_type": "company"}
        )
        cls.child_a = cls.env["res.partner"].create(
            {
                "name": "Wizard Contact A",
                "parent_id": cls.commercial_partner.id,
                "type": "contact",
            }
        )
        cls.child_b = cls.env["res.partner"].create(
            {
                "name": "Wizard Contact B",
                "parent_id": cls.commercial_partner.id,
                "type": "contact",
            }
        )

    def _wizard(self, **values):
        defaults = {
            "company_id": self.company.id,
            "certificate_type": "rte_fte",
            "fiscal_year": 2026,
            "period_type": "annual",
        }
        defaults.update(values)
        return self.wizard_model.create(defaults)

    def test_default_company_is_current_company(self):
        wizard = self.wizard_model.create({})
        self.assertEqual(wizard.company_id, self.env.company)

    def test_rte_fte_annual_dates(self):
        wizard = self._wizard()
        self.assertEqual(
            wizard._get_period_dates(), (date(2026, 1, 1), date(2026, 12, 31))
        )

    def test_rte_fte_annual_dates_without_onchange(self):
        wizard = self.wizard_model.create(
            {
                "company_id": self.company.id,
                "certificate_type": "rte_fte",
                "fiscal_year": 2026,
                "period_type": "annual",
            }
        )
        self.assertFalse(wizard.date_from)
        self.assertFalse(wizard.date_to)
        self.assertEqual(
            wizard._get_period_dates(), (date(2026, 1, 1), date(2026, 12, 31))
        )

    def test_rte_iva_first_bimester_dates(self):
        wizard = self._wizard(
            certificate_type="rte_iva", period_type="bimonthly", bimester="1"
        )
        self.assertEqual(
            wizard._get_period_dates(), (date(2026, 1, 1), date(2026, 2, 28))
        )

    def test_bimester_handles_leap_year(self):
        wizard = self._wizard(
            certificate_type="rte_iva", period_type="bimonthly", fiscal_year=2028, bimester="1"
        )
        self.assertEqual(
            wizard._get_period_dates(), (date(2028, 1, 1), date(2028, 2, 29))
        )

    def test_rte_iva_bimester_dates_without_onchange(self):
        wizard = self.wizard_model.create(
            {
                "company_id": self.company.id,
                "certificate_type": "rte_iva",
                "fiscal_year": 2026,
                "period_type": "bimonthly",
                "bimester": "3",
            }
        )
        self.assertEqual(
            wizard._get_period_dates(), (date(2026, 5, 1), date(2026, 6, 30))
        )

    def test_rte_iva_sixth_bimester_dates(self):
        wizard = self._wizard(
            certificate_type="rte_iva", period_type="bimonthly", bimester="6"
        )
        self.assertEqual(
            wizard._get_period_dates(), (date(2026, 11, 1), date(2026, 12, 31))
        )

    def test_custom_period_is_validated(self):
        wizard = self._wizard(
            period_type="custom",
            date_from=date(2026, 3, 1),
            date_to=date(2026, 3, 31),
        )
        self.assertEqual(
            wizard._get_period_dates(), (date(2026, 3, 1), date(2026, 3, 31))
        )

    def test_custom_period_rejects_reverse_dates(self):
        wizard = self._wizard(
            period_type="custom",
            date_from=date(2026, 3, 31),
            date_to=date(2026, 3, 1),
        )
        with self.assertRaises(ValidationError):
            wizard.action_preview()

    def test_empty_partners_means_all_partners(self):
        wizard = self._wizard()
        self.assertIsNone(wizard._get_normalized_partners())

    def test_child_partners_normalize_without_duplicates(self):
        wizard = self._wizard(partner_ids=[(6, 0, [self.child_a.id, self.child_b.id])])
        partners = wizard._get_normalized_partners()
        self.assertEqual(partners, self.commercial_partner)

    def test_invalid_period_for_certificate_type_is_rejected(self):
        wizard = self._wizard(period_type="bimonthly", bimester="1")
        with self.assertRaises(ValidationError):
            wizard.action_preview()

    def test_preview_without_data_raises_user_error(self):
        wizard = self._wizard(
            period_type="custom",
            date_from=date(2099, 1, 1),
            date_to=date(2099, 1, 31),
        )
        with self.assertRaisesRegex(UserError, "No withholding entries"):
            wizard.action_preview()

    def test_preview_populates_summary_from_engine(self):
        tax = self.env["account.tax"].create(
            {
                "name": "Wizard ReteFuente",
                "amount": -2.5,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "l10n_co_withholding_type": "rte_fte",
            }
        )
        product = self.env["product.product"].create(
            {"name": "Wizard service", "type": "service"}
        )
        move = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "company_id": self.company.id,
                "partner_id": self.commercial_partner.id,
                "invoice_date": "2026-06-15",
                "date": "2026-06-15",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "quantity": 1.0,
                            "price_unit": 1000000.0,
                            "tax_ids": [(6, 0, [tax.id])],
                        },
                    )
                ],
            }
        )
        move.action_post()

        wizard = self._wizard(partner_ids=[(6, 0, [self.child_a.id])])
        action = wizard.action_preview()

        self.assertEqual(action["res_id"], wizard.id)
        self.assertEqual(wizard.date_from, date(2026, 1, 1))
        self.assertEqual(wizard.date_to, date(2026, 12, 31))
        self.assertTrue(wizard.has_results)
        self.assertEqual(wizard.partner_count, 1)
        self.assertEqual(wizard.total_base_amount, 1000000.0)
        self.assertEqual(wizard.total_withheld_amount, 25000.0)

    def test_filter_change_clears_summary(self):
        wizard = self._wizard(
            partner_count=1,
            total_base_amount=10.0,
            total_withheld_amount=2.0,
            has_results=True,
        )
        wizard._onchange_filter()
        self.assertFalse(wizard.has_results)
        self.assertEqual(wizard.partner_count, 0)
        self.assertEqual(wizard.total_base_amount, 0.0)
        self.assertEqual(wizard.total_withheld_amount, 0.0)

    def test_accounting_user_can_manage_wizard_without_superuser(self):
        user = self.env["res.users"].create(
            {
                "name": "Certificate Accountant",
                "login": "certificate_accountant",
                "company_id": self.company.id,
                "company_ids": [(6, 0, [self.company.id])],
                "groups_id": [(6, 0, [self.env.ref("account.group_account_user").id])],
            }
        )
        self.assertFalse(user._is_superuser())
        user_env = self.env(user=user)
        wizard = user_env["l10n_co.withholding.certificate.wizard"].create(
            {
                "company_id": self.company.id,
                "certificate_type": "rte_fte",
                "fiscal_year": 2026,
                "period_type": "annual",
            }
        )
        self.assertEqual(wizard.with_user(user).read(["fiscal_year"])[0]["fiscal_year"], 2026)
        wizard.with_user(user).write({"fiscal_year": 2027})
        self.assertEqual(wizard.with_user(user).fiscal_year, 2027)
