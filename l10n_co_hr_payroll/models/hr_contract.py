# Copyright 2026 Juan Arcos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = "hr.contract"

    l10n_co_auxiliary_transport = fields.Boolean(
        string="Derecho a auxilio de transporte",
        default=True,
        help="El auxilio de transporte se causa si el trabajador devenga hasta "
        "2 SMMLV. No constituye salario ni hace parte del IBC.",
    )
    l10n_co_arl_risk_class = fields.Selection(
        [
            ("I", "Clase I"),
            ("II", "Clase II"),
            ("III", "Clase III"),
            ("IV", "Clase IV"),
            ("V", "Clase V"),
        ],
        string="Clase de riesgo ARL",
        help="Clase de riesgo del trabajador para el aporte de riesgos "
        "laborales (ARL).",
    )
    l10n_co_arl_rate = fields.Float(
        string="% ARL",
        digits="Payroll Rate",
        compute="_compute_l10n_co_arl_rate",
        store=True,
        readonly=True,
        help="Tarifa de riesgos laborales (ARL) según la clase de riesgo: "
        "I=0,522%, II=1,044%, III=2,436%, IV=4,350%, V=6,960%.",
    )

    @api.depends("l10n_co_arl_risk_class")
    def _compute_l10n_co_arl_rate(self):
        arl_rates = {
            "I": 0.522,
            "II": 1.044,
            "III": 2.436,
            "IV": 4.350,
            "V": 6.960,
        }
        for contract in self:
            contract.l10n_co_arl_rate = arl_rates.get(
                contract.l10n_co_arl_risk_class
            ) or 0.0