.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3

=================
Colombian Geodata
=================

This module extends the functionality of DevCO's Colombian Basic Accounting (l10n_co) to support colombian departments and municipalities with their corresponding official codes. It also aims to improve usability in adressfields and helps with disambiguation (ej. Armenia, Quindio vs. Armenia, Antioquia).It saves you the work of configuring colombian geo data manually.

Installation
============

To install this module, you need to:

* just install the module. Necessary additional modules are installed automatically.

Configuration
=============

To configure this module, you need to:

* do nothing, as we have built in sensible defaults.

Usage
=====

To use (test) this module, you need to:

#. go to your database management page and install an instance with demo data
#. play around with adress fields.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/195/10.0

For further information, please visit:

* `Professional Support (DevCO) <http://devco.co/>`_
* `Community Support (Colombian Odoo Community) <https://plus.google.com/communities/113251920989277948689>`_

Known issues / Roadmap
======================

* this module is considered production-ready and has no specific roadmap or improvement schedule.
* it might be planned to include ZIP codes, as they will be more widely adopted in colombia and open sourced by the MinTIC (Colombian Ministry of Information Technology, which is owner and copyright holder of the colombian ZIP Code Database)

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/odoo-colombia/l10n-colombia/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Images
------

* DevCO Colombia SAS: `Icon <https://github.com/odoo-colombia/l10n-colombia/blob/10.0/l10n_co_geo/static/description/icon.png>`_.

Contributors
------------

* David Arnold <dar@devco.co>
* Juan pablo Arias <jpa@devco.co>


Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
