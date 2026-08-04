# Copyright 2026 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    l10n_co_withholding_concept = fields.Selection(
        selection=[
            ("honorarios", "Honorarios"),
            ("servicios", "Servicios"),
            ("comisiones", "Comisiones"),
            ("compras", "Compras"),
            ("arrendamiento_mueble", "Arrendamiento Bienes Muebles"),
            ("arrendamiento_inmueble", "Arrendamiento Bienes Inmuebles"),
            ("rendimientos_financieros", "Rendimientos Financieros"),
            ("transporte_carga", "Transporte de Carga"),
            ("transporte_pasajeros", "Transporte de Pasajeros"),
            ("vigilancia", "Vigilancia y Aseo (AIU)"),
            ("temporal", "Servicios Temporales (AIU)"),
            ("salud", "Servicios de Salud"),
            ("hoteles_restaurantes", "Hoteles y Restaurantes"),
            ("software", "Licencias de Software"),
            ("it_consulting", "Consultoría TI"),
            ("obras_inmuebles", "Obras en Inmuebles"),
            ("vehiculos", "Adquisición de Vehículos"),
            ("inmuebles", "Bienes Raíces"),
            ("inmuebles_comerciales", "Bienes Raíces Comerciales"),
            ("agricola", "Bienes Agrícolas"),
            ("combustibles", "Combustibles"),
            ("cafe", "Café"),
            ("pagos_exterior", "Pagos al Exterior"),
            ("otros", "Otros"),
        ],
        string="Concepto de Retención",
        help=(
            "Concepto tributario de la retención en la fuente"
            " según el Estatuto Tributario colombiano."
        ),
    )
    l10n_co_min_base_uvt = fields.Float(
        string="Base Mínima (UVT)",
        help="Cuantía mínima en UVT para que aplique esta retención. "
        "Si la base gravable es inferior, la retención no se aplica.",
    )
    l10n_co_withholding_type = fields.Selection(
        selection=[
            ("rte_fte", "ReteFte (Renta)"),
            ("rte_iva", "ReteIVA"),
            ("rte_ica", "ReteICA"),
        ],
        string="Tipo de Retención",
        help="Tipo de retención: Renta, IVA o ICA.",
    )
    l10n_co_withholding_counterpart = fields.Boolean(
        string="Contrapartida de Retención",
        help=(
            "Impuesto positivo que compensa la retención en ventas para que el "
            "total de la factura no se reduzca ante la DIAN."
        ),
    )
    l10n_co_withholding_compensates_tax_id = fields.Many2one(
        "account.tax",
        string="Retención Compensada",
        help="Impuesto de retención de venta que esta contrapartida compensa.",
    )

    def l10n_co_get_positive_counterpart(self):
        self.ensure_one()
        return self.env["account.tax"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("type_tax_use", "=", "sale"),
                ("l10n_co_withholding_compensates_tax_id", "=", self.id),
                ("l10n_co_withholding_counterpart", "=", True),
            ],
            limit=1,
        )


class AccountTaxGroup(models.Model):
    _inherit = "account.tax.group"

    l10n_co_withholding_counterpart = fields.Boolean(
        string="Grupo de Contrapartida de Retención",
        help=(
            "Marca este grupo como el que agrupa las contrapartidas positivas "
            "de las retenciones de venta."
        ),
    )
