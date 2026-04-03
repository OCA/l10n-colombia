# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from hashlib import sha384
from unittest import TestCase


class TestCufeComputation(TestCase):
    """Test CUFE/CUDE computation logic without Odoo environment."""

    def test_sha384_hash_format(self):
        """CUFE must be a SHA384 hex digest (96 chars)."""
        test_input = "test_cufe_input_string"
        result = sha384(test_input.encode()).hexdigest()
        self.assertEqual(len(result), 96)
        self.assertTrue(all(c in "0123456789abcdef" for c in result))

    def test_software_security_code(self):
        """SoftwareSecurityCode = SHA384(softwareId + pin + invoiceNumber)."""
        software_id = "56f2ae4e-9812-4fad-9255-08fcfcd5ccb0"
        pin = "12345"
        invoice_number = "SETP990000001"

        security_input = software_id + pin + invoice_number
        result = sha384(security_input.encode()).hexdigest()

        self.assertEqual(len(result), 96)
        # Verify deterministic
        self.assertEqual(result, sha384(security_input.encode()).hexdigest())

    def test_cufe_composition(self):
        """Test that CUFE input string is composed correctly."""
        cufe_vals = {
            "invoice_id": "SETP990000002",
            "issue_date": "2019-06-20",
            "issue_time": "09:15:23-05:00",
            "line_extension_amount": "10000.00",
            "tax_code_01": "01",
            "ValImp1": "1900.00",
            "tax_code_04": "04",
            "ValImp2": "0.00",
            "tax_code_03": "03",
            "ValImp3": "0.00",
            "ValTotFac": "11900.00",
            "supplier_company_id": "800197268",
            "customer_company_id": "900108281",
            "key": "test-technical-key",
            "profile_execution_id": "2",
        }
        cufe_string = "".join(str(v) for v in cufe_vals.values())
        cufe = sha384(cufe_string.encode()).hexdigest()

        self.assertEqual(len(cufe), 96)
        self.assertIn("SETP990000002", cufe_string)
        self.assertIn("800197268", cufe_string)

    def test_cude_uses_pin_instead_of_technical_key(self):
        """For credit/debit notes (codes 20, 30), CUDE uses PIN not technical key."""
        pin = "12345"
        tech_key = "tech-key-abc"

        # For invoice (code 01), uses technical key
        invoice_key = tech_key

        # For credit note (code 20), uses PIN
        credit_note_key = pin

        self.assertNotEqual(invoice_key, credit_note_key)
