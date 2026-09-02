# Copyright 2026 juparmer - Juan Arcos <juanparmer@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase

from odoo.addons.l10n_co_verification_digit.models.res_partner import (
    compute_verification_digit,
)


class TestVerificationDigit(TransactionCase):
    def test_compute_verification_digit_standard(self):
        """Test DV computation for a standard 9-digit NIT."""
        self.assertEqual(compute_verification_digit("900123456"), 8)

    def test_compute_verification_digit_known(self):
        """Test DV for NIT 800003123."""
        self.assertEqual(compute_verification_digit("800003123"), 3)

    def test_compute_verification_digit_another(self):
        """Test DV for NIT 800153993."""
        self.assertEqual(compute_verification_digit("800153993"), 7)

    def test_compute_verification_digit_short_nit(self):
        """Test DV for a short NIT (less than 9 digits)."""
        result = compute_verification_digit("123456")
        self.assertIn(result, range(10))

    def test_partner_computes_dv(self):
        """Test that the partner computes the verification digit."""
        country_co = self.env.ref("base.co")
        partner = self.env["res.partner"].create(
            {
                "name": "Test CO Partner",
                "country_id": country_co.id,
                "vat": "900123456",
            },
        )
        self.assertEqual(partner.l10n_co_verification_digit, "8")

    def test_partner_no_dv_for_non_co(self):
        """Test that non-Colombian partners have no verification digit."""
        partner = self.env["res.partner"].create(
            {
                "name": "Test US Partner",
                "country_id": self.env.ref("base.us").id,
                "vat": "123456789",
            },
        )
        self.assertFalse(partner.l10n_co_verification_digit)
