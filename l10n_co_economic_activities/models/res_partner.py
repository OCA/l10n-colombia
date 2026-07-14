# Copyright 2026 juparmer - Juan Arcos <juanparmer@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_co_economic_activity_id = fields.Many2one(
        comodel_name="l10n.co.economic.activity",
        string="Actividad Económica Principal",
        index=True,
        help="Actividad económica principal según CIIU Colombia",
    )
    l10n_co_secondary_activity_id = fields.Many2one(
        comodel_name="l10n.co.economic.activity",
        string="Actividad Económica Secundaria",
        index=True,
        help="Actividad económica secundaria según CIIU Colombia",
    )
    l10n_co_other_activity_ids = fields.Many2many(
        comodel_name="l10n.co.economic.activity",
        relation="res_partner_other_economic_activities_rel",
        column1="partner_id",
        column2="activity_id",
        string="Otras Actividades Económicas",
        help="Otras actividades económicas según CIIU Colombia",
    )
