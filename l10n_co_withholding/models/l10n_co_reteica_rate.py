# Copyright 2026 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class L10nCoReteicaRate(models.Model):
    _name = "l10n.co.reteica.rate"
    _description = "Tarifa ReteICA por Ciudad y Actividad Económica"
    _order = "city_id, economic_activity_id"

    city_id = fields.Many2one(
        comodel_name="res.city",
        string="Ciudad",
        required=True,
        help="Ciudad/municipio para la cual aplica esta tarifa de ReteICA.",
    )
    economic_activity_id = fields.Many2one(
        comodel_name="l10n.co.economic.activity",
        string="Actividad Económica",
        required=True,
        help="Actividad económica CIIU para la cual aplica esta tarifa de ReteICA.",
    )
    rate = fields.Float(
        string="Tarifa (%)",
        required=True,
        digits=(6, 4),
        help="Porcentaje de retención de ReteICA.",
    )
    min_base_services_uvt = fields.Float(
        string="Base Mínima Servicios (UVT)",
        digits=(6, 2),
        default=4.0,
        help="Base mínima en UVT para aplicar ReteICA en servicios.",
    )
    min_base_purchases_uvt = fields.Float(
        string="Base Mínima Compras (UVT)",
        digits=(6, 2),
        default=27.0,
        help="Base mínima en UVT para aplicar ReteICA en compras.",
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "unique_city_activity",
            "unique(city_id, economic_activity_id)",
            "Ya existe una tarifa para esta ciudad y actividad económica.",
        ),
    ]

    @api.model
    def get_rate_for_partner(self, partner):
        """Get ReteICA rate for partner based on city and activity."""
        if not partner or not partner.city_id:
            return self.browse()

        city = partner.city_id
        activity = partner.l10n_co_economic_activity_id

        if not activity:
            return self.browse()

        rate = self.search(
            [
                ("city_id", "=", city.id),
                ("economic_activity_id", "=", activity.id),
            ],
            limit=1,
        )

        if not rate:
            rate = self.search(
                [
                    ("city_id", "=", city.id),
                    ("economic_activity_id.code", "=like", f"{activity.code[:2]}%"),
                ],
                limit=1,
            )

        if not rate:
            rate = self.search(
                [
                    ("city_id", "=", city.id),
                    ("economic_activity_id.code", "=", "0000"),
                ],
                limit=1,
            )

        return rate
