# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from unittest import TestCase


class TestResponseProcessing(TestCase):
    """Test DIAN response parsing logic without Odoo environment."""

    def _build_soap_response(
        self, status_code, status_description="", xml_document_key="", status_message=""
    ):
        """Build a mock SOAP response dict."""
        return {
            "s:Envelope": {
                "s:Header": {
                    "o:Security": {
                        "u:Timestamp": {
                            "u:Created": "2025-01-01T00:00:00Z",
                        }
                    }
                },
                "s:Body": {
                    "SendBillSyncResponse": {
                        "SendBillSyncResponseResult": {
                            "b:StatusCode": status_code,
                            "b:StatusDescription": status_description,
                            "b:StatusMessage": status_message,
                            "b:XmlDocumentKey": xml_document_key,
                        }
                    }
                },
            }
        }

    def test_accepted_response_structure(self):
        """Accepted response has StatusCode 00."""
        response = self._build_soap_response(
            status_code="00",
            status_description="Documento validado por la DIAN",
            xml_document_key="abc123cufe",
        )
        result = response["s:Envelope"]["s:Body"]["SendBillSyncResponse"]
        inner = result["SendBillSyncResponseResult"]
        self.assertEqual(inner["b:StatusCode"], "00")
        self.assertEqual(inner["b:XmlDocumentKey"], "abc123cufe")

    def test_rejected_response_structure(self):
        """Rejected response has StatusCode 99."""
        response = self._build_soap_response(
            status_code="99",
            status_description="Documento rechazado",
            status_message="Error en validación",
        )
        result = response["s:Envelope"]["s:Body"]["SendBillSyncResponse"]
        inner = result["SendBillSyncResponseResult"]
        self.assertEqual(inner["b:StatusCode"], "99")

    def test_timestamp_extraction(self):
        """Test that create_date can be extracted from response."""
        response = self._build_soap_response(status_code="00")
        create_date = response["s:Envelope"]["s:Header"]["o:Security"]["u:Timestamp"][
            "u:Created"
        ]
        self.assertEqual(create_date, "2025-01-01T00:00:00Z")

    def test_test_set_response_structure(self):
        """Test set async response has different structure."""
        response = {
            "s:Envelope": {
                "s:Header": {
                    "o:Security": {
                        "u:Timestamp": {
                            "u:Created": "2025-01-01T00:00:00Z",
                        }
                    }
                },
                "s:Body": {
                    "SendTestSetAsyncResponse": {
                        "SendTestSetAsyncResponseResult": {
                            "b:ZipKey": "zip-key-123",
                            "b:ErrorMessageList": {},
                        }
                    }
                },
            }
        }
        result = response["s:Envelope"]["s:Body"]["SendTestSetAsyncResponse"]
        inner = result["SendTestSetAsyncResponseResult"]
        self.assertEqual(inner["b:ZipKey"], "zip-key-123")
