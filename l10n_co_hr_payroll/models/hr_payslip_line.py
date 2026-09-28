# Copyright 2026 Juan Arcos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class HrPayslipLine(models.Model):
    _inherit = "hr.payslip.line"

    def _get_partner_id(self, credit_account):
        """Set the third-party partner on social security / parafiscal
        liabilities.

        Colombian payroll pays social security, pension and parafiscal
        contributions to external entities (EPS, AFP, ARL, compensation box,
        SENA, ICBF). Those liability lines (e.g. 237000) must carry the
        third-party partner provided by the entity, not the employee.

        The partner is resolved from the salary rule so health / pension lines
        use the employee EPS / AFP (falling back to the company default),
        while ARL / compensation box / SENA / ICBF use the company partner set
        in the Payroll Settings. Expense and net-payable lines are left to the
        standard behavior.
        """
        account = (
            self.salary_rule_id.account_credit
            if credit_account
            else self.salary_rule_id.account_debit
        )
        if (
            not account
            or account.account_type not in ("liability_payable", "liability_current")
        ):
            return super()._get_partner_id(credit_account)

        partner = self._l10n_co_third_party_partner()
        if partner:
            return partner.id
        return super()._get_partner_id(credit_account)

    def _l10n_co_third_party_partner(self):
        """Return the third-party partner for a social security / parafiscal
        rule, or an empty recordset when the rule is not a contribution line.
        """
        company = self.slip_id.company_id
        employee = self.slip_id.employee_id
        code = self.salary_rule_id.code
        partners = self.env["res.partner"]
        if code in ("HEALTH_EMP_DEDUCTION", "HEALTH_EMPLOYER"):
            partner = employee.l10n_co_eps or company.l10n_co_eps_partner_id
        elif code in ("PENSION_EMP_DEDUCTION", "PENSION_EMPLOYER"):
            partner = employee.l10n_co_afp or company.l10n_co_afp_partner_id
        elif code == "ARL":
            partner = company.l10n_co_arl_partner_id
        elif code == "PARAFISCAL_CCF":
            partner = company.l10n_co_ccf_partner_id
        elif code == "PARAFISCAL_SENA":
            partner = company.l10n_co_sena_partner_id
        elif code == "PARAFISCAL_ICBF":
            partner = company.l10n_co_icbf_partner_id
        else:
            return partners
        return partner or partners
