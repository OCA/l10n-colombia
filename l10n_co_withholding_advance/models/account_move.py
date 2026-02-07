# Copyright 2026 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from contextlib import ExitStack, contextmanager

from odoo import models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_l10n_co_withholding_advance_info(self, entry_type):
        config_parameter = self.env["ir.config_parameter"].sudo()
        enabled = config_parameter.get_param("l10n_co_withholding_advance.enabled")
        if not enabled or enabled == "False":
            return False, None, 0.0

        account_param = config_parameter.get_param(
            f"l10n_co_withholding_advance.{entry_type}_account_id"
        )
        if not account_param:
            return False, None, 0.0

        account_id = self.env["account.account"].sudo().browse(int(account_param))
        if not account_id.exists():
            _logger.warning(
                "Cuenta de autorretención %s no encontrada (ID: %s)",
                entry_type,
                account_param,
            )
            return False, None, 0.0

        percentage = float(
            config_parameter.get_param("l10n_co_withholding_advance.rate") or 0.0
        )

        return True, account_id, percentage

    @contextmanager
    def _sync_dynamic_lines(self, container):
        with self._disable_recursion(container, "skip_invoice_sync") as disabled:
            if disabled:
                yield
                return

            def update_containers():
                tax_container["records"] = container["records"].filtered(
                    lambda m: m.is_invoice(True)
                    or m.line_ids.tax_ids
                    or m.line_ids.tax_repartition_line_id
                )
                invoice_container["records"] = container["records"].filtered(
                    lambda m: m.is_invoice(True)
                )
                misc_container["records"] = container["records"].filtered(
                    lambda m: m.is_entry() and not m.tax_cash_basis_origin_move_id
                )

            tax_container, invoice_container, misc_container = ({} for __ in range(3))
            update_containers()
            with ExitStack() as stack:
                stack.enter_context(
                    self._sync_dynamic_line(
                        existing_key_fname="term_key",
                        needed_vals_fname="needed_terms",
                        needed_dirty_fname="needed_terms_dirty",
                        line_type="payment_term",
                        container=invoice_container,
                    )
                )
                stack.enter_context(self._sync_unbalanced_lines(misc_container))
                stack.enter_context(self._sync_rounding_lines(invoice_container))
                stack.enter_context(
                    self._sync_dynamic_line(
                        existing_key_fname="discount_allocation_key",
                        needed_vals_fname="line_ids.discount_allocation_needed",
                        needed_dirty_fname="line_ids.discount_allocation_dirty",
                        line_type="discount",
                        container=invoice_container,
                    )
                )
                stack.enter_context(self._sync_tax_lines(tax_container))
                stack.enter_context(
                    self._sync_l10n_co_withholding_lines(invoice_container)
                )
                stack.enter_context(
                    self._sync_dynamic_line(
                        existing_key_fname="epd_key",
                        needed_vals_fname="line_ids.epd_needed",
                        needed_dirty_fname="line_ids.epd_dirty",
                        line_type="epd",
                        container=invoice_container,
                    )
                )
                stack.enter_context(self._sync_invoice(invoice_container))
                line_container = {"records": self.line_ids}
                with self.line_ids._sync_invoice(line_container):
                    yield
                    line_container["records"] = self.line_ids
                update_containers()

    @contextmanager
    def _sync_l10n_co_withholding_lines(self, container):
        if self.env.context.get("skip_l10n_co_withholding_sync"):
            yield
            return

        records = container.get("records") if container else self.browse()
        yield

        moves = records.filtered(
            lambda m: m.move_type in ("out_invoice", "out_refund")
            and m.state == "draft"
        )
        if not moves:
            return

        cache = {}
        base_ctx = dict(
            self.env.context,
            skip_invoice_sync=True,
            skip_l10n_co_withholding_sync=True,
        )
        unlink_ctx = {**base_ctx, "dynamic_unlink": True}
        create_ctx = {**base_ctx, "check_move_validity": False}
        line_model = self.env["account.move.line"]

        for move in moves:
            targets = self._l10n_co_prepare_withholding_targets(move, cache)
            if not targets:
                continue
            self._l10n_co_apply_withholding_lines(
                move,
                targets,
                line_model,
                unlink_ctx,
                create_ctx,
                base_ctx,
            )

    def _l10n_co_prepare_withholding_targets(self, move, cache):
        targets = {}
        has_product_lines = any(
            line.display_type == "product" for line in move.line_ids
        )
        tax_totals = move.tax_totals or {}
        base_amount = tax_totals.get("base_amount", 0.0)

        for entry_type in ("debit", "credit"):
            enabled, account, percentage = self._l10n_co_get_cached_config(
                move.company_id.id, entry_type, cache
            )
            if not enabled or not account:
                targets[entry_type] = {"account": None, "vals": None}
                continue

            vals = None
            if has_product_lines and percentage and base_amount:
                vals = self._l10n_co_build_withholding_line_vals(
                    move, entry_type, account, percentage, base_amount
                )

            targets[entry_type] = {"account": account, "vals": vals}

        return targets

    def _l10n_co_get_cached_config(self, company_id, entry_type, cache):
        entry_cache = cache.setdefault(entry_type, {})
        if company_id not in entry_cache:
            entry_cache[company_id] = self._get_l10n_co_withholding_advance_info(
                entry_type
            )
        return entry_cache[company_id]

    def _l10n_co_build_withholding_line_vals(
        self, move, entry_type, account, percentage, base_amount
    ):
        company_currency = move.company_id.currency_id
        amount = base_amount * percentage / 100.0
        if company_currency.is_zero(amount):
            return None

        debit = amount if entry_type == "debit" else 0.0
        credit = amount if entry_type == "credit" else 0.0
        if move.move_type == "out_refund":
            debit, credit = credit, debit

        return {
            "move_id": move.id,
            "account_id": account.id,
            "display_type": "tax",
            "name": self._l10n_co_withholding_line_name(account),
            "debit": debit,
            "credit": credit,
        }

    def _l10n_co_apply_withholding_lines(
        self, move, targets, line_model, unlink_ctx, create_ctx, write_ctx
    ):
        desired_accounts = {
            data["account"].id for data in targets.values() if data["account"]
        }

        candidate_lines = move.line_ids.filtered(
            lambda line: line.display_type == "tax"
            and (
                line.account_id.id in desired_accounts
                or (line.name or "").startswith("Autorretención")
            )
        )

        if not candidate_lines and not any(data["vals"] for data in targets.values()):
            return

        lines_by_account = {
            line.account_id.id: line for line in candidate_lines if line.account_id
        }
        remaining_lines = candidate_lines

        for entry_type in ("debit", "credit"):
            info = targets.get(entry_type)
            if not info:
                continue
            account = info["account"]
            desired_vals = info["vals"]
            line = (
                lines_by_account.get(account.id)
                if account
                else self.env["account.move.line"]
            )

            if line:
                remaining_lines -= line
                if desired_vals:
                    write_data = {
                        "name": desired_vals["name"],
                        "debit": desired_vals["debit"],
                        "credit": desired_vals["credit"],
                        "account_id": desired_vals["account_id"],
                    }
                    line.with_context(**write_ctx).write(write_data)
                else:
                    line.with_context(**unlink_ctx).unlink()
            elif desired_vals:
                line_model.with_context(**create_ctx).create(desired_vals)

        if remaining_lines:
            remaining_lines.with_context(**unlink_ctx).unlink()

    def _l10n_co_withholding_line_name(self, account):
        return f"Autorretención {account.code}" if account.code else "Autorretención"
