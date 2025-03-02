/*
*   Jorels S.A.S. - Copyright (C) 2019-2023
*
*   This file is part of l10n_co_edi_jorels_pos.
*
*   This program is free software: you can redistribute it and/or modify
*   it under the terms of the GNU Lesser General Public License as published by
*   the Free Software Foundation, either version 3 of the License, or
*   (at your option) any later version.
*
*   This program is distributed in the hope that it will be useful,
*   but WITHOUT ANY WARRANTY; without even the implied warranty of
*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*   GNU Lesser General Public License for more details.
*
*   You should have received a copy of the GNU Lesser General Public License
*   along with this program. If not, see <https://www.gnu.org/licenses/>.
*
*   email: info@jorels.com
*/

odoo.define('l10n_co_edi_jorels_pos.PartnerDetailsEdit', function(require) {
    'use strict';

    const Registries = require('point_of_sale.Registries');
    const PartnerDetailsEdit = require('point_of_sale.PartnerDetailsEdit');

    const JPartnerDetailsEdit = (PartnerDetailsEdit) =>
        class extends PartnerDetailsEdit {
            setup() {
                super.setup();
                this.intFields.push(
                    'l10n_latam_identification_type_id',
                    'type_regime_id',
                    'type_liability_id',
                    'municipality_id'
                );
                const partner = this.props.partner;
                this.changes = Object.assign({}, this.changes,
                    {
                        vat: partner.vat,
                        company_type: partner.company_type,
                        city: partner.city,
                        l10n_latam_identification_type_id: partner.l10n_latam_identification_type_id && partner.l10n_latam_identification_type_id[0],
                        type_regime_id: partner.type_regime_id && partner.type_regime_id[0],
                        type_liability_id: partner.type_liability_id && partner.type_liability_id[0],
                        municipality_id: partner.municipality_id && partner.municipality_id[0]
                    }
                );
            }
        };

    Registries.Component.extend(PartnerDetailsEdit, JPartnerDetailsEdit);

    return PartnerDetailsEdit;
});