# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _get_l10n_co_dian_self_params(self):
        """Return required fiscal params tuple for backwards compatibility."""
        self.ensure_one()
        partner = self.commercial_partner_id
        is_foreign = partner.country_id.code != "CO"

        if is_foreign:
            return (
                partner.country_id,
                partner.name,
                partner.l10n_latam_identification_type_id,
                partner.vat,
            )
        return (
            partner.country_id,
            partner.vat,
            partner.l10n_latam_identification_type_id,
            partner.l10n_co_regimen_fiscal,
            partner.l10n_co_responsibility_ids,
        )

    def _check_l10n_co_dian_self_params(self):
        """Validate fiscal params and return list of missing field errors."""
        self.ensure_one()
        partner = self.commercial_partner_id
        missing = []

        if not partner.country_id:
            missing.append(self.env._("País"))
        if not partner.name:
            missing.append(self.env._("Nombre"))
        if not partner.l10n_latam_identification_type_id:
            missing.append(self.env._("Tipo de identificación"))
        if not partner.vat:
            missing.append(self.env._("Número de identificación (NIT/CC/ID)"))

        is_foreign = partner.country_id.code != "CO"
        if not is_foreign:
            if not partner.l10n_co_regimen_fiscal:
                missing.append(self.env._("Régimen fiscal"))
            if not partner.l10n_co_responsibility_ids:
                missing.append(self.env._("Responsabilidades fiscales"))

        return missing
