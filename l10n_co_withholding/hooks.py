# Copyright 2026 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

RTE_FTE_TAXES = {
    "l10n_co_tax_23": {"name": "4% RteFte S L", "amount": -4.0},
    "l10n_co_tax_25": {"name": "6% RteFte S G", "amount": -6.0},
    "l10n_co_tax_32": {"name": "10% RteFte N", "amount": -10.0},
    "l10n_co_tax_40": {"name": "11% RteFte F L E", "amount": -11.0},
    "l10n_co_tax_19": {"name": "2.5% RteFte D", "amount": -2.5},
    "l10n_co_tax_27": {"name": "3.5% RteFte Soft", "amount": -3.5},
}

RTE_IVA_TAXES = {
    "l10n_co_tax_12": {"name": "15% RteVAT 19%", "amount": -2.85},
    "l10n_co_tax_13": {"name": "15% RteVAT 5%", "amount": -0.75},
}

RTE_ICA_TAXES = {
    "l10n_co_tax_44": {"name": "0.69% RteICA", "amount": -0.69},
    "l10n_co_tax_45": {"name": "1.104% RteICA", "amount": -1.104},
}

ACCOUNT_MAPPINGS = {
    "co_puc_236515": "co_puc_135515",
    "co_puc_236520": "co_puc_135515",
    "co_puc_236525": "co_puc_135515",
    "co_puc_236530": "co_puc_135515",
    "co_puc_236535": "co_puc_135515",
    "co_puc_236540": "co_puc_135515",
    "co_puc_236550": "co_puc_135515",
    "co_puc_236700": "co_puc_135517",
    "co_puc_236800": "co_puc_135518",
}


def _l10n_co_withholding_post_init(env):
    _set_default_uvt_value(env)
    companies = env["res.company"].search([("chart_template", "=", "co")])
    for company in companies:
        _setup_withholding_for_company(env, company)


def _set_default_uvt_value(env):
    param = env["ir.config_parameter"].sudo()
    if not param.get_param("l10n_co_withholding.uvt_value"):
        param.set_param("l10n_co_withholding.uvt_value", "52374")
        _logger.info("UVT value set to 52374 (2026)")


def _setup_withholding_for_company(env, company):
    env = api.Environment(env.cr, SUPERUSER_ID, {})
    company = company.with_company(company)
    rte_fte_0 = _get_or_create_zero_tax(
        env, company, "RteFte 0%", "l10n_co.tax_group_r_ren_0", "rte_fte"
    )
    rte_iva_0 = _get_or_create_zero_tax(
        env, company, "RteIVA 0%", "l10n_co.tax_group_r_iva_075", "rte_iva"
    )
    rte_ica_0 = env["account.tax"].search(
        [
            ("company_id", "=", company.id),
            ("name", "=", "0% RteICA"),
            ("amount", "=", 0.0),
        ],
        limit=1,
    )
    if not rte_ica_0:
        rte_ica_0 = env["account.tax"].search(
            [("company_id", "=", company.id), ("name", "=", "0% RteICA")],
            limit=1,
        )
    _create_fiscal_position_simple(env, company, rte_fte_0)
    _create_fiscal_position_non_taxpayer(env, company, rte_fte_0, rte_iva_0, rte_ica_0)


def _get_or_create_zero_tax(env, company, name, tax_group_xmlid, wh_type):
    existing = env["account.tax"].search(
        [
            ("company_id", "=", company.id),
            ("name", "=", name),
            ("amount", "=", 0.0),
        ],
        limit=1,
    )
    if existing:
        return existing
    tax_group = env.ref(tax_group_xmlid, raise_if_not_found=False)
    if not tax_group:
        tax_group = env["account.tax.group"].search(
            [("company_id", "in", (company.id, False))], limit=1
        )
    return env["account.tax"].create(
        {
            "name": name,
            "amount": 0.0,
            "amount_type": "percent",
            "type_tax_use": "purchase",
            "tax_group_id": tax_group.id if tax_group else False,
            "company_id": company.id,
            "l10n_co_withholding_type": wh_type,
            "price_include_override": "tax_excluded",
        }
    )


def _find_tax_by_xmlid(env, company, xmlid):
    tax = env.ref(xmlid, raise_if_not_found=False)
    if tax and tax.company_id == company:
        return tax
    return env["account.tax"].search(
        [("company_id", "=", company.id), ("name", "ilike", xmlid.split(".")[-1])],
        limit=1,
    )


