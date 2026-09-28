# Copyright 2026 Juan Arcos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    # Category codes owned by this localization (see data/hr_salary_rule_data.xml)
    L10N_CO_CATEGORY_IBC = ("BASIC", "SALARIAL")
    L10N_CO_CATEGORY_DEVENGO = ("BASIC", "SALARIAL", "NO_SALARIAL")
    L10N_CO_CATEGORY_DEDUCTION = ("DEDUCTION",)
    L10N_CO_CATEGORY_NET = ("NET",)
    L10N_CO_CATEGORY_EMPLOYER_SS = ("EMPLOYER_SS",)
    L10N_CO_CATEGORY_PARAFISCAL = ("PARAFISCAL",)
    L10N_CO_CATEGORY_PROVISION = ("PROVISION",)

    currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        readonly=True,
    )
    l10n_co_ibc = fields.Monetary(
        string="IBC",
        currency_field="currency_id",
        compute="_compute_l10n_co_columns",
        help="Ingreso Base de Cotización: salario + otros devengados "
        "salariales (horas extras, comisiones, etc.). No incluye el auxilio "
        "de transporte.",
    )
    l10n_co_total_devengado = fields.Monetary(
        string="Total Devengado",
        currency_field="currency_id",
        compute="_compute_l10n_co_columns",
    )
    l10n_co_total_deducciones = fields.Monetary(
        string="Total Deducciones",
        currency_field="currency_id",
        compute="_compute_l10n_co_columns",
    )
    l10n_co_neto = fields.Monetary(
        string="Neto a Pagar",
        currency_field="currency_id",
        compute="_compute_l10n_co_columns",
    )
    l10n_co_employer_cost = fields.Monetary(
        string="Costo Total para el Empleador",
        currency_field="currency_id",
        compute="_compute_l10n_co_columns",
        help="Total que representa la nómina para el empleador: neto a pagar "
        "más aportes a la seguridad social, parafiscales y provisiones de "
        "prestaciones sociales.",
    )

    def _l10n_co_category_total(self, codes):
        self.ensure_one()
        return sum(
            self.line_ids.filtered(
                lambda line: line.category_id.code in codes
            ).mapped("total")
        )

    @api.depends(
        "line_ids",
        "line_ids.total",
        "line_ids.category_id",
        "line_ids.category_id.code",
    )
    def _compute_l10n_co_columns(self):
        for slip in self:
            slip.l10n_co_ibc = slip._l10n_co_category_total(
                self.L10N_CO_CATEGORY_IBC
            )
            slip.l10n_co_total_devengado = slip._l10n_co_category_total(
                self.L10N_CO_CATEGORY_DEVENGO
            )
            slip.l10n_co_total_deducciones = -(
                slip._l10n_co_category_total(self.L10N_CO_CATEGORY_DEDUCTION)
            )
            slip.l10n_co_neto = slip._l10n_co_category_total(
                self.L10N_CO_CATEGORY_NET
            )
            slip.l10n_co_employer_cost = slip._l10n_co_category_total(
                self.L10N_CO_CATEGORY_NET
                + self.L10N_CO_CATEGORY_EMPLOYER_SS
                + self.L10N_CO_CATEGORY_PARAFISCAL
                + self.L10N_CO_CATEGORY_PROVISION
            )