# Copyright 2026 Juan Arcos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def post_init_hook(env):
    """Set the Colombian payroll legal default values on existing companies."""
    companies = env["res.company"].search([])
    companies._l10n_co_set_payroll_defaults()
    companies._l10n_co_set_payroll_account_defaults()