# Copyright 2026 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from calendar import monthrange
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class WithholdingCertificateWizard(models.TransientModel):
    _name = "l10n_co.withholding.certificate.wizard"
    _description = "Colombian Withholding Certificate Wizard"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        domain=lambda self: [("id", "in", self.env.user.company_ids.ids)],
    )
    certificate_type = fields.Selection(
        selection=[
            ("rte_fte", "Retención en la Fuente"),
            ("rte_iva", "Retención de IVA"),
            ("rte_ica", "Retención ICA"),
        ],
        string="Certificate type",
        required=True,
        default="rte_fte",
    )
    fiscal_year = fields.Integer(
        string="Fiscal year",
        required=True,
        default=lambda self: date.today().year,
    )
    period_type = fields.Selection(
        selection=[
            ("annual", "Annual"),
            ("bimonthly", "Bimonthly"),
            ("custom", "Custom"),
        ],
        string="Period",
        required=True,
        default="annual",
    )
    bimester = fields.Selection(
        selection=[
            ("1", "Enero - Febrero"),
            ("2", "Marzo - Abril"),
            ("3", "Mayo - Junio"),
            ("4", "Julio - Agosto"),
            ("5", "Septiembre - Octubre"),
            ("6", "Noviembre - Diciembre"),
        ],
        string="Bimester",
    )
    date_from = fields.Date(string="From", readonly=False)
    date_to = fields.Date(string="To", readonly=False)
    partner_ids = fields.Many2many(
        "res.partner",
        string="Commercial partners",
        domain=[("parent_id", "=", False)],
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id", string="Currency", readonly=True
    )
    partner_count = fields.Integer(string="Partners", readonly=True)
    total_base_amount = fields.Monetary(
        string="Total base", currency_field="currency_id", readonly=True
    )
    total_withheld_amount = fields.Monetary(
        string="Total withheld", currency_field="currency_id", readonly=True
    )
    has_results = fields.Boolean(string="Has results", readonly=True)

    @api.onchange("certificate_type")
    def _onchange_certificate_type(self):
        if self.certificate_type == "rte_fte":
            if self.period_type == "bimonthly":
                self.period_type = "annual"
            self.bimester = False
        elif self.period_type == "annual":
            self.period_type = "bimonthly"
        self._clear_preview()
        self._onchange_period_configuration()

    @api.onchange("period_type", "fiscal_year", "bimester", "date_from", "date_to")
    def _onchange_period_configuration(self):
        self._clear_preview()
        if not self.fiscal_year or self.period_type == "custom":
            return
        try:
            date_from, date_to = self._get_period_dates()
        except ValidationError:
            return
        self.date_from = date_from
        self.date_to = date_to

    @api.onchange("company_id", "partner_ids")
    def _onchange_filter(self):
        self._clear_preview()

    def _clear_preview(self):
        self.partner_count = 0
        self.total_base_amount = 0.0
        self.total_withheld_amount = 0.0
        self.has_results = False

    def _get_period_dates(self):
        self.ensure_one()
        if self.fiscal_year < 1:
            raise ValidationError(_("Fiscal year must be a positive year."))
        if self.period_type == "annual":
            return date(self.fiscal_year, 1, 1), date(self.fiscal_year, 12, 31)
        if self.period_type == "bimonthly":
            if not self.bimester:
                raise ValidationError(_("Select a bimester for this period."))
            bimester = int(self.bimester)
            first_month = 1 + (bimester - 1) * 2
            last_month = first_month + 1
            last_day = monthrange(self.fiscal_year, last_month)[1]
            return (
                date(self.fiscal_year, first_month, 1),
                date(self.fiscal_year, last_month, last_day),
            )
        if self.period_type == "custom":
            if not self.date_from or not self.date_to:
                raise ValidationError(
                    _("Select both start and end dates for a custom period.")
                )
            if self.date_from > self.date_to:
                raise ValidationError(
                    _("The start date must be before or equal to the end date.")
                )
            return self.date_from, self.date_to
        raise ValidationError(_("Select a valid period."))

    def _validate_configuration(self):
        self.ensure_one()
        if self.certificate_type == "rte_fte" and self.period_type == "bimonthly":
            raise ValidationError(
                _("ReteFuente supports annual or custom periods only.")
            )
        if self.certificate_type in ("rte_iva", "rte_ica") and self.period_type == "annual":
            raise ValidationError(
                _("This certificate type supports bimonthly or custom periods only.")
            )
        return self._get_period_dates()

    def _get_normalized_partners(self):
        self.ensure_one()
        if not self.partner_ids:
            return None
        commercial_partners = self.partner_ids.mapped("commercial_partner_id")
        return commercial_partners.sorted(key=lambda partner: partner.id)

    def action_preview(self):
        self.ensure_one()
        date_from, date_to = self._validate_configuration()
        partners = self._get_normalized_partners()
        engine = self.env["l10n_co.withholding.certificate.engine"]
        data = engine.get_certificate_data(
            company=self.company_id,
            date_from=date_from,
            date_to=date_to,
            certificate_type=self.certificate_type,
            partners=partners,
        )
        partner_data = data["partners"]
        if not partner_data:
            raise UserError(
                _("No withholding entries were found for the selected criteria.")
            )
        self.write(
            {
                "date_from": date_from,
                "date_to": date_to,
                "partner_count": len(partner_data),
                "total_base_amount": sum(
                    partner["base_amount"] for partner in partner_data
                ),
                "total_withheld_amount": sum(
                    partner["withheld_amount"] for partner in partner_data
                ),
                "has_results": True,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Withholding Certificate"),
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }

    def action_print_certificate(self):
        self.ensure_one()
        report_map = {
            "rte_fte": "action_report_withholding_certificate",
            "rte_iva": "action_report_withholding_iva_certificate",
            "rte_ica": "action_report_withholding_ica_certificate",
        }
        report_xmlid = report_map.get(self.certificate_type)
        if not report_xmlid:
            raise UserError(
                _(
                    "PDF certificates are currently available for ReteFuente, "
                    "ReteIVA, and ReteICA."
                )
            )
        date_from, date_to = self._validate_configuration()
        partners = self._get_normalized_partners()
        engine = self.env["l10n_co.withholding.certificate.engine"]
        data = engine.get_certificate_data(
            company=self.company_id,
            date_from=date_from,
            date_to=date_to,
            certificate_type=self.certificate_type,
            partners=partners,
        )
        if not data["partners"]:
            raise UserError(
                _("No withholding entries were found for the selected criteria.")
            )
        return self.env.ref(
            "l10n_co_withholding_certificate.%s" % report_xmlid
        ).report_action(
            self,
            data={
                "company_id": self.company_id.id,
                "certificate_type": self.certificate_type,
                "date_from": fields.Date.to_string(date_from),
                "date_to": fields.Date.to_string(date_to),
                "partner_ids": partners.ids if partners else [],
                "fiscal_year": self.fiscal_year,
                "period_type": self.period_type,
                "bimester": self.bimester,
            },
            config=False,
        )
