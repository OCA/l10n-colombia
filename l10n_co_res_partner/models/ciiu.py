# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2016  Dominic Krimmer                                         #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

from openerp import models, fields, api


class Ciiu(models.Model):
    _name = "ciiu"
    _description = "ISIC List"

    name = fields.Char(
        string="Code and Description",
        store=True,
        compute="_concat_name"
    )
    code = fields.Char('Code', required=True)
    description = fields.Char('Description', required=True)
    type = fields.Char(
        'Type',
        store=True,
        compute="_set_type"
    )
    hasParent = fields.Boolean('Has Parent?')
    parent = fields.Many2one('ciiu', 'Parent')

    hasDivision = fields.Boolean('Has Division?')
    division = fields.Many2one('ciiu', 'Division')

    hasSection = fields.Boolean('Has Section?')
    section = fields.Many2one('ciiu', 'Section')

    hierarchy = fields.Selection(
        [
            (1, 'Has Parent?'),
            (2, 'Has Division?'),
            (3, 'Has Section?')
        ],
        'Hierarchy'
    )

    @api.one
    @api.depends('code', 'description')
    def _concat_name(self):
        """
        This function concatinates two fields in order to be able to search
        for CIIU as number or string
        @return: void
        """
        if self.code is False or self.description is False:
            self.name = ''
        else:
            self.name = str(self.code.encode('utf-8').strip()) + \
                        ' - ' + str(self.description.encode('utf-8').strip())

    @api.one
    @api.depends('hasParent')
    def _set_type(self):
        """
        Section, Division and Parent should be visually separated in the tree view.
        Therefore we tag them accordingly as 'view' or 'other'
        @return: void
        """
        # Child
        if self.hasParent is True:
            if self.division is True:
                self.type = 'view'
            elif self.section is True:
                self.type = 'view'
            else:
                self.type = 'other'
        # Division
        else:
            self.type = 'view'
