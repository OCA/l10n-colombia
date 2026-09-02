# Copyright 2026 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def l10n_co_get_withholding_taxes(self, partner, tax_type="purchase"):
        domain = [
            ("company_id", "in", (self.company_id.id, False)),
            ("type_tax_use", "=", tax_type),
            ("amount", "<", 0),
        ]
        return self.env["account.tax"].search(domain)

    def l10n_co_check_min_base(self, tax, base_amount):
        if not tax.l10n_co_min_base_uvt:
            return True
        uvt_value = self.company_id._l10n_co_get_uvt_value()
        min_base = tax.l10n_co_min_base_uvt * uvt_value
        return abs(base_amount) >= min_base

    def l10n_co_get_applicable_withholding_taxes(self):
        self.ensure_one()
        partner = self.partner_id
        company = self.company_id

        if not company.l10n_co_is_retention_agent:
            return self.env["account.tax"]

        applicable_taxes = self.env["account.tax"]

        if company.l10n_co_default_rte_fte_tax_ids:
            applicable_taxes |= company.l10n_co_default_rte_fte_tax_ids
        if company.l10n_co_default_rte_iva_tax_ids:
            applicable_taxes |= company.l10n_co_default_rte_iva_tax_ids
        if company.l10n_co_default_rte_ica_tax_ids:
            applicable_taxes |= company.l10n_co_default_rte_ica_tax_ids

        if partner.l10n_co_tax_regime == "simple":
            applicable_taxes = applicable_taxes.filtered(
                lambda t: t.l10n_co_withholding_type != "rte_fte",
            )
        elif partner.l10n_co_tax_regime == "non_taxpayer":
            applicable_taxes = self.env["account.tax"]

        return applicable_taxes

    def l10n_co_compute_withholding_taxes(self):
        self.ensure_one()
        if self.state != "draft":
            raise UserError(
                _("Solo se pueden calcular retenciones en facturas en borrador."),
            )

        if self.move_type not in (
            "in_invoice",
            "in_refund",
            "out_invoice",
            "out_refund",
        ):
            raise UserError(_("Este documento no soporta retenciones."))

        applicable_taxes = self.l10n_co_get_applicable_withholding_taxes()

        if not applicable_taxes:
            return {
                "applied": 0,
                "message": _("No hay retenciones aplicables."),
            }

        product_lines = self.line_ids.filtered(
            lambda line: line.display_type == "product",
        )
        if not product_lines:
            return {
                "applied": 0,
                "message": _("No hay líneas de producto para aplicar retenciones."),
            }

        applied_count = 0
        for line in product_lines:
            current_taxes = line.tax_ids
            for wh_tax in applicable_taxes:
                if wh_tax not in current_taxes:
                    base_amount = line.price_subtotal

                    # Para ReteICA, verificar si hay tarifa específica
                    if wh_tax.l10n_co_withholding_type == "rte_ica":
                        reteica_rate = self.env[
                            "l10n.co.reteica.rate"
                        ].get_rate_for_partner(self.partner_id)
                        if reteica_rate:
                            uvt_value = self.company_id._l10n_co_get_uvt_value()
                            if self.move_type in (
                                "in_invoice",
                                "out_invoice",
                            ):
                                min_base = (
                                    reteica_rate.min_base_services_uvt * uvt_value
                                )
                            else:
                                min_base = (
                                    reteica_rate.min_base_purchases_uvt * uvt_value
                                )

                            if abs(base_amount) < min_base:
                                continue

                    # Verificar base mínima del impuesto
                    if self.l10n_co_check_min_base(wh_tax, base_amount):
                        line.tax_ids = current_taxes + wh_tax
                        current_taxes = line.tax_ids
                        applied_count += 1

        return {
            "applied": applied_count,
            "message": _("Se aplicaron %d retenciones.") % applied_count,
        }

    def l10n_co_remove_withholding_taxes(self, line_ids, withholding_tax_ids):
        for line in self.env["account.move.line"].browse(line_ids):
            if line.display_type != "product":
                continue
            current_taxes = line.tax_ids
            taxes_to_remove = current_taxes & withholding_tax_ids
            if taxes_to_remove:
                line.tax_ids = current_taxes - taxes_to_remove
        return True
