# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase


class L10nCoElectronicInvoiceTestCommon(TransactionCase):
    """Common test fixtures for Colombian electronic invoice tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Company
        cls.company = cls.env.ref("base.main_company")
        cls.company.write(
            {
                "country_id": cls.env.ref("base.co").id,
                "vat": "900197268",
                "account_fiscal_country_id": cls.env.ref("base.co").id,
            }
        )

        # Partner (customer)
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Customer Colombia",
                "vat": "900108281",
                "country_id": cls.env.ref("base.co").id,
                "is_company": True,
                "city": "Bogotá",
                "state_id": cls.env.ref("base.state_co_11", False)
                and cls.env.ref("base.state_co_11").id
                or False,
            }
        )

        # Journal
        cls.journal = cls.env["account.journal"].search(
            [
                ("type", "=", "sale"),
                ("company_id", "=", cls.company.id),
            ],
            limit=1,
        )
        if cls.journal:
            cls.journal.write(
                {
                    "l10n_co_dian_operation_mode": "test",
                    "l10n_co_dian_software_identification": "test-software-id",
                    "l10n_co_dian_software_pin": "12345",
                    "l10n_co_dian_software_technical_key_test": "test-tech-key",
                    "l10n_co_electronic_document_resolution_test": "18760000001",
                    "l10n_co_electronic_document_prefix_test": "SETP",
                    "l10n_co_electronic_document_start_number_test": 990000000,
                    "l10n_co_electronic_document_end_number_test": 995000000,
                }
            )
