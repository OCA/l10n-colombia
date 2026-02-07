# Copyright 2026 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from contextlib import contextmanager

from odoo import models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def _l10n_co_update_withholding_advance(
        self, move, entry_type, account_id, percentage
    ):
        autoreten_amount = move.tax_totals.get("base_amount", 0) * percentage / 100
        product_lines = move.line_ids.filtered(
            lambda line: line.display_type == "product"
        )

        _logger.warning(
            f"Actualizando retención anticipada para {move.name}: "
            f"autoreten={autoreten_amount}, "
            f"product_lines={len(product_lines)}"
        )

        withholding_line_id = move.line_ids.filtered(
            lambda line: line.display_type == "tax"
            and line.account_id.id == account_id.id
        )
        if not product_lines:
            if withholding_line_id:
                withholding_line_id.unlink()
                return

        name = " ".join([f"[{move.name}]" if move.name else "", account_id.name or ""])
        values = {
            "name": name.strip(),
            "debit": autoreten_amount if entry_type == "debit" else 0,
            "credit": autoreten_amount if entry_type == "credit" else 0,
        }

        # Invertir en notas de crédito
        if move.move_type == "out_refund":
            values["debit"], values["credit"] = values["credit"], values["debit"]

        if not withholding_line_id:
            move.line_ids.create(
                {
                    "move_id": move.id,
                    "account_id": account_id.id,  # cuenta de autoreten​ción anticipada
                    "display_type": "tax",
                    **values,
                }
            )
        else:
            withholding_line_id.write(values)

    def _get_l10n_co_withholding_advance_info(self, entry_type):
        config_parameter = self.env["ir.config_parameter"].sudo()
        enabled = bool(
            config_parameter.get_param("l10n_co_withholding_advance.enabled")
        )
        if not enabled:
            return False, None, 0.0

        account = int(
            config_parameter.get_param(
                f"l10n_co_withholding_advance.{entry_type}_account_id"
            )
        )
        account_id = self.env["account.account"].sudo().browse(account)
        percentage = float(
            config_parameter.get_param("l10n_co_withholding_advance.rate")
        )
        return enabled, account_id, percentage

    @contextmanager
    def _l10n_co_withholding_advance_debit(self, container):
        enabled, account_id, percentage = self._get_l10n_co_withholding_advance_info(
            entry_type="debit"
        )

        yield
        if not enabled:
            return

        # Solo en facturas de clientes/ventas
        for move in container["records"].filtered(
            lambda move: move.move_type in ["out_invoice", "out_refund"]
        ):
            self._l10n_co_update_withholding_advance(
                move=move,
                entry_type="debit",
                account_id=account_id,
                percentage=percentage,
            )

    @contextmanager
    def _l10n_co_withholding_advance_credit(self, container):
        enabled, account_id, percentage = self._get_l10n_co_withholding_advance_info(
            entry_type="credit"
        )

        yield
        if not enabled:
            return

        # Solo en facturas de clientes/ventas
        for move in container["records"].filtered(
            lambda move: move.move_type in ["out_invoice", "out_refund"]
        ):
            self._l10n_co_update_withholding_advance(
                move=move,
                entry_type="credit",
                account_id=account_id,
                percentage=percentage,
            )

    def _get_sync_stack(self, container):
        stack, update_containers = super()._get_sync_stack(container)
        tax_container, invoice_container, misc_container = update_containers()

        stack.extend(
            [
                (
                    98,
                    self._l10n_co_withholding_advance_debit(
                        container=invoice_container
                    ),
                ),
                (
                    99,
                    self._l10n_co_withholding_advance_credit(
                        container=invoice_container
                    ),
                ),
            ]
        )

        return stack, update_containers