def _find_account_by_code(env, company, code):
    return env["account.account"].search(
        [("company_id", "=", company.id), ("code", "=", code)],
        limit=1,
    )


def _add_account_mappings(env, company, fp):
    for src_code, dest_code in ACCOUNT_MAPPINGS.items():
        src_account = _find_account_by_code(env, company, src_code)
        dest_account = _find_account_by_code(env, company, dest_code)
        if src_account and dest_account:
            existing = env["account.fiscal.position.account"].search(
                [
                    ("position_id", "=", fp.id),
                    ("account_src_id", "=", src_account.id),
                ],
                limit=1,
            )
            if not existing:
                env["account.fiscal.position.account"].create(
                    {
                        "position_id": fp.id,
                        "account_src_id": src_account.id,
                        "account_dest_id": dest_account.id,
                    }
                )


def _create_fiscal_position_simple(env, company, rte_fte_0):
    fp = env["account.fiscal.position"].search(
        [
            ("company_id", "=", company.id),
            ("name", "=", "Régimen Simple (Sin ReteFte)"),
        ],
        limit=1,
    )
    if not fp:
        fp = env["account.fiscal.position"].create(
            {
                "name": "Régimen Simple (Sin ReteFte)",
                "company_id": company.id,
            }
        )
    for xmlid in RTE_FTE_TAXES:
        src_tax = _find_tax_by_xmlid(env, company, f"l10n_co.{xmlid}")
        if src_tax:
            existing = env["account.fiscal.position.tax"].search(
                [
                    ("position_id", "=", fp.id),
                    ("tax_src_id", "=", src_tax.id),
                ],
                limit=1,
            )
            if not existing:
                env["account.fiscal.position.tax"].create(
                    {
                        "position_id": fp.id,
                        "tax_src_id": src_tax.id,
                        "tax_dest_id": rte_fte_0.id,
                    }
                )
    _add_account_mappings(env, company, fp)


def _create_fiscal_position_non_taxpayer(
    env, company, rte_fte_0, rte_iva_0, rte_ica_0
):
    fp = env["account.fiscal.position"].search(
        [
            ("company_id", "=", company.id),
            ("name", "=", "No Contribuyente (Sin Retenciones)"),
        ],
        limit=1,
    )
    if not fp:
        fp = env["account.fiscal.position"].create(
            {
                "name": "No Contribuyente (Sin Retenciones)",
                "company_id": company.id,
            }
        )
    for xmlid in RTE_FTE_TAXES:
        src_tax = _find_tax_by_xmlid(env, company, f"l10n_co.{xmlid}")
        if src_tax:
            existing = env["account.fiscal.position.tax"].search(
                [
                    ("position_id", "=", fp.id),
                    ("tax_src_id", "=", src_tax.id),
                ],
                limit=1,
            )
            if not existing:
                env["account.fiscal.position.tax"].create(
                    {
                        "position_id": fp.id,
                        "tax_src_id": src_tax.id,
                        "tax_dest_id": rte_fte_0.id,
                    }
                )
    for xmlid in RTE_IVA_TAXES:
        src_tax = _find_tax_by_xmlid(env, company, f"l10n_co.{xmlid}")
        if src_tax:
            existing = env["account.fiscal.position.tax"].search(
                [
                    ("position_id", "=", fp.id),
                    ("tax_src_id", "=", src_tax.id),
                ],
                limit=1,
            )
            if not existing:
                env["account.fiscal.position.tax"].create(
                    {
                        "position_id": fp.id,
                        "tax_src_id": src_tax.id,
                        "tax_dest_id": rte_iva_0.id,
                    }
                )
    for xmlid in RTE_ICA_TAXES:
        src_tax = _find_tax_by_xmlid(env, company, f"l10n_co.{xmlid}")
        if src_tax and rte_ica_0:
            existing = env["account.fiscal.position.tax"].search(
                [
                    ("position_id", "=", fp.id),
                    ("tax_src_id", "=", src_tax.id),
                ],
                limit=1,
            )
            if not existing:
                env["account.fiscal.position.tax"].create(
                    {
                        "position_id": fp.id,
                        "tax_src_id": src_tax.id,
                        "tax_dest_id": rte_ica_0.id,
                    }
                )
    _add_account_mappings(env, company, fp)
