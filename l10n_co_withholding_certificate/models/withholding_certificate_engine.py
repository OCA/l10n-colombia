# Copyright 2026 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import ValidationError


class WithholdingCertificateEngine(models.AbstractModel):
    _name = "l10n_co.withholding.certificate.engine"
    _description = "Colombian Withholding Certificate Engine"

    _supported_certificate_types = ("rte_fte", "rte_iva", "rte_ica")

    def _validate_certificate_type(self, certificate_type):
        if certificate_type not in self._supported_certificate_types:
            raise ValidationError(
                _(
                    "Unsupported certificate type '%(type)s'. Supported values are: %(valid)s",
                    type=certificate_type,
                    valid=", ".join(self._supported_certificate_types),
                )
            )

    def _get_line_withholding_type(self, line):
        tax = line.tax_line_id
        if not tax:
            return False
        return tax.l10n_co_get_certificate_withholding_type()

    def _get_signed_base_amount(self, line):
        if not line.tax_base_amount:
            return 0.0
        if line.credit > 0:
            return line.tax_base_amount
        if line.debit > 0:
            return -line.tax_base_amount
        return 0.0

    def _get_signed_withheld_amount(self, line):
        return line.credit - line.debit

    def _get_partner_group_key(self, line):
        partner = line.partner_id.commercial_partner_id or line.partner_id
        return partner.id

    def _get_concept_key(self, tax):
        if tax and getattr(tax, "l10n_co_withholding_concept", False):
            return tax.l10n_co_withholding_concept
        if tax:
            return tax.name or "sin_concepto"
        return "sin_concepto"

    def _get_withholding_lines(self, company, date_from, date_to, certificate_type, partners=None):
        self._validate_certificate_type(certificate_type)

        if date_from > date_to:
            raise ValidationError(_("The start date must be before or equal to the end date."))

        domain = [
            ("company_id", "=", company.id),
            ("parent_state", "=", "posted"),
            ("date", ">=", date_from),
            ("date", "<=", date_to),
            ("tax_line_id", "!=", False),
            ("partner_id", "!=", False),
        ]
        if partners:
            partner_ids = partners if isinstance(partners, (list, tuple, set)) else partners.ids
            domain.append(("move_id.commercial_partner_id", "in", partner_ids))

        lines = self.env["account.move.line"].search(domain)
        return lines.filtered(lambda line: self._get_line_withholding_type(line) == certificate_type)

    def _prepare_concept_data(self, tax, context_lines):
        concept_key = self._get_concept_key(tax)
        return {
            "concept": concept_key,
            "tax": tax,
            "rate": float(tax.amount) if tax and tax.amount else 0.0,
            "base_amount": sum(self._get_signed_base_amount(line) for line in context_lines),
            "withheld_amount": sum(self._get_signed_withheld_amount(line) for line in context_lines),
            "move_line_ids": [line.id for line in context_lines],
        }

    def _group_lines_by_partner(self, lines, certificate_type):
        grouped = {}

        for line in lines:
            if self._get_line_withholding_type(line) != certificate_type:
                continue

            partner = line.partner_id.commercial_partner_id or line.partner_id
            partner_key = partner.id
            if partner_key not in grouped:
                grouped[partner_key] = {
                    "partner": partner,
                    "base_amount": 0.0,
                    "withheld_amount": 0.0,
                    "concepts": {},
                    "move_line_ids": [],
                }

            base_amount = self._get_signed_base_amount(line)
            withheld_amount = self._get_signed_withheld_amount(line)

            grouped[partner_key]["base_amount"] += base_amount
            grouped[partner_key]["withheld_amount"] += withheld_amount
            grouped[partner_key]["move_line_ids"].append(line.id)

            concept_key = self._get_concept_key(line.tax_line_id)
            if concept_key not in grouped[partner_key]["concepts"]:
                grouped[partner_key]["concepts"][concept_key] = {
                    "concept": concept_key,
                    "tax": line.tax_line_id,
                    "rate": float(line.tax_line_id.amount) if line.tax_line_id and line.tax_line_id.amount else 0.0,
                    "base_amount": 0.0,
                    "withheld_amount": 0.0,
                    "move_line_ids": [],
                }

            grouped[partner_key]["concepts"][concept_key]["base_amount"] += base_amount
            grouped[partner_key]["concepts"][concept_key]["withheld_amount"] += withheld_amount
            grouped[partner_key]["concepts"][concept_key]["move_line_ids"].append(line.id)

        return grouped

    def get_certificate_data(self, company, date_from, date_to, certificate_type, partners=None):
        """Return certificate-ready data for posted withholding lines.

        The returned structure is optimized for later presentation layers. It includes
        partner and tax recordsets plus IDs for traceability.
        """
        self._validate_certificate_type(certificate_type)

        lines = self._get_withholding_lines(company, date_from, date_to, certificate_type, partners=partners)
        grouped = self._group_lines_by_partner(lines, certificate_type)

        partners_data = []
        for partner_id, values in grouped.items():
            partner_data = {
                "partner": values["partner"],
                "base_amount": values["base_amount"],
                "withheld_amount": values["withheld_amount"],
                "concepts": [
                    {
                        "concept": concept["concept"],
                        "tax": concept["tax"],
                        "rate": concept["rate"],
                        "base_amount": concept["base_amount"],
                        "withheld_amount": concept["withheld_amount"],
                        "move_line_ids": concept["move_line_ids"],
                    }
                    for concept in values["concepts"].values()
                ],
                "move_line_ids": values["move_line_ids"],
            }
            partners_data.append(partner_data)

        return {
            "company": company,
            "date_from": date_from,
            "date_to": date_to,
            "certificate_type": certificate_type,
            "partners": partners_data,
        }
