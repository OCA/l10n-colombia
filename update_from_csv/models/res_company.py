# -*- coding: utf-8 -*-
#
# Jorels S.A.S. - Copyright (2019-2021)
#
# This file is part of update_from_csv.
#
# update_from_csv is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# update_from_csv is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with update_from_csv.  If not, see <https://www.gnu.org/licenses/>.
#
# email: info@jorels.com
#

from odoo import api, fields, models, _
from odoo.modules import module

import csv
from pathlib import Path

import logging

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    def init_csv_data(self, model):
        try:
            module_name = model.split('.')[0]
            model = model[len(module_name) + 1:]
            file_name = model + '.csv'
            _logger.debug("Import csv file: %s", file_name)

            module_path = module.get_module_path(module_name)
            file_path = Path(module_path) / 'data' / file_name
            table_name = model.replace(".", "_")

            with open(file_path, mode="r", encoding="utf-8-sig") as csv_file:
                csv_reader = csv.DictReader(csv_file, delimiter=',', quotechar='"')
                line_count = 0
                for row in csv_reader:
                    if line_count == 0:
                        _logger.debug(f'Column names are {", ".join(row)}')
                        field_names = row

                    # Insert
                    query = "insert into " + table_name + "("
                    for field_name in field_names:
                        query = query + field_name + ","
                    query = query + "create_uid,create_date,write_uid,write_date) values("
                    for field_name in field_names:
                        val = "$$" + row[field_name] + "$$"
                        if val == "$$$$":
                            val = 'NULL'
                        query = query + val + ','
                    query = query + str(self.env.user.id) + ',NOW(),' + str(
                        self.env.user.id) + ',NOW()) ON CONFLICT(id) DO UPDATE SET '

                    # Update
                    for field_name in field_names:
                        val = "$$" + row[field_name] + "$$"
                        if val == "$$$$":
                            val = 'NULL'
                        query = query + field_name + "=" + val + ","
                    query = query + "write_uid=" + str(self.env.user.id) + ",write_date=NOW()"

                    # Execute query
                    # _logger.debug(query)
                    self._cr.execute(query)

                    # Count
                    line_count += 1

                self._cr.execute("select max(id) from " + table_name)
                max_id = self._cr.dictfetchall()[0]['max']
                self._cr.execute(f"SELECT setval('{table_name}_id_seq',{str(max_id + 1)}, true)")
                _logger.debug(f'Processed {line_count} records on table {table_name}')
        except Exception as e:
            _logger.debug("init_csv_data %s", e)
