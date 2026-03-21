# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.fields import Domain


class CIIU(models.Model):
    _name = "l10n_co.ciiu"
    _description = "Clasificación de Actividades Económicas CIIU"
    _order = "code"

    @api.depends("code", "description")
    def _compute_display_name(self):
        for record in self:
            if "l10n_co_ciiu_shortname" in self.env.context:
                record.display_name = record.code or ""
            else:
                record.display_name = f"{record.code} - {record.description}"

    @api.model
    def _name_search(self, name, domain=None, operator="ilike", limit=None, order=None):
        domain = domain or []
        if name:
            domain = Domain.AND(
                [
                    ["|", ("code", operator, name), ("description", operator, name)],
                    domain,
                ]
            )
        return self._search(domain, limit=limit, order=order)

    code = fields.Char(string="Código", required=True, readonly=True)
    description = fields.Char(
        string="Descripción", required=True, readonly=True, translate=True
    )
    parent_id = fields.Many2one("l10n_co.ciiu", string="Padre", readonly=True)
    is_code = fields.Boolean(string="¿Es código?", readonly=True)
    active = fields.Boolean(string="Activo", default=True)
