# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.osv import expression


class CIIU(models.Model):
    _name = "l10n_co.ciiu"
    _description = "Clasificación de Actividades Económicas CIIU"
    _order = "code"

    def name_get(self):
        result = []
        if "l10n_co_ciiu_shortname" in self.env.context:
            convert = self._fields["code"].convert_to_display_name
            for record in self:
                result.append((record.id, convert(record["code"], record)))
        else:
            for record in self:
                name = record.code + " - " + record.description
                result.append((record.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=80):
        args = args or []
        domain = ["|", ("code", operator, name), ("description", operator, name)]
        recs = self.search(expression.AND([domain, args]), limit=limit)
        ctx = dict(self.env.context)
        ctx.pop("l10n_co_ciiu_shortname", None)
        return recs.with_context(**ctx).name_get()

    code = fields.Char(string="Código", required=True, readonly=True)
    description = fields.Char(
        string="Descripción", required=True, readonly=True, translate=True
    )
    parent_id = fields.Many2one("l10n_co.ciiu", string="Padre", readonly=True)
    is_code = fields.Boolean(string="¿Es código?", readonly=True)
    active = fields.Boolean(string="Activo", default=True)
