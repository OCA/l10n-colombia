# Copyright 2026 juparmer - Juan Arcos <juanparmer@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields, models


def compute_verification_digit(base_nit):
    """Compute the Colombian NIT verification digit.

    Algorithm defined in Orden Administrativa 4 of 1989 by DIAN.
    Multipliers are applied from left to right, then the sum is taken
    modulo 11. If the remainder is 0 or 1, that is the digit; otherwise
    the digit is 11 minus the remainder.
    """
    digits = [int(c) for c in str(base_nit) if c.isdigit()]
    if not digits:
        return False
    multipliers = [41, 37, 29, 23, 19, 17, 13, 7, 3]
    if len(digits) == len(multipliers):
        mult = multipliers
    elif len(digits) < len(multipliers):
        mult = multipliers[len(multipliers) - len(digits) :]
    else:
        base = list(reversed(multipliers))
        mult = []
        for i in range(len(digits)):
            idx = len(digits) - 1 - i
            if idx < len(base):
                mult.append(base[idx])
            else:
                mult.append(base[-1] + (idx - len(base) + 1) * 6)
        mult.reverse()
    total = sum(d * m for d, m in zip(digits, mult, strict=False))
    remainder = total % 11
    if remainder <= 1:
        return remainder
    return 11 - remainder


class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_co_verification_digit = fields.Char(
        string="DV",
        size=1,
        compute="_compute_l10n_co_verification_digit",
        store=True,
        readonly=True,
    )

    @api.depends("vat", "country_id")
    def _compute_l10n_co_verification_digit(self):
        for partner in self:
            if partner.country_id.code == "CO" and partner.vat:
                cleaned = re.sub(r"\D", "", partner.vat)
                if cleaned:
                    digit = compute_verification_digit(cleaned)
                    partner.l10n_co_verification_digit = (
                        str(digit) if digit is not False else False
                    )
                    continue
            partner.l10n_co_verification_digit = False
