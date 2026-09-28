# Copyright 2026 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import format_date
from odoo.tools.image import image_data_uri
from odoo.tools import LazyTranslate



class WithholdingCertificateReport(models.AbstractModel):
    _name = "report.l10n_co_withholding_certificate.rte_fte_certificate"
    _description = "Colombian Withholding Certificate"

    @api.model
    def _get_bimester_labels(self):
        return {
            "1": _("Enero - Febrero"),
            "2": _("Marzo - Abril"),
            "3": _("Mayo - Junio"),
            "4": _("Julio - Agosto"),
            "5": _("Septiembre - Octubre"),
            "6": _("Noviembre - Diciembre"),
        }

    @api.model
    def _address_values(self, partner):
        return [
            value
            for value in (
                partner.street,
                partner.street2,
                partner.city,
                partner.state_id.name,
                partner.country_id.name,
            )
            if value
        ]

    @api.model
    def _prepare_certificate(self, company, partner_data, fiscal_year):
        partner = partner_data["partner"].commercial_partner_id or partner_data["partner"]
        concepts = [
            concept
            for concept in partner_data["concepts"]
            if concept["base_amount"] or concept["withheld_amount"]
        ]
        return {
            "partner": partner,
            "partner_name": partner.name,
            "partner_vat": partner.vat or "",
            "partner_address": self._address_values(partner),
            "company": company,
            "company_name": company.partner_id.name,
            "company_vat": company.partner_id.vat or "",
            "company_address": self._address_values(company.partner_id),
            "company_logo": image_data_uri(company.logo) if company.logo else False,
            "fiscal_year": fiscal_year,
            "concepts": concepts,
            "base_amount": partner_data["base_amount"],
            "withheld_amount": partner_data["withheld_amount"],
            "currency": company.currency_id,
            "issue_date": fields.Date.context_today(self),
        }

    @api.model
    def _get_period_label(self, wizard, date_from, date_to, period_type, bimester):
        if period_type == "bimonthly" and bimester:
            return self._get_bimester_labels().get(bimester, "")
        if period_type == "custom":
            return _("%s - %s") % (
                format_date(self.env, date_from),
                format_date(self.env, date_to),
            )
        return _("Enero - Diciembre")

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        wizard = self.env["l10n_co.withholding.certificate.wizard"].browse(docids).exists()
        if not wizard:
            raise UserError(_("The withholding certificate wizard no longer exists."))
        wizard.ensure_one()

        certificate_type = data.get("certificate_type", wizard.certificate_type)
        if certificate_type not in ("rte_fte", "rte_iva", "rte_ica"):
            raise UserError(
                _(
                    "PDF certificates are currently available for ReteFuente, "
                    "ReteIVA, and ReteICA."
                )
            )
        company = self.env["res.company"].browse(
            data.get("company_id", wizard.company_id.id)
        ).exists()
        if not company:
            raise UserError(_("The certificate company could not be found."))
        date_from = fields.Date.from_string(data["date_from"]) if data.get("date_from") else wizard._get_period_dates()[0]
        date_to = fields.Date.from_string(data["date_to"]) if data.get("date_to") else wizard._get_period_dates()[1]
        period_type = data.get("period_type", wizard.period_type)
        bimester = data.get("bimester", wizard.bimester)
        partner_ids = data.get("partner_ids")
        partners = (
            self.env["res.partner"].browse(partner_ids).exists()
            if partner_ids
            else wizard._get_normalized_partners()
        )
        engine = self.env["l10n_co.withholding.certificate.engine"]
        certificate_data = engine.get_certificate_data(
            company=company,
            date_from=date_from,
            date_to=date_to,
            certificate_type=certificate_type,
            partners=partners or None,
        )
        if not certificate_data["partners"]:
            raise UserError(
                _("No withholding entries were found for the selected criteria.")
            )
        certificates = [
            self._prepare_certificate(company, partner_data, wizard.fiscal_year)
            for partner_data in certificate_data["partners"]
        ]
        period_label = self._get_period_label(
            wizard, date_from, date_to, period_type, bimester
        )
        for certificate in certificates:
            certificate.update(
                {
                    "certificate_type": certificate_type,
                    "certificate_title": (
                        _("CERTIFICADO DE RETENCIÓN EN LA FUENTE")
                        if certificate_type == "rte_fte"
                        else (
                            _("CERTIFICADO DE RETENCIÓN DE IVA")
                            if certificate_type == "rte_iva"
                            else _("CERTIFICADO DE RETENCIÓN DE ICA")
                        )
                    ),
                    "certificate_description": (
                        _(
                            "La compañía certifica que durante el periodo indicado "
                            "practicó las siguientes retenciones en la fuente al "
                            "beneficiario identificado en este documento."
                        )
                        if certificate_type == "rte_fte"
                        else (
                            _(
                                "La compañía certifica que durante el periodo indicado "
                                "practicó las siguientes retenciones de IVA al "
                                "beneficiario identificado en este documento."
                            )
                            if certificate_type == "rte_iva"
                            else _(
                                "La compañía certifica que durante el periodo indicado "
                                "practicó las siguientes retenciones de ICA al "
                                "beneficiario identificado en este documento."
                            )
                        )
                    ),
                    "period_label": period_label,
                }
            )
        return {
            "doc_ids": wizard.ids,
            "doc_model": wizard._name,
            "docs": wizard,
            "company": company,
            "certificates": certificates,
            "certificate_type": certificate_type,
            "date_from": date_from,
            "date_to": date_to,
            "period_label": period_label,
        }
