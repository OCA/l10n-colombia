.. image:: https://odoo-community.org/readme-banner-image
   :target: https://odoo-community.org/get-involved?utm_source=readme
   :alt: Odoo Community Association

=====================================
Colombia - Nómina
=====================================

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/license-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-OCA%2Fl10n--colombia-lightgray.png?logo=github
    :target: https://github.com/OCA/l10n-colombia/tree/18.0/l10n_co_hr_payroll
    :alt: OCA/l10n-colombia
.. |badge4| image:: https://img.shields.io/badge/weblate-Translate%20me-F47D42.png
    :target: https://translation.odoo-community.org/projects/l10n-colombia-18-0/l10n-colombia-18-0-l10n_co_hr_payroll
    :alt: Translate me on Weblate
.. |badge5| image:: https://img.shields.io/badge/runboat-Try%20me-875A7B.png
    :target: https://runboat.odoo-community.org/builds?repo=OCA/l10n-colombia&target_branch=18.0
    :alt: Try me on Runboat

|badge1| |badge2| |badge3| |badge4| |badge5|

Liquidación de nómina para Colombia: salario, seguridad social, aportes
parafiscales y prestaciones sociales. Funciona sobre el motor de nómina de la
OCA (`payroll`) tanto en Odoo Community como en Odoo Enterprise.

**Table of contents**

.. contents::
   :local:

Installation
============

El módulo depende del motor de nómina de la OCA (`payroll`), el backport libre
del módulo `hr_payroll` de Odoo Enterprise.

**Odoo Community**

1. Instale el addon `payroll` de la OCA (ramas `18.0` de
   `OCA/payroll <https://github.com/OCA/payroll>`_).
2. Instale este módulo normalmente (*Aplicaciones → Nómina*).

**Odoo Enterprise**

En Enterprise no se puede cargar `hr_payroll` (módulo propietario) junto con
una localización que herede de él, porque Odoo no soporta dependencias
alternativas entre módulos. La solución soportada y estándar en OCA es:

1. Instale el addon `payroll` de la OCA como reemplazo (drop-in) de
   `hr_payroll`: usa los **mismos modelos** (`hr.payslip`, `hr.salary.rule`,
   `hr.payroll.structure`, etc.).
2. Desinstale (o no instale) `hr_payroll` de Enterprise para evitar conflictos
   de definición de modelos.
3. Instale este módulo.

Con `payroll` de la OCA como motor, esta localización se comporta igual en
Community y en Enterprise.

Configuration
=============

**Compañía (Ajustes → Nómina → bloque "Colombia (Nómina)")**

- **SMMLV**: Salario Mínimo Legal Mensual Vigente (por defecto 1.750.905 COP
  para 2026).
- **Auxilio de Transporte**: valor mensual (por defecto 249.095 COP para
  2026).
- **Exoneración de aportes de salud y parafiscales**: márquelo solo si
  **todos** los trabajadores de la empresa ganan menos de 10 SMMLV
  (art. 114-1 del E.T. / Ley 1819 de 2016). Exonera el 8,5% de salud del
  empleador, el SENA (2%) y el ICBF (3%). La Caja de Compensación y la
  pensión del empleador se siguen causando.
- **Porcentajes**: tasas aplicadas sobre el IBC (salud, pensión, parafiscales
  y provisiones). Se entregan con los valores legales; ajústelos solo si la
  norma cambia.

**Empleado (ficha → pestaña "Colombia (Nómina)")**

- **EPS**: Entidad Promotora de Salud.
- **Fondo de Pensiones (AFP)**: administradora de pensiones.

**Contrato (grupo Salario)**

- **Derecho a auxilio de transporte**: se activa por defecto; el sistema
  además verifica que el salario no supere 2 SMMLV.
- **Clase de riesgo ARL**: I a V; la tarifa se calcula automáticamente.
- **Estructura salarial**: debe ser la estructura mensual de Colombia
  (`Nómina Mensual Colombia`).

Usage
=====

**Generar la nómina**

1. En *Nómina → Nóminas de empleados* cree una tanda (batch) o un recibo de
   nómina individual con el periodo (mes completo).
2. El recibo toma la estructura y el contrato del empleado.
3. En la pestaña *Jornadas laborales e Inputs* registre los valores del mes:
   - **Horas Extras y Recargos** (código `EXTRAS`): valor ya liquidado de las
     horas extras y recargos (diurnas, nocturnas, dominicales o festivas
     según la Ley 2466 de 2025).
   - **Comisiones y Ventas** (código `COMMISSIONS`).
   - **Otros Devengados Salariales** (código `OTHER_SALARY`): bonificaciones
     salariales etc.
   - **Otras Deducciones** (código `OTHER_DEDUCTIONS`): libranzas, embargos.
4. Pulse **Compute Sheet** y luego **Confirm**.

El recibo muestra los totales colombianos en el bloque *Nómina Colombia*:
IBC, total devengado, total deducciones, neto a pagar y costo total para el
empleador.

**Imprimir el desprendible**

Pulse el botón de reporte **Desprendible de Nómina (Colombia)** en el recibo
para generar el PDF en español con el detalle del devengado, las deducciones,
el neto y el costo para el empleador.

Known issues / Roadmap
======================

- Retención en la fuente sobre salarios (ReteFuente trabajador).
- Cálculo automático de horas extras y recargos desde el horario y las
  asistencias.
- Periodos quincenales y proporcionalidad por días trabajados.
- Soporte para empleados con múltiples contratos y empleadores simultáneos.
- Contabilización automática de la nómina (asientos contables).

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-colombia/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us to smash it by providing a detailed and welcomed
`feedback <https://github.com/OCA/l10n-colombia/issues/new?body=module:%20l10n_co_hr_payroll%0Aversion:%2018.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
-------

* Juan Arcos

Contributors
------------

* Juan Arcos (juanparmer) <juancarlos.arcos@gmail.com>

Maintainers
-----------

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

This module is part of the `OCA/l10n-colombia <https://github.com/OCA/l10n-colombia/tree/18.0/l10n_co_hr_payroll>`_ project on GitHub.

You are welcome to contribute. To learn how please visit https://odoo-community.org/page/Contribute.