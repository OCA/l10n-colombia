# Copyright 2026 Juan Arcos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_co_minimum_wage = fields.Monetary(
        related="company_id.l10n_co_minimum_wage",
        readonly=False,
    )
    l10n_co_transport_assistance = fields.Monetary(
        related="company_id.l10n_co_transport_assistance",
        readonly=False,
    )
    l10n_co_exempt_health_parafiscal = fields.Boolean(
        related="company_id.l10n_co_exempt_health_parafiscal",
        readonly=False,
    )
    l10n_co_eps_partner_id = fields.Many2one(
        related="company_id.l10n_co_eps_partner_id",
        readonly=False,
    )
    l10n_co_afp_partner_id = fields.Many2one(
        related="company_id.l10n_co_afp_partner_id",
        readonly=False,
    )
    l10n_co_arl_partner_id = fields.Many2one(
        related="company_id.l10n_co_arl_partner_id",
        readonly=False,
    )
    l10n_co_ccf_partner_id = fields.Many2one(
        related="company_id.l10n_co_ccf_partner_id",
        readonly=False,
    )
    l10n_co_sena_partner_id = fields.Many2one(
        related="company_id.l10n_co_sena_partner_id",
        readonly=False,
    )
    l10n_co_icbf_partner_id = fields.Many2one(
        related="company_id.l10n_co_icbf_partner_id",
        readonly=False,
    )
    l10n_co_health_employee_percentage = fields.Float(
        related="company_id.l10n_co_health_employee_percentage",
        readonly=False,
    )
    l10n_co_health_employer_percentage = fields.Float(
        related="company_id.l10n_co_health_employer_percentage",
        readonly=False,
    )
    l10n_co_pension_employee_percentage = fields.Float(
        related="company_id.l10n_co_pension_employee_percentage",
        readonly=False,
    )
    l10n_co_pension_employer_percentage = fields.Float(
        related="company_id.l10n_co_pension_employer_percentage",
        readonly=False,
    )
    l10n_co_parafiscal_ccf_percentage = fields.Float(
        related="company_id.l10n_co_parafiscal_ccf_percentage",
        readonly=False,
    )
    l10n_co_parafiscal_sena_percentage = fields.Float(
        related="company_id.l10n_co_parafiscal_sena_percentage",
        readonly=False,
    )
    l10n_co_parafiscal_icbf_percentage = fields.Float(
        related="company_id.l10n_co_parafiscal_icbf_percentage",
        readonly=False,
    )
    l10n_co_provision_prima_percentage = fields.Float(
        related="company_id.l10n_co_provision_prima_percentage",
        readonly=False,
    )
    l10n_co_provision_cesantias_percentage = fields.Float(
        related="company_id.l10n_co_provision_cesantias_percentage",
        readonly=False,
    )
    l10n_co_provision_interests_percentage = fields.Float(
        related="company_id.l10n_co_provision_interests_percentage",
        readonly=False,
    )
    l10n_co_provision_vacaciones_percentage = fields.Float(
        related="company_id.l10n_co_provision_vacaciones_percentage",
        readonly=False,
    )