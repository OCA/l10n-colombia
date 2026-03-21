# Copyright 2026 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Colombia - Factura Electrónica Software Propio",
    "version": "19.0.2.0.0",
    "category": "Accounting/Localizations",
    "summary": "Integración con la DIAN Colombia para la emisión\
        de Facturas Electrónicas en modo de operación software propio",
    "author": "IKU Solutions - Yan Chirino, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-colombia",
    "license": "AGPL-3",
    "depends": [
        "account_edi",
        "account_edi_ubl_cii",
        "l10n_co_electronic_invoice",
        "certificate",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/account_edi_format_data.xml",
        "data/ir_sequence_data.xml",
        "templates/soap_envelope.xml",
        "templates/invoice_ubl.xml",
        "templates/credit_note_ubl.xml",
        "templates/debit_note_ubl.xml",
        "templates/numbering_range_query.xml",
        "templates/attached_document.xml",
        "templates/demo_response.xml",
        "wizards/l10n_co_radian_event_wizard_views.xml",
        "views/account_journal_views.xml",
        "views/account_move_views.xml",
        "reports/report_invoice.xml",
    ],
    "external_dependencies": {
        "python": [
            "xmlsig",
            "lxml",
            "cryptography",
            "xmltodict",
            "requests",
            "qrcode",
        ]
    },
    "application": False,
    "auto_install": False,
    "installable": True,
}
