# Copyright 2026 Juan Arcos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # Default Colombian chart accounts (simplified PUC) for the payroll rules.
    # Each rule is mapped only when the account exists in the company chart.
    # - 510500 Gastos de personal (expense)
    # - 237000 Retenciones y aportes de nómina (current liability)
    # - 250500 Salarios por pagar (current liability, partner = employee)
    # - 261000 Para obligaciones laborales (non current liability)
    L10N_CO_PAYROLL_ACCOUNT_DEFAULTS = {
        "salary_rule_basic": {"account_debit": "510500"},
        "salary_rule_extras": {"account_debit": "510500"},
        "salary_rule_commissions": {"account_debit": "510500"},
        "salary_rule_other_salary": {"account_debit": "510500"},
        "salary_rule_aux_transport": {"account_debit": "510500"},
        "salary_rule_health_employee": {"account_debit": "237000"},
        "salary_rule_pension_employee": {"account_debit": "237000"},
        "salary_rule_other_deductions": {"account_debit": "237000"},
        "salary_rule_net": {"account_credit": "250500"},
        "salary_rule_health_employer": {
            "account_debit": "510500",
            "account_credit": "237000",
        },
        "salary_rule_pension_employer": {
            "account_debit": "510500",
            "account_credit": "237000",
        },
        "salary_rule_arl": {
            "account_debit": "510500",
            "account_credit": "237000",
        },
        "salary_rule_parafiscal_ccf": {
            "account_debit": "510500",
            "account_credit": "237000",
        },
        "salary_rule_parafiscal_sena": {
            "account_debit": "510500",
            "account_credit": "237000",
        },
        "salary_rule_parafiscal_icbf": {
            "account_debit": "510500",
            "account_credit": "237000",
        },
        "salary_rule_provision_prima": {
            "account_debit": "510500",
            "account_credit": "261000",
        },
        "salary_rule_provision_cesantias": {
            "account_debit": "510500",
            "account_credit": "261000",
        },
        "salary_rule_provision_intereses": {
            "account_debit": "510500",
            "account_credit": "261000",
        },
        "salary_rule_provision_vacaciones": {
            "account_debit": "510500",
            "account_credit": "261000",
        },
    }

    l10n_co_minimum_wage = fields.Monetary(
        string="Salario Mínimo Legal Mensual Vigente (SMMLV)",
        currency_field="currency_id",
        help="SMMLV vigente (año 2026: 1.750.905 COP). Se usa para el límite "
        "del auxilio de transporte y para la exención de parafiscales.",
    )
    l10n_co_transport_assistance = fields.Monetary(
        string="Auxilio de Transporte",
        currency_field="currency_id",
        help="Auxilio de transporte mensual vigente (año 2026: 249.095 COP). "
        "No constituye salario ni hace parte del IBC.",
    )
    l10n_co_max_salary_transport = fields.Monetary(
        string="Salario máximo con auxilio de transporte",
        currency_field="currency_id",
        compute="_compute_l10n_co_max_salary_transport",
        store=True,
        help="Salario máximo para tener derecho al auxilio de transporte "
        "(2 SMMLV).",
    )
    l10n_co_exempt_health_parafiscal = fields.Boolean(
        string="Exonerado de aportes de salud y parafiscales (SENA/ICBF)",
        help="Marque esta casilla cuando TODOS los trabajadores de la empresa "
        "ganen menos de 10 SMMLV. En ese caso (art. 114-1 del Estatuto "
        "Tributario, Ley 1819 de 2016) no se aporta el 8,5% de salud, ni el "
        "SENA (2%) ni el ICBF (3%). La Caja de Compensación (4%) y la pensión "
        "(12%) del empleador se mantienen.",
    )
    l10n_co_eps_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="EPS por defecto",
        help="Entidad Promotora de Salud por defecto para los trabajadores de "
        "la compañía. Se usa cuando el empleado no tiene asignada una EPS.",
    )
    l10n_co_afp_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Fondo de Pensiones (AFP) por defecto",
        help="Administradora del Fondo de Pensiones por defecto para los "
        "trabajadores de la compañía. Se usa cuando el empleado no tiene "
        "asignado un fondo.",
    )
    l10n_co_arl_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="ARL",
        help="Administradora de Riesgos Laborales de la compañía. Tercero "
        "acreedor de la cuenta por pagar de riesgos laborales (237000).",
    )
    l10n_co_ccf_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Caja de Compensación Familiar",
        help="Caja de Compensación a la que pertenece la compañía. Tercero "
        "acreedor de la cuenta por pagar del aporte parafiscal (237000).",
    )
    l10n_co_sena_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="SENA",
        help="Servicio Nacional de Aprendizaje. Tercero acreedor de la cuenta "
        "por pagar del aporte parafiscal SENA (237000).",
    )
    l10n_co_icbf_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="ICBF",
        help="Instituto Colombiano de Bienestar Familiar. Tercero acreedor de "
        "la cuenta por pagar del aporte parafiscal ICBF (237000).",
    )
    l10n_co_health_employee_percentage = fields.Float(
        string="% Salud (trabajador)",
        digits="Payroll Rate",
        default=4.0,
        help="Aporte del trabajador a salud sobre el IBC.",
    )
    l10n_co_health_employer_percentage = fields.Float(
        string="% Salud (empleador)",
        digits="Payroll Rate",
        default=8.5,
        help="Aporte del empleador a salud sobre el IBC (se exonera si "
        "l10n_co_exempt_health_parafiscal está marcado).",
    )
    l10n_co_pension_employee_percentage = fields.Float(
        string="% Pensión (trabajador)",
        digits="Payroll Rate",
        default=4.0,
        help="Aporte del trabajador a pensión sobre el IBC.",
    )
    l10n_co_pension_employer_percentage = fields.Float(
        string="% Pensión (empleador)",
        digits="Payroll Rate",
        default=12.0,
        help="Aporte del empleador a pensión sobre el IBC.",
    )
    l10n_co_parafiscal_ccf_percentage = fields.Float(
        string="% Caja de Compensación Familiar",
        digits="Payroll Rate",
        default=4.0,
        help="Aporte parafiscal a la Caja de Compensación Familiar sobre el "
        "IBC. Siempre se causa, sin importar la exención del art. 114-1 ET.",
    )
    l10n_co_parafiscal_sena_percentage = fields.Float(
        string="% SENA",
        digits="Payroll Rate",
        default=2.0,
        help="Aporte parafiscal SENA sobre el IBC (se exonera si "
        "l10n_co_exempt_health_parafiscal está marcado).",
    )
    l10n_co_parafiscal_icbf_percentage = fields.Float(
        string="% ICBF",
        digits="Payroll Rate",
        default=3.0,
        help="Aporte parafiscal ICBF sobre el IBC (se exonera si "
        "l10n_co_exempt_health_parafiscal está marcado).",
    )
    l10n_co_provision_prima_percentage = fields.Float(
        string="% Provisión prima de servicios",
        digits="Payroll Rate",
        default=8.33,
        help="Provisión mensual de la prima de servicios (20 días → 8,33% de "
        "la base = salario + auxilio de transporte).",
    )
    l10n_co_provision_cesantias_percentage = fields.Float(
        string="% Provisión cesantías",
        digits="Payroll Rate",
        default=8.33,
        help="Provisión mensual de cesantías (30 días → 8,33% de la base = "
        "salario + auxilio de transporte).",
    )
    l10n_co_provision_interests_percentage = fields.Float(
        string="% Provisión intereses a las cesantías",
        digits="Payroll Rate",
        default=1.0,
        help="Provisión mensual de intereses a las cesantías "
        "(12% anual sobre las cesantías → 1% mensual).",
    )
    l10n_co_provision_vacaciones_percentage = fields.Float(
        string="% Provisión vacaciones",
        digits="Payroll Rate",
        default=4.17,
        help="Provisión mensual de vacaciones (15 días → 4,17% del salario, "
        "sin auxilio de transporte).",
    )

    def _compute_l10n_co_max_salary_transport(self):
        for company in self:
            company.l10n_co_max_salary_transport = (
                company.l10n_co_minimum_wage * 2
            )

    def write(self, values):
        res = super().write(values)
        if any(
            field in values
            for field in (
                "l10n_co_arl_partner_id",
                "l10n_co_ccf_partner_id",
                "l10n_co_sena_partner_id",
                "l10n_co_icbf_partner_id",
                "l10n_co_eps_partner_id",
                "l10n_co_afp_partner_id",
            )
        ):
            self._l10n_co_sync_third_party_registers()
        return res

    def _l10n_co_set_payroll_defaults(self, values=None):
        """Set the legal 2026 values if the fields are empty.

        Used by the post install hook so existing companies get the current
        legal values without overwriting user changes.
        """
        defaults = {
            "l10n_co_minimum_wage": 1750905.0,
            "l10n_co_transport_assistance": 249095.0,
        }
        defaults.update(values or {})
        for company in self:
            vals = {}
            for field, value in defaults.items():
                if not company[field]:
                    vals[field] = value
            if vals:
                company.write(vals)
        self._compute_l10n_co_max_salary_transport()
        self._l10n_co_sync_third_party_registers()

    def _l10n_co_sync_third_party_registers(self):
        """Mirror the company third-party partners onto the contribution
        registers of the payroll contribution rules (ARL and parafiscales).

        EPS / AFP are per-employee, so they are not synced here. The payroll
        accounting override resolves the partner from the salary rule anyway;
        this keeps the register partner in sync for display and fallback.
        """
        IrModelData = self.env["ir.model.data"]
        model_registers = {
            "register_arl": "l10n_co_arl_partner_id",
            "register_ccf": "l10n_co_ccf_partner_id",
        }
        for xmlid, company_field in model_registers.items():
            register = self.env["hr.contribution.register"].browse(
                IrModelData._xmlid_to_res_id(f"l10n_co_hr_payroll.{xmlid}")
            )
            if not register:
                continue
            register.write(
                {
                    "partner_id": self[company_field].id
                    if self[company_field]
                    else False
                }
            )

    def _l10n_co_set_payroll_account_defaults(self):
        """Map the Colombian chart accounts onto every salary rule.

        The rule accounting fields are company dependent, so they are set per
        company looking up the account by its chart code. Companies without a
        chart loaded yet are skipped: the user can map the accounts manually
        in Payroll > Configuration > Salary Rules, or re-run this method.
        """
        Rule = self.env["hr.salary.rule"]
        model_data = self.env["ir.model.data"]
        account_codes = []
        for mapping in self.L10N_CO_PAYROLL_ACCOUNT_DEFAULTS.values():
            account_codes.extend(mapping.values())
        account_codes = list(dict.fromkeys(account_codes))
        for company in self:
            accounts = {
                account.code: account
                for account in self.env["account.account"].with_company(
                    company
                ).search(
                    [
                        ("company_ids", "in", [company.id]),
                        ("code", "in", account_codes),
                    ]
                )
            }
            if not accounts:
                continue
            for xmlid, mapping in self.L10N_CO_PAYROLL_ACCOUNT_DEFAULTS.items():
                rule = Rule.browse(
                    model_data._xmlid_to_res_id(f"l10n_co_hr_payroll.{xmlid}")
                )
                vals = {
                    field: account.id
                    for field, code in mapping.items()
                    if (account := accounts.get(code))
                }
                if vals:
                    rule.with_company(company).write(vals)