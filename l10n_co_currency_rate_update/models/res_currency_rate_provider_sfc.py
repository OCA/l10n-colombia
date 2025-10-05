# Copyright 2025 IKU Solutions - Yan Chirino <yan.chirino@iku.solutions>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

import requests
from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError

WSDL = (
    "https://www.superfinanciera.gov.co/SuperfinancieraWebServiceTRM/"
    "TCRMServicesWebService/TCRMServicesWebService?WSDL"
)


class ResCurrencyRateProviderSFC(models.Model):
    _inherit = "res.currency.rate.provider"

    service = fields.Selection(
        selection_add=[("SFC", "Superfinanciera Colombia")],
        ondelete={"SFC": "set default"},
    )

    @api.model
    def _get_supported_currencies(self):
        self.ensure_one()
        if self.service == "SFC":
            return [
                "COP",
                "USD",
            ]

        return super()._get_supported_currencies()

    @api.model
    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service == "SFC":
            if base_currency != "COP":
                raise UserError(
                    _(
                        "Superfinanciera is suitable only for companies"
                        " with COP as base currency!"
                    )
                )

            usd_currency_id = self.env.ref("base.USD")
            rate_date_list = []
            current_date = date_from
            while current_date <= date_to:
                rate_date_list.append(current_date.strftime("%Y-%m-%d"))
                current_date += timedelta(days=1)

            data = {}
            for rate_date in rate_date_list:
                body = f"""
                <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                    xmlns:act="http://action.trm.services.generic.action.superfinanciera.nexura.sc.com.co/">
                <soapenv:Header/>
                <soapenv:Body>
                    <act:queryTCRM>
                        <!--Optional:-->
                        <tcrmQueryAssociatedDate>{rate_date}</tcrmQueryAssociatedDate>
                    </act:queryTCRM>
                </soapenv:Body>
                </soapenv:Envelope>
                """
                response = requests.post(
                    WSDL, data=body, headers={"content-type": "text/xml"}, timeout=10
                )
                rate = float(etree.XML(response.content).xpath("//value")[0].text)
                data[rate_date] = {usd_currency_id.name: 1 / rate}

            return data

        return super()._obtain_rates(base_currency, currencies, date_from, date_to)
