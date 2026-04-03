# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import hashlib
import logging
import random
import uuid
from datetime import datetime

import pytz
import xmlsig
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import Encoding
from lxml import etree

from ..utils.constants import (
    DEFAULT_POLICY_ID,
    DEFAULT_POLICY_NAME,
    NSD,
    POLICY_HASH_VALUE,
)

_logger = logging.getLogger(__name__)


class XMLSigner:
    """Firma XML según estándares DIAN Colombia."""

    def __init__(self, exchange_record, public_cert, private_key):
        self.exchange_record = exchange_record
        self.public_cert = public_cert
        self.private_key = private_key

    def sign_xml(self, xml_content):
        try:
            return self._document_sign(xml_content)
        except Exception as e:
            _logger.error("Error al firmar XML: %s", str(e))
            raise ValueError(f"Error al firmar el XML: {e}") from e

    def _document_sign(self, xml_content):
        rand_min = 1
        rand_max = 99999
        signature_id = f"Signature{random.randint(rand_min, rand_max):05d}"
        signed_properties_id = (
            f"{signature_id}-SignedProperties{random.randint(rand_min, rand_max):05d}"
        )
        key_info_id = f"KeyInfo{random.randint(rand_min, rand_max):05d}"
        reference_id = f"Reference{random.randint(rand_min, rand_max):05d}"
        object_id = f"Object{random.randint(rand_min, rand_max):05d}"

        etsi = "http://uri.etsi.org/01903/v1.3.2#"

        sig_policy_identifier = DEFAULT_POLICY_ID
        sig_policy_hash_value = POLICY_HASH_VALUE

        root = etree.fromstring(xml_content)

        sign = xmlsig.template.create(
            c14n_method=xmlsig.constants.TransformInclC14N,
            sign_method=xmlsig.constants.TransformRsaSha256,
            name=signature_id,
            ns="ds",
        )

        key_info = xmlsig.template.ensure_key_info(sign, name=key_info_id)
        x509_data = xmlsig.template.add_x509_data(key_info)
        xmlsig.template.x509_data_add_certificate(x509_data)
        xmlsig.template.add_key_value(key_info)

        xmlsig.template.add_reference(
            sign,
            xmlsig.constants.TransformSha256,
            uri="#" + signed_properties_id,
            uri_type="http://uri.etsi.org/01903#SignedProperties",
        )
        xmlsig.template.add_reference(
            sign, xmlsig.constants.TransformSha256, uri="#" + key_info_id
        )
        ref = xmlsig.template.add_reference(
            sign, xmlsig.constants.TransformSha256, name=reference_id, uri=""
        )
        xmlsig.template.add_transform(ref, xmlsig.constants.TransformEnveloped)

        object_node = etree.SubElement(
            sign,
            etree.QName(xmlsig.constants.DSigNs, "Object"),
            nsmap={"etsi": etsi},
            attrib={xmlsig.constants.ID_ATTR: object_id},
        )

        qualifying_properties = etree.SubElement(
            object_node,
            etree.QName(etsi, "QualifyingProperties"),
            attrib={"Target": "#" + signature_id},
        )

        signed_properties = etree.SubElement(
            qualifying_properties,
            etree.QName(etsi, "SignedProperties"),
            attrib={xmlsig.constants.ID_ATTR: signed_properties_id},
        )

        signed_signature_properties = etree.SubElement(
            signed_properties, etree.QName(etsi, "SignedSignatureProperties")
        )

        bogota_tz = pytz.timezone("America/Bogota")
        now = datetime.now(pytz.utc).astimezone(bogota_tz)
        etree.SubElement(
            signed_signature_properties, etree.QName(etsi, "SigningTime")
        ).text = now.isoformat(timespec="milliseconds")

        signing_certificate = etree.SubElement(
            signed_signature_properties, etree.QName(etsi, "SigningCertificate")
        )
        signing_certificate_cert = etree.SubElement(
            signing_certificate, etree.QName(etsi, "Cert")
        )
        cert_digest = etree.SubElement(
            signing_certificate_cert, etree.QName(etsi, "CertDigest")
        )
        etree.SubElement(
            cert_digest,
            etree.QName(xmlsig.constants.DSigNs, "DigestMethod"),
            attrib={"Algorithm": "http://www.w3.org/2001/04/xmlenc#sha256"},
        )
        hash_cert = hashlib.sha256(self.public_cert.public_bytes(Encoding.DER))
        etree.SubElement(
            cert_digest, etree.QName(xmlsig.constants.DSigNs, "DigestValue")
        ).text = base64.b64encode(hash_cert.digest()).decode()

        issuer_serial = etree.SubElement(
            signing_certificate_cert, etree.QName(etsi, "IssuerSerial")
        )
        etree.SubElement(
            issuer_serial, etree.QName(xmlsig.constants.DSigNs, "X509IssuerName")
        ).text = xmlsig.utils.get_rdns_name(self.public_cert.issuer.rdns)
        etree.SubElement(
            issuer_serial, etree.QName(xmlsig.constants.DSigNs, "X509SerialNumber")
        ).text = str(self.public_cert.serial_number)

        signature_policy_identifier = etree.SubElement(
            signed_signature_properties,
            etree.QName(etsi, "SignaturePolicyIdentifier"),
        )
        signature_policy_id = etree.SubElement(
            signature_policy_identifier, etree.QName(etsi, "SignaturePolicyId")
        )
        sig_policy_id = etree.SubElement(
            signature_policy_id, etree.QName(etsi, "SigPolicyId")
        )
        etree.SubElement(
            sig_policy_id, etree.QName(etsi, "Identifier")
        ).text = sig_policy_identifier
        etree.SubElement(
            sig_policy_id, etree.QName(etsi, "Description")
        ).text = DEFAULT_POLICY_NAME

        sig_policy_hash = etree.SubElement(
            signature_policy_id, etree.QName(etsi, "SigPolicyHash")
        )
        etree.SubElement(
            sig_policy_hash,
            etree.QName(xmlsig.constants.DSigNs, "DigestMethod"),
            attrib={"Algorithm": "http://www.w3.org/2001/04/xmlenc#sha256"},
        )
        etree.SubElement(
            sig_policy_hash, etree.QName(xmlsig.constants.DSigNs, "DigestValue")
        ).text = sig_policy_hash_value

        signer_role = etree.SubElement(
            signed_signature_properties, etree.QName(etsi, "SignerRole")
        )
        claimed_roles = etree.SubElement(signer_role, etree.QName(etsi, "ClaimedRoles"))
        etree.SubElement(
            claimed_roles, etree.QName(etsi, "ClaimedRole")
        ).text = "supplier"

        root.append(sign)

        ctx = xmlsig.SignatureContext()
        ctx.x509 = self.public_cert
        ctx.public_key = self.public_cert.public_key()
        ctx.private_key = self.private_key

        ctx.sign(sign)

        ext_ns = (
            "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
        )
        ubl_extensions = root.find(f"{{{ext_ns}}}UBLExtensions")
        if ubl_extensions is not None:
            ubl_extension_2 = ubl_extensions.findall(f"{{{ext_ns}}}UBLExtension")
            if len(ubl_extension_2) >= 2:
                ext_content = ubl_extension_2[1].find(f"{{{ext_ns}}}ExtensionContent")
                if ext_content is not None:
                    root.remove(sign)
                    ext_content.append(sign)

        return etree.tostring(
            root, xml_declaration=True, encoding="UTF-8", standalone=True
        )

    def _envelope_sign(
        self,
        soap_envelope,
    ):
        try:
            root = self._prepare_xml_for_signing(soap_envelope)

            sign_id = f"SIG-{uuid.uuid1()}"
            sign = xmlsig.template.create(
                c14n_method=xmlsig.constants.TransformExclC14N,
                sign_method=xmlsig.constants.TransformRsaSha256,
                ns="ds",
                name=sign_id,
            )

            if sign is None:
                raise Exception(
                    "Ocurrió un error al crear plantilla para firma digital."
                )

            header = root.find("soap:Header", namespaces=NSD)
            security = header.find("wsse:Security", namespaces=NSD)  # type: ignore
            security.append(sign)  # type: ignore

            to_id = header.find("wsa:To", namespaces=NSD).attrib.get(
                "{http://docs.oasis-open.org/wss/2004/01/"
                "oasis-200401-wss-wssecurity-utility-1.0.xsd}Id"
            )
            ref = xmlsig.template.add_reference(
                node=sign,
                digest_method=xmlsig.constants.TransformSha256,
                uri=f"#{to_id}",
            )
            xmlsig.template.add_transform(
                node=ref,
                transform=xmlsig.constants.TransformExclC14N,
            )
            key_info = xmlsig.template.ensure_key_info(node=sign)
            key_info.attrib["Id"] = f"KI-{uuid.uuid1()}"

            ctx = xmlsig.SignatureContext()
            ctx.x509 = self.public_cert
            ctx.public_key = self.public_cert.public_key()
            ctx.private_key = self.private_key

            binary_security_token = security.find(
                "wsse:BinarySecurityToken", namespaces=NSD
            )
            binary_security_token_id = f"X509-{uuid.uuid1()}"
            binary_security_token.attrib[etree.QName(NSD["wsu"], "Id")] = (
                binary_security_token_id
            )
            binary_security_token.text = base64.b64encode(
                ctx.x509.public_bytes(encoding=serialization.Encoding.DER)
            )

            security_token_reference = etree.SubElement(
                key_info,
                etree.QName(NSD["wsse"], "SecurityTokenReference"),
                nsmap={"wsse": NSD["wsse"]},
            )
            security_token_reference.attrib[etree.QName(NSD["wsu"], "Id")] = (
                f"STR-{uuid.uuid1()}"
            )

            key_info_reference = etree.SubElement(
                security_token_reference,
                etree.QName(NSD["wsse"], "Reference"),
                nsmap={"wsse": NSD["wsse"]},
            )
            key_info_reference.attrib["URI"] = f"#{binary_security_token_id}"
            key_info_reference.attrib["ValueType"] = (
                "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3"
            )

            ctx.sign(sign)
            ctx.verify(sign)
            _logger.info("Mensaje SOAP firmado correctamente")
            return etree.tostring(root).decode("utf-8")
        except Exception as e:
            _logger.error(f"Error al firmar el mensaje SOAP: {e}")
            raise ValueError(f"Error al firmar el mensaje SOAP: {e}") from e

    def _prepare_xml_for_signing(self, xml_content):
        root = etree.fromstring(xml_content)
        # Normalizar textos donde típicamente hay indentación
        for e in root.iter():
            if e.text and e.text.strip():
                e.text = e.text.strip()
            elif e.text:
                e.text = None
            e.tail = None
        return root
