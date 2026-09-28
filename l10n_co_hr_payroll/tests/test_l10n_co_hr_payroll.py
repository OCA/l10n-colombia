# Copyright 2026 Juan Arcos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestL10nCoHrPayroll(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.structure = cls.env.ref(
            "l10n_co_hr_payroll.structure_colombia_monthly"
        )
        cls.calendar = cls.env.ref("resource.resource_calendar_std")
        cls.payroll_journal = cls.env["account.journal"].create(
            {
                "name": "Diario Nómina Test",
                "code": "NOM",
                "type": "general",
                "company_id": cls.company.id,
            }
        )

    def _create_payslip(self, wage, arl_class="I", aux_transport=True):
        employee = self.env["hr.employee"].create(
            {
                "name": "Trabajador CO",
                "company_id": self.company.id,
            }
        )
        contract = self.env["hr.contract"].create(
            {
                "name": "Contrato CO",
                "employee_id": employee.id,
                "company_id": self.company.id,
                "wage": wage,
                "date_start": "2026-01-01",
                "state": "open",
                "struct_id": self.structure.id,
                "resource_calendar_id": self.calendar.id,
                "l10n_co_auxiliary_transport": aux_transport,
                "l10n_co_arl_risk_class": arl_class,
                "journal_id": self.payroll_journal.id,
            }
        )
        payslip = self.env["hr.payslip"].create(
            {
                "name": "Nómina Test CO",
                "employee_id": employee.id,
                "contract_id": contract.id,
                "struct_id": self.structure.id,
                "date_from": "2026-01-01",
                "date_to": "2026-01-31",
                "company_id": self.company.id,
            }
        )
        return employee, contract, payslip

    def _line_total(self, payslip, code):
        line = payslip.line_ids.filtered(lambda line: line.code == code)
        return line.total if line else 0.0

    def _category_total(self, payslip, codes):
        return sum(
            payslip.line_ids.filtered(
                lambda line: line.category_id.code in codes
            ).mapped("total")
        )

    def test_post_init_sets_2026_legal_values(self):
        self.assertEqual(self.company.l10n_co_minimum_wage, 1750905.0)
        self.assertEqual(self.company.l10n_co_transport_assistance, 249095.0)
        self.assertEqual(self.company.l10n_co_max_salary_transport, 3501810.0)

    def test_salary_structure_contents(self):
        self.assertTrue(self.structure.rule_ids)
        codes = {rule.code for rule in self.structure.rule_ids}
        self.assertEqual(
            codes,
            {
                "BASIC",
                "EXTRAS",
                "COMMISSIONS",
                "OTHER_SALARY",
                "AUX_TRANSPORT",
                "HEALTH_EMP_DEDUCTION",
                "PENSION_EMP_DEDUCTION",
                "OTHER_DEDUCTIONS",
                "NET",
                "HEALTH_EMPLOYER",
                "PENSION_EMPLOYER",
                "ARL",
                "PARAFISCAL_CCF",
                "PARAFISCAL_SENA",
                "PARAFISCAL_ICBF",
                "PROVISION_PRIMA",
                "PROVISION_CESANTIAS",
                "PROVISION_INTERESES",
                "PROVISION_VACACIONES",
            },
        )

    def test_payslip_smmlv_worker(self):
        company = self.company
        wage = company.l10n_co_minimum_wage
        aux = company.l10n_co_transport_assistance
        _, _, payslip = self._create_payslip(wage, arl_class="I")
        payslip.compute_sheet()

        ibc = wage
        health_emp = ibc * company.l10n_co_health_employee_percentage / 100.0
        pension_emp = ibc * company.l10n_co_pension_employee_percentage / 100.0
        health_employer = (
            ibc * company.l10n_co_health_employer_percentage / 100.0
        )
        pension_employer = ibc * company.l10n_co_pension_employer_percentage / 100.0
        arl = ibc * 0.522 / 100.0
        ccf = ibc * company.l10n_co_parafiscal_ccf_percentage / 100.0
        sena = ibc * company.l10n_co_parafiscal_sena_percentage / 100.0
        icbf = ibc * company.l10n_co_parafiscal_icbf_percentage / 100.0
        provision_base = wage + aux
        prima = (
            provision_base * company.l10n_co_provision_prima_percentage / 100.0
        )
        cesantias = (
            provision_base * company.l10n_co_provision_cesantias_percentage / 100.0
        )
        intereses = (
            cesantias * company.l10n_co_provision_interests_percentage / 100.0
        )
        vacaciones = (
            wage * company.l10n_co_provision_vacaciones_percentage / 100.0
        )
        net = wage + aux - health_emp - pension_emp

        self.assertAlmostEqual(self._line_total(payslip, "AUX_TRANSPORT"), aux, delta=0.01)
        self.assertAlmostEqual(self._line_total(payslip, "HEALTH_EMP_DEDUCTION"), -health_emp, delta=0.01)
        self.assertAlmostEqual(self._line_total(payslip, "PENSION_EMP_DEDUCTION"), -pension_emp, delta=0.01)
        self.assertAlmostEqual(self._line_total(payslip, "HEALTH_EMPLOYER"), health_employer, delta=0.01)
        self.assertAlmostEqual(self._line_total(payslip, "PENSION_EMPLOYER"), pension_employer, delta=0.01)
        self.assertAlmostEqual(self._line_total(payslip, "ARL"), arl, delta=0.01)
        self.assertAlmostEqual(self._line_total(payslip, "PARAFISCAL_CCF"), ccf, delta=0.01)
        self.assertAlmostEqual(self._line_total(payslip, "PARAFISCAL_SENA"), sena, delta=0.01)
        self.assertAlmostEqual(self._line_total(payslip, "PARAFISCAL_ICBF"), icbf, delta=0.01)
        self.assertAlmostEqual(self._line_total(payslip, "PROVISION_PRIMA"), prima, delta=0.01)
        self.assertAlmostEqual(self._line_total(payslip, "PROVISION_CESANTIAS"), cesantias, delta=0.01)
        self.assertAlmostEqual(self._line_total(payslip, "PROVISION_INTERESES"), intereses, delta=0.01)
        self.assertAlmostEqual(self._line_total(payslip, "PROVISION_VACACIONES"), vacaciones, delta=0.01)
        self.assertAlmostEqual(self._line_total(payslip, "NET"), net, delta=0.01)

        self.assertAlmostEqual(payslip.l10n_co_ibc, ibc, delta=0.01)
        self.assertAlmostEqual(
            payslip.l10n_co_total_devengado, wage + aux, delta=0.01
        )
        self.assertAlmostEqual(
            payslip.l10n_co_total_deducciones,
            health_emp + pension_emp,
            delta=0.01,
        )
        self.assertAlmostEqual(payslip.l10n_co_neto, net, delta=0.01)
        self.assertAlmostEqual(
            payslip.l10n_co_employer_cost,
            (
                net
                + health_employer
                + pension_employer
                + arl
                + ccf
                + sena
                + icbf
                + prima
                + cesantias
                + intereses
                + vacaciones
            ),
            delta=0.01,
        )

    def test_aux_transport_not_applied_high_salary(self):
        company = self.company
        wage = 4000000.0
        _, _, payslip = self._create_payslip(wage)
        payslip.compute_sheet()

        self.assertFalse(payslip.line_ids.filtered(lambda l: l.code == "AUX_TRANSPORT"))
        ibc = wage
        health_emp = ibc * company.l10n_co_health_employee_percentage / 100.0
        pension_emp = ibc * company.l10n_co_pension_employee_percentage / 100.0
        net = wage - health_emp - pension_emp
        self.assertAlmostEqual(self._line_total(payslip, "NET"), net, delta=0.01)

    def test_parafiscal_exemption(self):
        company = self.company
        wage = company.l10n_co_minimum_wage
        aux = company.l10n_co_transport_assistance
        self.company.l10n_co_exempt_health_parafiscal = True
        _, _, payslip = self._create_payslip(wage)
        payslip.compute_sheet()

        for code in ("HEALTH_EMPLOYER", "PARAFISCAL_SENA", "PARAFISCAL_ICBF"):
            self.assertFalse(
                payslip.line_ids.filtered(lambda line: line.code == code),
                "La regla %s no debe existir con exoneración activa" % code,
            )
        # Las reglas no exoneradas siguen presentes
        for code in ("PARAFISCAL_CCF", "PENSION_EMPLOYER", "ARL"):
            self.assertTrue(
                payslip.line_ids.filtered(lambda line: line.code == code),
                "La regla %s debe existir aun con exoneración activa" % code,
            )
        # El neto del trabajador no cambia con la exoneración
        health_emp = wage * company.l10n_co_health_employee_percentage / 100.0
        pension_emp = wage * company.l10n_co_pension_employee_percentage / 100.0
        net = wage + aux - health_emp - pension_emp
        self.assertAlmostEqual(self._line_total(payslip, "NET"), net, delta=0.01)

    def test_arl_rate_by_risk_class(self):
        company = self.company
        wage = company.l10n_co_minimum_wage
        _, contract, payslip = self._create_payslip(wage, arl_class="V")
        self.assertEqual(contract.l10n_co_arl_rate, 6.960)
        payslip.compute_sheet()
        self.assertAlmostEqual(
            self._line_total(payslip, "ARL"),
            wage * 6.960 / 100.0,
            delta=0.01,
        )

    def test_inputs_affect_ibc(self):
        company = self.company
        wage = company.l10n_co_minimum_wage
        extras = 100000.0
        _, contract, payslip = self._create_payslip(wage)
        self.env["hr.payslip.input"].create(
            {
                "payslip_id": payslip.id,
                "contract_id": contract.id,
                "name": "Horas Extras y Recargos",
                "code": "EXTRAS",
                "amount": extras,
            }
        )
        payslip.compute_sheet()

        self.assertEqual(round(self._line_total(payslip, "EXTRAS"), 2), extras)
        ibc = wage + extras
        self.assertEqual(round(payslip.l10n_co_ibc, 2), round(ibc, 2))
        # El neto sube con las extras menos los aportes del trabajador sobre ellas
        health_emp = ibc * company.l10n_co_health_employee_percentage / 100.0
        pension_emp = ibc * company.l10n_co_pension_employee_percentage / 100.0
        net = wage + extras + company.l10n_co_transport_assistance - health_emp - pension_emp
        self.assertAlmostEqual(self._line_total(payslip, "NET"), net, delta=0.01)

    def test_accounting_entries(self):
        company = self.company
        wage = company.l10n_co_minimum_wage
        aux = company.l10n_co_transport_assistance
        eps_partner = self.env["res.partner"].create({"name": "EPS Test"})
        afp_partner = self.env["res.partner"].create(
            {"name": "AFP Test"}
        )
        arl_partner = self.env["res.partner"].create({"name": "ARL Test"})
        ccf_partner = self.env["res.partner"].create({"name": "CCF Test"})
        sena_partner = self.env.ref("l10n_co_hr_payroll.res_partner_sena")
        icbf_partner = self.env.ref("l10n_co_hr_payroll.res_partner_icbf")
        company.write(
            {
                "l10n_co_eps_partner_id": eps_partner.id,
                "l10n_co_afp_partner_id": afp_partner.id,
                "l10n_co_arl_partner_id": arl_partner.id,
                "l10n_co_ccf_partner_id": ccf_partner.id,
                "l10n_co_sena_partner_id": sena_partner.id,
                "l10n_co_icbf_partner_id": icbf_partner.id,
            }
        )
        _, _, payslip = self._create_payslip(wage, arl_class="I")
        payslip.compute_sheet()
        payslip.action_payslip_done()

        move = payslip.move_id
        self.assertTrue(move, "La nómina debe generar un asiento contable")
        self.assertTrue(move.line_ids)
        debit = sum(move.line_ids.mapped("debit"))
        credit = sum(move.line_ids.mapped("credit"))
        self.assertAlmostEqual(debit, credit, places=2)
        self.assertGreater(debit, 0.0)

        line_accounts = {
            line.account_id.code: line for line in move.line_ids
        }
        net = self._line_total(payslip, "NET")
        self.assertAlmostEqual(
            line_accounts["250500"].credit, net, places=2,
        )
        self.assertGreater(sum(move.line_ids.filtered(
            lambda line: line.account_id.code == "510500"
        ).mapped("debit")), 0.0)

        # Aporte de salud del trabajador: crédito 237000 con partner de la EPS
        # (default de compañía, ya que el empleado no tiene EPS asignada)
        health_emp = round(
            wage * company.l10n_co_health_employee_percentage / 100.0, 2
        )
        eps_lines = move.line_ids.filtered(
            lambda line: line.account_id.code == "237000"
            and line.credit
            and round(line.credit, 2) == health_emp
            and line.partner_id == eps_partner
        )
        self.assertTrue(eps_lines, "Falta el crédito de salud con partner EPS")

        # Provisiones: crédito 261000 (obligaciones laborales)
        self.assertTrue(
            move.line_ids.filtered(
                lambda line: line.account_id.code == "261000" and line.credit
            )
        )

        # El neto a pagar no lleva el partner del register de terceros
        self.assertNotEqual(
            line_accounts["250500"].partner_id, eps_partner,
        )

        # Cada aporte a terceros usa el partner de la entidad correspondiente.
        # Se verifica por partner porque algunos montos coinciden (salud del
        # trabajador y CCF son ambos 4% del IBC).
        third_party_partners = set(
            move.line_ids.filtered(
                lambda line: line.account_id.code == "237000"
                and line.credit
                and line.partner_id
            ).mapped("partner_id")
        )
        for expected in (
            eps_partner,
            afp_partner,
            arl_partner,
            ccf_partner,
            sena_partner,
            icbf_partner,
        ):
            self.assertIn(
                expected,
                third_party_partners,
                "Falta el crédito 237000 al tercero %s" % expected.name,
            )

        # Y los montos correctos van a los terceros correctos. Solo se validan
        # los montos únicos por entidad (ARL, SENA e ICBF); el 4% de salud del
        # trabajador, pensión del trabajador y CCF coinciden y se verifican
        # arriba por presencia del partner.
        net_wage = wage
        arl_amount = round(net_wage * 0.522 / 100.0, 2)
        sena_amount = round(
            net_wage * company.l10n_co_parafiscal_sena_percentage / 100.0, 2
        )
        icbf_amount = round(
            net_wage * company.l10n_co_parafiscal_icbf_percentage / 100.0, 2
        )
        partners_by_amount = {
            round(line.credit, 2): line.partner_id
            for line in move.line_ids.filtered(
                lambda line: line.account_id.code == "237000" and line.credit
            )
        }
        self.assertEqual(partners_by_amount[arl_amount], arl_partner)
        self.assertEqual(partners_by_amount[sena_amount], sena_partner)
        self.assertEqual(partners_by_amount[icbf_amount], icbf_partner)
