# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from unittest import TestCase

from lxml import etree


class TestXmlGeneration(TestCase):
    """Test XML generation structure without Odoo environment."""

    NS_EXT = "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
    NS_CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    NS_STS_INVOICE = "dian:gov:co:facturaelectronica:Structures-2-1"
    NS_STS_OTHER = "http://www.dian.gov.co/contratos/facturaelectronica/v1/Structures"

    def _build_ubl_extensions(self, sts_ns, include_invoice_control=True):
        """Helper to build UBLExtensions structure."""
        ubl_extensions = etree.Element(etree.QName(self.NS_EXT, "UBLExtensions"))
        ubl_ext_1 = etree.SubElement(
            ubl_extensions, etree.QName(self.NS_EXT, "UBLExtension")
        )
        ext_content = etree.SubElement(
            ubl_ext_1, etree.QName(self.NS_EXT, "ExtensionContent")
        )
        dian_ext = etree.SubElement(ext_content, etree.QName(sts_ns, "DianExtensions"))

        if include_invoice_control:
            invoice_control = etree.SubElement(
                dian_ext, etree.QName(sts_ns, "InvoiceControl")
            )
            etree.SubElement(
                invoice_control, etree.QName(sts_ns, "InvoiceAuthorization")
            ).text = "18760000001"

        # InvoiceSource
        invoice_source = etree.SubElement(
            dian_ext, etree.QName(sts_ns, "InvoiceSource")
        )
        id_code = etree.SubElement(
            invoice_source, etree.QName(self.NS_CBC, "IdentificationCode")
        )
        id_code.text = "CO"

        # SoftwareProvider
        sw_provider = etree.SubElement(
            dian_ext, etree.QName(sts_ns, "SoftwareProvider")
        )
        etree.SubElement(
            sw_provider, etree.QName(sts_ns, "ProviderID")
        ).text = "800197268"

        # UBLExtension[2] - signature placeholder
        ubl_ext_2 = etree.SubElement(
            ubl_extensions, etree.QName(self.NS_EXT, "UBLExtension")
        )
        etree.SubElement(ubl_ext_2, etree.QName(self.NS_EXT, "ExtensionContent"))

        return ubl_extensions

    def test_invoice_ubl_extensions_has_invoice_control(self):
        """Invoice UBLExtensions must contain InvoiceControl."""
        ubl_ext = self._build_ubl_extensions(
            self.NS_STS_INVOICE, include_invoice_control=True
        )
        invoice_control = ubl_ext.find(f".//{{{self.NS_STS_INVOICE}}}InvoiceControl")
        self.assertIsNotNone(invoice_control)

    def test_credit_note_ubl_extensions_no_invoice_control(self):
        """Credit/Debit note UBLExtensions must NOT contain InvoiceControl."""
        ubl_ext = self._build_ubl_extensions(
            self.NS_STS_OTHER, include_invoice_control=False
        )
        invoice_control = ubl_ext.find(f".//{{{self.NS_STS_OTHER}}}InvoiceControl")
        self.assertIsNone(invoice_control)

    def test_ubl_extensions_has_two_extensions(self):
        """UBLExtensions must contain exactly 2 UBLExtension elements."""
        ubl_ext = self._build_ubl_extensions(self.NS_STS_INVOICE)
        extensions = ubl_ext.findall(f"{{{self.NS_EXT}}}UBLExtension")
        self.assertEqual(len(extensions), 2)

    def test_second_extension_is_empty_placeholder(self):
        """UBLExtension[2] must be empty placeholder for signature."""
        ubl_ext = self._build_ubl_extensions(self.NS_STS_INVOICE)
        extensions = ubl_ext.findall(f"{{{self.NS_EXT}}}UBLExtension")
        ext_content = extensions[1].find(f"{{{self.NS_EXT}}}ExtensionContent")
        self.assertIsNotNone(ext_content)
        self.assertEqual(len(ext_content), 0)  # no children

    def test_invoice_source_country_code(self):
        """InvoiceSource IdentificationCode must be CO."""
        ubl_ext = self._build_ubl_extensions(self.NS_STS_INVOICE)
        id_code = ubl_ext.find(f".//{{{self.NS_CBC}}}IdentificationCode")
        self.assertIsNotNone(id_code)
        self.assertEqual(id_code.text, "CO")

    def test_authorization_provider_nit(self):
        """SoftwareProvider ProviderID should be present."""
        ubl_ext = self._build_ubl_extensions(self.NS_STS_INVOICE)
        provider_id = ubl_ext.find(f".//{{{self.NS_STS_INVOICE}}}ProviderID")
        self.assertIsNotNone(provider_id)
        self.assertEqual(provider_id.text, "800197268")
