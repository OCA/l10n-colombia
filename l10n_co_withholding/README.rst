.. image:: https://odoo-community.org/readme-banner-image
   :target: https://odoo-community.org/get-involved?utm_source=readme
   :alt: Odoo Community Association

=====================================
Colombia - Retención en la Fuente
=====================================

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/license-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-OCA%2Fl10n--colombia-lightgray.png?logo=github
    :target: https://github.com/OCA/l10n-colombia/tree/18.0/l10n_co_withholding
    :alt: OCA/l10n-colombia
.. |badge4| image:: https://img.shields.io/badge/weblate-Translate%20me-F47D42.png
    :target: https://translation.odoo-community.org/projects/l10n-colombia-18-0/l10n-colombia-18-0-l10n_co_withholding
    :alt: Translate me on Weblate
.. |badge5| image:: https://img.shields.io/badge/runboat-Try%20me-875A7B.png
    :target: https://runboat.odoo-community.org/builds?repo=OCA/l10n-colombia&target_branch=18.0
    :alt: Try me on Runboat

|badge1| |badge2| |badge3| |badge4| |badge5|

Este módulo implementa el soporte para retención en la fuente (RteFte),
ReteIVA y ReteICA en la localización contable de Colombia.

**Table of contents**

.. contents::
   :local:

Configuration
=============

**Company Configuration**

1. Go to **Settings > Companies** and open your company
2. In the tab **"Retenciones Colombia"**:
   - Enable **"Agente de Retención"** if your company acts as withholding agent
   - Configure default withholdings:
     - **ReteFte por Defecto**: Income tax withholding taxes
     - **ReteIVA por Defecto**: VAT withholding taxes
     - **ReteICA por Defecto**: ICA withholding taxes

**UVT Value Configuration**

The UVT value is configured as a system parameter:

1. Go to **Settings > Technical > System Parameters**
2. Find parameter `l10n_co_withholding.uvt_value`
3. Update the value annually according to DIAN resolution (default: 52374 for 2026)

**Partner Configuration**

1. Open a contact (supplier or customer)
2. In the tab **"Retenciones Colombia"**:
   - **Régimen Tributario**: Ordinario, Simple or No Contribuyente
   - **Tipo de Persona**: Natural or Jurídica
   - **Gran Contribuyente**: If applicable
   - **Autorretenedor**: If applicable

Usage
=====

**Calculate Withholdings on Invoices**

1. Create an invoice (supplier or customer)
2. Add product/service lines
3. Click the **"Calcular Retenciones"** button in the top bar
4. The system will automatically calculate applicable withholdings based on:
   - Company configuration (withholding agent + default withholdings)
   - Partner regime (Simple doesn't apply RteFte, No Contribuyente doesn't apply any)
   - Partner type
   - Minimum base amounts in UVT

**Fiscal Positions**

The module includes pre-configured fiscal positions with account mappings:

- **Régimen Simple (Sin ReteFte)**: Removes income tax withholdings (RteFte)
  but keeps ReteIVA and ReteICA. Maps liability accounts (236xxx) to asset
  accounts (135xxx)
- **No Contribuyente (Sin Retenciones)**: Removes all withholdings (RteFte,
  ReteIVA, ReteICA). Maps liability accounts to asset accounts

Assign the corresponding fiscal position to the partner for automatic
withholding adjustments.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-colombia/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us to smash it by providing a detailed and welcomed
`feedback <https://github.com/OCA/l10n-colombia/issues/new?body=module:%20l10n_co_withholding%0Aversion:%2018.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
-------

* OCA

Maintainers
-----------

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

This module is part of the `OCA/l10n-colombia <https://github.com/OCA/l10n-colombia/tree/18.0/l10n_co_withholding>`_ project on GitHub.

You are welcome to contribute. To learn how please visit https://odoo-community.org/page/Contribute.
