# -*- coding: utf-8 -*-
#
# Jorels S.A.S. - Copyright (2019-2022)
#
# This file is part of l10n_co_edi_jorels.
#
# l10n_co_edi_jorels is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# l10n_co_edi_jorels is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with l10n_co_edi_jorels.  If not, see <https://www.gnu.org/licenses/>.
#
# email: info@jorels.com
#

# First import languages
from . import languages

# Then import others models
from . import correction_concepts
from . import countries
from . import departments
from . import discounts
from . import municipalities
from . import payment_forms
from . import payment_methods
from . import payroll_periods
from . import reference_prices
from . import tax_details
from . import taxes
from . import type_currencies
from . import type_document_identifications
from . import type_documents
from . import type_environments
from . import type_item_identifications
from . import type_liabilities
from . import type_operations
from . import type_organizations
from . import type_regimes
from . import type_workers
from . import subtype_workers
from . import type_contracts
from . import unit_measures
from . import type_coverages
from . import type_users
from . import events
from . import type_incapacities
from . import organization_provenances
from . import payroll_periods
from . import rejection_concepts
from . import type_deliveries
from . import type_document_references
from . import type_endorsement_events
from . import type_event_payments
from . import type_item_sector_identifications
from . import type_mandate_times
from . import type_nature_mandates
from . import type_operation_events
from . import type_payroll_notes
from . import type_principals
from . import type_scope_mandates
from . import type_times

# Postal
from . import postal_department
from . import postal_municipality
from . import postal
