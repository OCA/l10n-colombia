# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    John W. Viloria Amaris <john.viloria.amaris@gmail.com>
#    Christian Camilo Camargo <ccamargov20@gmail.com﻿>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api
from suds.client import Client
from datetime import datetime
import xml.etree.ElementTree as ET
import suds
import logging

_logger = logging.getLogger(__name__)

BANREP_URL ="http://obiee.banrep.gov.co/analytics/saw.dll?wsdl"


class trmColombian(models.Model):
    _inherit = 'res.currency.rate'

    def _get_soap_trm(self):
        rate_name = False
        rate_value = 0.0
        client = Client(BANREP_URL, service = "SAWSessionService")
        session_id = client.service.logon("publico", "publico")
        client.set_options(service = "XmlViewService")
        report = {
            "reportPath": "/shared/Consulta Series Estadisticas desde Excel/1. Tasa de Cambio Peso Colombiano/1.1 TRM - Disponible desde el 27 de noviembre de 1991/1.1.3 Serie historica para un rango de fechas dado",
            "reportXml": "null"
        }
        options = {
            "async" : "false",
            "maxRowsPerPage" : "100",
            "refresh" : "true",
            "presentationInfo" : "true"
        }
        try:
            result_query = client.service.executeXMLQuery(report, "SAWRowsetData", options, session_id)
            client.set_options(service = "SAWSessionService")
            xml_data = ET.fromstring(result_query.rowset)
            rate_name = xml_data[0][1].text
            rate_value = float(xml_data[0][2].text)
        except suds.WebFault as detail:
            _logger.critical("Error while fetching info from BancoRep API: " + detail)
        client.service.logoff(session_id)
        return rate_name, rate_value

    @api.model
    def get_colombian_trm(self):    #Este método debe ser llamado por un cron de Odoo
        rate_name, trm = self._get_soap_trm()
        currency_id = self.env['res.currency'].search([('name','in',('USD','usd'))])[0].id
        try:
            old_trm = self.search([('currency_id','=',currency_id)], limit=1, order='id desc')[0].rate
        except:
            old_trm = 0
        if trm > 0 and trm != old_trm:  #Solo se actualiza si ha cambiado
            vals = {
                'rate': trm,
                'currency_id': currency_id,
                'name': rate_name,
            }
            self.create(vals)