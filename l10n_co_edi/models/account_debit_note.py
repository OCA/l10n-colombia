# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountDebitNote(models.TransientModel):
    _inherit = 'account.debit.note'

    def _prepare_default_values(self, move):
        default_values = super(AccountDebitNote, self)._prepare_default_values(move)

        default_values['is_out_country'] = move.is_out_country

        return default_values
