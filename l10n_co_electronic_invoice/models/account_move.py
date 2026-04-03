# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_co_payment_term = fields.Selection(
        selection=[("1", "Contado"), ("2", "Credito")],
        default="1",
        string="Forma de Pago",
    )
    l10n_co_payment_method_id = fields.Many2one(
        comodel_name="l10n_co.payment.method",
        default=lambda self: self.env.ref(
            "l10n_co_electronic_invoice.l10n_co_payment_method_1", False
        ),
        string="Medio de Pago",
    )
    l10n_co_dian_operation_type = fields.Selection(
        [
            ("10", "Estandar"),
            ("09", "AIU"),
            ("11", "Mandatos"),
            ("12", "Transporte"),
            ("13", "Cambiario"),
            ("15", "Compra Divisas"),
            ("16", "Venta Divisas"),
            ("20", "Nota Crédito que referencia una factura electrónica"),
            ("22", "Nota Crédito sin referencia a facturas"),
            ("30", "Nota Débito que referencia una factura electrónica"),
            ("32", "Nota Débito sin referencia a facturas"),
            (
                "33",
                "Inactivo: Nota Débito para facturación electrónica V1 (Decreto 2242)",
            ),
        ],
        string="Operation Type (CO)",
        compute="_compute_operation_type",
        store=True,
    )
    l10n_co_invoice_period_start = fields.Date(
        string="Periodo Inicio",
        help="Fecha de inicio del periodo de facturación que "
        "modifica esta nota crédito/débito. Obligatorio "
        "para NC/ND sin referencia a factura (DIAN CAE02).",
    )
    l10n_co_invoice_period_end = fields.Date(
        string="Periodo Fin",
        help="Fecha de fin del periodo de facturación que "
        "modifica esta nota crédito/débito. Obligatorio "
        "para NC/ND sin referencia a factura (DIAN CAE04).",
    )
    l10n_co_discrepancy_response_code = fields.Selection(
        selection=[
            (
                "nc_1",
                "NC - Devolución parcial de los bienes y/o "
                "no aceptación parcial del servicio",
            ),
            (
                "nc_2",
                "NC - Anulación de factura electrónica",
            ),
            (
                "nc_3",
                "NC - Rebaja o descuento parcial o total",
            ),
            ("nc_4", "NC - Ajuste de precio"),
            (
                "nc_5",
                "NC - Descuento comercial por pronto pago",
            ),
            (
                "nc_6",
                "NC - Descuento comercial por volumen de ventas",
            ),
            ("nd_1", "ND - Intereses"),
            ("nd_2", "ND - Gastos por cobrar"),
            ("nd_3", "ND - Cambio del valor"),
            ("nd_4", "ND - Otros"),
        ],
        string="Concepto de Corrección",
    )
    l10n_co_edi_cufe_cude_ref = fields.Char(
        string="CUFE/CUDE", copy=False, readonly=True
    )
    l10n_co_dian_status = fields.Selection(
        selection=[
            ("not_sent", "No enviado"),
            ("sent", "Enviado"),
            ("accepted", "Aceptado"),
            ("rejected", "Rechazado"),
            ("error", "Error"),
        ],
        string="Estado en DIAN",
    )
    l10n_co_dian_generation_date = fields.Datetime(
        string="Fecha de generación del documento"
    )
    l10n_co_dian_zip_key = fields.Char(
        string="ZipKey DIAN",
        copy=False,
        readonly=True,
        help="TrackId/ZipKey retornado por SendTestSetAsync. "
        "Se usa para consultar el estado con GetStatusZip.",
    )

    @api.depends(
        "move_type",
        "l10n_latam_document_type_id",
        "reversed_entry_id",
        "debit_origin_id",
    )
    def _compute_operation_type(self):
        for move in self:
            doc_code = move.l10n_latam_document_type_id.code or False
            if move.move_type in ("out_refund", "in_refund"):
                if move.reversed_entry_id:
                    move.l10n_co_dian_operation_type = "20"
                else:
                    move.l10n_co_dian_operation_type = "22"
            elif move.debit_origin_id:
                move.l10n_co_dian_operation_type = "30"
            elif doc_code in ("01", "02", "03", "05"):
                move.l10n_co_dian_operation_type = "10"
            else:
                move.l10n_co_dian_operation_type = False

    @api.depends("l10n_latam_use_documents", "l10n_latam_document_type_id")
    def _compute_show_reset_to_draft_button(self):
        super()._compute_show_reset_to_draft_button()
        for move in self.filtered(
            lambda m: m.move_type
            in ("out_invoice", "out_refund", "in_invoice", "in_refund")
            and m.l10n_latam_use_documents
        ):
            if move.l10n_co_dian_status in ("sent", "accepted"):
                move.show_reset_to_draft_button = False
        return
