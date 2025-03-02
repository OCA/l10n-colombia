# -*- coding: utf-8 -*-
#
#   l10n_co_hr_payroll
#   Copyright (C) 2023  Jorels SAS
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published
#   by the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#   email: info@jorels.com
#

import datetime as dt
import json
import logging

import babel
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrPayslipEdi(models.Model):
    _name = "hr.payslip.edi"
    _inherit = [
        'mail.thread',
        'mail.activity.mixin',
        'l10n_co_hr_payroll.edi'
    ]
    _description = "Payslip Edi"

    note = fields.Text(string='Internal Note', readonly=True, states={'draft': [('readonly', False)]})
    contract_id = fields.Many2one('hr.contract', string='Contract', readonly=True,
                                  states={'draft': [('readonly', False)]})
    credit_note = fields.Boolean(string='Adjustment note', readonly=True, states={'draft': [('readonly', False)]},
                                 help="Indicates this edi payslip has a refund of another")
    origin_payslip_id = fields.Many2one(comodel_name="hr.payslip.edi", string="Origin Edi payslip", readonly=True,
                                        states={'draft': [('readonly', False)]}, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Rejected'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft',
        help="""* When the payslip is created the status is \'Draft\'
                \n* If the payslip is under verification, the status is \'Waiting\'.
                \n* If the payslip is confirmed then status is set to \'Done\'.
                \n* When user cancel payslip the status is \'Rejected\'.""")
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=True,
                                  states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', readonly=True, copy=False,
                                 default=lambda self: self.env.company,
                                 states={'draft': [('readonly', False)]})
    number = fields.Char(string='Reference', readonly=True, copy=False, states={'draft': [('readonly', False)]})
    name = fields.Char(string='Edi Payslip Name', compute='_compute_name', store=True)

    # Edi fields
    date = fields.Date("Date", required=True, readonly=True, states={'draft': [('readonly', False)]},
                       default=fields.Date.context_today, copy=False)
    payslip_ids = fields.Many2many(comodel_name='hr.payslip', string='Payslips',
                                   relation='hr_payslip_hr_payslip_edi_rel',
                                   readonly=True, states={'draft': [('readonly', False)]}, copy=True)

    month = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December')
    ], string='Month', index=True, copy=False, required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: str(fields.Date.context_today(self).month))
    year = fields.Integer(string='Year', index=True, copy=False, required=True, readonly=True,
                          states={'draft': [('readonly', False)]},
                          default=lambda self: fields.Date.context_today(self).year)

    @api.depends('employee_id', 'month', 'year')
    def _compute_name(self):
        for rec in self:
            if (not rec.employee_id) or (not rec.month) or (not rec.year):
                return

            employee = self.employee_id

            date_ym = dt.date(rec.year, int(rec.month), 1)
            locale = self.env.context.get('lang') or 'en_US'
            rec.name = _('Salary Slip of %s for %s') % (
                employee.name,
                tools.ustr(babel.dates.format_date(date=date_ym, format='MMMM-y', locale=locale))
            )

    def unlink(self):
        if any(self.filtered(lambda payslip: payslip.state not in ('draft', 'cancel'))):
            raise UserError(_('You cannot delete a Edi payslip which is not draft or cancelled!'))
        return super(HrPayslipEdi, self).unlink()

    def action_payslip_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})
        return True

    def action_payslip_cancel(self):
        for rec in self:
            if not rec.edi_is_valid:
                rec.write({'state': 'cancel'})
            else:
                raise UserError(_("You cannot cancel a electronic payroll that has already been validated to the DIAN"))
        return True

    def compute_sheet(self):
        for rec in self:
            number = rec.number or _('New')

            # The date is the sending date
            date = fields.Date.context_today(self)

            # Save
            rec.write({
                'number': number,
                'date': date,
            })

            # Payload
            payload = rec.get_json_request()
            edi_payload = json.dumps(payload, indent=4, sort_keys=False)

            # Save
            rec.write({
                'edi_sync': rec.company_id.edi_payroll_is_not_test,
                'edi_is_not_test': rec.company_id.edi_payroll_is_not_test,
                'edi_payload': edi_payload,
            })

        return True

    def get_json_request(self):
        for rec in self:
            if not rec.number:
                raise UserError(_("The payroll must have a consecutive number, 'Reference' field"))
            if not rec.contract_id.payroll_period_id:
                raise UserError(_("The contract must have the 'Scheduled Pay' field configured"))
            if not rec.company_id.name:
                raise UserError(_("Your company does not have a name"))
            if not rec.company_id.type_document_identification_id:
                raise UserError(_("Your company does not have an identification type"))
            if not rec.company_id.vat:
                raise UserError(_("Your company does not have a document number"))
            if not rec.company_id.partner_id.postal_municipality_id:
                raise UserError(_("Your company does not have a postal municipality"))
            if not rec.company_id.street:
                raise UserError(_("Your company does not have an address"))
            if not rec.contract_id.type_worker_id:
                raise UserError(_("The contract must have the 'Type worker' field configured"))
            if not rec.contract_id.subtype_worker_id:
                raise UserError(_("The contract must have the 'Subtype worker' field configured"))
            if not rec.employee_id.address_home_id.first_name:
                raise UserError(_("Employee does not have a first name"))
            if not rec.employee_id.address_home_id.surname:
                raise UserError(_("Employee does not have a surname"))
            if not rec.employee_id.address_home_id.type_document_identification_id:
                raise UserError(_("Employee does not have an identification type"))
            if rec.employee_id.address_home_id.type_document_identification_id.id == 6:
                raise UserError(_("The employee's document type cannot be NIT"))
            if not rec.employee_id.address_home_id.vat:
                raise UserError(_("Employee does not have an document number"))
            if not rec.employee_id.address_home_id.postal_municipality_id:
                raise UserError(_("Employee does not have a postal municipality"))
            if not rec.employee_id.address_home_id.street:
                raise UserError(_("Employee does not have an address."))
            if not rec.contract_id.name:
                raise UserError(_("Contract does not have a name"))
            if rec.contract_id.wage <= 0:
                raise UserError(_("The contract must have the 'Wage' field configured"))
            if not rec.contract_id.type_contract_id:
                raise UserError(_("The contract must have the 'Type contract' field configured"))
            if not rec.contract_id.date_start:
                raise UserError(_("The contract must have the 'Start Date' field configured"))
            # if not rec.date_from:
            #     raise UserError(_("The payroll must have a period"))
            # if not rec.date_to:
            #     raise UserError(_("The payroll must have a period"))
            if not rec.payment_form_id:
                raise UserError(_("The payroll must have a payment form"))
            if not rec.payment_method_id:
                raise UserError(_("The payroll must have a payment method"))
            # if not rec.payment_date:
            #     raise UserError(_("The payroll must have a payment date"))
            if not rec.month:
                raise UserError(_("The payroll must have a month"))
            if not rec.year:
                raise UserError(_("The payroll must have a year"))

            sequence = {}
            if rec.number and rec.number not in ('New', _('New')):
                sequence_number = ''.join([i for i in rec.number if i.isdigit()])
                sequence_prefix = rec.number.split(sequence_number)
                if sequence_prefix:
                    sequence = {
                        # "worker_code": "string",
                        "prefix": sequence_prefix[0],
                        "number": int(sequence_number)
                    }
                else:
                    raise UserError(_("The sequence must have a prefix"))

            json_request = {}

            # Others fields
            if rec.payslip_ids:
                for index, payslip in enumerate(rec.payslip_ids):
                    if index > 0:
                        json_request = rec.join_dicts(json_request, json.loads(payslip.edi_payload),
                                                      fields.Date.to_string(rec.date))
                    else:
                        json_request = json.loads(payslip.edi_payload)

            # Sequence
            if sequence:
                json_request['sequence'] = sequence

            # Notes
            if rec.note:
                notes = [{
                    "text": rec.note
                }]
                json_request['notes'] = notes

            # Save
            rec.write({
                'payment_form_id': json_request['payment']['code'],
                'payment_method_id': json_request['payment']['method_code'],
                'accrued_total_amount': json_request['accrued_total'],
                'deductions_total_amount': json_request['deductions_total'],
                'total_amount': json_request['total'],
                'worked_days_total': json_request['earn']['basic']['worked_days'],
            })

            # Credit note
            if rec.credit_note:
                if rec.origin_payslip_id:
                    if rec.origin_payslip_id.edi_is_valid:
                        json_request['payroll_reference'] = {
                            'number': rec.origin_payslip_id.edi_number,
                            'uuid': rec.origin_payslip_id.edi_uuid,
                            'issue_date': str(rec.origin_payslip_id.edi_issue_date)
                        }
                    else:
                        json_request['payroll_reference'] = {
                            'number': rec.origin_payslip_id.number,
                            'issue_date': str(rec.origin_payslip_id.date)
                        }
                else:
                    raise UserError(_("The Origin payslip is required for adjusment notes."))

                json_request = rec.get_json_delete_request(json_request)

            return json_request

    def validate_dian_generic(self):
        for rec in self:
            if not rec.company_id.edi_payroll_enable or not rec.company_id.edi_payroll_consolidated_enable:
                continue
            requests_data = rec.get_json_request()
            rec._validate_dian_generic(requests_data)

    def validate_dian(self):
        for rec in self:
            rec.validate_dian_generic()

    def action_payslip_done(self):
        for rec in self:
            if not rec.number or rec.number in ('New', _('New')):
                if rec.credit_note:
                    rec.number = self.env['ir.sequence'].next_by_code('salary.slip.edi.note')
                else:
                    rec.number = self.env['ir.sequence'].next_by_code('salary.slip.edi')

            if not self.env.context.get('without_compute_sheet'):
                rec.compute_sheet()
            rec.write({'state': 'done'})

            if rec.company_id.edi_payroll_enable \
                    and rec.company_id.edi_payroll_consolidated_enable \
                    and not rec.company_id.edi_payroll_enable_validate_state:
                rec.validate_dian_generic()

        return True

    def status_zip(self):
        for rec in self:
            if not rec.company_id.edi_payroll_enable or not rec.company_id.edi_payroll_consolidated_enable:
                continue

            # This line ensures that the electronic fields of the payroll are updated in Odoo, before the request
            payload = json.dumps(rec.get_json_request(), indent=2, sort_keys=False)
            rec._status_zip(payload)

    def refund_sheet(self):
        refund_payslip = None
        for payslip in self:
            if payslip.credit_note:
                raise UserError(_("A adjustment note should not be made to a adjustment note"))

            refund_payslip = payslip.copy({'credit_note': True,
                                           'name': _('Refund: ') + payslip.name,
                                           'origin_payslip_id': payslip.id,
                                           'number': _('New'),
                                           })
            refund_payslip.with_context(without_compute_sheet=True).action_payslip_done()

            if payslip.edi_payload and not refund_payslip.edi_payload:
                payload = refund_payslip.get_json_request()
                refund_payslip.write({'edi_payload': json.dumps(payload, indent=2, sort_keys=False)})

        formview_ref = self.env.ref('l10n_co_hr_payroll.view_hr_payslip_edi_form', False)
        treeview_ref = self.env.ref('l10n_co_hr_payroll.view_hr_payslip_edi_tree', False)

        if refund_payslip is not None:
            domain = "[('id', 'in', %s)]" % refund_payslip.ids
        else:
            domain = "[(credit_note, '=', True)]"

        return {
            'name': ("Refund Edi Payslip"),
            'view_mode': 'tree, form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'hr.payslip.edi',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'views': [(treeview_ref and treeview_ref.id or False, 'tree'),
                      (formview_ref and formview_ref.id or False, 'form')],
            'context': {}
        }

    def status_document_log(self):
        for rec in self:
            if not rec.company_id.edi_payroll_enable or not rec.company_id.edi_payroll_consolidated_enable:
                continue

            # This line ensures that the electronic fields of the payroll are updated in Odoo,
            # before the request
            payload = rec.get_json_request()
            rec._status_document_log(payload)
