# Copyright 2026 Juan Arcos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Colombia - Nómina",
    "summary": "Liquidación de nómina para Colombia: salario, seguridad social, "
    "aportes parafiscales y prestaciones sociales",
    "author": "Juan Arcos, Odoo Community Association (OCA)",
    "maintainers": ["juanparmer"],
    "website": "https://github.com/OCA/l10n-colombia",
    "license": "AGPL-3",
    "category": "Human Resources/Payroll",
    "version": "18.0.1.0.0",
    "depends": [
        "payroll_account",
        "payroll",
        "hr_contract",
        "hr",
        "mail",
        "connector_facturapi_ne",
    ],
    "data": [
        "data/hr_salary_rule_data.xml",
        "data/res_partner_data.xml",
        "views/res_config_settings_views.xml",
        "views/hr_employee_views.xml",
        "views/hr_contract_views.xml",
        "views/hr_payslip_views.xml",
        "report/report.xml",
    ],
    "external_dependencies": {
        "python": [],
    },
    "assets": {},
    "application": False,
    "installable": True,
    "auto_install": False,
    "post_init_hook": "post_init_hook",
}